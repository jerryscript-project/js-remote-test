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

from ..common import paths
from ..common import utils


class ResultSaver(base.ResultSaverBase):
    '''
    The default ResultSaver class.
    '''
    def __init__(self, testrunner):
        super(self.__class__, self).__init__(testrunner)

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
        if app_name is 'iotjs':
            target_path = utils.join(paths.IOTJS_WEB_DATA_PATH, device_dir)
            index_file = utils.join(target_path, 'index.json')
            utils.copy_file(result_file_path, target_path)
        else:
            target_path = utils.join(paths.JERRY_WEB_DATA_PATH, device_dir)
            index_file = utils.join(target_path, 'index.json')
            utils.copy_file(result_file_path, target_path)

        with open(index_file, 'r') as filename_p:
            data = filename_p.read()

            filenames = json.loads(data)
            filenames.insert(0, result_file_name)

        utils.write_json_file(index_file, filenames)

        # Write statistics information to JSON files.
        binstat_file = utils.join(target_path, 'binstat.json')
        memstat_file = utils.join(target_path, 'memstat.json')

        binstats = []
        memstats = []

        for result_file in filenames:
            with open(utils.join(target_path, result_file)) as data_file:
                data = json.load(data_file)

            # Create sizestat entry.
            binstat = {
                'date': data['date'],
                'binary': int(data['bin']['total']),
                'commit': data['submodules']['iotjs']['commit']
            }

            binstats.append(binstat)

            # Summarize the memory consumption.
            mem_total = 0

            for test in data['tests']:
                if 'memory' in test and test['memory'] != 'n/a':
                    mem_total += int(test['memory'])

            # Create memstat entry.
            if mem_total:
                memstat = {
                    'date': data['date'],
                    'memory': mem_total,
                    'commit': data['submodules']['iotjs']['commit']
                }

                memstats.append(memstat)

        utils.write_json_file(binstat_file, binstats[::-1])
        utils.write_json_file(memstat_file, memstats[::-1])

        # Publish testresults to the web
        utils.execute(target_path, 'git', ['add', utils.join(target_path, result_file_name)])
        utils.execute(target_path, 'git', ['add', '-u'])
        utils.execute(target_path, 'git', ['commit', '--amend', '--no-edit'])
        utils.execute(target_path, 'git', ['push', '-f'])
