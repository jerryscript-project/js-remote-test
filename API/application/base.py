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


class ApplicationBase(object):
    '''
    Base class to define an interface for the devices.
    '''
    def __init__(self, name, cmd, os_name, device):
        self.device = device
        self.name = name
        self.cmd = cmd
        self.os_name = os_name

    def get_name(self):
        '''
        Return the name of the application.
        '''
        return self.name

    def get_cmd(self):
        '''
        Return the command to run the application.
        '''
        return self.cmd

    def get_device(self):
        '''
        Return the device.
        '''
        return self.device

    def get_section_sizes(self):
        '''
        Returns the sizes of the main sections.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def get_image(self):
        '''
        Return the path to the binary.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def get_home_dir(self):
        '''
        Return the path to the application files.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def get_install_dir(self):
        '''
        Return the path where the application files should be copied.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def get_test_dir(self):
        '''
        Return the path to the application test files.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def get_config_file(self):
        '''
        Return the path to OS configuration file.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def get_romfs_file(self):
        '''
        Return the path of the generated ROMFS image.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def update_repository(self, branch, commit):
        '''
        Update the repository to the given branch and commit.
        '''
        raise NotImplementedError('Use the concrete subclasses.')

    def build(self, buildtype):
        '''
        Build the application.
        '''
        raise NotImplementedError('Use the concrete subclasses.')
