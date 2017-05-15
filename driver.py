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

import API.application
import API.device
import API.os
import API.resultsaver
import API.testrunner


def parse_arguments():
    '''
    Parse the given arguments.
    '''
    parser = argparse.ArgumentParser('Remote testrunner for microcontrollers')

    parser.add_argument('--app', choices=['iotjs', 'jerryscript'], default='iotjs',
                        help='the target application (default: %(default)s)')

    parser.add_argument('--branch', metavar='name', default='master',
                        help='an existing branch name for the app (default: %(default)s)')

    parser.add_argument('--buildtype', choices=['release', 'debug'], default='release',
                        help='buildtype for the os and the app (default: %(default)s)')

    parser.add_argument('--commit', metavar='hash', default='HEAD',
                        help='an existing hash within a branch (default: %(default)s)')

    parser.add_argument('--device', choices=['stm32f4dis', 'fake', 'rpi2'], default='stm32f4dis',
                        help='indicate the device for testing (default: %(default)s)')

    parser.add_argument('--address', metavar='address',
                        help='address of the target device (ip or ip:port)')

    parser.add_argument('--os', choices=['nuttx'], default='nuttx',
                        help='the target oprating system (default: %(default)s)')

    parser.add_argument('--public', action='store_true', default=False,
                        help='pusblish results to the web (default: %(default)s)')

    parser.add_argument('--timeout', metavar='sec', type=int, default=180,
                        help='timeout for tests (default: %(default)s sec)')

    parser.add_argument('--username', metavar='nick', default='pi',
                        help='User name to login to the board.')

    parser.add_argument('--remote-path', metavar='path', default='/',
                        help='The root path of the remote testing on the device.')

    return parser.parse_args()


def main():
    '''
    Main function of the remote testrunner.
    '''
    arguments = parse_arguments()

    device = API.device.create(arguments.device)
    device.set_root_path(arguments.remote_path)
    device.set_username(arguments.username)
    device.set_address(arguments.address)
    device.set_timeout(arguments.timeout)

    app = API.application.create(arguments.app, arguments.os, device)
    app.update_repository(arguments.branch, arguments.commit)

    os = API.os.create(arguments.os, device, app)

    os.prebuild()
    app.build(arguments.buildtype)
    os.build(arguments.buildtype, 'all')

    device.flash(os)

    testrunner = API.testrunner.create(os, app, device)
    testrunner.run()

    resultsaver = API.resultsaver.create("default", testrunner)
    resultsaver.save(arguments.public)


if __name__ == '__main__':
    main()
