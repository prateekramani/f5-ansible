# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import pytest
import sys

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_profile_http2 import ApiParameters
    from library.modules.bigip_profile_http2 import ModuleParameters
    from library.modules.bigip_profile_http2 import ModuleManager
    from library.modules.bigip_profile_http2 import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_profile_http2 import ApiParameters
        from ansible.modules.network.f5.bigip_profile_http2 import ModuleParameters
        from ansible.modules.network.f5.bigip_profile_http2 import ModuleManager
        from ansible.modules.network.f5.bigip_profile_http2 import ArgumentSpec
        from ansible.module_utils.network.f5.common import F5ModuleError
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from units.modules.utils import set_module_args
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except Exception:
        pass

    fixture_data[path] = data
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            name='foo',
            parent='bar',
            description='This is a Test',
            streams=20,
            enforce_tls_requirements=True,
            frame_size=1024,
            activation_modes=['always'],
            insert_header=True,
            insert_header_name='FOO'

        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.parent == '/Common/bar'
        assert p.description == 'This is a Test'
        assert p.streams == 20
        assert p.enforce_tls_requirements == 'enabled'
        assert p.frame_size == 1024
        assert p.activation_modes == ['always']
        assert p.insert_header == 'enabled'
        assert p.insert_header_name == 'FOO'

    def test_api_parameters(self):
        args = load_fixture('load_ltm_http2_profile.json')
        p = ApiParameters(params=args)
        assert p.name == 'test'
        assert p.streams == 10
        assert p.enforce_tls_requirements == 'disabled'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            name='foo',
            enforce_tls_requirements='yes',
            parent='bar',
            password='password',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['enforce_tls_requirements'] == 'no'
