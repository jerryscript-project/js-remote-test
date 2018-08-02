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

import time

from jstest.common import console, utils, paths
from jstest.testrunner.devices.ssh_device import SSHDevice

class ARTIK530Device(SSHDevice):
    '''
    Device of the ARTIK530 target.
    '''
    def __init__(self, env):
        SSHDevice.__init__(self, env, 'tizen')

    def initialize(self):
        '''
        Flash the device.
        '''
        # 1. Call initialize from the super class to copy necessary files.
        SSHDevice.initialize(self)

        if not self.env['info']['no_memstat']:
            utils.copy(paths.FREYA_CONFIG, self._build_path)

            # Resolve the iotjs-dirname macro in the Freya configuration file.
            basename = utils.basename(paths.GBS_IOTJS_PATH)
            sed_flags = ['-i', 's/%%{iotjs-dirname}/%s/g' % basename, 'iotjs-freya.config']
            utils.execute(self._build_path, 'sed', sed_flags)

        # 2. Deploy the build folder to the device.
        self.login()
        self.channel.exec_command('mount -o remount,rw /')

        self._deploy_to_device()

        # 3. Install rpm package
        template = 'rpm -ivh --force --nodeps %s/%s-1.0.0-0.armv7l.rpm'
        self.channel.exec_command(template % (self.workdir, self.app))

        self.logout()

    def login(self):
        '''
        Login to the device.
        '''
        SSHDevice.login(self)

        if self.app != 'iotjs':
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
