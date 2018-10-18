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


import pyrebase

from jstest.common import console, paths, utils


class TestResult(object):
    '''
    Basic class to store the build and testrunner results.
    '''
    def __init__(self, options):
        self.options = options
        self.results = {}

    def append(self, job_id, build_path):
        '''
        Save data to the member variable.
        '''
        self.results[job_id] = build_path

    def create_result(self):
        '''
        Create a final JSON result file from the build and test information.
        '''
        result = {
            'bin': {},
            'date': {},
            'tests': {},
            'submodules': {}
        }

        labels = {
            'profiles/minimal-profile-build': 'minimal-profile',
            'profiles/target-profile-build': 'target-profile'
        }

        for job_id, build_path in self.results.iteritems():
            # Append the binary information.
            if 'test-build' in job_id:
                filename = utils.join(build_path, 'testresults.json')
                # Do not save the testresults if there is no available data.
                if not utils.exists(filename):
                    continue

                result.update(utils.read_json_file(filename))

            else:
                filename = utils.join(build_path, 'build.json')
                # Do not save build info if there is no available data.
                if not utils.exists(filename):
                    continue

                bin_data = utils.read_json_file(filename)
                # Translate job_id to database schema name.
                label = labels[job_id]

                result['bin'][label] = bin_data['bin']
                result['submodules'] = bin_data['submodules']
                result['date'] = bin_data['last-commit-date']

        filepath = utils.join(paths.RESULT_PATH, self.options.app, self.options.device)
        filename = utils.join(filepath, utils.current_date() + '.json')
        # Save the content info a result file.
        utils.write_json_file(filename, result)

        console.log()
        console.log('The results are written into:', console.TERMINAL_BLUE)
        console.log('  {json_file}'.format(json_file=filename))
        console.log()

        return result

    def upload(self):
        '''
        Upload the results of the testrunner to the Firebase database.
        '''
        # Merge the build and test data into one dictionary.
        test_info = self.create_result()

        if not self.options.public:
            return

        email = utils.get_environment('FIREBASE_USER')
        password = utils.get_environment('FIREBASE_PWD')

        if not (email and password):
            return

        config = {
            'apiKey': 'AIzaSyDMgyPr0V49Rdf5ODAU9nLY02ZGEUNoxiM',
            'authDomain': 'remote-testrunner.firebaseapp.com',
            'databaseURL': 'https://remote-testrunner.firebaseio.com',
            'storageBucket': 'remote-testrunner.appspot.com',
        }

        firebase = pyrebase.initialize_app(config)
        database = firebase.database()
        authentication = firebase.auth()

        user = authentication.sign_in_with_email_and_password(email, password)

        # Identify the place where the data should be stored.
        database_path = '%s/%s' % (self.options.app, self.options.device)

        if self.options.coverage:
            database_path = 'coverage/%s' % database_path
            database.child(database_path).remove(user['idToken'])

        database.child(database_path).push(test_info, user['idToken'])

        if self.options.coverage:
            return

        # Update the status images.
        status = 'passed'
        for test in test_info['tests']:
            if test['result'] in ['fail', 'timeout']:
                status = 'failed'
                break

        # The storage service allows to upload images to Firebase.
        storage = firebase.storage()
        # Download the corresponding status badge.
        storage_status_path = 'status/%s.svg' % status
        storage.child(storage_status_path).download('status.svg')
        # Upload the status badge for the appropriate app-device pair.
        storage_badge_path = 'status/%s/%s.svg' % (self.options.app, self.options.device)
        storage.child(storage_badge_path).put('status.svg', user['idToken'])

        utils.remove_file('status.svg')
