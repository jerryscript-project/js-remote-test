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
import os
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

    def init_os(self):
        '''
        Initialize the used OS.
        '''
        return os.nuttx.OperatingSystem()

    def install_dependencies(self):
        '''
        Install dependencies of the board.
        '''
        if utils.exists(utils.join(paths.STLINK_BUILD_PATH, 'st-flash')):
            return

        utils.execute(paths.STLINK_PATH, 'make', ['release'])

    def flash(self, app):
        '''
        Flash the given operating system to the board.
        '''
        os = self.get_os()
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

    def execute(self, app, args=[]):
        '''
        Run commands for the given app on the board.
        '''
        cmd = app.get_cmd()

        self.reset()
        self.login()

        # Send testrunner command to the device and process its result.
        stdout = self.serial.exec_command('%s %s' % (cmd, ' '.join(args).encode('utf8')))

        jerry_peak_alloc = 'n/a'
        malloc_peak = 'n/a'
        stack_peak = 'n/a'

        if stdout.find('Heap stats:') != -1:
            # Process jerry-memstat output.
            match = re.search(r'Peak allocated = (\d+) bytes', str(stdout))

            if match:
                jerry_peak_alloc = int(match.group(1))

            # Process malloc peak output.
            match = re.search(r'Malloc peak allocated: (\d+) bytes', str(stdout))

            if match:
                malloc_peak = int(match.group(1))

            # Process stack usage output.
            match = re.search(r'Stack usage: (\d+)', str(stdout))

            if match:
                stack_peak = int(match.group(1))

            # Remove memstat from the output.
            stdout, _ = stdout.split("Heap stats:", 1)

        # Process the exitcode of the last command.
        exitcode = self.serial.exec_command('echo $?')

        self.logout()

        # Make HTML friendly stdout.
        stdout = stdout.replace('\n', '<br>')

        return {
            'exitcode': exitcode,
            'output': stdout,
            'jerry_peak_alloc': jerry_peak_alloc,
            'malloc_peak': malloc_peak,
            'stack_peak': stack_peak
        }
