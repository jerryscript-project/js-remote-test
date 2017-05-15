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


class Application(base.ApplicationBase):
    '''
    IoT.js application.
    '''
    def __init__(self, os_name, device):
        super(self.__class__, self).__init__('iotjs', 'iotjs', os_name, device)

    def get_image(self):
        '''
        Return the path to the binary.
        '''
        return utils.join(paths.IOTJS_BUILD_PATH, 'iotjs')

    def get_home_dir(self):
        '''
        Return the path to the application files.
        '''
        return paths.IOTJS_APPS_PATH

    def get_section_sizes(self):
        '''
        Returns the sizes of the main sections.
        '''
        iotjs_bin = utils.join(paths.IOTJS_MINIMAL_BIN_PATH, 'iotjs')
        utils.execute(paths.IOTJS_PATH, 'arm-linux-gnueabi-strip', [iotjs_bin])
        sections, exitcode = utils.execute(paths.IOTJS_PATH, 'arm-linux-gnueabi-size', ['-A', iotjs_bin], quiet=True)

        sizes = {}

        for line in sections.splitlines():
            for key in ['text', 'data', 'rodata', 'bss']:
                if '.%s' % key in line:
                    sizes[key] = line.split()[1]

        sizes['total'] = utils.size(iotjs_bin)

        return sizes

    def get_install_dir(self):
        '''
        Return the path to where the application files should be copied.
        '''
        return utils.join(paths.NUTTX_APPS_SYSTEM_PATH, 'iotjs')

    def get_test_dir(self):
        '''
        Return the path to the application test files.
        '''
        return paths.IOTJS_TEST_PATH

    def get_config_file(self):
        '''
        Return the path to OS configuration file.
        '''
        return utils.join(paths.CONFIG_PATH, 'iotjs.config')

    def get_romfs_file(self):
        '''
        Return the path of the generated ROMFS image.
        '''
        utils.generate_romfs(paths.IOTJS_PATH, paths.IOTJS_TEST_PATH)

        return utils.join(paths.IOTJS_PATH, 'nsh_romfsimg.h')

    def update_repository(self, branch, commit):
        '''
        Update the repository to the given branch and commit.
        '''
        utils.execute(paths.IOTJS_PATH, 'rm', ['-rf', 'deps'])

        utils.execute(paths.IOTJS_PATH, 'git', ['clean', '-dxf'])
        utils.execute(paths.IOTJS_PATH, 'git', ['reset', '--hard'])

        utils.execute(paths.IOTJS_PATH, 'git', ['fetch'])
        utils.execute(paths.IOTJS_PATH, 'git', ['checkout', branch])
        utils.execute(paths.IOTJS_PATH, 'git', ['pull', 'origin', branch])
        utils.execute(paths.IOTJS_PATH, 'git', ['checkout', commit])

    def apply_patches(self):
        '''
        Apply memstat patches to measure the memory consumption of IoT.js
        '''
        if self.device.get_type() is not 'stm32f4dis':
            return

        iotjs_memstat_patch = utils.join(paths.PATCHES_PATH, 'iotjs-memstat.diff')
        utils.execute(paths.IOTJS_PATH, 'git', ['apply', iotjs_memstat_patch])

        libtuv_memstat_patch = utils.join(paths.PATCHES_PATH, 'libtuv-memstat.diff')
        utils.execute(paths.IOTJS_LIBTUV_PATH, 'git', ['apply', libtuv_memstat_patch])
        utils.execute(paths.IOTJS_LIBTUV_PATH, 'git', ['add', '-u'])

        jerry_memstat_patch = utils.join(paths.PATCHES_PATH, 'jerry-memstat.diff')
        utils.execute(paths.IOTJS_JERRY_PATH, 'git', ['apply', jerry_memstat_patch])
        utils.execute(paths.IOTJS_JERRY_PATH, 'git', ['add', '-u'])

    def build(self, buildtype):
        '''
        Build IoT.js for the target device/OS and for Raspberry Pi 2.
        '''
        devtype = self.device.get_type()

        if devtype == 'fake':
            return

        # Note: We should build IoT.js for Raspberry Pi 2, since the
        # binary size information (showed on the test-result webpages)
        # is based on this target.
        minimal_build_flags = [
            '--clean',
            '--buildtype=release',
            '--target-arch=arm',
            '--no-parallel-build',
            '--target-board=rpi2',
            '--builddir=%s' % paths.IOTJS_MINIMAL_BUILD_PATH
        ]

        utils.execute(paths.IOTJS_PATH, 'tools/build.py', minimal_build_flags)

        # The following builds are target specific with memory usage features.
        build_flags = [
            '--clean',
            '--target-arch=arm',
            '--buildtype=%s' % buildtype,
        ]

        if devtype == 'stm32f4dis' and self.os_name == 'nuttx':
            build_flags.append('--target-board=stm32f4dis')
            build_flags.append('--target-os=nuttx')
            build_flags.append('--jerry-heaplimit=78')
            build_flags.append('--jerry-memstat')
            build_flags.append('--no-parallel-build')
            build_flags.append('--nuttx-home=%s' % paths.NUTTX_PATH)

            # Enable memstat for IoT.js (libtuv, jerryscript, iotjs)
            self.apply_patches()

            utils.execute(paths.IOTJS_PATH, 'tools/build.py', build_flags)

        elif devtype == 'rpi2':
            build_flags.append('--target-board=rpi2')
            build_flags.append('--jerry-cmake-param=-DFEATURE_VALGRIND_FREYA=ON')
            build_flags.append('--compile-flag=-g')
            build_flags.append('--jerry-compile-flag=-g')

            utils.execute(paths.IOTJS_PATH, 'tools/build.py', build_flags)
