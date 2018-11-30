# Copyright 2018-present Samsung Electronics Co., Ltd. and other contributors
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

from jstest.common import console
from jstest.testrunner import utils as testrunner_utils
from jstest.testrunner.devices.device_base import RemoteDevice
from jstest.testrunner.devices.connections.serialcom import SerialConnection
from jstest.testrunner.devices.connections.telnetcom import TelnetConnection

class SerialDevice(RemoteDevice):
    '''
    Common super class for serial devices.
    '''
    def __init__(self, env, os, prompt):
        RemoteDevice.__init__(self, env, os)

        data = {
            'timeout': env.options.timeout,
            'prompt': prompt
        }

        if env.options.ip:
            # FIXME: In this case there is no need for serial connection.
            # So, the SerialDevice is a misleading class name for STM32F4-DISCOVERY
            data['ip'] = env.options.ip
            self.channel = TelnetConnection(data)
        else:
            data['dev-id'] = env.options.device_id
            data['baud'] = env.options.baud
            self.channel = SerialConnection(data)

    def check_args(self):
        '''
        Check that all the arguments are established.
        '''
        if not self.env.options.device_id:
            console.fail('Please use the --device-id to select the device.')

    def reset(self):
        '''
        Dummy method.
        '''
        pass

    def login(self):
        '''
        Login to the device.
        '''
        try:
            self.channel.open()
            self.channel.exec_command('cd /test')

        except Exception as e:
            console.fail(str(e))

    def _prepare_command(self, testset, test):
        '''
        Prepare the command which will be executed.
        '''
        # Absolute path to the test file on the device.
        testfile = '/test/%s/%s' % (testset, test['name'])

        args = []
        if not self.env.options.no_memstat:
            args = ['--mem-stats']

        if self.env.options.debugger and self.env.options.debugger != 'no_address':
            port = testrunner_utils.read_port_from_url(self.env.options.debugger)
            args.append('--start-debug-server')
            args.append('--debug-port')
            args.append('%s' % port)

        command = {
            'iotjs': 'iotjs %s %s' % (' '.join(args), testfile),
            'jerryscript': 'jerry %s %s' % (testfile, ' '.join(args))
        }

        return command
