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
    parser = argparse.ArgumentParser('Remote testrunner for microcontrollers')

    parser.add_argument('--app', choices=['iotjs', 'jerryscript'], default='iotjs',
                        help='the target application (default: %(default)s)')

    parser.add_argument('--buildtype', choices=['release', 'debug'], default='release',
                        help='buildtype for the os and the app (default: %(default)s)')

    parser.add_argument('--device', choices=['stm32f4dis', 'rpi2', 'artik053'], default='stm32f4dis',
                        help='indicate the device for testing (default: %(default)s)')

    parser.add_argument('--public', action='store_true', default=False,
                        help='pusblish results to the web (default: %(default)s)')

    parser.add_argument('--timeout', metavar='sec', type=int, default=180,
                        help='timeout for tests (default: %(default)s sec)')

    group = parser.add_argument_group("SSH communication")

    group.add_argument('--username', metavar='nick',
                       help='username of the target device')

    group.add_argument('--address', metavar='address',
                        help='address of the target device (ip or ip:port)')

    group.add_argument('--remote-path', metavar='path',
                        help='remote test folder on the device')

    group = parser.add_argument_group("Serial communication")

    group.add_argument('--port', metavar='device',
                       help='serial port name (e.g. /dev/ttyACM0 or /dev/ttyUSB0)')

    group.add_argument('--baud', metavar='baud', type=int, default=115200,
                       help='baud rate (default: %(default)s)')

    return parser.parse_args()


def main():
    '''
    Main function of the remote testrunner.
    '''
    options = parse_options()

    device = API.device.create(options)
    app = API.application.create(options)

    app.build(device)

    device.flash(app)

    testrunner = API.testrunner.TestRunner()
    testrunner.run(app, device, options.public)

if __name__ == '__main__':
    main()
