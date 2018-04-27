#!/bin/bash

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

SDB=$HOME'/tizen-studio/tools/sdb' # check your tizen-studio path

DEVICES=`sdb devices | wc -l`;

if [ $DEVICES != 2 ]
then
  echo "Please connect sdb to device"
  echo ""
  exit
fi

# Initialize device
$SDB root on
$SDB shell mount -o rw,remount /

# Download packages
PACKAGES_DIR='packages'
mkdir $PACKAGES_DIR
wget -P $PACKAGES_DIR http://download.tizen.org/snapshots/tizen/base/tizen-base_20180420.1/repos/standard/packages/armv7l/db4-4.8.30.NC-3.250.armv7l.rpm
wget -P $PACKAGES_DIR http://download.tizen.org/snapshots/tizen/base/tizen-base_20180420.1/repos/standard/packages/armv7l/libpython-2.7.8-4.33.armv7l.rpm
wget -P $PACKAGES_DIR http://download.tizen.org/snapshots/tizen/base/tizen-base_20180420.1/repos/standard/packages/armv7l/python-2.7.8-4.33.armv7l.rpm
wget -P $PACKAGES_DIR http://download.tizen.org/releases/previews/iot/preview1/tizen-4.0-unified_20171016.1/repos/standard/packages/armv7l/openssh-6.6p1-1.2.armv7l.rpm
wget -P $PACKAGES_DIR http://download.tizen.org/releases/previews/iot/preview1/tizen-4.0-unified_20171016.1/repos/standard/packages/armv7l/rsync-3.1.1-2.1.armv7l.rpm

# Push packages file to device and install them.
$SDB push $PACKAGES_DIR/*.rpm /tmp/
$SDB shell rpm -Uvh --force --nodeps /tmp/*.rpm

rm -rf $PACKAGES_DIR
