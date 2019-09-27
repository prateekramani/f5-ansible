#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_device_dns
short_description: Manage BIG-IP device DNS settings
description:
  - Manage BIG-IP device DNS settings.
version_added: 2.2
options:
  cache:
    description:
      - Specifies whether the system caches DNS lookups or performs the
        operation each time a lookup is needed. Please note that this applies
        only to Access Policy Manager features, such as ACLs, web application
        rewrites, and authentication.
    type: str
    choices:
       - enabled
       - disabled
       - enable
       - disable
  name_servers:
    description:
      - A list of name servers that the system uses to validate DNS lookups
    type: list
  search:
    description:
      - A list of domains that the system searches for local domain lookups,
        to resolve local host names.
    type: list
  ip_version:
    description:
      - Specifies whether the DNS specifies IP addresses using IPv4 or IPv6.
    type: int
    choices:
      - 4
      - 6
  state:
    description:
      - The state of the variable on the system. When C(present), guarantees
        that an existing variable is set to C(value).
    type: str
    choices:
      - absent
      - present
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Set the DNS settings on the BIG-IP
  bigip_device_dns:
    name_servers:
      - 208.67.222.222
      - 208.67.220.220
    search:
      - localdomain
      - lab.local
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
cache:
  description: The new value of the DNS caching
  returned: changed
  type: str
  sample: enabled
name_servers:
  description: List of name servers that were set
  returned: changed
  type: list
  sample: ['192.0.2.10', '172.17.12.10']
search:
  description: List of search domains that were set
  returned: changed
  type: list
  sample: ['192.0.2.10', '172.17.12.10']
ip_version:
  description: IP version that was set that DNS will specify IP addresses in
  returned: changed
  type: int
  sample: 4
warnings:
  description: The list of warnings (if any) generated by module based on arguments
  returned: always
  type: list
  sample: ['...', '...']
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import is_empty_list
except ImportError:
    from ansible_collections.f5networks.f5_modules.plugins.module_utils.bigip import F5RestClient
    from ansible_collections.f5networks.f5_modules.plugins.module_utils.common import F5ModuleError
    from ansible_collections.f5networks.f5_modules.plugins.module_utils.common import AnsibleF5Parameters
    from ansible_collections.f5networks.f5_modules.plugins.module_utils.common import f5_argument_spec
    from ansible_collections.f5networks.f5_modules.plugins.module_utils.common import is_empty_list


class Parameters(AnsibleF5Parameters):
    api_map = {
        'dns.cache': 'cache',
        'nameServers': 'name_servers',
        'include': 'ip_version',
    }

    api_attributes = [
        'nameServers', 'search', 'include',
    ]

    updatables = [
        'cache', 'name_servers', 'search', 'ip_version',
    ]

    returnables = [
        'cache', 'name_servers', 'search', 'ip_version',
    ]

    absentables = [
        'name_servers', 'search',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def search(self):
        search = self._values['search']
        if search is None:
            return None
        if isinstance(search, str) and search != "":
            result = list()
            result.append(str(search))
            return result
        if is_empty_list(search):
            return []
        return search

    @property
    def name_servers(self):
        name_servers = self._values['name_servers']
        if name_servers is None:
            return None
        if isinstance(name_servers, str) and name_servers != "":
            result = list()
            result.append(str(name_servers))
            return result
        if is_empty_list(name_servers):
            return []
        return name_servers

    @property
    def cache(self):
        if self._values['cache'] is None:
            return None
        if str(self._values['cache']) in ['enabled', 'enable']:
            return 'enable'
        else:
            return 'disable'

    @property
    def ip_version(self):
        if self._values['ip_version'] == 6:
            return "options inet6"
        elif self._values['ip_version'] == 4:
            return ""
        else:
            return None


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                change = getattr(self, returnable)
                if isinstance(change, dict):
                    result.update(change)
                else:
                    result[returnable] = change
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    @property
    def ip_version(self):
        if self._values['ip_version'] == 'options inet6':
            return 6
        elif self._values['ip_version'] == "":
            return 4
        else:
            return None


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def ip_version(self):
        if self.want.ip_version is None:
            return None
        if self.want.ip_version == "" and self.have.ip_version is None:
            return None
        if self.want.ip_version == self.have.ip_version:
            return None
        if self.want.ip_version != self.have.ip_version:
            return self.want.ip_version

    @property
    def name_servers(self):
        state = self.want.state
        if self.want.name_servers is None:
            return None
        if state == 'absent':
            if self.have.name_servers is None and self.want.name_servers:
                return None
            if set(self.want.name_servers) == set(self.have.name_servers):
                return []
            if set(self.want.name_servers) != set(self.have.name_servers):
                return list(set(self.want.name_servers).difference(self.have.name_servers))
        if not self.want.name_servers:
            if self.have.name_servers is None:
                return None
            if self.have.name_servers is not None:
                return self.want.name_servers
        if self.have.name_servers is None:
            return self.want.name_servers
        if set(self.want.name_servers) != set(self.have.name_servers):
            return self.want.name_servers

    @property
    def search(self):
        state = self.want.state
        if self.want.search is None:
            return None
        if not self.want.search:
            if self.have.search is None:
                return None
            if self.have.search is not None:
                return self.want.search
        if state == 'absent':
            if self.have.search is None and self.want.search:
                return None
            if set(self.want.search) == set(self.have.search):
                return []
            if set(self.want.search) != set(self.have.search):
                return list(set(self.want.search).difference(self.have.search))
        if self.have.search is None:
            return self.want.search
        if set(self.want.search) != set(self.have.search):
            return self.want.search


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.pop('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def _absent_changed_options(self):
        diff = Difference(self.want, self.have)
        absentables = Parameters.absentables
        changed = dict()
        for k in absentables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.update()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def should_absent(self):
        result = self._absent_changed_options()
        if result:
            return True
        return False

    def absent(self):
        self.have = self.read_current_from_device()
        if not self.should_absent():
            return False
        if self.module.check_mode:
            return True
        self.absent_on_device()
        return True

    def read_dns_cache_setting(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/db/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            'dns.cache'
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response

    def read_current_from_device(self):
        cache = self.read_dns_cache_setting()
        uri = "https://{0}:{1}/mgmt/tm/sys/dns/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if cache:
            response['cache'] = cache['value']
        return ApiParameters(params=response)

    def update_on_device(self):
        params = self.changes.api_params()
        if params:
            uri = "https://{0}:{1}/mgmt/tm/sys/dns/".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
            )
            resp = self.client.api.patch(uri, json=params)
            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] == 400:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)
        if self.want.cache:
            uri = "https://{0}:{1}/mgmt/tm/sys/db/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                'dns.cache'
            )
            payload = {"value": self.want.cache}
            resp = self.client.api.patch(uri, json=payload)
            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] == 400:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)

    def absent_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/dns/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            cache=dict(
                choices=['disabled', 'enabled', 'disable', 'enable']
            ),
            name_servers=dict(
                type='list'
            ),
            search=dict(
                type='list'
            ),
            ip_version=dict(
                choices=[4, 6],
                type='int'
            ),
            state=dict(
                default='present',
                choices=['absent', 'present']
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_one_of = [
            ['name_servers', 'search', 'ip_version', 'cache']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_one_of=spec.required_one_of
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
