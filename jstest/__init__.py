# Copyright 2017-present Samsung Electronics Co., Ltd. and other contributors
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

from jstest import builder
from jstest.common import utils, paths
from jstest.testrunner import testrunner


def load_testing_environment(options):
    '''
    Create a testing environment object that contains the
    module information and the user specified options.
    '''
    resources = utils.read_json_file(paths.RESOURCES_JSON)

    # Get the dependencies of the current device.
    deps = resources['targets'][options.device]
    # Update the deps list with user selected projects.
    deps.append(options.app)

    # Get the required module information.
    modules = {
        name: resources['modules'][name] for name in deps
    }

    # Update the path of the target application.
    if options.app_path:
        modules[options.app]['src'] = options.app_path
    # Add an 'app' named module that is just a reference
    # to the user defined target application.
    modules['app'] = modules[options.app]
    modules['app']['name'] = options.app

    # Create the testing environment object.
    environment = {
        'info': vars(options),
        'modules': modules,
        'paths': resources['paths']
    }

    _resolve_symbols(environment)

    return environment


def _resolve_symbols(env):
    '''
    Resolve all the symbols in the environment object.

    e.g. %iotjs/test/ -> /home/user/iotjs/test/
    '''
    for key, value in env.iteritems():
        env[key] = _resolve(value, env)


def _resolve(node, env):
    '''
    Recursive function to loop the environment object
    and replace the symbols.
    '''
    if not isinstance(node, dict):
        return node

    for key, value in node.iteritems():
        if isinstance(value, dict):
            node[key] = _resolve(value, env)
        elif isinstance(value, list):
            ret = []
            for obj in value:
                ret.append(_resolve(obj, env))
            node[key] = ret
        elif isinstance(value, (str, unicode)):
            node[key] = _replacer(value, env)

    return node


# Device - OS mapping.
_TARGETS = {
    'stm32f4dis': 'arm-nuttx',
    'artik053': 'arm-tizenrt',
    'rpi2': 'arm-linux',
    'artik530': 'noarch-tizen'
}


def _replacer(string, env):
    '''
    Replace symbols with the corresponding string data.
    '''
    if '%' not in string:
        return string

    symbol_table = {
        'app': env['info']['app'],
        'device': env['info']['device'],
        'build-type': env['info']['buildtype'],
        'target': _TARGETS.get(env['info']['device']),
        'js-remote-test': paths.PROJECT_ROOT,
        'result-path': paths.RESULT_PATH,
        'build-path': paths.BUILD_PATH,
        'patches': paths.PATCHES_PATH,
        'config': paths.CONFIG_PATH,
        'home': paths.HOME,
        'memstat': not env['info']['no_memstat'],
        'coverage': bool(env['info']['coverage'])
    }

    for symbol in re.findall('%{(.*?)}', string):
        # Resolve the symbol from the symbol table.
        value = symbol_table.get(symbol, None)

        # If the symbol is not found, but that is a valid module name in
        # resources.json, resolve the symbol as a path to the module.
        if value is None and symbol in env['modules']:
            value = env['modules'][symbol]['src']

        if value is None:
            continue

        string = string.replace('%%{%s}' % symbol, str(value))

    return string
