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

from API.common import utils
from API.builder import builder


class ARTIK530Builder(builder.BuilderBase):
    '''
    Build all modules for the Artik530 target.
    '''
    def __init__(self, options):
        super(self.__class__, self).__init__(options)

    def _build(self, profile, builddir, use_extra_flags=False):
        '''
        Main method to build the target.
        '''
        application = self.env['modules']['app']

        self._build_application(profile, use_extra_flags)
        self._copy_build_files(application, builddir)

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

        utils.execute(iotjs['src'], 'config/tizen/gbsbuild.sh')

        tizen_build_dir = utils.join(paths.GBS_IOTJS_PATH, 'build')
        iotjs_build_dir = utils.join(iotjs['src'], 'build')
        # Copy the GBS created binaries to the iotjs build folder.
        # Note: GBS compiles iotjs in the GBS folder.
        utils.copy(tizen_build_dir, iotjs_build_dir)
