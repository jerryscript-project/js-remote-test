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

from API.common import console, paths, utils
from API.testrunner.devices.connections.serialcom import SerialConnection
from threading import Thread

class ARTIK053Device(object):
    '''
    Device of the ARTIK053 target.
    '''
    def __init__(self, env):
        self.os = 'tizenrt'
        self.app = env['info']['app']
        self.tizenrt = env['modules']['tizenrt']
        self.env = env

        # Check the members before testing.
        self.check_args()

        data = {
            'dev-id': env['info']['device_id'],
            'baud': env['info']['baud'],
            'timeout': env['info']['timeout'],
            'prompt': 'TASH>>'
        }

        self.channel = SerialConnection(data)

    def check_args(self):
        '''
        Check that all the arguments are established.
        '''
        if not self.env['info']['device_id']:
            console.fail('Please use the --device-id to select the device.')

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
        flags = ['download', 'reset']

        utils.execute(self.tizenrt['paths']['os'], 'make', flags, quiet=True)
        # Wait a moment to boot the device.
        time.sleep(2)

    def login(self):
        '''
        Login to the device.
        '''
        try:
            self.channel.open()

            # Press enters to start the serial communication and
            # go to the test folder because some tests require resources.
            self.channel.exec_command('\n\n')
            self.channel.exec_command('cd /rom')

            if self.env['info']['coverage'] and self.app == 'iotjs':
                # Set up the wifi connection.
                wifi_name = utils.get_environment('ARTIK_COV_WIFI_NAME')
                wifi_pwd =  utils.get_environment('ARTIK_COV_WIFI_PWD')

                self.channel.exec_command('wifi startsta')
                self.channel.exec_command('wifi join %s %s' % (wifi_name, wifi_pwd))
                self.channel.exec_command('ifconfig wl1 dhcp')
                time.sleep(1)

        except Exception as e:
            console.fail(str(e))

    def logout(self):
        '''
        Logout from the device.
        '''
        self.channel.close()

    def execute(self, testset, test):
        '''
        Execute the given test.
        '''
        self.reset()
        self.login()

        # Absolute path to the test file on the device.
        testfile = '/rom/%s/%s' % (testset, test['name'])

        args = []
        if not self.env['info']['no_memstat']:
            args = ['--mem-stats']

        if self.env['info']['coverage']:
            args.append('--start-debug-server')
            port = utils.read_port_from_url(self.env['info']['coverage'])
            args.append('--debug-port %s' % port)

        command = {
            'iotjs': 'iotjs %s %s\n' % (' '.join(args), testfile),
            'jerryscript': 'jerry %s %s\n' % (testfile, ' '.join(args))
        }

        # Run the test on the device.
        self.channel.putc(command[self.app])
        self.channel.readline()

        if self.env['info']['coverage'] and self.app == 'iotjs':
            # Start the client script on a different thread for coverage.
            client_thread = Thread(target=utils.run_coverage_script, kwargs={'env': self.env})
            client_thread.daemon = True
            client_thread.start()

        message, output = self.channel.read_until('arm_dataabort', 'TASH>>')

        if message == 'arm_dataabort':
            output += self.channel.readline().replace('\r\n', '')

        stdout, memstat, exitcode = utils.process_output(output)

        self.logout()

        return {
            'output': stdout.rstrip('\r\n').replace('\r\n', '<br>'),
            'memstat': memstat,
            'exitcode': exitcode
        }
