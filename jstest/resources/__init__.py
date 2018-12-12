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


from jstest.common import paths, utils


def fetch_modules(env):
    '''
    Download all the required modules.
    '''
    for module in env.modules.values():
        # Skip if the module is already exist.
        if utils.exists(module['src']):
            continue

        fetch_url = module['url']
        fetch_dir = module['src']

        utils.execute('.', 'git', ['clone', fetch_url, fetch_dir])
        utils.execute(module['src'], 'git', ['checkout', module['version']])
        utils.execute(module['src'], 'git', ['submodule', 'update', '--init'])


def config_modules(env, revert=False):
    '''
    Configure all the required modules.
    '''
    for module in env.modules.values():
        for config in module.get('config', []):
            # Do not configure if the result of the condition is false.
            condition = config.get('condition', 'True')

            if not eval(condition):
                continue

            if revert:
                utils.restore_file(module['src'], config['dst'])

            else:
                utils.symlink(config['src'], config['dst'])


def patch_modules(env, revert=False):
    '''
    Modify the source code of the required modules.
    '''
    for module in env.modules.values():
        # Get patches that belong to the current job.
        for patch in module.get('patches', {}).get(env.options.id, []):
            # Do not patch if the result of the condition is false.
            condition = patch.get('condition', 'True')

            if not eval(condition):
                continue

            # By default, the project is patched. If there is a
            # submodule information, the subproject will be patched.
            project = patch.get('submodule', module['src'])
            utils.patch(project, patch['file'], revert)


def initialize(env):
    '''
    Public method to initialize the project.
    '''
    fetch_modules(env)
    config_modules(env)
    patch_modules(env)


def finalize(env):
    '''
    Public method to restore the project files.
    '''
    config_modules(env, revert=True)
    patch_modules(env, revert=True)
