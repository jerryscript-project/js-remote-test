#! /bin/bash

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
