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
import pyrebase

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
        bin_sizes = {}
        if app.get_name() == 'iotjs':
            target_profile_mapfile = app.get_target_profile_mapfile()
            minimal_profile_mapfile = app.get_minimal_profile_mapfile()

            target_bin_sizes = utils.get_section_sizes_from_map(target_profile_mapfile)
            minimal_bin_sizes = utils.get_section_sizes_from_map(minimal_profile_mapfile)

            bin_sizes = {
                'target_profile': target_bin_sizes,
                'minimal_profile': minimal_bin_sizes
            }

        else:
            bin_sizes = utils.get_section_sizes(app.get_minimal_image())

        result = {
            'bin' : bin_sizes,
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

        user = utils.get_environment('FIREBASE_USER')
        pwd =  utils.get_environment('FIREBASE_PWD')

        if not (pwd and user):
            return

        config = {
            "apiKey": "AIzaSyDMgyPr0V49Rdf5ODAU9nLY02ZGEUNoxiM",
            "authDomain": "remote-testrunner.firebaseapp.com",
            "databaseURL": "https://remote-testrunner.firebaseio.com",
            "storageBucket": "remote-testrunner.appspot.com",
        }

        firebase = pyrebase.initialize_app(config)
        auth = firebase.auth()
        db = firebase.database()

        user = auth.sign_in_with_email_and_password(user, pwd)

        with open(result_file_path) as result_file:
            result_data = json.load(result_file)
            db.child(app.get_name() + '/' + device_dir).push(result_data, user['idToken'])

            # Update the status icon after upload was successful.
            self.__update_status_icon(app.get_name(), device.get_type())

    def __run_test_on_device(self, app, device, testset, test):
        '''
        Execute the current test on the device.
        '''
        testfile = utils.join(device.get_test_path(), testset, test['name'])

        if device.get_type() in ['stm32f4dis', 'artik053']:
            if app.get_name() is "jerryscript":
                return device.execute(app, [testfile, '--mem-stats', '--log-level 2'])
            elif app.get_name() is "iotjs":
                return device.execute(app, ['--memstat', testfile])

        return device.execute(app, [testfile])

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
                    result = self.__run_test_on_device(app, device, testset, test)

                except utils.TimeoutException:
                    reporter.report_timeout(test['name'])
                    testresult['result'] = 'timeout'
                    self.results.append(testresult)
                    continue

                # 3. Process the result.
                if bool(int(result['exitcode'])) == test.get('expected-failure', False):
                    reporter.report_pass(test['name'])
                    testresult['result'] = 'pass'

                    jerry_peak = result['jerry_peak_alloc']
                    malloc_peak = result['malloc_peak']
                    stack_peak = result['stack_peak']
                    total_peak = utils.to_int(jerry_peak) + utils.to_int(malloc_peak) + utils.to_int(stack_peak)

                    if app.get_name() == 'iotjs':
                        testresult['memory'] = {
                            'jerry': jerry_peak,
                            'malloc': malloc_peak,
                            'stack': stack_peak,
                            'total': total_peak
                        }
                    # JerryScript supports only jerry-heap data.
                    elif app.get_name() == 'jerryscript':
                        testresult['memory'] = jerry_peak
                else:
                    reporter.report_fail(test['name'])
                    testresult['result'] = 'fail'

                testresult['output'] = result['output']

                self.results.append(testresult)

        reporter.report_final(self.results)

        # save results
        self.__save(app, device, is_publish)
