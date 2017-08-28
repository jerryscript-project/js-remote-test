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

import rpi2
import stm32f4dis
import artik053


DEVICES = {
    'rpi2': rpi2.Device,
    'stm32f4dis': stm32f4dis.Device,
    'artik053': artik053.Device
}


def create(options):
    '''
    Create a device to the given type.
    '''
    device_class = DEVICES[options.device]

    return device_class(options)
