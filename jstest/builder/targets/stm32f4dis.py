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

from jstest.builder import builder
from jstest.common import utils
from jstest.builder import utils as builder_utils

class STM32F4Builder(builder.BuilderBase):
    '''
    Build all modules for the STM32F4-Discovery target.
    '''
    def _build(self, profile, builddir, use_extra_flags=False):
        '''
        Main method to build all the dependencies of the target.
        '''
        nuttx = self.env['modules']['nuttx']

        self._prebuild_nuttx()
        self._build_application(profile, use_extra_flags)
        self._build_nuttx()
        self._build_stlink()

        self._copy_build_files(nuttx, builddir)

    def _prebuild_nuttx(self):
        '''
        Clean NuttX and configure it for serial communication.
        '''
        nuttx = self.env['modules']['nuttx']
        config = ['stm32f4discovery/usbnsh']

        utils.execute(nuttx['src'], 'make', ['distclean'])
        utils.execute(nuttx['paths']['tools'], './configure.sh', config)
        utils.execute(nuttx['src'], 'make', ['clean'])
        utils.execute(nuttx['src'], 'make', ['context'])

    def _build_nuttx(self):
        '''
        Build the NuttX Operating System.
        '''
        nuttx = self.env['modules']['nuttx']
        buildtype = self.env['info']['buildtype']

        utils.define_environment('R', int(buildtype == 'release'))
        utils.define_environment('EXTRA_LIBS', '-Map=nuttx.map')

        # Provide test files as ROMFS content.
        self._append_testfiles()

        utils.execute(nuttx['src'], 'make', ['-j1'])

    def _build_stlink(self):
        '''
        Build the ST-Link flasher tool.
        '''
        stlink = self.env['modules']['stlink']

        # Do not build if not necessary.
        if utils.exists(stlink['paths']['st-flash']):
            return

        utils.execute(stlink['src'], 'make', ['release'])

    def _build_jerryscript(self, profile, extra_flags):
        '''
        Build JerryScript for NuttX target.
        '''
        nuttx = self.env['modules']['nuttx']
        jerry = self.env['modules']['jerryscript']

        profiles = {
            'minimal': jerry['paths']['minimal-profile'],
            'target': jerry['paths']['es2015-subset-profile']
        }

        build_flags = [
            '--clean',
            '--lto=OFF',
            '--jerry-cmdline=OFF',
            '--jerry-libc=OFF',
            '--jerry-libm=ON',
            '--all-in-one=OFF',
            '--mem-heap=70',
            '--profile=%s' % profiles[profile],
            '--toolchain=%s' % jerry['paths']['stm32f4dis-toolchain'],
            '--compile-flag=-I%s' % jerry['paths']['stm32f4dis-target'],
            '--compile-flag=-isystem %s' % nuttx['paths']['include']
        ] + extra_flags

        # NuttX requires the path of the used JerryScript folder.
        utils.define_environment('JERRYSCRIPT_ROOT_DIR', jerry['src'])

        utils.execute(jerry['src'], 'tools/build.py', build_flags)

    def _build_iotjs(self, profile, extra_flags):
        '''
        Build IoT.js for NuttX target.
        '''
        iotjs = self.env['modules']['iotjs']
        nuttx = self.env['modules']['nuttx']

        profiles = {
            'minimal': iotjs['paths']['minimal-profile'],
            'target': iotjs['paths']['nuttx-profile']
        }

        build_flags = [
            '--clean',
            '--no-parallel-build',
            '--no-init-submodule',
            '--target-arch=arm',
            '--target-os=nuttx',
            '--target-board=stm32f4dis',
            '--jerry-heaplimit=64',
            '--profile=%s' % profiles[profile],
            '--buildtype=%s' % self.env['info']['buildtype'],
            '--nuttx-home=%s' % nuttx['src']
        ] + extra_flags

        # NuttX requires the path of the used IoT.js folder.
        utils.define_environment('IOTJS_ROOT_DIR', iotjs['src'])

        utils.execute(iotjs['src'], 'tools/build.py', build_flags)

    def _append_testfiles(self):
        '''
        Add test files to the ROMFS file of NuttX.
        '''
        target_app = self.env['modules']['app']
        nuttx_apps = self.env['modules']['nuttx-apps']

        tests = target_app['paths']['tests']
        romfs = nuttx_apps['paths']['romfs']
        # Override the default ROMFS file of NuttX.
        builder_utils.generate_romfs(tests, romfs)
