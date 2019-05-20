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
import traceback

import jstest
from jstest import Builder, TestResult, TestRunner
from jstest import flasher, paths, pseudo_terminal, twisted_server, utils


EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def parse_options():
    '''
    Parse the given options.
    '''
    parser = argparse.ArgumentParser(description='[J]ava[S]cript [remote] [test]runner',
                                     prog='jstest')

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

    parser.add_argument('--debugger', nargs='?', const='no_address', metavar='ADDRESS',
                        help='Enable jerry debugger (Set ADDRESS to run debugger at startup')

    parser.add_argument('--device',
                        choices=['stm32f4dis', 'rpi2', 'artik053', 'rpi3'],
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
                        action='store_true', default=False,
                        help='calculate the JS source code coverage (default: %(default)s)')

    parser.add_argument('--quiet',
                        action='store_true', default=False,
                        help='display less verbose output')

    parser.add_argument('--emulate',
                       default=False, action='store_true',
                       help='emulate the connection')

    parser.add_argument('--testsuite',
                        metavar='TEST_SUITE_PATH',
                        help='specify the path to user-owned tests')

    group = parser.add_argument_group("Secure Shell communication")

    group.add_argument('--username',
                       metavar='USER',
                       help='specify the username to login to the device')

    group.add_argument('--password',
                       help='specify the password to login to the device')

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
    if options.device == 'rpi3' and options.app == 'jerryscript':
        jstest.console.warning('JerryScript is not supported for Tizen.')
        sys.exit(1)

    # TODO: resolve this section, debugger should work on every target.
    if options.debugger:
        if options.device == 'stm32f4dis':
            jstest.console.warning('Debugger is disabled, beacuse it is not supported on'
                                   ' STM32F4-Discovery')
            options.debugger = None
        elif options.device == 'artik053' and options.app == 'jerryscript':
            jstest.console.warning('Debugger is disabled, because it is not supported on'
                                   ' ARTIK053 with JerryScript')
            options.debugger = None

    if options.emulate:
        options.no_flash = True

        if options.device in ['rpi2', 'rpi3']:
            options.username = 'js-remote-test'
            options.password = 'jerry'
            options.ip = '127.0.0.1'
            options.port = 2022
            options.remote_workdir = 'emulated_workdir'

            twisted_server.run(options.device)
            atexit.register(twisted_server.stop)

        else:
            options.device_id = pseudo_terminal.open_pseudo_terminal(options.device)
            atexit.register(pseudo_terminal.close_pseudo_terminal, options)

    if options.coverage:
        if not options.debugger or options.debugger == 'no_address':
            jstest.console.error('Coverage measurement is require the enabled debugger option'
                                 ' with a valid server ADDRESS')
            sys.exit(1)

        if options.app != 'iotjs':
            jstest.console.warning('Coverage measurement is only supported with IoT.js!')
            sys.exit(1)

        if options.buildtype != 'debug':
            jstest.console.warning('Buidltype was set to debug because the coverage measurement is'
                                   ' only supported with debug build type!')
            # Overwrite the buildtype option to debug.
            # In IoT.js the code is minimized in release mode, which will mess up the line numbers.
            options.buildtype = 'debug'

    if options.quiet:
        utils.define_environment('QUIET', 1)

        if utils.get_environment('VERBOSE'):
            jstest.console.warning('--quiet option disables VERBOSE output!')

    if options.testsuite:
        options.testsuite = utils.abspath(options.testsuite)

    if options.app_path:
        options.app_path = utils.abspath(options.app_path)

    return options


def main():
    '''
    Main function of the remote testrunner.
    '''
    user_options = adjust_options(parse_options())
    testresult = TestResult(user_options)
    exitcode = EXIT_SUCCESS

    try:
        # Execute all the jobs defined in the runnable.jobs file.
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
        # Don't print backtrace for keyboard interrupt.
        if isinstance(e, Exception):
            traceback.print_exc()

        exitcode = EXIT_FAILURE

    # Revert all the patches and restore all the modified files.
    jstest.resources.finalize(env)

    sys.exit(exitcode)


if __name__ == '__main__':
    main()
