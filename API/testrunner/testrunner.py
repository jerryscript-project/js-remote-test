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

import json

from firebase_admin import credentials, db, initialize_app

from API.common import paths, reporter, utils


TEST_RESULTS_WEB_PATH = {
    "jerryscript" : paths.JERRY_TEST_RESULTS_WEB_PATH,
    "iotjs" : paths.IOTJS_TEST_RESULTS_WEB_PATH
}


class TestRunner(object):
    '''
    Base class for the concrete target testrunners.
    '''
    def __init__(self):
        self.results = []

    def __update_status_icon(self, app_name, device_type):
        '''
        Update the status icon.
        '''
        results_web_path = TEST_RESULTS_WEB_PATH[app_name]
        if not utils.exists(results_web_path):
            return

        utils.execute(results_web_path, 'git', ['pull', 'origin', 'gh-pages'])
        status = 'passing'
        for test in self.results:
            if test['result'] == 'fail':
                status = 'failing'
                break

        current_status_icon = utils.join(results_web_path, 'status', '%s.svg' % device_type)

        if not utils.exists(current_status_icon):
            return

        with open(current_status_icon) as file:
            if status in file.read():
                return

        image = 'pass.svg' if status is 'passing' else 'fail.svg'
        copied_status_icon = utils.join(results_web_path, 'img', image)
        utils.copy_file(copied_status_icon, current_status_icon)

        utils.execute(results_web_path, 'git', ['add', current_status_icon])
        utils.execute(results_web_path, 'git', ['commit', '-m', 'Update the status badge.'])
        utils.execute(results_web_path, 'git', ['push'])

    def __save(self, app, device, is_publish):
        '''
        Save the testresults.
        '''

        os = device.get_os()
        device_type = device.get_type()

        # Create submodule information.
        submodules = {
            app.get_name() : utils.last_commit_info(app.get_home_dir()),
            os.get_name() : utils.last_commit_info(os.get_home_dir())
        }

        if os.get_name() is 'nuttx':
            submodules['apps'] = utils.last_commit_info(paths.NUTTX_APPS_PATH)

        # Create the result.
        result = {
            'bin' : utils.get_section_sizes(app.get_minimal_image()),
            'date' : utils.get_standardized_date(),
            'tests' : self.results,
            'submodules' : submodules
        }

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

        # Publish results to firebase

        # Service account credential will allow our server to authenticate
        # with Firebase as an admin and disregard any security rules.
        # Keep it confidential and never store it in a public repository.
        serviceAccountKey = utils.join(paths.PROJECT_ROOT, 'serviceAccountKey.json')

        if not utils.exists(serviceAccountKey):
            return

        # Fetch the service account key JSON file contents
        cred = credentials.Certificate(serviceAccountKey)

        # Initialize the app with a service account, granting admin privileges
        initialize_app(cred, {
            'databaseURL': "https://remote-testrunner.firebaseio.com",
            'databaseAuthVariableOverride': {
                'uid': 'testrunner-service'
            }
        })

        ref = db.reference(app.get_name() + '/' + device_dir)

        with open(result_file_path) as result_file:
            data = json.load(result_file)
            ref.push(data)

            # Update the status icon after upload was successful.
            self.__update_status_icon(app.get_name(), device.get_type())

    def __run_test_on_device(self, app, device, testset, test):
        '''
        Execute the current test on the device.
        '''
        testfile = utils.join(device.get_test_path(), testset, test['name'])

        if device.get_type() is 'stm32f4dis':
            if app.get_name() is "jerryscript":
                return device.execute(app.get_cmd(), [testfile, '--mem-stats', '--log-level 2'])
            elif app.get_name() is "iotjs":
                return device.execute(app.get_cmd(), ['--memstat', testfile])

        return device.execute(app.get_cmd(), [testfile])

    def run(self, app, device, is_publish):
        '''
        Main method to run IoT.js tests.
        '''
        reporter.report_start()

        # Clear results before execution.
        self.results = []

        os = device.get_os()

        for testset, tests in app.read_testsets(device).items():
            reporter.report_testset(testset)

            # Loop on all tests and process their results.
            for test in tests:
                testresult = { 'name': test['name'] }

                # 1. Skip tests
                if app.skip_test(test, os.get_name()):
                    reporter.report_skip(test['name'], test.get('reason'))

                    testresult['result'] = 'skip'
                    testresult['reason'] = test.get('reason')
                    self.results.append(testresult)

                    continue

                # 2. execute the test and handle timeout.
                try:
                    exitcode, stdout, memory = self.__run_test_on_device(app, device, testset, test)

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
        self.__save(app, device, is_publish)
