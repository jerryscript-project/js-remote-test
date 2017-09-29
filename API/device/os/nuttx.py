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

from API.common import paths, utils


class OperatingSystem(base.OperatingSystemBase):
    '''
    NuttX real-time operating system class.
    '''
    def __init__(self):
        super(self.__class__, self).__init__('nuttx')

    def apply_pacthes(self):
        # Note: since not the latest master is used, we should apply
        # some fixes for the NuttX.
        patch = utils.join(paths.PATCHES_PATH, 'nuttx-7.19.diff')
        utils.execute(paths.NUTTX_PATH, 'git', ['reset', '--hard'])
        utils.execute(paths.NUTTX_PATH, 'git', ['apply', patch])

    def get_home_dir(self):
        '''
        Return the path to the operating system.
        '''
        return paths.NUTTX_PATH

    def get_image(self):
        '''
        Return the path to the operating system.
        '''
        return utils.join(paths.NUTTX_PATH, 'nuttx.bin')

    def copy_app_files(self, app):
        '''
        Copy application files into the NuttX apps.
        '''
        utils.copy_files(app.get_home_dir(), app.get_install_dir())

        # Override the default romfs image file.
        utils.copy_file(app.get_romfs_file(), utils.join(paths.NUTTX_APPS_NSHLIB_PATH, 'nsh_romfsimg.h'))

    def configure(self, app):
        '''
        Configuring NuttX.
        '''
        utils.execute(paths.NUTTX_TOOLS_PATH, './configure.sh', ['stm32f4discovery/netnsh'])

        # Override the default config file with a prepared one.
        utils.copy_file(app.get_config_file(), utils.join(paths.NUTTX_PATH, '.config'))

    def prebuild(self, app, buildtype='release'):
        self.apply_pacthes()
        self.copy_app_files(app)
        self.configure(app)
        '''
        Pre-build the operating system (for the generated headers).
        '''
        self.build(app, buildtype, 'clean')
        self.build(app, buildtype, 'context')

    def build(self, app, buildtype, maketarget):
        '''
        Build the operating system.
        '''
        if buildtype == 'release':
            utils.define_environment('R', '1')
        else:
            utils.define_environment('R', '0')

        utils.define_environment('IOTJS_ROOT_DIR', paths.IOTJS_PATH)

        utils.execute(paths.NUTTX_PATH, 'make', ['-j1', maketarget])
