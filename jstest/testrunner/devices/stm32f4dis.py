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

from jstest.common import console, utils
from jstest.testrunner.devices.device_base import RemoteDevice
from jstest.testrunner.devices.connections.serialcom import SerialConnection

class STM32F4Device(RemoteDevice):
    '''
    Device of the STM32F4-Discovery target.
    '''
    def __init__(self, env):
        self.os = 'nuttx'
        self.stlink = env['modules']['stlink']

        RemoteDevice.__init__(self, env)

        data = {
            'dev-id': env['info']['device_id'],
            'baud': env['info']['baud'],
            'timeout': env['info']['timeout'],
            'prompt': 'nsh> '
        }

        self.channel = SerialConnection(data)

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

    def execute(self, testset, test):
        '''
        Execute the given test.
        '''
        self.reset()
        self.login()

        # Absolute path to the test file on the device.
        testfile = '/test/%s/%s' % (testset, test['name'])

        args = []
        if not self.env['info']['no_memstat']:
            args = ['--mem-stats']

        command = {
            'iotjs': 'iotjs %s %s' % (' '.join(args), testfile),
            'jerryscript': 'jerry %s %s' % (testfile, ' '.join(args))
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
