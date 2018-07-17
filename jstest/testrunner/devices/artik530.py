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
from threading import Thread

from jstest.testrunner.devices.device_base import RemoteDevice
from jstest.common import utils, paths
from jstest.testrunner import utils as testrunner_utils
from jstest.testrunner.devices.connections.sshcom import SSHConnection

class ARTIK530Device(RemoteDevice):
    '''
    Device of the ARTIK530 target.
    '''
    def __init__(self, env):
        self.os = 'tizen'

        RemoteDevice.__init__(self, env)

        data = {
            'username': self.user,
            'ip': self.ip,
            'port': self.port,
            'timeout': env['info']['timeout']
        }

        self.channel = SSHConnection(data)

    def initialize(self):
        '''
        Flash the device.
        '''
        if self.env['info']['no_flash']:
            return

        target_app = self.env['modules']['app']
        build_path = self.env['paths']['build']

        test_src = target_app['paths']['tests']
        test_dst = utils.join(build_path, 'tests')

        # 1. Copy all the necessary files.
        # Copy applicaiton RPM package file.
        rpm_package_path = self.env['paths']['tizen-rpm-package']
        utils.copy(rpm_package_path, build_path)

        # Copy all the tests into the build folder.
        utils.copy(test_src, test_dst)

        utils.copy(paths.FREYA_TESTER, build_path)

        if not self.env['info']['no_memstat']:
            utils.copy(paths.FREYA_CONFIG, build_path)

            # Resolve the iotjs-dirname macro in the Freya configuration file.
            basename = utils.basename(paths.GBS_IOTJS_PATH)
            sed_flags = ['-i', 's/%%{iotjs-dirname}/%s/g' % basename, 'iotjs-freya.config']
            utils.execute(build_path, 'sed', sed_flags)

        # 2. Deploy the build folder to the device.
        self.login()
        self.channel.exec_command('mount -o remount,rw /')

        shell_flags = 'ssh -p %s' % self.port
        rsync_flags = ['--rsh', shell_flags, '--recursive', '--compress', '--delete']
        # Note: slash character is required after the path.
        # In this case `rsync` copies the whole folder, not
        # the subcontents to the destination.
        src = self.env['paths']['build'] + '/'
        dst = '%s@%s:%s' % (self.user, self.ip, self.workdir)

        utils.execute('.', 'rsync', rsync_flags + [src, dst])

        # 3. Install rpm package
        template = 'rpm -ivh --force --nodeps %s/%s-1.0.0-0.armv7l.rpm'
        self.channel.exec_command(template % (self.workdir, self.app))

        self.logout()

    def execute(self, testset, test):
        '''
        Execute the given test.
        '''
        self.login()

        template = 'python %s/tester.py --cwd %s --cmd %s --testfile %s'
        # Absolute path to the test folder.
        testdir = '%s/tests' % self.workdir
        # Absolute path to the test file.
        testfile = '%s/%s/%s' % (testdir, testset, test['name'])
        # Absolute path to the application.
        iotjs = '%s/iotjs' % self.workdir

        # Create the command that the device will execute.
        command = template % (self.workdir, testdir, iotjs, testfile)

        if self.env['info']['no_memstat']:
            command += ' --no-memstat'

        if self.env['info']['coverage'] and self.app == 'iotjs':
            port = testrunner_utils.read_port_from_url(self.env['info']['coverage'])
            command += ' --coverage-port %s' % port

            # Start the client script on a different thread for coverage.
            client_thread = Thread(target=testrunner_utils.run_coverage_script, kwargs={'env': self.env})
            client_thread.daemon = True
            client_thread.start()

        stdout = self.channel.exec_command(command)

        # Since the stdout is a JSON text, parse it.
        result = json.loads(stdout)
        # Make HTML friendly stdout.
        result['output'] = result['output'].rstrip('\n').replace('\n', '<br>')

        self.logout()

        return result
