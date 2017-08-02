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
import os
import json

from ..common import paths
from ..common import utils


class TestRunner(base.TestRunnerBase):
    '''
    IoT.js test runner.
    '''
    def __init__(self, os, app, device):
        super(self.__class__, self).__init__(os, app, device)

    def read_testsets(self):
        '''
        Read tests from the testsets.json file.
        '''
        testsets = os.path.join(paths.IOTJS_TEST_PATH, 'testsets.json')

        with open(testsets, 'r') as testsets_p:
            data = testsets_p.read()

        return json.loads(data)

    def skip_test(self, test):
        '''
        Determine if a test should be skipped.
        '''
        skip_list = test.get('skip', [])

        for i in ['all', self.os.get_name(), 'stable']:
            # Fixme: a temporary hack to the linux skip list. Remove this.
            if 'linux' in skip_list and self.os.get_name() == 'dummy':
                return True

            if i in skip_list:
                return True

        if self.device.get_type() == 'stm32f4dis':
        # Fixme: filesystem tests require writable memory space.
        # Since these are in read-only space, skipping them locally.
            filesystem_tests = [
                'test_fs_callbacks_called.js',
                'test_fs_rename.js',
                'test_fs_rename_sync.js',
                'test_fs_writefile.js',
                'test_fs_writefile_sync.js',
                'test_fs_writefile_unlink.js',
                'test_fs_writefile_unlink_sync.js'
            ]

            return test['name'] in filesystem_tests

        return False

    def run_test_on_device(self, testset, test):
        '''
        Send commands via telnet to run the current test on the device.
        '''

        testfile = utils.join(self.device.get_test_path(), testset, test['name'])

        if self.device.get_type() is 'stm32f4dis':
            return self.device.execute(self.app.get_cmd(), ['--memstat', testfile])

        return self.device.execute(self.app.get_cmd(), [testfile])
