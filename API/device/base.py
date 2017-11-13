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

from API.common import utils

class DeviceBase(object):
    '''
    Base class to define an interface for the devices.
    '''
    def __init__(self, device_type, remote_path):
        self.devtype = device_type
        self.remote_path = remote_path
        self.install_dependencies()
        self.os = self.init_os();

    def get_os(self):
        '''
        Return the os.
        '''
        return self.os

    def get_type(self):
        '''
        Return the type of the board.
        '''
        return self.devtype

    def get_test_path(self):
        '''
        Return the test path on the device.
        '''
        return utils.join(self.remote_path, 'test')

    def init_os(self):
        '''
        Initialize the used OS.
        '''
        raise NotImplementedError('Use the concrete subclasses.')


    def install_dependencies(self):
        '''
        Install dependencies of the board.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def flash(self, app):
        '''
        Flash the given operating system to the board.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def execute(self, app, args=[]):
        '''
        Run commands of the given command on the board.
        '''
        raise NotImplementedError('Use the concrete subclasses.')
