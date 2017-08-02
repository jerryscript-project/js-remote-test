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

import base
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

from ..common import paths
from ..common import utils


class ResultSaver(base.ResultSaverBase):
    '''
    The default ResultSaver class.
    '''
    def __init__(self, testrunner):
        super(self.__class__, self).__init__(testrunner)

    # Fixme: eliminate spaghetti code ...
    def save(self, is_publish):
        '''
        Save the testresults.
        '''
        os = self.testrunner.get_os()
        app = os.get_app()

        if not app:
            return

        device = self.testrunner.get_device()

        dev_type = device.get_type()

        if not dev_type in ['stm32f4dis', 'rpi2']:
            return

        if dev_type is 'stm32f4dis':
            device_dir = 'stm32'
        else:
            device_dir = 'rpi2'

        app_name = app.get_name()
        app_home = app.get_home_dir()

        os_name = os.get_name()
        os_home = os.get_home_dir()

        # Create submodule information.
        submodules = {
            app_name : utils.last_commit_info(app_home),
            os_name: utils.last_commit_info(os_home)
        }

        if os_name is 'nuttx':
            submodules['apps'] = utils.last_commit_info(paths.NUTTX_APPS_PATH)

        # Create the result.
        result = {
            'bin' : app.get_section_sizes(),
            'date' : utils.get_standardized_date(),
            'tests' : self.testrunner.get_result(),
            'submodules' : submodules
        }

        # Save the results into a JSON file.
        result_dir = utils.join(paths.OUTPUT_PATH, app_name, device_dir)

        if not utils.exists(result_dir):
            utils.mkdir(result_dir)

        result_file_name = result['date'] + '.json'
        result_file_name = result_file_name.replace(':', '.')
        result_file_path = utils.join(result_dir, result_file_name)

        utils.write_json_file(result_file_path, result)

        # Do not share the results if it not public.
        if not is_publish or not app_name in ['iotjs', 'jerryscript']:
            return

        # Copy the testresult to the web project.
        #
        # Fixme: eliminate the following condition and use dictionaries
        #        to store the target specific paths.
        #
        #  e.g.: TARGET_WEB_PATH[app_name], TARGET_WEB_DATA_PATH[app_name]
        #
        if app_name is 'iotjs':
            target_web_path = paths.IOTJS_WEB_PATH
        else:
            target_web_path = paths.JERRY_WEB_PATH

        # Copy the appropriate icon to the status folder
        status_icon = utils.join(target_web_path, 'img', 'pass.svg')
        status_file = utils.join(target_web_path, 'status', '%s.svg' % dev_type)

        for test in self.testrunner.get_result():
            if test['result'] == 'fail':
                status_icon = utils.join(target_web_path, 'img', 'fail.svg')
                break

        utils.copy_file(status_icon, status_file)

        # TODO: Publish icons to the web
        #utils.execute(target_web_path, 'git', ['add', '-u'])
        #utils.execute(target_web_path, 'git', ['commit', '-m', 'Update the status badget.'])
        #utils.execute(target_web_path, 'git', ['push'])

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
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://remote-testrunner.firebaseio.com",
            'databaseAuthVariableOverride': {
                'uid': 'testrunner-service'
            }
        })

        ref = db.reference(app_name + '/' + device_dir)

        with open(result_file_path) as result_file:
            data = json.load(result_file)
            ref.push(data)