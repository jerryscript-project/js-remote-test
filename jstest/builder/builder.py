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

from jstest import resources
from jstest.common import utils, paths
from jstest.builder import utils as builder_utils


def init_modules(modules):
    '''
    Execute all the init commands that the modules define.
    '''
    for build_info in modules.values():
        for command in build_info.get('init', []):
            exec_cmd(command)


def build_modules(modules, builddir):
    '''
    Build all the modules and save the artifacts.
    '''
    # FIXME: remove the sorted function that helps to
    # build iotjs and jerryscript before NuttX.
    for _, build_info in sorted(modules.iteritems()):
        exec_cmd(build_info.get('build'))

        for artifact in build_info.get('artifacts', []):
            # Do not copy the artifact if not necessary.
            if 'dst' not in artifact:
                continue

            src = artifact.get('src')
            dst = artifact.get('dst')

            utils.copy(src, utils.join(builddir, dst))


def exec_cmd(command):
    '''
    Run the command defined in the build.config file.
    '''
    cwd = command.get('cwd', '.')
    cmd = command.get('cmd', '')
    args = command.get('args', [])
    env = command.get('env', {})

    # Update the arguments and the env variables with
    # the values under the condition-options.
    for option in command.get('conditional-options', []):
        if not eval(option.get('condition')):
            continue

        args.extend(option.get('args', []))
        env = utils.merge_dicts(env, option.get('env', {}))

    # Convert array values to string to be real env values.
    for key, value in env.iteritems():
        env[key] = ' '.join(value)

    utils.execute(cwd, cmd, args=args, env=env)


class Builder(object):
    '''
    A basic builder class to build all the required modules.
    '''
    def __init__(self, env):
        self.env = env
        self.device = env.options.device
        self.build_dir = env.paths.builddir

        # Do not initialize the modules if the build is disabled.
        if env.options.no_build:
            return

        # Fetch and configure the modules before build.
        resources.fetch_modules(env)
        resources.config_modules(env)
        resources.patch_modules(env)

    def build(self):
        '''
        Public method to build the module by the given build_info object.
        '''
        if self.env.options.no_build:
            return

        modules = self.read_modules()

        init_modules(modules)
        build_modules(modules, self.build_dir)

        # Create build information.
        builder_utils.create_build_info(self.env)
        # Revert all the patches from the projects.
        resources.patch_modules(self.env, revert=True)

    def should_build(self, build_info):
        '''
        Test weather a component should be built or not.
        '''
        condition = build_info.get('build-condition', 'True')

        if not eval(condition):
            return False

        # Always build the projects that don't have 'build-once' marker.
        if 'build-once' not in build_info:
            return True

        build_info = build_info[self.device]
        # Some projects don't require to build them over-and-over again.
        # e.g. Freya, ST-Link. In their case, just check if the project
        # has already built.
        for artifact in build_info.get('artifacts', []):
            src = artifact.get('src', '')
            dst = artifact.get('dst', '')

            # If dst is provided, check that first. If it doesn't, it's
            # enough just check the src.
            if dst and not utils.exists(utils.join(self.build_dir, dst)):
                return True

            if not dst and not utils.exists(src):
                return True

        return False

    def read_modules(self):
        '''
        Collect buildable modules and their build instructions.
        '''
        modules = {}

        for name in self.env.modules:
            filename = utils.join(paths.BUILDER_MODULES_PATH, '%s.build.config' % name)
            # Skip modules that don't have configuration file (e.g. nuttx-apps).
            if not utils.exists(filename):
                continue

            build_info = utils.read_config_file(filename, self.env)
            # Check if the project is alredy built.
            if self.should_build(build_info):
                modules[name] = build_info[self.device]

        return modules
