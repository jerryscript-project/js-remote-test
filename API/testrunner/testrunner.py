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

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

class TestRunner(object):
    '''
    Base class for the concrete target testrunners.
    '''
    def __init__(self, os):
        self.os = os
        self.results = []

    def __save(self, is_publish):
        '''
        Save the testresults.
        '''

        app = self.os.get_app()

        # Create submodule information.
        submodules = {
            app.get_name() : utils.last_commit_info(app.get_home_dir()),
            self.os.get_name() : utils.last_commit_info(self.os.get_home_dir())
        }

        if self.os.get_name() is 'nuttx':
            submodules['apps'] = utils.last_commit_info(paths.NUTTX_APPS_PATH)

        # Create the result.
        result = {
            'bin' : app.get_section_sizes(),
            'date' : utils.get_standardized_date(),
            'tests' : self.results,
            'submodules' : submodules
        }

        device = app.get_device()
        device_type = device.get_type()
        device_dir = "stm32" if device_type == "stm32f4dis" else device_type

        # Save the results into a JSON file.

        result_dir = utils.join(paths.OUTPUT_PATH, app.get_name(), device_dir)

        if not utils.exists(result_dir):
            utils.mkdir(result_dir)

        result_file_name = result['date'] + '.json'
        result_file_name = result_file_name.replace(':', '.')
        result_file_path = utils.join(result_dir, result_file_name)

        utils.write_json_file(result_file_path, result)

        # Do not share the results if it not public.
        if not is_publish:
            return

        # TODO: update the appropriate icon to the status folder

        # Publish results to firebase

        # Service account credential will allow our server to authenticate
        # with Firebase as an admin and disregard any security rules.
        # Keep it confidential and never store it in a public repository.
        serviceAccountKey = utils.join(paths.PROJECT_ROOT, 'serviceAccountKey.json')

        if not utils.exists(serviceAccountKey):
            return

        # Fetch the service account key JSON file contents
        cred = firebase_admin.credentials.Certificate(serviceAccountKey)

        # Initialize the app with a service account, granting admin privileges
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://remote-testrunner.firebaseio.com",
            'databaseAuthVariableOverride': {
                'uid': 'testrunner-service'
            }
        })

        ref = firebase_admin.db.reference(app.get_name() + '/' + device_dir)

        with open(result_file_path) as result_file:
            data = json.load(result_file)
            ref.push(data)

    def run(self, is_publish):
        '''
        Main method to run IoT.js tests.
        '''
        reporter.report_start()

        # Clear results before execution.
        self.results = []

        app = self.os.get_app()

        for testset, tests in app.read_testsets().items():
            reporter.report_testset(testset)

            # Loop on all tests and process their results.
            for test in tests:
                testresult = { 'name': test['name'] }

                # 1. Skip tests
                if app.skip_test(test):
                    reporter.report_skip(test['name'], test.get('reason'))

                    testresult['result'] = 'skip'
                    testresult['reason'] = test.get('reason')
                    self.results.append(testresult)

                    continue

                # 2. execute the test and handle timeout.
                try:
                    exitcode, stdout, memory = app.run_test_on_device(testset, test)

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

        # save results
        self.__save(is_publish)
