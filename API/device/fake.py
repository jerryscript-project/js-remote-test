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

import base


class Device(base.DeviceBase):
    '''
    Fake device class. (Only for testing the testrunner.)
    '''
    def __init__(self):
        super(self.__class__, self).__init__('fake')

    def install_dependencies(self):
        '''
        Install dependencies of the board.
        '''
        pass

    def flash(self, os):
        '''
        Flash the given operating system to the board.
        '''
        pass

    def execute(self, cmd, args=[]):
        '''
        Run the given command on the board.
        '''
        return 0, '', 0
