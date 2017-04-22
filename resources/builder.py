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

from . import console
from . import executor
from . import paths


def clean_all():
    '''
    Clean up all the submodules.
    '''
    console.info("Clean submodules")

    executor.run_cmd(paths.WEB_PATH, 'git', ['clean', '-dxf'])
    executor.run_cmd(paths.APPS_PATH, 'git', ['clean', '-dxf'])
    executor.run_cmd(paths.NUTTX_PATH, 'git', ['clean', '-dxf'])
    executor.run_cmd(paths.IOTJS_PATH, 'git', ['clean', '-dxf'])
    executor.run_cmd(paths.STLINK_PATH, 'git', ['clean', '-dxf'])

    executor.run_cmd(paths.WEB_PATH, 'git', ['checkout', 'gh-pages'])
    executor.run_cmd(paths.APPS_PATH, 'git', ['checkout', 'nuttx-7.19'])
    executor.run_cmd(paths.NUTTX_PATH, 'git', ['checkout', 'nuttx-7.19'])
    executor.run_cmd(paths.IOTJS_PATH, 'git', ['checkout', 'master'])
    executor.run_cmd(paths.STLINK_PATH, 'git', ['checkout', 'master'])


def build_kconfig():
    '''
    Build kconfig-fronted submodule.
    '''
    console.info("Build kconfig")

    configure_args = ['--enable-mconf', '--disable-werror']

    executor.run_cmd(paths.KCONFIG_PATH, './bootstrap')
    executor.run_cmd(paths.KCONFIG_PATH, './configure', configure_args)
    executor.run_cmd(paths.KCONFIG_PATH, 'make')


def build_stlink():
    '''
    Build st-link submodule.
    '''
    console.info("Build st-link")

    executor.run_cmd(paths.STLINK_PATH, 'make', ['release'])


def build_nuttx():
    '''
    Build NuttX submodule.
    '''
    console.info("Build NuttX")

    # For release build.
    os.environ["R"] = "1"

    executor.run_cmd(paths.NUTTX_PATH, 'make', ['dirlinks'])
    executor.run_cmd(paths.NUTTX_PATH, 'make', ['apps_preconfig'])
    executor.run_cmd(paths.NUTTX_PATH, 'make', ['-j1'])


def build_iotjs_for_nuttx():
    '''
    Build IoT.js for NuttX target.
    '''
    console.info("Build IoT.js")

    build_options = [
        '--clean',
        '--buildtype=release',
        '--target-board=stm32f4dis',
        '--target-arch=arm',
        '--target-os=nuttx',
        '--nuttx-home=%s' % paths.NUTTX_PATH,
        '--jerry-heaplimit=78'
    ]

    executor.run_cmd(paths.IOTJS_PATH, 'tools/build.py', build_options)


def build_iotjs_for_rpi2():
    '''
    Build IoT.js for rpi2 target.
    '''
    console.info("Build IoT.js to RPI2")

    build_options = [
        '--clean',
        '--target-arch=arm',
        '--target-board=rpi2',
        '--buildtype=release'
    ]

    iotjs = os.path.join(paths.IOTJS_BUILD_PATH, 'iotjs')

    executor.run_cmd(paths.IOTJS_PATH, 'tools/build.py', build_options)
    executor.run_cmd(paths.IOTJS_PATH, 'arm-linux-gnueabi-strip', [iotjs])


def update_iotjs():
    '''
    Update IoT.js submodule.
    '''
    console.info("Update IoT.js")

    executor.run_cmd(paths.IOTJS_PATH, 'git', ['reset', '--hard'])
    executor.run_cmd(paths.IOTJS_PATH, 'git', ['pull', 'origin', 'master'])


def add_iotjs_to_nuttx():
    '''
    Add IoT.js to NuttX as a builtin application.
    '''
    console.info("Add IoT.js to NuttX")

    executor.copy_files(paths.IOTJS_APPS_PATH, paths.APPS_IOTJS_PATH)


def configure_nuttx_for_netnsh():
    '''
    Configure NuttX for netnsh.
    '''
    console.info("Configure NuttX to netnsh")

    config_args = ['stm32f4discovery/netnsh']

    executor.run_cmd(paths.NUTTX_TOOLS_PATH, './configure.sh', config_args)

    #
    # A prepared configured file should replace the default .config file.
    #
    # Reasons:
    #  * More ethernet settings (ip, netmask, gateway, loopback, etc.)
    #  * More other settings to tun tests (timer, pwm, adc, etc.)
    #  * ROMFS file system support to store tests on the build-in flash
    #
    original_config_file = os.path.join(paths.NUTTX_PATH, '.config')
    prepared_config_file = os.path.join(paths.CONFIG_PATH, 'netnsh.config')

    executor.copy_file(prepared_config_file, original_config_file)


def generate_romfs_image():
    '''
    Generate ROMFS file from the iotjs test folder.
    '''
    console.info("Generate ROMFS image")

    original_romfs_file = os.path.join(paths.NSHLIB_PATH, 'nsh_romfsimg.h')
    prepared_romfs_file = os.path.join(paths.IOTJS_PATH, 'nsh_romfsimg.h')

    genromfs_args = ['-f', 'romfs_img', '-d', 'test']
    xxd_args = ['-i', 'romfs_img', 'nsh_romfsimg.h']
    sed_args = ['-ie', 's/unsigned/const\ unsigned/g', 'nsh_romfsimg.h']

    executor.run_cmd(paths.IOTJS_PATH, 'genromfs', genromfs_args)
    executor.run_cmd(paths.IOTJS_PATH, 'xxd', xxd_args)
    executor.run_cmd(paths.IOTJS_PATH, 'sed', sed_args)

    # Fixme: just override the existing file, don't check the existance.
    if os.path.exists(original_romfs_file):
        os.remove(original_romfs_file)

    executor.move(prepared_romfs_file, paths.NSHLIB_PATH)


def init_env():
    '''
    Build and initialize neccessary submodules.
    '''
    clean_all()

    build_kconfig()

    build_stlink()

    configure_nuttx_for_netnsh()

    build_nuttx()


def build_iotjs_and_nuttx():
    '''
    Update and build IoT.js to stm32f4.
    '''
    update_iotjs()

    build_iotjs_for_rpi2()

    build_iotjs_for_nuttx()

    add_iotjs_to_nuttx()

    generate_romfs_image()

    build_nuttx()
