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

from jstest.common import utils
from jstest.testrunner.devices.ssh_device import SSHDevice

class RPi2Device(SSHDevice):
    '''
    Device of the Raspberry Pi 2 target.
    '''
    def __init__(self, env):
        SSHDevice.__init__(self, env, 'linux')

    def initialize(self):
        '''
        Flash the device.
        '''
        if not self.env.options.no_memstat:
            # Resolve the iotjs-dirname macro in the Freya configuration file.
            basename = utils.basename(self.env.modules.app['src'])

            sed_flags = ['-i', 's/%%{iotjs-dirname}/%s/g' % basename, 'iotjs-freya.config']
            utils.execute(self.env.paths.builddir, 'sed', sed_flags)

        # 2. Deploy the build folder to the device.
        self._deploy_to_device()
