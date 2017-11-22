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
    Artik053 device class. (Only for testing the testrunner.)
    '''
    def __init__(self, options):
        super(self.__class__, self).__init__('artik053', remote_path='/')
        self.serial = connection.serialcom.Connection(options, 'TASH>>')
        self.platform = utils.get_system().lower() + utils.get_architecture()

    def init_os(self):
        '''
        Initialize the used OS.
        '''
        return os.tizenrt.OperatingSystem()

    def install_dependencies(self):
        '''
        Install dependencies of the board.
        '''
        pass

    def get_test_path(self):
        '''
        Return the test path on the device.
        '''
        return '/rom'

    def flash(self, app):
        '''
        Flash the given operating system to the board.
        '''
        utils.execute(paths.TIZENRT_OS_PATH, 'make', ['download', 'ALL'])

    def reset(self):
        '''
        Reset the board.
        '''
        utils.execute(paths.TIZENRT_OS_PATH, 'make', ['download', 'reset'], quiet=True)

        # Wait a moment to boot the device.
        time.sleep(2)

    def login(self):
        '''
        Create connection.
        '''
        try:
            self.serial.open()

            # Press enters to start the serial communication and
            # go to the test folder because some tests require resources.
            self.serial.exec_command('\n\n')
            self.serial.exec_command('cd /rom')

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
        cmd_stack = app.get_cmd_stack()

        self.reset()
        self.login()

        # Send testrunner command to the device and process its result.
        self.serial.putc('%s %s\n' % (cmd, ' '.join(args).encode('utf8')))
        self.serial.readline()
        message, stdout = self.serial.read_until(self.serial.get_prompt(), 'arm_dataabort')

        exitcode = 1
        if message == self.serial.get_prompt():
            # Find the test result from stdout.
            match = re.search('IoT.js Result: (\d+)', stdout)
            if match:
                exitcode = match.group(1)
            else:
                exitcode = 1
        else:
            stdout += self.serial.readline().replace('\n', '')

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

        return {
            'exitcode': exitcode,
            'output': stdout,
            'jerry_peak_alloc': jerry_peak_alloc,
            'malloc_peak': malloc_peak,
            'stack_peak': stack_peak
        }
