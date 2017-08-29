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

# Root directory for the project (dirname).
ROOT_FOLDER = os.path.join(os.path.dirname(__file__), '../..')

#
# ================================
#

# Root directory for the project (abs path).
PROJECT_ROOT = os.path.abspath(ROOT_FOLDER)

#
# ================================
#

# Path to the config folder.
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config')

#
# ================================
#

# Path to the submodule folder.
PROJECTS_ROOT = os.path.join(PROJECT_ROOT, 'projects')

#
# ================================
#

# Path to the memstat pathes.
PATCHES_PATH = os.path.join(PROJECT_ROOT, 'patches')

#
# ================================
#

OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'results')

#
# ================================
#

# Path to the iotjs-test-results folder.
IOTJS_WEB_PATH = os.path.join(PROJECTS_ROOT, 'iotjs-test-results')

# Path to the data folder within iotjs-test-results.
IOTJS_WEB_DATA_PATH = os.path.join(IOTJS_WEB_PATH, 'data')

# Path to the jerryscript-test-results folder.
JERRY_WEB_PATH = os.path.join(PROJECTS_ROOT, 'jerryscript-test-results')

# Path to the data folder within jerryscript-test-results.
JERRY_WEB_DATA_PATH = os.path.join(JERRY_WEB_PATH, 'data')

#
# ================================
#

# Path to the iotjs folder.
IOTJS_PATH = os.path.join(PROJECTS_ROOT, 'iotjs')

# Path to the apps folder within iotjs.
IOTJS_APPS_PATH = os.path.join(IOTJS_PATH, 'config/nuttx/stm32f4dis/app/')

# Path to the build folder within iotjs.
IOTJS_BUILD_PATH = os.path.join(IOTJS_PATH, 'build/arm-linux/%s/bin')

# Root directory of the test folder.
IOTJS_TEST_PATH = os.path.join(IOTJS_PATH, 'test')

# Path to the minimal build folder.
IOTJS_MINIMAL_BUILD_PATH = os.path.join(IOTJS_PATH, 'features_disable/build')

# Path to the bin folder of the minimal build.
IOTJS_MINIMAL_BIN_PATH = os.path.join(IOTJS_MINIMAL_BUILD_PATH, 'arm-linux/%s/bin/')

# Path to the deps/libtuv folder.
IOTJS_LIBTUV_PATH = os.path.join(IOTJS_PATH, 'deps/libtuv')

# Path to the deps/jerry folder.
IOTJS_JERRY_PATH = os.path.join(IOTJS_PATH, 'deps/jerry')

# Path to the config folder within iotjs.
IOTJS_CONFIG_PATH = os.path.join(IOTJS_PATH, 'config')

# Path to the tizenrt apps folder within iotjs.
IOTJS_TIZENRT_APPS_PATH = os.path.join(IOTJS_CONFIG_PATH, 'tizenrt/artik05x/app/')

# Path to the tizenrt config folder within iotjs.
IOTJS_TIZENRT_CONFIGS_PATH = os.path.join(IOTJS_CONFIG_PATH, 'tizenrt/artik05x/configs/')

# Path to the lib folder of the tizenrt build.
IOTJS_TIZENRT_BUILD_PATH = os.path.join(IOTJS_PATH, 'build/arm-tizenrt/%s/lib')

#
# ================================
#

# Path to the stlink folder.
STLINK_PATH = os.path.join(PROJECTS_ROOT, 'stlink')

# Path to the build folder within stlink.
STLINK_BUILD_PATH = os.path.join(STLINK_PATH, 'build/Release/')

#
# ================================
#

# Path to the nuttx folder.
NUTTX_PATH = os.path.join(PROJECTS_ROOT, 'nuttx')

# Path to the tools folder within nuttx.
NUTTX_TOOLS_PATH = os.path.join(NUTTX_PATH, 'tools')

# Path to the apps folder.
NUTTX_APPS_PATH = os.path.join(PROJECTS_ROOT, 'apps')

# Path to the nshlib folder within apps.
NUTTX_APPS_NSHLIB_PATH = os.path.join(NUTTX_APPS_PATH, 'nshlib')

# Path to the iotjs folder within apps.
NUTTX_APPS_SYSTEM_PATH = os.path.join(NUTTX_APPS_PATH, 'system')

# Path to the interpreter.
NUTTX_APPS_INTERPRETER_PATH = os.path.join(NUTTX_APPS_PATH, 'interpreters')

#
# ================================
#

# Path to the tizenrt folder.
TIZENRT_PATH = os.path.join(PROJECTS_ROOT, 'TizenRT')

# Path to the apps folder.
TIZENRT_APPS_PATH = os.path.join(TIZENRT_PATH, 'apps')

# Path to the os folder.
TIZENRT_OS_PATH = os.path.join(TIZENRT_PATH, 'os')

# Path to the system app folder.
TIZENRT_APP_SYSTEM_PATH = os.path.join(TIZENRT_APPS_PATH, 'system')

# Path to the build folder.
TIZENRT_BUILD_PATH = os.path.join(TIZENRT_PATH, 'build')

# Path to the tools folder within nuttx.
TIZENRT_TOOLS_PATH = os.path.join(TIZENRT_OS_PATH, 'tools')

# Path to the tizenrt configs folder.
TIZENRT_CONFIGS_PATH = os.path.join(TIZENRT_BUILD_PATH, 'configs')

# Path to the openocd folder.
TIZENRT_OPENOCD_PATH = os.path.join(TIZENRT_CONFIGS_PATH, 'artik053/tools/openocd')

# Path to the build output folder.
TIZENRT_BUILD_OUTPUT_PATH = os.path.join(TIZENRT_BUILD_PATH, 'output')

# Path to the build libraries folder.
TIZENRT_BUILD_LIBRARIES_PATH = os.path.join(TIZENRT_BUILD_OUTPUT_PATH, 'libraries')

# Path to the bin folder.
TIZENRT_BIN_PATH = os.path.join(TIZENRT_BUILD_OUTPUT_PATH, 'bin')

#
# ================================
#

# Path to the iotjs folder.
JERRY_PATH = os.path.join(PROJECTS_ROOT, 'jerryscript')

# Path to the apps folder within jerry.
JERRY_APPS_PATH = os.path.join(JERRY_PATH, 'targets/nuttx-stm32f4/')

# Path to the targets folder within jerry.
JERRY_TARGETS_PATH = os.path.join(JERRY_PATH, 'targets')

JERRY_TEST_JERRY_PATH = os.path.join(JERRY_PATH, 'tests/jerry')

JERRY_BUILD_PATH = os.path.join(JERRY_PATH, 'build/bin')

JERRY_MINIMAL_BUILD_PATH = os.path.join(JERRY_PATH, 'features_disable/build')

JERRY_MINIMAL_BIN_PATH = os.path.join(JERRY_MINIMAL_BUILD_PATH, 'bin')
