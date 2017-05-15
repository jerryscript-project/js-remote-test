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

from ..common import utils

class DeviceBase(object):
    '''
    Base class to define an interface for the devices.
    '''
    def __init__(self, devtype):
        self.devtype = devtype
        self.address = '0.0.0.0'
        self.timeout = 0
        self.username = 'pi'
        self.root_path = '/'

        self.install_dependencies()

    def set_address(self, address):
        '''
        Set the IP address of the board.
        '''
        self.address = address

    def set_username(self, username):
        '''
        Set the username to login.
        '''
        self.username = username

    def set_root_path(self, path):
        '''
        Set the root path where testing environment is located.
        '''
        self.root_path = path

    def set_timeout(self, timeout):
        '''
        Set the maximum time to wait to the board.
        '''
        self.timeout = timeout

    def get_type(self):
        '''
        Return the type of the board.
        '''
        return self.devtype

    def get_test_path(self):
        '''
        Return the test path on the device.
        '''
        return utils.join(self.root_path, 'test')

    def install_dependencies(self):
        '''
        Install dependencies of the board.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def flash(self, os):
        '''
        Flash the given operating system to the board.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def execute(self, cmd, args=[]):
        '''
        Run the given command on the board.
        '''
        raise NotImplementedError('Use the concrete subclasses.')
