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

from API import resources
from API.common import utils


class BuilderBase(object):
    '''
    This class holds all the common properties of the targets.
    '''
    def __init__(self, env):
        # Get all the information about of the modules.
        self.env = env

        # Download all the projects.
        resources.fetch_modules(self.env)
        resources.config_modules(self.env)

    def create_profile_builds(self):
        '''
        Build IoT.js and JerryScript on different profiles.

        Note: this step is only for binary size measurement.
        '''
        info = self.env['info']
        paths = self.env['paths']

        if info['no_build'] or info['no_profile_build']:
            return

        self._build('minimal', paths['build-minimal'])
        self._build('target', paths['build-target'])

        utils.create_build_info(self.env)

    def create_test_build(self):
        '''
        Build IoT.js and JerryScript on different profiles.
        '''
        info = self.env['info']
        paths = self.env['paths']

        if info['no_build']:
            return

        # Apply memory measurement patches.
        resources.patch_modules(self.env)

        self._build('target', paths['build'], use_extra_flags=True)

        # Clean up the patches.
        resources.patch_modules(self.env, revert=True)

    def _build_application(self, profile, use_extra_flags):
        '''
        Build IoT.js or JerryScript applications.
        '''
        application = self.env['modules']['app']
        device = self.env['info']['device']

        builders = {
            'iotjs': self._build_iotjs,
            'jerryscript': self._build_jerryscript
        }

        extra_flags = []
        # Append extra-flags that are defined in the resources.json file.
        if use_extra_flags:
            extra_flags = application['extra-build-flags'][device]

        builder = builders.get(application['name'])
        builder(profile, extra_flags)
