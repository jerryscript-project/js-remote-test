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
    TizenRT real-time operating system class.
    '''
    def __init__(self):
        super(self.__class__, self).__init__('tizenrt')

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

    def __update_repository(self):
        '''
        Update the repository.
        '''
        utils.execute(paths.TIZENRT_PATH, 'git', ['clean', '-dxf'])
        utils.execute(paths.TIZENRT_PATH, 'git', ['reset', '--hard'])
        utils.execute(paths.TIZENRT_PATH, 'git', ['pull'])

    def __apply_patches(self, app):
        '''
        Apply patch file.
        '''
        patch = utils.join(paths.PATCHES_PATH, 'tizenrt-%s.diff' % app.get_name())
        utils.execute(paths.TIZENRT_PATH, 'git', ['apply', patch])

    def __configure(self, app):
        '''
        Configuring TizenRT.
        '''

        # FIXME: now it supports artik053 device only
        configure_name = utils.join('artik053', app.get_name())
        utils.execute(paths.TIZENRT_TOOLS_PATH, './configure.sh', [configure_name])

    def __copy_app_files(self, app):
        '''
        Copy application files into the NuttX apps.
        '''
        app_name = app.get_name()
        if app_name == 'jerryscript':
            # FIXME: now it supports artik053 device only
            app_config_dir = utils.join(paths.JERRY_TARGETS_PATH,
                                    '%s-%s' % (self.get_name(), 'artik053'))

            app_path = utils.join(app_config_dir, 'apps/jerryscript/')
            app_config_path = utils.join(app_config_dir, 'configs/jerryscript/')

            tizenrt_app_path = utils.join(paths.TIZENRT_APP_SYSTEM_PATH, app_name)
            utils.copy_files(app_path, tizenrt_app_path)
            rt_config_path = utils.join(paths.TIZENRT_CONFIGS_PATH, 'artik053', app_name)
            utils.copy_files(app_config_path, rt_config_path)

    def __copy_test_files(self, app):
        '''
        Copy sample files into the NuttX apps.
        '''
        if utils.exists(paths.TIZENRT_ROMFS_CONTENTS_PATH):
            utils.execute(paths.TIZENRT_FS_PATH, 'rm', ['-rf', 'contents'])

        utils.execute(paths.ROOT_FOLDER, 'cp',
                      [app.get_test_dir(), paths.TIZENRT_ROMFS_CONTENTS_PATH, '-r'])

    def prebuild(self, app, buildtype='release'):
        self.__update_repository()
        self.__copy_app_files(app)
        self.__apply_patches(app)
        self.__configure(app)
        self.__copy_test_files(app)

        utils.execute(paths.TIZENRT_OS_PATH, 'make', ['clean'])

    def build(self, app, buildtype, maketarget):
        '''
        Build the operating system.
        '''
        app_name = app.get_name()
        if app_name == 'iotjs':
            # TODO: Support release build
            build_options = ['IOTJS_ROOT_DIR=' + paths.IOTJS_PATH]
            build_options.append('IOTJS_BUILD_OPTION=' +
                                 '--clean ' +
                                 '--jerry-memstat ' +
                                 '--profile=%s' % utils.join(paths.IOTJS_TEST_PROFILES_PATH,
                                                             'tizenrt.profile'))

            utils.execute(paths.TIZENRT_OS_PATH, 'make', build_options)
        elif app_name == 'jerryscript':
            utils.execute(paths.TIZENRT_OS_PATH, 'make')
