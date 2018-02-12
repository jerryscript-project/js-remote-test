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

from API.builder import builder
from API.common import paths, utils, console


class RPi2Builder(builder.BuilderBase):
    '''
    Build all modules for the Raspberry Pi 2 target.
    '''
    def __init__(self, options):
        super(self.__class__, self).__init__(options)

    def _build(self, profile, builddir, use_extra_flags=False):
        '''
        Main method to build the target.
        '''
        application = self.env['modules']['app']

        self._build_application(profile, use_extra_flags)
        self._build_freya()

        build_linker_map = utils.join(builddir, 'linker.map')
        # Copy the linker map file and the image to the build folder.
        utils.copy(application['paths']['linker-map'], build_linker_map)
        utils.copy(application['paths']['image'], builddir)

    def _build_freya(self):
        '''
        Cross-compile Valgrind and its Freya tool.
        '''
        freya = self.env['modules']['freya']

        build_dir = utils.join(self.env['paths']['build'], 'valgrind_freya')
        # Do not build if not necessary.
        if utils.exists(build_dir):
            return

        utils.define_environment('LD', 'arm-linux-gnueabihf-ld')
        utils.define_environment('AR', 'arm-linux-gnueabihf-ar')
        utils.define_environment('CC', 'arm-linux-gnueabihf-gcc')
        utils.define_environment('CPP', 'arm-linux-gnueabihf-cpp')
        utils.define_environment('CXX', 'arm-linux-gnueabihf-g++')

        configure_options = ['--host=armv7-linux-gnueabihf']

        utils.execute(freya['src'], './autogen.sh')
        utils.execute(freya['src'], './configure', configure_options)
        utils.execute(freya['src'], 'make', ['TOOLS=freya'])

        utils.unset_environment('LD')
        utils.unset_environment('AR')
        utils.unset_environment('CC')
        utils.unset_environment('CPP')
        utils.unset_environment('CXX')

        # Copy necessary files into the output directory.
        valgrind_files = [
            'vg-in-place',
            'coregrind/valgrind',
            '.in_place/freya-arm-linux',
            '.in_place/vgpreload_core-arm-linux.so',
            '.in_place/vgpreload_freya-arm-linux.so'
        ]

        for file in valgrind_files:
            src = utils.join(freya['src'], file)
            dst = utils.join(build_dir, file)

            utils.copy(src, dst)


    def _build_jerryscript(self, profile, extra_flags):
        '''
        Collect build-flags for JerryScript.
        '''
        jerry = self.env['modules']['jerryscript']

        profiles = {
            'minimal': jerry['paths']['minimal-profile'],
            'target': jerry['paths']['es2015-subset-profile']
        }

        build_flags = [
            '--clean',
            '--lto=OFF',
            '--jerry-libc=ON',
            '--jerry-libm=ON',
            '--all-in-one=OFF',
            '--linker-flag=-Wl,-Map=jerry.map',
            '--toolchain=%s' % jerry['paths']['rpi2-toolchain'],
            '--profile=%s' % profiles[profile]
        ] + extra_flags

        utils.execute(jerry['src'], 'tools/build.py', build_flags)

    def _build_iotjs(self, profile, extra_flags):
        '''
        Build IoT.js for NuttX target.
        '''
        iotjs = self.env['modules']['iotjs']

        profiles = {
            'minimal': iotjs['paths']['minimal-profile'],
            'target': iotjs['paths']['rpi2-profile']
        }

        build_flags = [
            '--clean',
            '--no-parallel-build',
            '--no-init-submodule',
            '--target-arch=arm',
            '--target-os=linux',
            '--target-board=rpi2',
            '--profile=%s' % profiles[profile],
            '--buildtype=%s' % self.env['info']['buildtype']
        ] + extra_flags

        utils.execute(iotjs['src'], 'tools/build.py', build_flags)
