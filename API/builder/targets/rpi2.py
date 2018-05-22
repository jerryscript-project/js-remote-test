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
from API.common import utils


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

        if not self.env['info']['no_memstat']:
            self._build_freya()

        self._copy_build_files(application, builddir)

    def _build_freya(self):
        '''
        Cross-compile Valgrind and its Freya tool.
        '''
        freya = self.env['modules']['freya']

        utils.define_environment('LD', 'arm-linux-gnueabihf-ld')
        utils.define_environment('AR', 'arm-linux-gnueabihf-ar')
        utils.define_environment('CC', 'arm-linux-gnueabihf-gcc')
        utils.define_environment('CPP', 'arm-linux-gnueabihf-cpp')
        utils.define_environment('CXX', 'arm-linux-gnueabihf-g++')

        configure_options = ['--host=armv7-linux-gnueabihf']

        utils.execute(freya['src'], './autogen.sh')
        utils.execute(freya['src'], './configure', configure_options)
        utils.execute(freya['src'], 'make', ['clean'])
        utils.execute(freya['src'], 'make', ['TOOLS=freya'])

        utils.unset_environment('LD')
        utils.unset_environment('AR')
        utils.unset_environment('CC')
        utils.unset_environment('CPP')
        utils.unset_environment('CXX')

        build_dir = utils.join(self.env['paths']['build'], 'valgrind_freya')
        # Copy necessary files into the output directory.
        valgrind_files = [
            'vg-in-place',
            'coregrind/valgrind',
            '.in_place/freya-arm-linux',
            '.in_place/vgpreload_core-arm-linux.so',
            '.in_place/vgpreload_freya-arm-linux.so'
        ]

        for valgrind_file in valgrind_files:
            src = utils.join(freya['src'], valgrind_file)
            dst = utils.join(build_dir, valgrind_file)

            utils.copy(src, dst)

    def _build_jerryscript(self, profile, extra_flags):
        '''
        Build JerryScript for Linux target.
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
        Build IoT.js for Linux target.
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
