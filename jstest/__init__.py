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

from jstest.builder.builder import Builder
from jstest.common import console, paths, symbol_resolver, utils
from jstest.emulate import pseudo_terminal, twisted_server
from jstest.flasher import flasher
from jstest.testresult import TestResult
from jstest.testrunner.testrunner import TestRunner


class ObjectDict(dict):
    '''
    Helper class to refer dict members as object property.
    '''
    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        if name in self:
            return self[name]

        raise AttributeError("No attribute found: " + name)

    def __delattr__(self, name):
        if name in self:
            del self[name]

        raise AttributeError("No attribute found: " + name)


def namespace_as_dict(namespace):
    '''
    Convert NameSpace object to dict.
    '''
    return dict(vars(namespace))


def encode_as_objdict(node):
    '''
    Convert dictionary to object.
    '''
    if isinstance(node, dict):
        return ObjectDict({key: encode_as_objdict(value) for key, value in node.iteritems()})

    if isinstance(node, list):
        return [encode_as_objdict(value) for value in node]

    return node


def create_testing_environment(user_options, job_options):
    '''
    Load the resource infromation that all modules define.
    '''
    resources = encode_as_objdict(utils.read_json_file(paths.RESOURCES_JSON))
    # Merge the two options.
    # Modify the user options with the options for the current job.
    options = namespace_as_dict(user_options)
    options.update(job_options)
    # Create an object from the dictionary.
    options = encode_as_objdict(options)

    # Get the dependencies of the current device.
    deps = resources.targets[options.device]
    # Update the deps list with user selected project.
    deps.insert(0, options.app)

    # Get the required module information. Drop all the
    # modules that are not required by the target.
    modules = encode_as_objdict({name: resources.modules[name] for name in deps})

    # Update the path of the target application if custom
    # iotjs or jerryscript is used.
    if options.app_path:
        modules[options.app].src = options.app_path

    # Add an 'app' named module that is just a reference
    # to the user defined target application.
    modules.app = modules[options.app]
    modules.app.name = options.app

    # Set the current build directory to the paths.
    resources.paths.builddir = utils.join(resources.paths.build, options.id)

    # Modify the no-build options according to the no-profile-build option.
    no_profile_build = options.no_profile_build and 'profile' in options.id
    options.no_build = options.no_build or no_profile_build

    environment = encode_as_objdict({
        'options': options,
        'modules': modules,
        'paths': resources.paths
    })

    # Resolve the symbolic values in the resources.json file.
    return encode_as_objdict(symbol_resolver.resolve(environment, environment))
