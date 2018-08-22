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

import time
from threading import Thread

from jstest.common import console, utils
from jstest.testrunner import utils as testrunner_utils
from jstest.testrunner.devices.serial_device import SerialDevice

class ARTIK053Device(SerialDevice):
    '''
    Device of the ARTIK053 target.
    '''
    def __init__(self, env):
        self.tizenrt = env['modules']['tizenrt']

        SerialDevice.__init__(self, env, 'tizenrt', 'TASH>>')

    def initialize(self):
        '''
        Flash the device.
        '''
        if self.env['info']['no_flash']:
            return

        tizenrt = self.env['modules']['tizenrt']
        utils.execute(tizenrt['paths']['os'], 'make', ['download', 'ALL'])

    def reset(self):
        '''
        Reset the device to create clean environment.
        '''
        if self.env['info']['emulate']:
            return

        flags = ['download', 'reset']

        utils.execute(self.tizenrt['paths']['os'], 'make', flags, quiet=True)
        # Wait a moment to boot the device.
        time.sleep(2)

    def execute(self, testset, test):
        '''
        Execute the given test.
        '''
        self.reset()
        self.login()

        command = self._prepare_command(testset, test)
        # Run the test on the device.
        self.channel.putc(command[self.app])
        self.channel.readline()

        if self.env['info']['coverage'] and self.app == 'iotjs':
            # Start the client script on a different thread for coverage.
            client_thread = Thread(target=testrunner_utils.run_coverage_script,
                                   kwargs={'env': self.env})
            client_thread.daemon = True
            client_thread.start()

        message, output = self.channel.read_until('arm_dataabort', 'TASH>>')

        if message == 'arm_dataabort':
            output += self.channel.readline().replace('\r\n', '')

        stdout, memstat, exitcode = testrunner_utils.process_output(output)

        self.logout()

        return {
            'output': stdout.rstrip('\r\n').replace('\r\n', '<br>'),
            'memstat': memstat,
            'exitcode': exitcode
        }

    def login(self):
        '''
        Login to the device.
        '''
        SerialDevice.login(self)

        # The JerryScript testsuite does not require Internet connection.
        if self.app == 'jerryscript':
            return

        try:
            # Set up the wifi connection.
            wifi_name = utils.get_environment('ARTIK_WIFI_NAME')
            wifi_pwd = utils.get_environment('ARTIK_WIFI_PWD')

            self.channel.exec_command('wifi startsta')
            self.channel.exec_command('wifi join %s %s' % (wifi_name, wifi_pwd))
            self.channel.exec_command('ifconfig wl1 dhcp')

            # Set the current date and time on the device.
            # Note: test_tls_ca.js requires the current datetime.
            datetime = utils.current_date('%b %d %H:%M:%S %Y')
            self.channel.exec_command('date -s %s' % datetime)
            time.sleep(1)

        except Exception as e:
            console.fail(str(e))
