#!/usr/bin/env python

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

import argparse

import API


def parse_options():
    '''
    Parse the given options.
    '''
    parser = argparse.ArgumentParser(description='[J]ava[S]cript [remote] [test]runner')

    parser.add_argument('--app',
                        choices=['iotjs', 'jerryscript'], default='iotjs',
                        help='specify the target application (default: %(default)s)')

    parser.add_argument('--app-path',
                        metavar='PATH',
                        help='specify the path to the application (default: %(default)s)')

    parser.add_argument('--buildtype',
                        choices=['release', 'debug'], default='release',
                        help='specify the build type (default: %(default)s)')

    parser.add_argument('--no-build',
                        action='store_true', default=False,
                        help='do not build the projects (default: %(default)s)')

    parser.add_argument('--no-profile-build',
                        action='store_true', default=False,
                        help='do not build the different profiles (default: %(default)s)')

    parser.add_argument('--no-flash',
                        action='store_true', default=False,
                        help='do not flash the device (default: %(default)s)')

    parser.add_argument('--no-test',
                        action='store_true', default=False,
                        help='do not test the application (default: %(default)s)')

    parser.add_argument('--device',
                        choices=['stm32f4dis', 'rpi2', 'artik053', 'artik530'], default='stm32f4dis',
                        help='specify the target device (default: %(default)s)')

    parser.add_argument('--public',
                        action='store_true', default=False,
                        help='upload the test results (default: %(default)s)')

    parser.add_argument('--timeout',
                        metavar='SEC', default=180, type=int,
                        help='specify the timeout (default: %(default)s sec)')

    parser.add_argument('--coverage',
                        metavar='SERVER_ADDRESS(HOST:PORT)',
                        help='use jerry-debugger to calculate the JS source code coverage')

    group = parser.add_argument_group("Secure Shell communication")

    group.add_argument('--username',
                       metavar='USER',
                       help='specify the username to login to the device.')

    group.add_argument('--ip',
                       metavar='IPADDR',
                       help='specify the IP address of the device')

    group.add_argument('--port',
                       metavar='PORT', default=22, type=int,
                       help='specify the SSH port (default: %(default)s)')

    group.add_argument('--remote-workdir',
                       metavar='PATH',
                       help='specify the test folder on the device')

    group = parser.add_argument_group("Serial communication")

    group.add_argument('--device-id',
                       metavar='DEVICE-ID',
                       help='specify the device ID (e.g. /dev/ttyACM0)')

    group.add_argument('--baud',
                       type=int, default=115200,
                       help='specify the baud rate (default: %(default)s)')

    return parser.parse_args()


def main():
    '''
    Main function of the remote testrunner.
    '''
    options = parse_options()

    # Get an environment object that holds all the necessary
    # information for the build and the test.
    env = API.load_testing_environment(options)

    # Initialize the testing environment by building all the
    # required modules to be ready to run tests.
    builder = API.builder.create(env)
    builder.create_profile_builds()
    builder.create_test_build()

    # Run all the tests.
    testrunner = API.testrunner.TestRunner(env)
    testrunner.run()
    testrunner.save()


if __name__ == '__main__':
    main()
