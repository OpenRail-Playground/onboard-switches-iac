#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The arg spec for the hirschmann_vlans module
"""


class VlansArgs(object):  # pylint: disable=R0903
    """The arg spec for the hirschmann_vlans module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {'config': {'elements': 'dict',
            'options': {'name': {'type': 'str'},
                        'vlan_id': {'required': True, 'type': 'int'}},
            'type': 'list'},
 'state': {'choices': ['merged', 'deleted'],
           'default': 'merged',
           'type': 'str'}}  # pylint: disable=C0301
