from copy import deepcopy

from ansible.module_utils.six import iteritems


class FactsBase(object):

    facts_argument_spec = {}
    data = None

    def __init__(self, data, argspec=None, subspec=None, options=None):
        self.data = data

        if argspec:
            spec = deepcopy(argspec)
            if subspec:
                if options:
                    self.facts_argument_spec = spec[subspec][options]
                else:
                    self.facts_argument_spec = spec[subspec]
            else:
                self.facts_argument_spec = spec


    def generate_dict(self, spec):
        obj = {}
        if not spec:
            return obj

        for k, v in iteritems(spec):
            if 'default' in v:
                d = {k: v['default']}
            else:
                d = {k: None}
            obj.update(d)

        return obj
