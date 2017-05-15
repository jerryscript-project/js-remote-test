#! /bin/bash

if [ -d "projects" ]; then
  rm -rf "projects"
fi

git clone https://github.com/jameswalmsley/kconfig-frontends.git "projects/kconfig-frontends"
git clone https://github.com/texane/stlink.git "projects/stlink"
git clone https://github.com/Samsung/iotjs.git "projects/iotjs"
git clone https://github.com/jerryscript-project/jerryscript.git "projects/jerryscript"
git clone -b "nuttx-7.19" https://bitbucket.org/nuttx/apps.git "projects/apps"
git clone -b "nuttx-7.19" https://bitbucket.org/nuttx/nuttx.git "projects/nuttx"
git clone -b "gh-pages" https://github.com/Samsung/iotjs-test-results.git "projects/iotjs-test-results"
git clone -b "gh-pages" https://github.com/jerryscript-project/jerryscript-test-results.git "projects/jerryscript-test-results"
