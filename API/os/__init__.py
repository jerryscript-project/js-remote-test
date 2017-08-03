# Copyright 2017-present Samsung Electronics Co., Ltd. and other contributors
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import dummy
import nuttx


OPERATING_SYSTEMS = {
    'dummy': dummy.OperatingSystem,
    'nuttx': nuttx.OperatingSystem
}


def create(os, device, app):
    '''
    Create the given operating system.
    '''
    if device.get_type() in ['rpi2']:
        os_class = OPERATING_SYSTEMS['dummy']
    else:
        os_class = OPERATING_SYSTEMS[os]

    return os_class(app)
