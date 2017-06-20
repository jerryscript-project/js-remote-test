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

import re
import signal
import telnetlib
import time

from ..common import utils
from ..common import paths
from ..common import console


def alarm_handler(signum, frame):
    '''
    Throw exception when alarm happens.
    '''
    raise utils.TimeoutException


class Device(base.DeviceBase):
    '''
    Device class for the stm32f4-discovery board.
    '''
    def __init__(self):
        super(self.__class__, self).__init__('stm32f4dis')

        self.telnet = telnetlib.Telnet()

        signal.signal(signal.SIGALRM, alarm_handler)

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

    def logout(self):
        '''
        Close connection.
        '''
        self.telnet.close()

    def login(self):
        '''
        Create connection.
        '''
        try:
            self.telnet.open(self.address)
            self.telnet.read_until('nsh> ')

        except Exception as e:
            console.fail(str(e))

    def send_command(self, cmd):
        '''
        Send command to the device and set a timeout.
        '''
        self.telnet.write('%s\n' % cmd)

    def read_data(self):
        '''
        Waiting for the prompt and removing that characters from the output.
        '''
        signal.alarm(self.timeout)

        stdout = self.telnet.read_until('nsh> ')

        signal.alarm(0)

        stdout = re.sub('\n\rnsh> ', '', stdout)
        stdout = re.sub('nsh> ', '', stdout)

        return stdout

    def execute(self, cmd, args=[]):
        '''
        Run the given command on the board.
        '''
        self.reset()
        self.login()

        # Some IoT.js tests require to run tests from the test folder.
        self.send_command('cd test')
        self.read_data()

        # Send testrunner command to the device and process its result.
        self.send_command('%s %s' % (cmd, ' '.join(args).encode('utf8')))
        stdout = self.read_data()

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
        self.send_command('echo $?')
        exitcode = self.read_data()

        self.logout()

        # Make HTML friendly stdout.
        stdout = stdout.rstrip('\n\r').replace('\n\r', '<br>')

        return exitcode, stdout, memory
