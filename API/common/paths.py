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

import os

# Root directory of the project (dirname).
ROOT_FOLDER = os.path.join(os.path.dirname(__file__), '../..')

# Root directory of the project (abs path).
PROJECT_ROOT = os.path.abspath(ROOT_FOLDER)

# Files for the NuttX/TizenRT measurement.
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config')

# Folder where the submodules can be found.
PROJECTS_ROOT = os.path.join(PROJECT_ROOT, 'projects')

# Folder where the necessary patch files can be found.
PATCHES_PATH = os.path.join(PROJECT_ROOT, 'patches')

# Folder where the results can be found.
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'results')

# Scripts for the js-remote-test project.
TOOLS_PATH = os.path.join(PROJECT_ROOT, 'tools')

# Files for the RPi2 measurement.
RESOURCES_PATH = os.path.join(PROJECT_ROOT, 'resources')

#
# ================ IoT.js ================
#

IOTJS_PATH = os.path.join(PROJECTS_ROOT, 'iotjs')

IOTJS_APPS_PATH = os.path.join(IOTJS_PATH, 'config/nuttx/stm32f4dis/app/')

IOTJS_BUILD_PATH = os.path.join(IOTJS_PATH, 'build/arm-linux/%s/bin')

IOTJS_TEST_PATH = os.path.join(IOTJS_PATH, 'test')

IOTJS_LIBTUV_PATH = os.path.join(IOTJS_PATH, 'deps/libtuv')

IOTJS_JERRY_PATH = os.path.join(IOTJS_PATH, 'deps/jerry')

IOTJS_TEST_PROFILES_PATH = os.path.join(IOTJS_PATH, 'test/profiles')

IOTJS_MINIMAL_PROFILE_PATH = os.path.join(IOTJS_PATH, 'profiles/minimal.profile')

IOTJS_MAP_DIR_PATH = os.path.join(IOTJS_PATH, "map")

IOTJS_MINIMAL_MAP_FILE_PATH = os.path.join(IOTJS_MAP_DIR_PATH, 'minimal_profile.map')

IOTJS_TARGET_MAP_FILE_PATH = os.path.join(IOTJS_MAP_DIR_PATH, 'target_profile.map')

IOTJS_BUILD_STACK_DIR = os.path.join(IOTJS_PATH, 'build_stack')

IOTJS_BUILD_STACK_PATH = os.path.join(IOTJS_BUILD_STACK_DIR, 'arm-linux/%s/bin/')

#
# ================ Stlink ================
#

STLINK_PATH = os.path.join(PROJECTS_ROOT, 'stlink')

STLINK_BUILD_PATH = os.path.join(STLINK_PATH, 'build/Release/')

#
# ================ NuttX ================
#

NUTTX_PATH = os.path.join(PROJECTS_ROOT, 'nuttx')

NUTTX_TOOLS_PATH = os.path.join(NUTTX_PATH, 'tools')

NUTTX_APPS_PATH = os.path.join(PROJECTS_ROOT, 'apps')

NUTTX_APPS_NSHLIB_PATH = os.path.join(NUTTX_APPS_PATH, 'nshlib')

NUTTX_APPS_SYSTEM_PATH = os.path.join(NUTTX_APPS_PATH, 'system')

NUTTX_APPS_INTERPRETER_PATH = os.path.join(NUTTX_APPS_PATH, 'interpreters')

#
# ================ TizenRT ================
#

TIZENRT_PATH = os.path.join(PROJECTS_ROOT, 'TizenRT')

TIZENRT_APPS_PATH = os.path.join(TIZENRT_PATH, 'apps')

TIZENRT_OS_PATH = os.path.join(TIZENRT_PATH, 'os')

TIZENRT_APP_SYSTEM_PATH = os.path.join(TIZENRT_APPS_PATH, 'system')

TIZENRT_BUILD_PATH = os.path.join(TIZENRT_PATH, 'build')

TIZENRT_TOOLS_PATH = os.path.join(TIZENRT_OS_PATH, 'tools')

TIZENRT_CONFIGS_PATH = os.path.join(TIZENRT_BUILD_PATH, 'configs')

TIZENRT_OPENOCD_PATH = os.path.join(TIZENRT_CONFIGS_PATH, 'artik053/tools/openocd')

TIZENRT_FS_PATH = os.path.join(TIZENRT_PATH, 'tools/fs')

TIZENRT_ROMFS_CONTENTS_PATH = os.path.join(TIZENRT_FS_PATH, 'contents')

#
# ================ JerryScript ================
#

JERRY_PATH = os.path.join(PROJECTS_ROOT, 'jerryscript')

JERRY_APPS_PATH = os.path.join(JERRY_PATH, 'targets/nuttx-stm32f4/')

JERRY_TARGETS_PATH = os.path.join(JERRY_PATH, 'targets')

JERRY_TEST_JERRY_PATH = os.path.join(JERRY_PATH, 'tests/jerry')

JERRY_BUILD_PATH = os.path.join(JERRY_PATH, 'build/bin')

JERRY_MINIMAL_BUILD_PATH = os.path.join(JERRY_PATH, 'features_disable/build')

JERRY_MINIMAL_BIN_PATH = os.path.join(JERRY_MINIMAL_BUILD_PATH, 'bin')

#
# ================ Freya ================
#

FREYA_PATH = os.path.join(PROJECTS_ROOT, 'Freya')
