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

from jstest.common import utils, paths


def flash(env):
    '''
    Flash the device.
    '''
    if env.options.no_flash:
        return

    config = utils.read_config_file(paths.FLASH_CONFIG_FILE, env)
    # Get the device specific flash instructions.
    flash_info = config[env.options.device]

    # Do the initialization steps.
    for command in flash_info.get('init', []):
        utils.execute_config_command(command)
    # Flash the device.
    utils.execute_config_command(flash_info.get('flash'))
