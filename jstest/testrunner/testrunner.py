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

from jstest.common import paths, reporter, utils
from jstest.testrunner import utils as testrunner_utils
from jstest.testrunner import devices
from jstest.testrunner.skiplist.skiplist import Skiplist


def read_testsets(env):
    '''
    Read all the tests into dictionary.
    '''
    testset = utils.join(env.modules.app.paths.tests, 'testsets.json')

    if utils.exists(testset):
        return utils.read_json_file(testset)

    return testrunner_utils.read_test_files(env)


class TestRunner(object):
    '''
    Testrunner class.
    '''
    def __init__(self, environment):
        self.env = environment

        # Do not initialize the members if testing is not enabled.
        if environment.options.no_test:
            return

        self.device = devices.create_device(environment)
        self.results = []
        self.coverage_info = {}

        # Flash the device to be able to run the tests.
        self.skiplist = Skiplist(environment, self.device)

        utils.execute('.', 'mosquitto', ['-d'])

    def run(self):
        '''
        Main method to run IoT.js or JerryScript tests.
        '''
        if self.env.options.no_test:
            return

        reporter.report_configuration(self.env)

        for testset, tests in read_testsets(self.env).items():
            self.run_testset(testset, tests)

        if self.env.options.coverage:
            device = self.env.options.device
            app_name = self.env.options.app

            if device in ['artik053', 'rpi3', 'rpi2'] and app_name == 'iotjs':
                iotjs = self.env.modules.iotjs
                commit_info = utils.last_commit_info(iotjs['src'])
                result_name = 'cov-%s-%s.json' % (commit_info['commit'], commit_info['date'])
                result_dir = utils.join(paths.RESULT_PATH, '%s/%s/' % (app_name, device))
                result_path = utils.join(result_dir, result_name)

            self.coverage_info = testrunner_utils.parse_coverage_info(self.env, result_path)

            reporter.report_coverage(self.coverage_info)

        reporter.report_final(self.results)

    def run_testset(self, testset, tests):
        '''
        Run all the tests that are in the given testset.
        '''
        reporter.report_testset(testset)

        for test in tests:
            testresult = {
                'name': test['name']
            }

            # 1. Skip tests.
            if self.skiplist.contains(testset, test):
                reporter.report_skip(test['name'], test.get('reason'))

                testresult['result'] = 'skip'
                testresult['reason'] = test.get('reason')
                self.results.append(testresult)

                continue

            # 2. Execute the test and handle timeout.
            try:
                result = self.device.execute(testset, test)

            except utils.TimeoutException:
                reporter.report_timeout(test['name'])

                testresult['result'] = 'timeout'
                self.results.append(testresult)

                continue

            # 3. Process the result of the test.
            expected_failure = test.get('expected-failure', False)
            exitcode = int(result['exitcode'])

            if bool(exitcode) == expected_failure:
                reporter.report_pass(test['name'])

                testresult['result'] = 'pass'
                testresult['memstat'] = result['memstat']

            else:
                reporter.report_fail(test['name'])
                testresult['result'] = 'fail'

            testresult['output'] = result['output']
            self.results.append(testresult)

    def save(self):
        '''
        Save the current testresults into JSON format.
        '''
        if self.env.options.no_test:
            return

        results = {}
        # Specify a date named results file.
        filename = utils.join(self.env.paths.builddir, 'testresults.json')

        if self.env.options.coverage:
            results['coverage_info'] = self.coverage_info
            filename += '_coverage'

        else:
            results['tests'] = self.results

        # Save the results into the date named file.
        utils.write_json_file(filename, results)
