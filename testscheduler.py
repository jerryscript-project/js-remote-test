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

import schedule
import time

import testrunner

from resources import builder
from resources import device
from resources import utils


def run_tests(testrunner):
    '''
    Main scheduled function.
    '''
    builder.update_iotjs()

    if not utils.shoud_test():
        return

    # Update IoT.js and build NuttX.
    builder.build_iotjs_and_nuttx()

    # Flash NuttX to the device.
    device.flash()

    # Run the tests.
    testrunner.run()
    testrunner.save()


def main():
    '''
    The main function.
    '''
    arguments = testrunner.get_arguments()

    # Build environment.
    if not arguments.skip_init:
        builder.init_env()

    # Scheduling the testing function.
    schedule.every().day.at("10:30").do(run_tests, testrunner.TestRunner(arguments))

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
