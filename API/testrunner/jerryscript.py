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

import base
import json
import os

from ..common import paths
from ..common import utils


class TestRunner(base.TestRunnerBase):
    '''
    JerryScript test runner.
    '''
    def __init__(self, os, app, device):
       super(self.__class__, self).__init__(os, app, device)

    def skip_test(self, test):
        '''
        Determine if a test should be skipped.
        '''
        return test.get('skip', False)

    def read_testsets(self):
        '''
        Read all the tests by walkin on the test path.
        '''
        skip_file = os.path.join(paths.PROJECT_ROOT, 'API/testrunner/jerry-skiplist.json')

        with open(skip_file, 'r') as skip_file_p:
            skiplist = json.loads(skip_file_p.read())

        # Select the target skiplist.
        skiptests = skiplist[self.device.get_type()]['testfiles']
        skiptestsets = skiplist[self.device.get_type()]['testsets']

        testsets = {}

        for root, dirs, files in os.walk(paths.JERRY_TEST_JERRY_PATH):
            testset = utils.relpath(root, paths.JERRY_TEST_JERRY_PATH)

            if not testset in testsets:
                testsets[testset] = []

            for file in files:
                test = { 'name': file }

                # Indicate expected-failure for fail tests.
                if 'fail' in testset:
                    test['expected-failure'] = True

                # Skip test if neccessary-
                for skiptest in skiptests:
                    if file == skiptest['name']:
                        test['skip'] = True
                        test['reason'] = skiptest['reason']

                # Skip the current test if its testset is skipped.
                for skiptestset in skiptestsets:
                    if testset == skiptestset['name']:
                        test['skip'] = True
                        test['reason'] = skiptestset['reason']

                testsets[testset].append(test)

        return testsets

    def run_test_on_device(self, testset, test):
        '''
        Send commands via telnet to run the current test on the device.
        '''
        testfile = utils.join(self.device.get_test_path(), testset, test['name'])

        if self.device.get_type() is 'stm32f4dis':
            return self.device.execute(self.app.get_cmd(), [testfile, '--mem-stats', '--log-level 2'])

        return self.device.execute(self.app.get_cmd(), [testfile])
