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

from jstest.common import utils, paths


class Skiplist(object):
    '''
    Skiplist class for IoT.js and JerryScript.
    '''
    def __init__(self, env, device):
        self.device = device
        self.app = env.options.app
        self.device_type = env.options.device

        if self.app == 'iotjs':
            buildinfo = self.device.iotjs_build_info()
            self.builtin_modules = buildinfo[0]
            self.builtin_features = buildinfo[1]
            self.stability = buildinfo[2]

        # Read the local skiplist.
        self.skiplist = self._read_skiplist()

    def contains(self, testset, test):
        '''
        Skip tests by the skiplists.
        '''
        result = self._find_in_skiplist(testset, test)

        # Update the reason of the test by the label
        # of the local skiplist.
        if result and 'reason' in result:
            test['reason'] = result['reason']
            return True

        # In case of iotjs, check if the test has to be skipped
        # based on the required modules and features.
        if self.app == 'iotjs':
            return self._skip_iotjs_test(test)

        return False

    def _skip_iotjs_test(self, test):
        '''
        Determine if an iotjs test has to be skipped.
        '''
        required_modules = set(test.get('required-modules', []))
        required_features = set(test.get('required-features', []))

        unsupported_modules = required_modules - self.builtin_modules
        unsupported_features = required_features - self.builtin_features

        # Skip the test if it requires a module which is not in iotjs.
        if unsupported_modules:
            test['reason'] = 'Required module(s) unsupported by iotjs build: '
            test['reason'] += ', '.join(sorted(unsupported_modules))
            return True

        # Skip the test if it uses features which are not in iotjs.
        if unsupported_features:
            test['reason'] = 'Required feature(s) unsupported by iotjs build: '
            test['reason'] += ', '.join(sorted(unsupported_features))
            return True

        return False

    def _read_skiplist(self):
        '''
        Read the local skiplists.
        '''
        skiplists = {
           'iotjs': 'iotjs-skiplist.json',
           'jerryscript': 'jerryscript-skiplist.json'
        }

        skipfile = utils.join(paths.SKIPLIST_PATH, skiplists[self.app])
        skiplist = utils.read_json_file(skipfile)

        return skiplist[self.device_type]

    def _find_in_skiplist(self, testset, test):
        '''
        Find element in the skiplist.
        '''
        for obj in self.skiplist['testsets']:
            if obj['name'] == testset:
                return obj

        for obj in self.skiplist['testfiles']:
            if obj['name'] == test['name']:
                return obj

        if self.app != 'iotjs':
            return None

        # IoT.js tests have skip information in the
        # official testsets.json file.
        for i in ['all', self.stability, self.device.os]:
            if i in test.get('skip', []):
                return test

        return None
