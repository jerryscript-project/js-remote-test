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
import atexit
import sys

import jstest
from jstest import Builder, TestResult, TestRunner
from jstest import flasher, paths, pseudo_terminal, utils


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
                        choices=['stm32f4dis', 'rpi2', 'artik053', 'artik530'],
                        default='stm32f4dis',
                        help='specify the target device (default: %(default)s)')

    parser.add_argument('--public',
                        action='store_true', default=False,
                        help='upload the test results (default: %(default)s)')

    parser.add_argument('--timeout',
                        metavar='SEC', default=180, type=int,
                        help='specify the timeout (default: %(default)s sec)')

    parser.add_argument('--no-memstat',
                        action='store_true', default=False,
                        help='do not measure memory statistics (default: %(default)s)')

    parser.add_argument('--coverage',
                        metavar='SERVER_ADDRESS(HOST:PORT)',
                        help='use jerry-debugger to calculate the JS source code coverage')

    parser.add_argument('--quiet',
                        action='store_true', default=False,
                        help='display less verbose output')

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

    group.add_argument('--emulate',
                       default=False, action='store_true',
                       help='Emulate the serial connection.')

    group = parser.add_argument_group("Telnet communication")

    group.add_argument('--router',
                       metavar='ROUTERADDR',
                       default='10.0.0.1',
                       help='specify the router address')

    group.add_argument('--netmask',
                       metavar='NETMASK',
                       default='255.255.255.0',
                       help='specify the netmask')

    return parser.parse_args()


def adjust_options(options):
    '''
    Adjust some of the command line arguments.
    '''
    if options.device == 'artik530' and options.app == 'jerryscript':
        jstest.console.warning('JerryScript is not supported for Tizen.')
        options.no_build = True
        options.no_flash = True
        options.no_test = True

    if options.emulate:
        options.no_flash = True

        if options.device in ['rpi2', 'artik530']:
            options.no_test = True

        else:
            options.device_id = pseudo_terminal.open_pseudo_terminal(options.device)
            atexit.register(pseudo_terminal.close_pseudo_terminal, options)

    if options.coverage:
        if options.app != 'iotjs':
            jstest.console.warning('Coverage measurement is only supported with IoT.js!')
            options.coverage = None

        elif options.buildtype != 'debug':
            jstest.console.warning('Coverage measurement is only supported with debug build type!')
            # Overwrite the buildtype option to debug.
            # In IoT.js the code is minimized in release mode, which will mess up the line numbers.
            options.buildtype = 'debug'

    if options.quiet:
        utils.define_environment('QUIET', 1)

        if utils.get_environment('VERBOSE'):
            jstest.console.warning('--quiet option disables VERBOSE output!')

    return options


def main():
    '''
    Main function of the remote testrunner.
    '''
    user_options = adjust_options(parse_options())
    testresult = TestResult(user_options)

    try:
        # Execute all the jobs defined in the runnalble.jobs file.
        for job_options in utils.read_json_file(paths.RUNNABLE_JOBS):
            env = jstest.create_testing_environment(user_options, job_options)

            builder = Builder(env)
            builder.build()

            flasher.flash(env)

            testrunner = TestRunner(env)
            testrunner.run()
            testrunner.save()

            testresult.append(env.options.id, env.paths.builddir)
        # Upload all the results to the Firebase database.
        testresult.upload()

    except (Exception, KeyboardInterrupt) as e:
        jstest.resources.patch_modules(env, revert=True)
        jstest.console.error('[%s] %s' % (type(e).__name__, str(e)))

        sys.exit(1)


if __name__ == '__main__':
    main()
