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
import os


class OperatingSystem(base.OperatingSystemBase):
    '''
    Dummy operating system for devices who does not require OS.
    '''
    def __init__(self, app):
        super(self.__class__, self).__init__('dummy', app)

    def get_home_dir(self):
        '''
        Return the path to the operating system.
        '''
        return 'dummy'

    def get_image(self):
        '''
        Return the path to the target application.
        '''
        return self.app.get_image()

    def prebuild(self, buildtype='release'):
        '''
        Configure NuttX to netnsh and create the first build.
        '''
        pass

    def build(self, buildtype, maketarget):
        '''
        Build the operating system.
        '''
        pass