import re

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.nxos.nxos import get_interface_type
from ansible.module_utils.network.nxos.facts.base import FactsBase


class NxosInterfaces(FactsBase):

    def populate_facts(self):
        objs = []
        if self.data is None:
            return {}

        config = self.data.split('interface ')
        for conf in config:
            if conf:
                obj = self.parse_config(self.facts_argument_spec, conf)
                if obj:
                    objs.append(obj)

        facts = {}
        if objs:
            facts = {'config': objs}
        return facts

    def parse_config(self, facts_argument_spec, conf):
        config = {}
        generated_spec = self.generate_dict(facts_argument_spec)

        match = re.search(r'^(\S+)\n', conf)
        intf = match.group(1)
        if get_interface_type(intf) != 'unknown':
            name = intf
        else:
            return {}

        # get facts mapped to argpsec keys
        if generated_spec:
            config = self.parse_keys(conf, name, spec=generated_spec)

        # gather facts without argpsec mapping
        else:
            config = self._config_map_conf_to_obj(conf, name, spec={})
        return config
    
    def parse_keys(self, conf, name, spec):
        diff = set(spec.keys()) - set(self.facts_argument_spec.keys())
        if diff:
            return {}

        config = self._config_map_conf_to_obj(conf, name, spec=spec)
        return config

    def _config_map_conf_to_obj(self, conf, name, spec={}):
        obj = {
            'name': name,
            'description': self.parse_conf_arg(conf, 'description'),
            'speed': self.parse_conf_arg(conf, 'speed'),
            'mtu': self.parse_conf_arg(conf, 'mtu'),
            'duplex': self.parse_conf_arg(conf, 'duplex'),
            'enable': self.parse_conf_cmd_arg(conf, 'shutdown', False, default=spec.get('enable', True)),
            'mode': self.parse_conf_cmd_arg(conf, 'switchport', 'layer2', res2='layer3'),
            'fabric_forwarding_anycast_gateway': self.parse_conf_cmd_arg(conf, 'fabric forwarding mode anycast-gateway', True, res2=False),
            'ip_forward': self.parse_conf_cmd_arg(conf, 'ip forward', 'enable', res2='disable'),
        }
        return obj


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
