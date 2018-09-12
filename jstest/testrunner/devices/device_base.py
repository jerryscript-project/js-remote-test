# Copyright 2018-present Samsung Electronics Co., Ltd. and other contributors
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

import json
import time

from jstest.common import console
from jstest.testrunner import utils as testrunner_utils

class RemoteDevice(object):
    '''
    Base class of all the device classes.
    '''
    def __init__(self, env, os):
        self.env = env
        self.app = env.options.app
        self.device = env.options.device
        self.workdir = env.options.remote_workdir
        self.channel = None
        self.os = os

        self.check_args()

    def check_args(self):
        '''
        Check that all the arguments are established.
        '''
        if self.env.options.emulate:
            return

        if self.device not in ['rpi2', 'artik530', 'artik053', 'stm32f4dis']:
            console.fail('The selected device is not supported')

    def login(self):
        '''
        Login to the device.
        '''
        try:
            self.channel.open()

        except Exception as e:
            console.fail(str(e))

    def logout(self):
        '''
        Logout from the device.
        '''
        self.channel.close()

    def iotjs_build_info(self):
        '''
        Get buildinfo from iotjs.
        '''
        if self.device in ['rpi2', 'artik530']:
            iotjs = '%s/iotjs' % self.workdir
            buildinfo = '%s/tests/tools/iotjs_build_info.js' % self.workdir
            command = '%s %s' % (iotjs, buildinfo)

        elif self.device in ['artik053', 'stm32f4dis']:
            buildinfo = '/test/tools/iotjs_build_info.js'
            command = 'iotjs %s' % buildinfo

        # Wait a moment to boot the device.
        time.sleep(2)

        self.login()

        output = self.channel.exec_command(command)
        # Process the output to get the json string and the exitcode.
        build_info, _, exitcode = testrunner_utils.process_output(output)

        if exitcode != 0:
            console.fail('%s returned with exitcode %d' % (buildinfo, exitcode))

        info = json.loads(build_info)

        builtins = set(info['builtins'])
        features = set(info['features'])
        stability = info['stability']

        self.logout()

        return builtins, features, stability
