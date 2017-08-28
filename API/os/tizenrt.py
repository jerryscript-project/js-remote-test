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

from ..common import utils
from ..common import paths


class OperatingSystem(base.OperatingSystemBase):
    '''
    TizenRT real-time operating system class.
    '''
    def __init__(self, app):
        super(self.__class__, self).__init__('tizenrt', app)

        self.update_repository()
        self.copy_app_files(app)
        self.apply_patches()
        self.configure(app)
        self.copy_test_files(app)

    def get_home_dir(self):
        '''
        Return the path to the operating system.
        '''
        return paths.TIZENRT_PATH

    def get_image(self):
        '''
        Return the path to the target application.
        '''
        return utils.join(paths.TIZENRT_BIN_PATH, 'tinyara.bin')

    def update_repository(self):
        '''
        Update the repository.
        '''
        utils.execute(paths.TIZENRT_PATH, 'git', ['clean', '-dxf'])
        utils.execute(paths.TIZENRT_PATH, 'git', ['reset', '--hard'])
        utils.execute(paths.TIZENRT_PATH, 'git', ['pull'])

    def apply_patches(self):
        '''
        Apply patch file.
        '''
        patch = utils.join(paths.PATCHES_PATH, 'tizenrt.diff')
        utils.execute(paths.TIZENRT_PATH, 'git', ['apply', patch])

    def configure(self, app):
        '''
        Configuring TizenRT.
        '''
        configure_name = utils.join(app.get_device().get_type(), app.get_name())
        utils.execute(paths.TIZENRT_TOOLS_PATH, './configure.sh', [configure_name])

    def prebuild(self, buildtype='release'):
        '''
        Configure NuttX to netnsh and create the first build.
        '''
        utils.execute(paths.TIZENRT_OS_PATH, 'make', ['context'])

    def copy_app_files(self, app):
        '''
        Copy application files into the NuttX apps.
        '''
        app_path = utils.join(app.get_config_dir(), 'app/')
        tizenrt_app_path = utils.join(paths.TIZENRT_APP_SYSTEM_PATH, app.get_name())
        utils.copy_files(app_path, tizenrt_app_path)

        app_config_path = utils.join(app.get_config_dir(), 'configs/')
        rt_config_path = utils.join(paths.TIZENRT_CONFIGS_PATH,
            app.get_device().get_type(), app.get_name())
        utils.copy_files(app_config_path, rt_config_path)

    def copy_test_files(self, app):
        '''
        Copy sample files into the NuttX apps.
        '''
        res_path = utils.join(paths.TIZENRT_BUILD_OUTPUT_PATH, 'res')
        if utils.exists(res_path):
            utils.execute(paths.TIZENRT_BUILD_OUTPUT_PATH, 'rm', ['-rf', 'res'])
        utils.execute(paths.TIZENRT_BUILD_OUTPUT_PATH, 'mkdir', ['res'])

        utils.execute(paths.ROOT_FOLDER, 'cp', [app.get_test_dir(), res_path, '-r'])

    def apply_app_patches(self, app):
        '''
        Apply app patch file.
        '''
        app_patch = utils.join(paths.PATCHES_PATH, '%s-tizenrt.diff' % app.get_name())
        utils.execute(paths.IOTJS_PATH, 'git', ['apply', app_patch])

    def build(self, buildtype, maketarget):
        '''
        Build the operating system.
        '''
        lib_path = ''
        app_name = self.app.get_name()
        if app_name == 'iotjs':
            lib_path = 'IOTJS_LIB_DIR=' + paths.IOTJS_TIZENRT_BUILD_PATH % buildtype

        utils.execute(paths.TIZENRT_OS_PATH, 'make', [lib_path])
        utils.execute(paths.TIZENRT_OS_PATH, 'genromfs', ['-f', '../build/output/bin/rom.img',
            '-d', '../build/output/res/', '-V', "NuttXBootVol"])
