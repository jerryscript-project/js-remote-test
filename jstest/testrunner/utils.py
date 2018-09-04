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


import json
import os
import re
import time
import pyrebase

from jstest.common import console, paths, utils


def upload_data_to_firebase(env, test_info):
    '''
    Upload the results of the testrunner to the Firebase database.
    '''
    info = env['info']

    if not info['public']:
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

    if env['info']['coverage']:
        # Identify the place where the data should be stored.
        database_path = 'coverage/%s/%s' % (info['app'], info['device'])
        database.child(database_path).remove(user['idToken'])
    else:
        database_path = '%s/%s' % (info['app'], info['device'])

    database.child(database_path).push(test_info, user['idToken'])

    if env['info']['coverage']:
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
    storage_badge_path = 'status/%s/%s.svg' % (info['app'], info['device'])
    storage.child(storage_badge_path).put('status.svg', user['idToken'])

    utils.remove_file('status.svg')


def read_test_files(env):
    '''
    Read all the tests from the given folder and create a
    dictionary similar to the IoT.js testsets.json file.
    '''
    testsets = {}
    # Read all the tests from the application.
    app = env['modules']['app']
    testpath = app['paths']['tests']

    for root, _, files in os.walk(testpath):
        # The name of the testset is always the folder name.
        testset = utils.relpath(root, testpath)

        # Create a new testset entry if it doesn't exist.
        if testset not in testsets:
            testsets[testset] = []

        for filename in files:
            test = {
                'name': filename
            }

            if 'fail' in testset:
                test['expected-failure'] = True

            testsets[testset].append(test)

    return testsets


def parse_coverage_info(env, coverage_output):
    '''
    Parse and create coverage information
    '''
    coverage_info = {}

    iotjs = env['modules']['iotjs']
    js_folder = iotjs['paths']['js-sources']

    # Store line information from the JS sources.
    for js_file in os.listdir(js_folder):
        filename, _ = os.path.splitext(js_file)

        coverage_info[filename] = {}
        coverage_info[filename]['lines'] = []
        coverage_info[filename]['coverage'] = [0, 0]

        js_file_path = utils.join(js_folder, js_file)

        with open(js_file_path, "r") as js_source:
            lines = js_source.readlines()

            for line in lines:
                # '0' indicates that the line has not been reached yet.
                coverage_info[filename]['lines'].append([line, '0'])

    with open(coverage_output, 'r') as cov_p:
        raw_data = json.load(cov_p)

        ignore_list = ['run_pass', 'run_fail', 'node', 'tools']

        for js_name in raw_data:
            # Skip empty key value.
            if not js_name:
                continue

            # Ignore test and tool files.
            if any(ignored_name in js_name for ignored_name in ignore_list):
                continue

            filename, _ = os.path.splitext(js_name)

            # Iterate reached js files.
            for line_number, line_value in raw_data[js_name].iteritems():
                if line_value:
                    # Increase covered lines.
                    coverage_info[filename]['coverage'][0] += 1
                    # '2' indicates that the line has been covered.
                    coverage_info[filename]['lines'][int(line_number)-1][1] = '2'
                else:
                     # '1' indicates that the line has not been covered.
                    coverage_info[filename]['lines'][int(line_number)-1][1] = '1'

                coverage_info[filename]['coverage'][1] += 1

    return coverage_info


def process_output(output):
    '''
    Extract the runtime memory information from the output of the test.
    '''
    exitcode = 0
    memstat = {
        'heap-jerry': 'n/a',
        'heap-system': 'n/a',
        'stack': 'n/a'
    }

    match = re.search(r'(IoT.js|JerryScript) [Rr]esult: (\d+)', output)

    if match:
        exitcode = int(match.group(2))
        output, _ = output.split(match.group(), 1)

    if output.find('Heap stats:') != -1:
        # Process jerry-memstat output.
        match = re.search(r'Peak allocated = (\d+) bytes', output)

        if match:
            memstat['heap-jerry'] = int(match.group(1))

        # Process malloc peak output.
        match = re.search(r'Malloc peak allocated: (\d+) bytes', output)

        if match:
            memstat['heap-system'] = int(match.group(1))

        # Process stack usage output.
        match = re.search(r'Stack usage: (\d+)', output)

        if match:
            memstat['stack'] = int(match.group(1))

        # Remove memstat from the output.
        output, _ = output.split('Heap stats:', 1)

    return output, memstat, exitcode


def run_coverage_script(env):
    '''
    Start the client script.
    '''
    # Add latency because the start up of the debug server needs time.
    time.sleep(2)

    address = env['info']['coverage']
    iotjs = env['modules']['iotjs']
    coverage_client = iotjs['paths']['coverage-client']
    device = env['info']['device']
    app_name = env['info']['app']

    commit_info = utils.last_commit_info(iotjs['src'])
    result_name = 'cov-%s-%s.json' % (commit_info['commit'], commit_info['date'])
    result_dir = utils.join(paths.RESULT_PATH, '%s/%s/' % (app_name, device))
    result_path = utils.join(result_dir, result_name)

    utils.mkdir(result_dir)
    utils.execute(paths.PROJECT_ROOT, coverage_client, ['--non-interactive',
                                                        '--coverage-output=%s' % result_path,
                                                        address])


def read_port_from_url(url):
    '''
    Parse URL and return with the port number
    '''
    pattern = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'

    match = re.search(pattern, url)

    if not match:
        console.fail('Invalid URL: %s' % url)

    return match.group('port')
