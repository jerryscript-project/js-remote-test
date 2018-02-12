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

from API.common import utils, paths


class Skiplist(object):
    '''
    Skiplist class for IoT.js and JerryScript.
    '''
    def __init__(self, env, os):
        self.os = os
        self.app = env['info']['app']
        self.device = env['info']['device']

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

        return bool(result)

    def _read_skiplist(self):
        '''
        Read the local skiplists.
        '''
        skiplists = {
           'iotjs': 'iotjs-skiplist.json',
           'jerryscript': 'jerryscript-skiplist.json'
        }

        skipfile = utils.join(paths.TESTRUNNER_PATH, skiplists[self.app])
        skiplist = utils.read_json_file(skipfile)

        return skiplist[self.device]

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

        # IoT.js tests have skip information in the
        # official testsets.json file.
        for i in ['all', 'stable', self.os]:
            if i in test.get('skip', []):
                return test

        return None
