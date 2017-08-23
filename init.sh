#! /bin/bash

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

PROJECTS_DIR="projects"

if [ -d $PROJECTS_DIR ]; then
  echo "The \"$PROJECTS_DIR\" folder already exists, please remove it first!"
  exit 1
else
  mkdir $PROJECTS_DIR
fi

git -C $PROJECTS_DIR clone https://github.com/jameswalmsley/kconfig-frontends.git
git -C $PROJECTS_DIR clone https://github.com/texane/stlink.git
git -C $PROJECTS_DIR clone https://github.com/Samsung/iotjs.git
git -C $PROJECTS_DIR clone https://github.com/jerryscript-project/jerryscript.git
git -C $PROJECTS_DIR clone -b "nuttx-7.19" https://bitbucket.org/nuttx/apps.git
git -C $PROJECTS_DIR clone -b "nuttx-7.19" https://bitbucket.org/nuttx/nuttx.git
git -C $PROJECTS_DIR clone -b "gh-pages" https://github.com/Samsung/iotjs-test-results.git
git -C $PROJECTS_DIR clone -b "gh-pages" https://github.com/jerryscript-project/jerryscript-test-results.git
