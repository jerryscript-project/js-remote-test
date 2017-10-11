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

export CROSS_COMPILE=arm-linux-gnueabihf-
export CC=${CROSS_COMPILE}gcc
export CPP=${CROSS_COMPILE}cpp
export CXX=${CROSS_COMPILE}g++
export LD=${CROSS_COMPILE}ld
export AR=${CROSS_COMPILE}ar

# Configure and build.
./autogen.sh
./configure --host=armv7-linux-gnueabihf
make TOOLS=freya

# Create folders for required files.
OUT_DIR="./valgrind_freya/"
mkdir -p $OUT_DIR
mkdir -p $OUT_DIR/.in_place
mkdir -p $OUT_DIR/coregrind

cp ./vg-in-place $OUT_DIR
cp ./coregrind/valgrind $OUT_DIR/coregrind/valgrind
cp ./.in_place/freya-arm-linux $OUT_DIR/.in_place/freya-arm-linux
cp ./.in_place/vgpreload_core-arm-linux.so $OUT_DIR/.in_place/vgpreload_core-arm-linux.so
cp ./.in_place/vgpreload_freya-arm-linux.so $OUT_DIR/.in_place/vgpreload_freya-arm-linux.so
