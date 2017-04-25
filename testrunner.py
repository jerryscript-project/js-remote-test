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

from __future__ import print_function

import argparse
import glob
import json
import os
import re
import schedule
import time

from resources import builder
from resources import reporter
from resources import console
from resources import device
from resources import executor
from resources import net
from resources import paths
from resources import utils


class TestRunner(object):
    '''
    This class is responsible for running all the tests on stm32f4.
    '''
    def __init__(self, arguments):
        self.public = arguments.public
        self.telnet = net.Telnet(arguments.device_ip, arguments.timeout)
        self.results = []

    def save(self):
        '''
        Save the results into a JSON file.
        '''
        if not executor.exists(paths.OUTPUT_PATH):
            executor.mkdir(paths.OUTPUT_PATH)

        filename = time.strftime('%Y-%m-%dT%H.%M.%SZ') + '.json'
        indexfile = os.path.join(paths.OUTPUT_PATH, 'index.json')
        outputfile = os.path.join(paths.OUTPUT_PATH, filename)

        # Get the available result files.
        output_files = glob.glob(paths.OUTPUT_PATH + '/.*Z.json')
        output_files.append(outputfile)
        output_files = sorted(output_files, reverse=True)

        submodules = {
            'iotjs': utils.get_submodule_info(paths.IOTJS_PATH),
            'nuttx': utils.get_submodule_info(paths.NUTTX_PATH),
            'apps': utils.get_submodule_info(paths.APPS_PATH)
        }

        output = {
            'bin': utils.get_binary_info(),
            'date': utils.get_current_date(),
            'tests': self.results,
            'submodules': submodules
        }

        # Write the index.json and the current testresult file.
        utils.write_file(indexfile, output_files)
        utils.write_file(outputfile, output)

        # Do not share the results if it not public.
        if not self.public:
            return

        # Copy the testresult to the web project.
        index_file = os.path.join(paths.WEB_DATA_PATH, 'index.json')

        if executor.exists(index_file):
            # Update the indexfile.
            filenames = utils.read_file(index_file)
            filenames.insert(0, filename)

            utils.write_file(index_file, filenames)
        else:
            executor.copy_file(indexfile, paths.WEB_DATA_PATH)

        executor.copy_file(outputfile, paths.WEB_DATA_PATH)

        # Publish testresults to the web
        utils.publish_data(filename)

    def read_testsets(self):
        '''
        Read tests from the testsets.json file.
        '''
        file = os.path.join(paths.IOTJS_TEST_PATH, 'testsets.json')

        return utils.read_file(file)

    def skip_test(self, test):
        '''
        Determine if a test should be skipped.
        '''
        skip_list = test.get('skip', [])

        for i in ['all', 'nuttx', 'stable']:
            if i in skip_list:
                return True

        return False

    def run(self):
        '''
        Main method to run IoT.js tests.
        '''
        reporter.report_start()

        # Clear results before execute tests.
        self.results = []

        for testset, tests in self.read_testsets().items():
            reporter.report_testset(testset)

            self.run_tests(testset, tests)

        reporter.report_final(self.results)

    def run_tests(self, testset, tests):
        '''
        Loop on all tests and process their results.
        '''
        for test in tests:
            testresult = { 'name': test['name'] }

            # 1. Skip tests
            if self.skip_test(test):
                reporter.report_skip(test['name'], test.get('reason'))

                testresult['result'] = 'skip'
                testresult['reason'] = test.get('reason')
                self.results.append(testresult)

                continue

            # Fixme: filesystem tests require writable memory space.
            # Since these are in read-only space, skipping them locally.
            filesystem_tests = [
                'test_fs_callbacks_called.js',
                'test_fs_rename.js',
                'test_fs_rename_sync.js',
                'test_fs_writefile_unlink.js',
                'test_fs_writefile_unlink_sync.js'
            ]

            if test['name'] in filesystem_tests:
                reporter.report_skip(test['name'], test.get('reason'))

                testresult['result'] = 'skip'
                testresult['reason'] = 'test is in read-only memory space'
                self.results.append(testresult)

                continue

            # 2. Execute the test and handle timeout.
            try:
                exitcode, output = self.run_test(testset, test)

            except net.TimeoutException:
                reporter.report_timeout(test['name'])

                testresult['result'] = 'timeout'
                self.results.append(testresult)

                continue

            # 3. Process the result.
            if bool(int(exitcode)) == test.get('expected-failure', False):
                reporter.report_pass(test['name'])
                testresult['result'] = 'pass'
            else:
                reporter.report_fail(test['name'])
                testresult['result'] = 'fail'

            testresult['output'] = output
            self.results.append(testresult)

    def run_test(self, testset, test):
        '''
        Send commands via telnet to run the current test on stm32f4.
        '''
        testset_path = os.path.join(paths.DEVICE_TEST_PATH, testset)

        # Note: some tests fail if the board is not restarted before execution.
        device.reset()

        self.telnet.create_connection()

        self.telnet.run_cmd('cd', [testset_path])
        self.telnet.run_cmd('iotjs', [test['name']])
        self.telnet.run_cmd('echo', ['$?'])

        self.telnet.close_connection()

        exitcode = self.telnet.outputs['echo']
        output = self.telnet.outputs['iotjs']

        return exitcode, output


def get_arguments():
    '''
    Parse the given arguments.
    '''
    parser = argparse.ArgumentParser('IoT.js remote testrunner for stm32f4')

    parser.add_argument('--device-ip', metavar='device-ip',
                        help='ip address of the target device')

    parser.add_argument('--timeout', metavar='sec', default=120, type=int,
                        help='timeout for tests (default: %(default)s)')

    parser.add_argument('--skip-init', action='store_true', default=False,
                        help='skip building the basic environment')

    parser.add_argument('--public', action='store_true', default=False,
                        help='pusblish results to the web')

    return parser.parse_args()


def main():
    '''
    The main function.
    '''
    arguments = get_arguments()

    # Build environment.
    if not arguments.skip_init:
        builder.init_env()
    builder.build_iotjs_and_nuttx()

    # Flash NuttX to the device.
    device.flash()

    # Run tests.
    testrunner = TestRunner(arguments)
    testrunner.run()
    testrunner.save()


if __name__ == '__main__':
    main()

# python -m json.tool result.json | less
