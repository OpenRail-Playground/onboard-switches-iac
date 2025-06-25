from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import json

from itertools import chain

from ansible.module_utils._text import to_bytes, to_text
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode

DOCUMENTATION = """
---
name: hirschmann
short_description: Use hirschmann cliconf to run command on Hirschmann BXP platform
description:
  - This hirschmann plugin provides low level abstraction apis for
    sending and receiving CLI commands from Hirschmann BXP network devices.
"""


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'hirschmann'

        reply = self.get('show running-config script')
        data = to_text(reply, errors='surrogate_or_strict').strip()
        match = re.search(r'^system name (.+)', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    @enable_mode
    def get_config(self, source='running', flags=None, format='text'):
        if source not in ('running'):
            return ("fetching configuration from %s is not supported" % source)
        if source == 'running':
            cmd = 'show running-config script'
        return self.send_command(cmd)

    @enable_mode
    def edit_config(self, command) -> None:
        for cmd in chain(['configure'], to_list(command), ['exit']):
            self.send_command(to_bytes(cmd))

    def get(self, command, prompt=None, answer=None, sendonly=False, newline=True, check_all=False):
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        return json.dumps(result)
