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

import connection
import json
import time

from ..common import (console, paths, utils)


class Device(base.DeviceBase):
    '''
    Device class for the stm32f4-discovery board.
    '''
    def __init__(self, options):
        super(self.__class__, self).__init__('rpi2', remote_path=options.remote_path)

        self.ssh = connection.sshcom.Connection(options)

    def install_dependencies(self):
        '''
        Install dependencies of the board.
        '''
        pass

    def flash(self, os):
        '''
        Send the application and the testsuite to the device with SFTP.
        '''
        app = os.get_app()

        lpath_app = app.get_image()
        lpath_testsuite = utils.make_archive(app.get_test_dir(), 'tar')

        rpath_app = utils.join(self.remote_path, app.get_cmd())
        rpath_testsuite = utils.join(self.remote_path, 'test.tar')

        self.ssh.open()

        # Clean up in the remote folder.
        self.ssh.exec_command('rm -f ' + rpath_app)
        self.ssh.exec_command('rm -f ' + rpath_testsuite)
        self.ssh.exec_command('rm -rf ' + self.get_test_path())

        # Send the application and the testsuite.
        self.ssh.send_file(lpath_app, rpath_app)
        self.ssh.send_file(lpath_testsuite, rpath_testsuite)

        # Let the iotjs to be runnable and extract the tests.
        self.ssh.exec_command('chmod 770 ' + rpath_app)
        self.ssh.exec_command('mkdir ' + self.get_test_path())
        self.ssh.exec_command('tar -xmf ' + rpath_testsuite + ' -C ' + self.get_test_path())

    def reset(self):
        '''
        Since the SSH library stops the process in case of timeout, don't need any reset.
        '''
        pass

    def execute(self, cmd, args=[]):
        '''
        Run the given command on the board.
        '''
        command_template = 'python {root}/tester.py --cwd {cwd} --cmd {app} --testfile {file}'

        command = command_template.format(root=self.remote_path,
                                          cwd=self.get_test_path(),
                                          app=utils.join(self.remote_path, cmd),
                                          file=''.join(args))

        stdout = self.ssh.exec_command(command)

        # Since the stdout is a JSON text, parse it.
        result = json.loads(stdout)

        # Make HTML friendly stdout.
        stdout = result['output'].rstrip('\n').replace('\n', '<br>')

        return result['exitcode'], stdout, result['mempeak']
