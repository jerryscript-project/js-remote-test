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
import json

from API.common import console, paths, utils


class Application(base.ApplicationBase):
    '''
    IoT.js application.
    '''
    def __init__(self, options):
        super(self.__class__, self).__init__('iotjs', 'iotjs', options)

    def get_image(self):
        '''
        Return the path to the binary.
        '''
        return utils.join(paths.IOTJS_BUILD_PATH, 'iotjs') % self.buildtype

    def get_minimal_image(self):
        '''
        Return the path to the disable-features build.
        '''
        return utils.join(paths.IOTJS_MINIMAL_BIN_PATH, 'iotjs') % self.buildtype

    def get_home_dir(self):
        '''
        Return the path to the application files.
        '''
        return paths.IOTJS_APPS_PATH

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

    def __apply_patches(self, revert=False):
        '''
        Apply memstat patches to measure the memory consumption of IoT.js
        '''
        iotjs_memstat_patch = utils.join(paths.PATCHES_PATH, 'iotjs-memstat.diff')
        utils.patch(paths.IOTJS_PATH, iotjs_memstat_patch, revert)

        libtuv_memstat_patch = utils.join(paths.PATCHES_PATH, 'libtuv-memstat.diff')
        utils.patch(paths.IOTJS_LIBTUV_PATH, libtuv_memstat_patch, revert)
        utils.execute(paths.IOTJS_LIBTUV_PATH, 'git', ['add', '-u'])

        jerry_memstat_patch = utils.join(paths.PATCHES_PATH, 'jerry-memstat.diff')
        utils.patch(paths.IOTJS_JERRY_PATH, jerry_memstat_patch, revert)
        utils.execute(paths.IOTJS_JERRY_PATH, 'git', ['add', '-u'])

    def get_include_module_option(self, os_name):
        '''
        Get os dependency module list with include module option string.
        '''
        module_file_path = utils.join(paths.IOTJS_PATH, 'build.module')
        with open(module_file_path, 'r') as file:
            config = json.loads(file.read().encode('ascii'))
            extend_module = config['module']['supported']['extended']               
            return '--iotjs-include-module=' + ','.join(extend_module[os_name])

    def build(self, device):
        '''
        Build IoT.js for the target device/OS and for Raspberry Pi 2.
        '''

        # prebuild the OS
        os = device.get_os()
        os.prebuild(self)

        common_build_flags = [
            '--clean',
            '--buildtype=%s' % self.buildtype,
            '--target-arch=arm',
        ]

        # Note: We should build IoT.js for Raspberry Pi 2, since the
        # binary size information (showed on the test-result webpages)
        # is based on this target.
        minimal_build_flags = list(common_build_flags)
        minimal_build_flags.append('--target-board=rpi2')
        minimal_build_flags.append('--builddir=%s' % paths.IOTJS_MINIMAL_BUILD_PATH)

        # Run the buildscript with minimal build flags for binary information.
        utils.execute(paths.IOTJS_PATH, 'tools/build.py', minimal_build_flags)
        utils.execute(paths.IOTJS_PATH, 'arm-linux-gnueabi-strip',
                                                    [self.get_minimal_image()])


        # The following builds are target specific with memory usage features.
        build_flags = list(common_build_flags)
        # Enable further modules.
        build_flags.append(self.get_include_module_option(os.get_name()))

        # Specify target os.
        build_flags.append('--target-os=%s' % os.get_name())

        if device.get_type() == 'stm32f4dis':
            build_flags.append('--target-board=%s' % device.get_type())
            build_flags.append('--jerry-heaplimit=78')
            build_flags.append('--jerry-memstat')
            build_flags.append('--no-parallel-build')
            build_flags.append('--nuttx-home=%s' % paths.NUTTX_PATH)

            # Enable memstat for IoT.js (libtuv, jerryscript, iotjs)
            self.__apply_patches()

        elif device.get_type() == 'rpi2':
            build_flags.append('--target-board=%s' % device.get_type())
            build_flags.append('--jerry-cmake-param=-DFEATURE_VALGRIND_FREYA=ON')
            build_flags.append('--compile-flag=-g')
            build_flags.append('--jerry-compile-flag=-g')

        elif device.get_type() == 'artik053':
            build_flags.append('--target-board=artik05x')
            build_flags.append('--sysroot=%s' % paths.TIZENRT_OS_PATH)

        else:
            console.fail('Non-minimal IoT.js build failed, unsupported '
                         'device (%s)!' % device.get_type())

        # Run the buildscript.
        utils.execute(paths.IOTJS_PATH, 'tools/build.py', build_flags)

        # Revert all the memstat patches from the project.
        if device.get_type() == 'stm32f4dis':
            self.__apply_patches(revert=True)

        os.build(self, self.buildtype, 'all')

    def __in_dictlist(self, key, value, dictlist):
        for this in dictlist:
            if this[key] == value:
                return this
        return {}

    def __add_test_to_skip(self, os_name, test, reason):
        skip_os = test['skip'] if 'skip' in test else []

        if not ('all' and os_name) in skip_os:
            test['reason'] = reason
            skip_os.append(os_name)
            test['skip'] = skip_os

    def skip_test(self, test, os_name):
        '''
        Determine if a test should be skipped.
        '''
        skip_list = test.get('skip', [])

        for i in ['all', os_name, 'stable']:
            if i in skip_list:
                return True

        return False

    def read_testsets(self, device):
        '''
        Read all the tests
        '''

        # Read testsets
        testsets_file = utils.join(paths.IOTJS_TEST_PATH, 'testsets.json')
        testsets = {}

        with open(testsets_file, 'r') as testsets_p:
            testsets = json.load(testsets_p)

        # Read skip file
        skip_file = utils.join(paths.PROJECT_ROOT, 'API/testrunner/iotjs-skiplist.json')
        skip_list = self.get_skiplist(skip_file)
        skip_tests = skip_list[device.get_type()]['testfiles']
        skip_testsets = skip_list[device.get_type()]['testsets']

        os = device.get_os()
        os_name = os.get_name()

        # Update testset
        for testset in testsets:
            skip_testset = self.__in_dictlist('name', testset, skip_testsets)

            if skip_testset:
                for test in testsets[testset]:
                    self.__add_test_to_skip(os_name, test, skip_testset['reason'])

            else:
                for skip_test in skip_tests:
                    target_test = self.__in_dictlist('name', skip_test['name'], testsets[testset])

                    if target_test:
                        self.__add_test_to_skip(os_name, target_test, skip_test['reason'])

        return testsets
