# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Copyright 2022 BigML, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import traceback

from ipykernel.ipkernel import IPythonKernel
from ipykernel.kernelbase import Kernel
from .interpreter import Interpreter
from magics import WhizzMLMagic
from IPython import get_ipython


class WhizzMLKernel(Kernel):
    implementation = 'WhizzML'
    implementation_version = '0.1'
    language = 'WhizzML'
    language_version = '0.48.3'
    language_info = {
        'name': 'WhizzML',
        'mimetype': 'text/plain',
        'file_extension': '.whizzml',
    }
    banner = "WhizzML kernel - by BigML, Machine Learning Made Easy"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ipython_kernel = IPythonKernel(*args, **kwargs)

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):
        """Executes the cells code. We allow some magics to be added to the
        list of magics used in the Python kernel. We use the Python Kernel to
        execute those, as well as all python code written in cells with the
        %%python magic command. The rest of code is considered to be WhizzML
        code and is interpreted as such.
        """
        # Registering WhizzML-related magics
        if not hasattr(self, "ip"):
            self.ip = get_ipython()
            self.ip.register_magics(WhizzMLMagic)
        code = code.strip()
        # handling magics and shell commands through the Python kernel
        if code.startswith("%") or code.startswith("!"):
            if code.startswith("%%python\n"):
                code = code[9:]
            self.ipython_kernel.do_execute(
                code, silent, store_history=True,
                user_expressions=None, allow_stdin=False)
            return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }
        # WhizzML code
        try:
            if not hasattr(self.ip, "interpreter") or \
                    self.ip.interpreter is None:
                self.ip.interpreter = Interpreter(
                    os.environ.get('BIGML_USERNAME'),
                    os.environ.get('BIGML_API_KEY'),
                    os.environ.get('BIGML_DOMAIN'),
                    os.environ.get('BIGML_API_VERSION'),
                    os.environ.get('BIGML_PROJECT'),
                    os.environ.get('BIGML_ORGANIZATION'))
            result = self.ip.interpreter.eval(code)
        except Exception as exc:
            stream_content = {'name': 'stdout',
                              'text': "WhizzML error: %s" % exc}
            self.send_response(self.iopub_socket, 'stream', stream_content)
            return {'status': 'error',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }
        if not silent:
            stream_content = {'name': 'stdout', 'text': result}
            self.send_response(self.iopub_socket, 'stream', stream_content)
        return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=WhizzMLKernel)