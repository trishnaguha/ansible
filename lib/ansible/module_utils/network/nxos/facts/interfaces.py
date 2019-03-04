import re
from ansible.module_utils.network.nxos.nxos import get_interface_type

class NxosInterfaces(object):

    def __init__(self, data=None):
        pass

    def populate_facts(self, data):
        objs = []
        if data is None:
            return {}

        config = data.split('interface ')
        for conf in config:
            if conf:
                name = None
                match = re.search(r'^(\S+)\n', conf)
                intf = match.group(1)
                if get_interface_type(intf) != 'unknown':
                    name = intf

                if name:
                    obj = {
                        'name': name,
                        'description': self.parse_conf_arg(conf, 'description'),
                        'speed': self.parse_conf_arg(conf, 'speed'),
                        'mtu': self.parse_conf_arg(conf, 'mtu'),
                        'duplex': self.parse_conf_arg(conf, 'duplex'),
                        'enable': self.parse_conf_cmd_arg(conf, 'shutdown', False, default=True),
                        'mode': self.parse_conf_cmd_arg(conf, 'switchport', 'layer2', res2='layer3'),
                        'fabric_forwarding_anycast_gateway': self.parse_conf_cmd_arg(conf, 'fabric forwarding mode anycast-gateway', True, res2=False),
                        'ip_forward': self.parse_conf_cmd_arg(conf, 'ip forward', 'enable', res2='disable'),
                    }
                    objs.append(obj)
        facts = {}
        if objs:
            facts = {'config': objs}
        return facts

    def parse_conf_arg(self, cfg, arg):
        match = re.search(r'%s (.+)(\n|$)' % arg, cfg, re.M)
        if match:
            return match.group(1).strip()
        return None

    def parse_conf_cmd_arg(self, cfg, cmd, res1, res2=None, default=None):
        match = re.search(r'\n\s+%s(\n|$)' % cmd, cfg)
        if match:
            return res1
        else:
            if res2 is not None:
                match = re.search(r'\n\s+no %s(\n|$)' % cmd, cfg)
                if match:
                    return res2
        if default is not None:
            return default
        return None
