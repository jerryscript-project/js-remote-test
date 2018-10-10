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

from jstest.testrunner.devices.ssh_device import SSHDevice

class ARTIK530Device(SSHDevice):
    '''
    Device of the ARTIK530 target.
    '''
    def __init__(self, env):
        # Note: the PS1 prompt on the device has to have this ending.
        SSHDevice.__init__(self, env, 'tizen', ':~>')
