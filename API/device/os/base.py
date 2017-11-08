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


class OperatingSystemBase(object):
    '''
    Base class to define an interface for the operating systems.
    '''
    def __init__(self, name):
        self.name = name

    def get_name(self):
        '''
        Return the name of the operating system.
        '''
        return self.name

    def get_image(self):
        '''
        Return the path to the OS binary image.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def get_home_dir(self):
        '''
        Return the path to the operating system.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def prebuild(self, app, device=None, buildtype='release'):
        '''
        Pre-build the operating system (for the generated headers).
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def build(self, app, buildtype, buildoptions, maketarget):
        '''
        Build the operating system.
        '''
        raise NotImplementedError('Use the concrete subclasses.')
