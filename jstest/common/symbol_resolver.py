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

import re

from jstest.common import paths


# Device - OS mapping.
_TARGETS = {
    'stm32f4dis': 'arm-nuttx',
    'artik053': 'arm-tizenrt',
    'rpi2': 'arm-linux',
    'artik530': 'noarch-tizen'
}


def resolve(node, env):
    '''
    Recursively loop on the given node, and resolve all the
    symbols by the testing environment.

    For example: %{iotjs}/test/ -> /home/user/iotjs/test/
    '''
    if isinstance(node, dict):
        return resolve_dictionary(node, env)

    if isinstance(node, list):
        return resolve_list(node, env)

    if isinstance(node, (str, unicode)):
        return resolve_string(node, env)

    return node


def resolve_dictionary(node, env):
    '''
    Recursively loop on the given dictionary.
    '''
    return {
        key: resolve(value, env) for key, value in node.iteritems()
    }


def resolve_list(node, env):
    '''
    Recursively loop on the given list.
    '''
    return [
        resolve(value, env) for value in node
    ]


def resolve_string(node, env):
    '''
    Recursively replace the symbols in the given string.
    '''
    result = node

    if '%' not in result:
        return result

    for symbol in re.findall('%{(.*?)}', result):
        # Resolve the symbol from the symbol table.
        value = resolve_symbol(symbol, env)

        # If the symbol is not found, but that is a valid module name in
        # resources.json, resolve the symbol as a path to the module.
        if value is None and symbol in env.modules:
            value = env.modules[symbol].src

        if value is None:
            value = '(' + symbol + ' is not found)'

        result = result.replace('%%{%s}' % symbol, str(value))

    return resolve_string(result, env)


def resolve_symbol(symbol, env):
    '''
    Resolve the given symbol.
    '''
    symbol_table = {
        'device': env.options.device,
        'appname': env.options.app,
        'ip-addr': env.options.ip,
        'port': env.options.port,
        'user': env.options.username,
        'gateway': env.options.router,
        'netmask': env.options.netmask,
        'build-type': env.options.buildtype,
        'remote-workdir': env.options.remote_workdir,
        'use-stack': 'no-stack' if env.options.no_memstat else 'stack',
        'communication': 'telnet' if env.options.ip else 'serial',
        'target': _TARGETS[env.options.device],
        'js-remote-test': paths.PROJECT_ROOT,
        'result-path': paths.RESULT_PATH,
        'build-path': paths.BUILD_PATH,
        'gbs-iotjs': paths.GBS_IOTJS_PATH,
        'patches': paths.PATCHES_PATH,
        'config': paths.CONFIG_PATH,
        'home': paths.HOME,
        'flash': not env.options.no_flash,
        'memstat': not env.options.no_memstat,
        'coverage': bool(env.options.coverage),
        'minimal-profile-build': 'minimal-profile-build' in env.options.id,
        'test-build': 'test-build' in env.options.id,
        'build-dir': env.paths.builddir
    }

    return symbol_table.get(symbol, None)
