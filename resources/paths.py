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
ROOT_FOLDER = os.path.join(os.path.dirname(__file__), os.pardir)

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

# Path to the iotjs folder.
IOTJS_PATH = os.path.join(PROJECTS_ROOT, 'iotjs')

# Path to the tools folder within iotjs.
IOTJS_TOOLS_PATH = os.path.join(IOTJS_PATH, 'tools')

# Path to the apps folder within iotjs.
IOTJS_APPS_PATH = os.path.join(IOTJS_PATH, 'config/nuttx/stm32f4dis/app/')

# Path to the build folder within iotjs.
IOTJS_BUILD_PATH = os.path.join(IOTJS_PATH, 'build/arm-linux/release/bin')

# Root directory of the test folder.
IOTJS_TEST_PATH = os.path.join(IOTJS_PATH, 'test')

# Path to the run_pass folder within test.
IOTJS_TEST_RUN_PASS_PATH = os.path.join(IOTJS_TEST_PATH, 'run_pass')

# Path to the run_fail folder within test.
IOTJS_TEST_RUN_FAIL_PATH = os.path.join(IOTJS_TEST_PATH, 'run_fail')

# Path to the kconfig-frontends folder.
KCONFIG_PATH = os.path.join(PROJECTS_ROOT, 'kconfig-frontends')

# Path to the stlink folder.
STLINK_PATH = os.path.join(PROJECTS_ROOT, 'stlink')

# Path to the build folder within stlink.
STLINK_BUILD_PATH = os.path.join(STLINK_PATH, 'build/Release/')

# Path to the apps folder.
APPS_PATH = os.path.join(PROJECTS_ROOT, 'apps')

# Path to the nshlib folder within apps.
NSHLIB_PATH = os.path.join(APPS_PATH, 'nshlib')

# Path to the iotjs folder within apps.
APPS_IOTJS_PATH = os.path.join(APPS_PATH, 'system/iotjs')

# Path to the nuttx folder.
NUTTX_PATH = os.path.join(PROJECTS_ROOT, 'nuttx')

# Path to the tools folder within nuttx.
NUTTX_TOOLS_PATH = os.path.join(NUTTX_PATH, 'tools')

#
# ================================
#

OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'results')

#
# ================================
#

# Path to the web folder.
WEB_PATH = os.path.join(PROJECTS_ROOT, 'web')

# Path to the data folder within web.
WEB_DATA_PATH = os.path.join(WEB_PATH, 'data')

#
# ================================
#

# Path to the device folder.
DEVICE_DEV_PATH = '/dev'

# Path to the mounted mmcsd foler.
DEVICE_MOUNTED_MMCSD_PATH = '/mount/sdcard'

# Path to the mounted ROMFS test folder.
DEVICE_TEST_PATH = '/test'
