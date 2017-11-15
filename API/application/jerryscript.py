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
import os

from API.common import paths, utils


class Application(base.ApplicationBase):
    '''
    JerryScript application.
    '''
    def __init__(self, options):
        super(self.__class__, self).__init__('jerryscript', 'jerry', options)

    def get_image(self):
        '''
        Return the path to the binary.
        '''
        return utils.join(paths.JERRY_BUILD_PATH, 'jerry')

    def get_image_stack(self):
        '''
        Return the path to the stack binary.
        '''
        return 0

    def get_minimal_image(self):
        '''
        Return the path to the disable-features build.
        '''
        return utils.join(paths.JERRY_MINIMAL_BIN_PATH, 'jerry')

    def get_home_dir(self):
        '''
        Return the path to the application files.
        '''
        return paths.JERRY_APPS_PATH

    def get_install_dir(self):
        '''
        Return the path where the application files should be copied.
        '''
        return utils.join(paths.NUTTX_APPS_INTERPRETER_PATH, 'jerryscript')

    def get_test_dir(self):
        '''
        Return the path to the application test files.
        '''
        return paths.JERRY_TEST_JERRY_PATH

    def get_config_file(self):
        '''
        Return the path to OS configuration file.
        '''
        return utils.join(paths.CONFIG_PATH, 'jerryscript.config')

    def get_romfs_file(self):
        '''
        Return the path of the generated ROMFS image.
        '''
        utils.generate_romfs(paths.JERRY_PATH, paths.JERRY_TEST_JERRY_PATH)

        return utils.join(paths.JERRY_PATH, 'nsh_romfsimg.h')

    def build(self, device):
        '''
        Build IoT.js for the target device/OS and for Raspberry Pi 2.
        '''

        # prebuild the OS
        os = device.get_os()
        os.prebuild(self)

        # Note: We should build JerryScript for Raspberry Pi 2, since the
        # binary size information (showed on the test-result webpages)
        # is based on this target. 
        minimal_build_flags = [
            '--clean',
            '--toolchain=cmake/toolchain_linux_armv7l.cmake',
            '--builddir=%s' % paths.JERRY_MINIMAL_BUILD_PATH
        ]

        utils.execute(paths.JERRY_PATH, 'tools/build.py', minimal_build_flags)
        utils.execute(paths.JERRY_PATH, 'arm-linux-gnueabi-strip',
                                                    [self.get_minimal_image()])

        # The following builds are target specific with memory usage features.
        if device.get_type() == 'rpi2':
            build_flags = [
                '--clean',
                '--toolchain=cmake/toolchain_linux_armv7l.cmake',
                '--mem-stats=ON',
                '--profile=es2015-subset'
            ]

            utils.execute(paths.JERRY_PATH, 'tools/build.py', build_flags)

        elif device.get_type() == 'artik053':
            build_flags = [
                '-f',
                'targets/tizenrt-artik053/Makefile.tizenrt',
                'LIBTARGET_DIR=' + paths.TIZENRT_BUILD_LIBRARIES_PATH
            ]
            utils.execute(paths.JERRY_PATH, 'make', build_flags)

        os.build(self, self.buildtype, [], 'all')

    def skip_test(self, test, os_name):
        '''
        Determine if a test should be skipped.
        '''
        return test.get('skip', False)

    def read_testsets(self, device):
        '''
        Read all the tests by walkin on the test path.
        '''

        # # Read skip file
        skip_file = utils.join(paths.PROJECT_ROOT, 'API/testrunner/jerry-skiplist.json')
        skip_list = self.get_skiplist(skip_file)
        skip_tests = skip_list[device.get_type()]['testfiles']
        skip_testsets = skip_list[device.get_type()]['testsets']

        testsets = {}

        for root, dirs, files in os.walk(paths.JERRY_TEST_JERRY_PATH):
            testset = utils.relpath(root, paths.JERRY_TEST_JERRY_PATH)

            if not testset in testsets:
                testsets[testset] = []

            for file in files:
                test = { 'name': file }

                # Indicate expected-failure for fail tests.
                if 'fail' in testset:
                    test['expected-failure'] = True

                # Skip test if neccessary.
                for skip_test in skip_tests:
                    if file == skip_test['name']:
                        test['skip'] = True
                        test['reason'] = skip_test['reason']

                # Skip the current test if its testset is skipped.
                for skip_testset in skip_testsets:
                    if testset == skip_testset['name']:
                        test['skip'] = True
                        test['reason'] = skip_testset['reason']

                testsets[testset].append(test)

        return testsets
