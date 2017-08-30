# Copyright 2017-present Samsung Electronics Co., Ltd. and other contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base
import connection
import re
import time

from API.common import console, paths, utils


class Device(base.DeviceBase):
    '''
    Device class for the stm32f4-discovery board.
    '''
    def __init__(self, options):
        super(self.__class__, self).__init__('stm32f4dis', remote_path='/')

        self.serial = connection.serialcom.Connection(options, prompt='nsh> ')

    def install_dependencies(self):
        '''
        Install dependencies of the board.
        '''
        if utils.exists(utils.join(paths.STLINK_BUILD_PATH, 'st-flash')):
            return

        utils.execute(paths.STLINK_PATH, 'make', ['release'])

    def flash(self, os):
        '''
        Flash the given operating system to the board.
        '''
        options = ['write', os.get_image(), '0x8000000']

        utils.execute(paths.STLINK_BUILD_PATH, './st-flash', options)

    def reset(self):
        '''
        Reset the board.
        '''
        utils.execute(paths.STLINK_BUILD_PATH, './st-flash', ['reset'], quiet=True)

        # Wait a moment to boot the device.
        time.sleep(5)

    def login(self):
        '''
        Create connection.
        '''
        try:
            self.serial.open()

            # Press enters to start the serial communication and
            # go to the test folder because some tests require resources.
            self.serial.exec_command('\n\n')
            self.serial.exec_command('cd test')

        except Exception as e:
            console.fail(str(e))

    def logout(self):
        '''
        Close connection.
        '''
        self.serial.close()

    def execute(self, cmd, args=[]):
        '''
        Run the given command on the board.
        '''
        self.reset()
        self.login()

        # Send testrunner command to the device and process its result.
        stdout = self.serial.exec_command('%s %s' % (cmd, ' '.join(args).encode('utf8')))

        if stdout.rfind('Heap stat') != -1:
            stdout, heap = stdout.rsplit("Heap stats",1)

            match = re.search(r'Peak allocated = (\d+) bytes', str(heap))

            if match:
                memory = match.group(1)
            else:
                memory = 'n/a'
        else:
            memory = 'n/a'

        # Process the exitcode of the last command.
        exitcode = self.serial.exec_command('echo $?')

        self.logout()

        # Make HTML friendly stdout.
        stdout = stdout.replace('\n', '<br>')

        return exitcode, stdout, memory
