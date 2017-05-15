# Copyright 2017-present Samsung Electronics Co., Ltd. and other contributors
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import iotjs
import jerryscript


TESTRUNNERS = {
    'iotjs': iotjs.TestRunner,
    'jerryscript': jerryscript.TestRunner
}


def create(os, app, device):
    '''
    Create a TestRunner for the given target.
    '''
    runner_class = TESTRUNNERS[app.get_name()]

    return runner_class(os, app, device)
