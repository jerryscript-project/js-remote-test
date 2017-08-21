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

from ..common import paths
from ..common import reporter
from ..common import utils

class TestRunner(object):
    '''
    Base class for the concrete target testrunners.
    '''
    def __init__(self, os, app, device):
        self.os = os
        self.app = app
        self.device = device
        self.results = []

    def get_result(self):
        '''
        Get the test results.
        '''
        return self.results

    def get_os(self):
        '''
        Return the os
        '''
        return self.os

    def get_device(self):
        '''
        Return the device
        '''
        return self.device

    def run(self):
        '''
        Main method to run IoT.js tests.
        '''
        reporter.report_start()

        # Clear results before execution.
        self.results = []

        for testset, tests in self.app.read_testsets().items():
            reporter.report_testset(testset)

            # Loop on all tests and process their results.
            for test in tests:
                testresult = { 'name': test['name'] }

                # 1. Skip tests
                if self.app.skip_test(test):
                    reporter.report_skip(test['name'], test.get('reason'))

                    testresult['result'] = 'skip'
                    testresult['reason'] = test.get('reason')
                    self.results.append(testresult)

                    continue

                # 2. execute the test and handle timeout.
                try:
                    exitcode, stdout, memory = self.app.run_test_on_device(testset, test)

                except utils.TimeoutException:
                    reporter.report_timeout(test['name'])
                    testresult['result'] = 'timeout'
                    self.results.append(testresult)

                    continue

                # 3. Process the result.
                if bool(int(exitcode)) == test.get('expected-failure', False):
                    reporter.report_pass(test['name'])
                    testresult['result'] = 'pass'
                    if not 'n/a' in str(memory):
                        testresult['memory'] = memory
                else:
                    reporter.report_fail(test['name'])
                    testresult['result'] = 'fail'

                testresult['output'] = stdout

                self.results.append(testresult)

        reporter.report_final(self.results)
