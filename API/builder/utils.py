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

from API.common import utils, console, paths

def create_build_info(env):
    '''
    Write binary size and commit information into a file.
    '''
    app_name = env['info']['app']
    build_path = env['paths']['build']

    # Binary size information.
    minimal_builddir = env['paths']['build-minimal']
    target_builddir = env['paths']['build-target']

    bin_sizes = {
        'minimal-profile': utils.calculate_section_sizes(minimal_builddir),
        'target-profile': utils.calculate_section_sizes(target_builddir)
    }

    # Git commit information from the projects.
    submodules = {}

    for name, module in env['modules'].iteritems():
        # Don't duplicate the application information.
        if name == 'app':
            continue

        submodules[name] = utils.last_commit_info(module['src'])

    # Merge the collected values into a result object.
    build_info = {
        'build-date': utils.get_standardized_date(),
        'last-commit-date': submodules[app_name]['date'],
        'bin': bin_sizes,
        'submodules': submodules
    }

    utils.write_json_file(utils.join(build_path, 'build.json'), build_info)
