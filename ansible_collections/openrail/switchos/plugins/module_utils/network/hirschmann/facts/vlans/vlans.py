#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The hirschmann vlans fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import re
from copy import deepcopy

from ansible_collections.ansible.netcommon.plugins.module_utils.network.common import (
    utils,
)
from ansible_collections.openrail.switchos.plugins.module_utils.network.hirschmann.argspec.vlans.vlans import VlansArgs


class VlansFacts(object):
    """ The hirschmann vlans fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = VlansArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for vlans
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if connection:  # just for linting purposes, remove
            pass
        if not data:
            # typically data is populated from the current device configuration
            # data = connection.get('show running-config | section ^interface')
            # using mock data instead
            pass
        response = connection.get('show running-config script')
        data = self.parse_vlans(response)
        # self._module.fail_json(msg=f"DEEEEEEEEEEEEEEEEEEEEEEEEEBUG: {response}") # only way i found to print and debug values

        facts = {}
        if data:
            params = utils.validate_config(self.argument_spec, {'config': data})
            facts['vlans'] = params['config']

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts
    
    def parse_vlans(self, stdout_lines):
        config_text = "\n".join(stdout_lines)

        # Extract the vlan database block
        m = re.search(
            r"vlan database(.*?)^\s*exit\s*$", config_text, re.DOTALL | re.MULTILINE
        )
        if not m:
            return []
        block = m.group(1)

        # Find all vlan add lines
        vlans = re.findall(r"vlan add (\d+)", block)

        # Find all name lines
        names = dict(re.findall(r"name (\d+)\s+([^\n]+)", block))

        return [{"vlan_id": vlan, "name": names.get(vlan)} for vlan in vlans]

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        config['name'] = utils.parse_conf_arg(conf, 'resource')
        config['some_string'] = utils.parse_conf_arg(conf, 'a_string')

        match = re.match(r'.*key is property01 (\S+)',
                         conf, re.MULTILINE | re.DOTALL)
        if match:
            config['some_dict']['property_01'] = match.groups()[0]

        a_bool = utils.parse_conf_arg(conf, 'a_bool')
        if a_bool == 'true':
            config['some_bool'] = True
        elif a_bool == 'false':
            config['some_bool'] = False
        else:
            config['some_bool'] = None

        try:
            config['some_int'] = int(utils.parse_conf_arg(conf, 'an_int'))
        except TypeError:
            config['some_int'] = None
        return utils.remove_empties(config)
