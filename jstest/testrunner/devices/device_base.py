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

import json
import time

from jstest.common import console, utils

class RemoteDevice(object):
    '''
    Base class of all the device classes.
    '''
    def __init__(self, env):
        self.app = env['info']['app']
        self.user = env['info']['username']
        self.ip = env['info']['ip']
        self.port = env['info']['port']
        self.device = env['info']['device']
        self.env = env

        self.workdir = None
        self.channel = None

        self.check_args()

    def check_args(self):
        '''
        Check that all the arguments are established.
        '''
        if self.device in ['rpi2', 'artik530']:
            if not self.workdir:
                console.fail('Please use --remote-workdir for the device.')
            if not self.ip:
                console.fail('Please define the IP address of the device.')
            if not self.user:
                console.fail('Please define the username of the device.')

            if self.workdir is '/':
                console.fail('Please do not use the root folder as test folder.')

        elif self.device in ['artik053', 'stm32f4dis']:
            if not self.env['info']['device_id']:
                console.fail('Please use the --device-id to select the device.')

        else:
            console.fail('The selected device is not supported')

    def login(self):
        '''
        Login to the device.
        '''
        try:
            self.channel.open()

            if self.device in ['artik053', 'stm32f4dis']:
                # Press enters to start the serial communication and
                # go to the test folder because some tests require resources.
                self.channel.exec_command('\n\n')
                self.channel.exec_command('cd /test')

                if self.device == 'artik053' and self.app == 'iotjs':
                    # Set up the wifi connection.
                    wifi_name = utils.get_environment('ARTIK_WIFI_NAME')
                    wifi_pwd =  utils.get_environment('ARTIK_WIFI_PWD')

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

    def logout(self):
        '''
        Logout from the device.
        '''
        self.channel.close()

    def iotjs_build_info(self):
        '''
        Get buildinfo from iotjs.
        '''
        if self.device in ['rpi2', 'artik530']:
            iotjs = '%s/iotjs' % self.workdir
            buildinfo = '%s/tests/tools/iotjs_build_info.js' % self.workdir
            command = '%s %s' % (iotjs, buildinfo)

        elif self.device in ['artik053', 'stm32f4dis']:
            buildinfo = '/test/tools/iotjs_build_info.js'
            command = 'iotjs %s' % buildinfo

        # Wait a moment to boot the device.
        time.sleep(2)

        self.login()

        output = self.channel.exec_command(command)
        # Process the output to get the json string and the exitcode.
        build_info, _, exitcode = utils.process_output(output)

        if exitcode != 0:
            console.fail('%s returned with exitcode %d' % (buildinfo, exitcode))

        info = json.loads(build_info)

        builtins = set(info['builtins'])
        features = set(info['features'])
        stability = info['stability']

        self.logout()

        return builtins, features, stability
