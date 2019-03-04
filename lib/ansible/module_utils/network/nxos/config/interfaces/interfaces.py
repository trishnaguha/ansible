import re

from ansible.module_utils.facts import ansible_facts
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.nxos.config.base import ConfigBase
from ansible.module_utils.six import iteritems


class Interface(ConfigBase):

    config_spec = {
        'name': dict(type='str', required=True),
        'description': dict(),
        'enable': dict(default=True, type=bool),
        'speed': dict(),
        'mode': dict(choices=['layer2', 'layer3']),
        'mtu': dict(),
        'duplex': dict(choices=['full', 'half', 'auto']),
        'mode': dict(choices=['layer2', 'layer3']),
        'ip_forward': dict(choices=['enable', 'disable']),
        'fabric_forwarding_anycast_gateway': dict(type='bool'), 
    }

    argument_spec = {
        'operation': dict(default='merge', choices=['merge', 'replace', 'override', 'delete']),
        'config': dict(type='list', elements='dict', options=config_spec)
    }

    def set_config(self, module):
        want = self._config_map_params_to_obj(module)
        interfaces_facts = ansible_facts(module, ['interfaces'])
        interfaces = interfaces_facts['network_interfaces']
        have = []
        if interfaces:
            have = interfaces['config']
        resp = self.set_operation(want, have)
        return to_list(resp)

    def _config_map_params_to_obj(self, module):
        objs = []
        collection = module.params['config']
        for config in collection:
            obj = {
                'name': self.normalize_interface(config['name']),
                'description': config['description'],
                'enable': config['enable'],
                'speed': config['speed'],
                'mtu': config['mtu'],
                'duplex': config['duplex'],
                'mode': config['mode'],
                'ip_forward': config['ip_forward'],
                'fabric_forwarding_anycast_gateway': config['fabric_forwarding_anycast_gateway'],
            }
            objs.append(obj)

        return objs

    def set_operation(self, want, have):
        commands = list()

        operation = self.operation
        if operation == 'override':
            commands.extend(self._operation_override(want, have))
        else:
            for w in want:
                name = w['name']
                interface_type = self.get_interface_type(name)
                obj_in_have = self.search_obj_in_list(name, have)
                if operation == 'delete' and obj_in_have:
                    commands.append('no interface {0}'.format(w['name']))

                if operation == 'merge':
                    commands.extend(self._operation_merge(w, obj_in_have, interface_type))

                if operation == 'replace':
                    commands.extend(self._operation_replace(w, obj_in_have, interface_type))

        return commands

    def _operation_replace(self, w, obj_in_have, interface_type):
        commands = list()

        if interface_type in ('loopback', 'portchannel', 'svi'):
            commands.append('no interface {0}'. format(w['name']))
            commands.extend(self._operation_merge(w, obj_in_have, interface_type))
        else:
            commands.append('default interface {0}'.format(w['name']))
            commands.extend(self._operation_merge(w, obj_in_have, interface_type))

        return commands

    def _operation_override(self, want, have):
        """
        purge interfaces
        """
        commands = list()

        for h in have:
            name = h['name']
            obj_in_want = self.search_obj_in_list(name, want)
            if not obj_in_want:
                interface_type = self.get_interface_type(name)

                # Remove logical interfaces
                if interface_type in ('loopback', 'portchannel', 'svi'):
                    commands.append('no interface {0}'.format(name))
                elif interface_type == 'ethernet':
                    default = True
                    if h['enable'] is True:
                        keys = ('description', 'mode', 'mtu', 'speed', 'duplex', 'ip_forward','fabric_forwarding_anycast_gateway')
                        for k, v in iteritems(h):
                            if k in keys:
                                if h[k] is not None:
                                    default = False
                                    break
                    else:
                        default = False

                    if default is False:
                        # Put physical interface back into default state
                        commands.append('default interface {0}'.format(name))

        for w in want:
            name = w['name']
            interface_type = self.get_interface_type(name)
            obj_in_have = self.search_obj_in_list(name, have)
            commands.extend(self._operation_merge( w, obj_in_have, interface_type))

        return commands

    def _operation_merge(self, w, obj_in_have, interface_type):
        commands = list()

        args = ('speed', 'description', 'duplex', 'mtu')
        name = w['name']
        mode = w['mode']
        ip_forward = w['ip_forward']
        fabric_forwarding_anycast_gateway = w['fabric_forwarding_anycast_gateway']
        enable = w['enable']

        if name:
            interface = 'interface ' + name

        if not obj_in_have:
            commands.append(interface)
            if interface_type in ('ethernet', 'portchannel'):
                if mode == 'layer2':
                    commands.append('switchport')
                elif mode == 'layer3':
                    commands.append('no switchport')

            if enable is True:
                commands.append('no shutdown')
            elif enable is False:
                commands.append('shutdown')

            if ip_forward == 'enable':
                commands.append('ip forward')
            elif ip_forward == 'disable':
                commands.append('no ip forward')

            if fabric_forwarding_anycast_gateway is True:
                commands.append('fabric forwarding mode anycast-gateway')
            elif fabric_forwarding_anycast_gateway is False:
                commands.append('no fabric forwarding mode anycast-gateway')

            for item in args:
                candidate = w.get(item)
                if candidate:
                    commands.append(item + ' ' + str(candidate))

        else:
            if interface_type in ('ethernet', 'portchannel'):
                if mode == 'layer2' and mode != obj_in_have.get('mode'):
                    self.add_command_to_interface(interface, 'switchport', commands)
                elif mode == 'layer3' and mode != obj_in_have.get('mode'):
                    self.add_command_to_interface(interface, 'no switchport', commands)

            if enable is True and enable != obj_in_have.get('enable'):
                self.add_command_to_interface(interface, 'no shutdown', commands)
            elif enable is False and enable != obj_in_have.get('enable'):
                self.add_command_to_interface(interface, 'shutdown', commands)

            if ip_forward == 'enable' and ip_forward != obj_in_have.get('ip_forward'):
                self.add_command_to_interface(interface, 'ip forward', commands)
            elif ip_forward == 'disable' and ip_forward != obj_in_have.get('ip forward'):
                self.add_command_to_interface(interface, 'no ip forward', commands)

            if (fabric_forwarding_anycast_gateway is True and obj_in_have.get('fabric_forwarding_anycast_gateway') is False):
                self.add_command_to_interface(interface, 'fabric forwarding mode anycast-gateway', commands)

            elif (fabric_forwarding_anycast_gateway is False and obj_in_have.get('fabric_forwarding_anycast_gateway') is True):
                self.add_command_to_interface(interface, 'no fabric forwarding mode anycast-gateway', commands)

            for item in args:
                candidate = w.get(item)
                if candidate and candidate != obj_in_have.get(item):
                    cmd = item + ' ' + str(candidate)
                    self.add_command_to_interface(interface, cmd, commands)

            # if the mode changes from L2 to L3, the admin state
            # seems to change after the API call, so adding a second API
            # call to ensure it's in the desired state.
            if name and interface_type == 'ethernet':
                if mode and mode != obj_in_have.get('mode'):
                    enable = w.get('enable') or obj_in_have.get('enable')
                    if enable is True:
                        commands.append(self._get_admin_state(enable))

        return commands

    def _get_admin_state(self, enable):
        command = ''
        if enable is True:
            command = 'no shutdown'
        elif enable is False:
            command = 'shutdown'
        return command

    def add_command_to_interface(self, interface, cmd, commands):
        if interface not in commands:
            commands.append(interface)
        commands.append(cmd)
