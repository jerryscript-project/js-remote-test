# Copyright 2018-present Samsung Electronics Co., Ltd. and other contributors
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

from jstest.common import paths, utils
from jstest.builder import builder


class ARTIK530Builder(builder.BuilderBase):
    '''
    Build all modules for the Artik530 target.
    '''
    def _build(self, profile, builddir, use_extra_flags=False):
        '''
        Main method to build the target.
        '''
        application = self.env['modules']['app']

        self._build_application(profile, use_extra_flags)

        if not self.env['info']['no_memstat']:
            self._build_freya()

        self._copy_build_files(application, builddir)

    def _build_freya(self):
        '''
        Cross-compile Valgrind and its Freya tool.
        '''
        build_dir = utils.join(self.env['paths']['build'], 'valgrind_freya')
        valgrind_files = [
            'vg-in-place',
            'coregrind/valgrind',
            '.in_place/freya-arm-linux',
            '.in_place/vgpreload_core-arm-linux.so',
            '.in_place/vgpreload_freya-arm-linux.so'
        ]

        # Check if a Freya build already exists, if yes, skip the build.
        if utils.exist_files(build_dir, valgrind_files):
            return

        freya = self.env['modules']['freya']

        utils.define_environment('LD', 'arm-linux-gnueabi-ld')
        utils.define_environment('AR', 'arm-linux-gnueabi-ar')
        utils.define_environment('CC', 'arm-linux-gnueabi-gcc')
        utils.define_environment('CPP', 'arm-linux-gnueabi-cpp')
        utils.define_environment('CXX', 'arm-linux-gnueabi-g++')

        configure_options = ['--host=armv7-linux-gnueabi']

        utils.execute(freya['src'], './autogen.sh')
        utils.execute(freya['src'], './configure', configure_options)
        utils.execute(freya['src'], 'make', ['clean'])
        utils.execute(freya['src'], 'make', ['TOOLS=freya'])

        utils.unset_environment('LD')
        utils.unset_environment('AR')
        utils.unset_environment('CC')
        utils.unset_environment('CPP')
        utils.unset_environment('CXX')

        # Copy necessary files into the output directory.
        for valgrind_file in valgrind_files:
            src = utils.join(freya['src'], valgrind_file)
            dst = utils.join(build_dir, valgrind_file)

            utils.copy(src, dst)

    def _build_jerryscript(self, profile, extra_flags):
        '''
        Build JerryScript for Tizen target.
        '''
        # TODO

    def _build_iotjs(self, profile, extra_flags):
        '''
        Build IoT.js for Tizen target.
        '''
        iotjs = self.env['modules']['iotjs']

        profiles = {
            'minimal': 'profiles/minimal.profile',
            'target': 'test/profiles/tizen.profile'
        }

        build_flags = [
            '--clean',
            '--no-parallel-build',
            '--no-init-submodule',
            '--target-arch=noarch',
            '--target-os=tizen',
            '--target-board=rpi3',
            '--profile=%s' % profiles[profile],
            '--buildtype=%s' % self.env['info']['buildtype']
        ] + extra_flags

        iotjs_build_options = ' '.join(build_flags)
        # Note: these values should be defined for GBS, because
        #       it will compile the IoT.js itself.
        utils.define_environment('IOTJS_BUILD_OPTION', iotjs_build_options)

        args = ['--clean']

        if self.env['info']['buildtype'] == 'debug':
            args.append('--debug')

        utils.execute(iotjs['src'], 'config/tizen/gbsbuild.sh', args)

        tizen_build_dir = utils.join(paths.GBS_IOTJS_PATH, 'build')
        iotjs_build_dir = utils.join(iotjs['src'], 'build')
        # Copy the GBS created binaries to the iotjs build folder.
        # Note: GBS compiles iotjs in the GBS folder.
        utils.copy(tizen_build_dir, iotjs_build_dir)
