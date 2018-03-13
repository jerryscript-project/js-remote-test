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
        self._build_application(profile, use_extra_flags)

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

        utils.execute(iotjs['src'], 'config/tizen/gbsbuild.sh', ['--debug'])
