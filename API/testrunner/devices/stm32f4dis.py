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

from API.common import console, utils
from connections.serialcom import SerialConnection


class STM32F4Device(object):
    '''
    Device of the STM32F4-Discovery target.
    '''
    def __init__(self, env):
        self.os = 'nuttx'
        self.app = env['info']['app']
        self.stlink = env['modules']['stlink']
        self.env = env

        # Check the members before testing.
        self.check_args()

        data = {
            'port': env['info']['port'],
            'baud': env['info']['baud'],
            'timeout': env['info']['timeout'],
            'prompt': 'nsh> '
        }

        self.channel = SerialConnection(data)

    def check_args(self):
        '''
        Check that all the arguments are established.
        '''
        if not self.env['info']['port']:
            console.fail('Please use the --port to select the device.')

    def initialize(self):
        '''
        Flash the device.
        '''
        if self.env['info']['no_flash']:
            return

        stlink = self.env['modules']['stlink']
        nuttx = self.env['modules']['nuttx']

        flash_flags = ['write', nuttx['paths']['image'], '0x8000000']

        utils.execute(stlink['src'], 'build/Release/st-flash', flash_flags)

    def reset(self):
        '''
        Reset the device to create clean environment.
        '''
        flasher = self.stlink['paths']['st-flash']

        utils.execute('.', flasher, ['reset'], quiet=True)
        # Wait a moment to boot the device.
        time.sleep(5)

    def login(self):
        '''
        Login to the device.
        '''
        try:
            self.channel.open()

            # Press enters to start the serial communication and
            # go to the test folder because some tests require resources.
            self.channel.exec_command('\n\n')
            self.channel.exec_command('cd /test')

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
        testfile = '/test/%s/%s' % (testset, test['name'])

        command = {
            'iotjs': 'iotjs --memstat %s' % testfile,
            'jerryscript': 'jerry %s --mem-stats' % testfile
        }

        # Run the test on the device.
        output = self.channel.exec_command(command[self.app])

        stdout, memstat, _ = utils.process_output(output)
        # Process the exitcode of the last command.
        exitcode = self.channel.exec_command('echo $?')

        self.logout()

        return {
            'output': stdout.rstrip('\n').replace('\n', '<br>'),
            'memstat': memstat,
            'exitcode': exitcode
        }
