
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.directives.code import LiteralIncludeReader, container_wrapper
from sphinx.util.nodes import set_source_info

class AnsibleIncludeDirective(Directive):
 
    '''
    Largely copied from sphinx.directives.code.LiteralIncludeDirective
    '''

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'dedent': int,
        'linenos': directives.flag,
        'lineno-start': int,
        'lineno-match': directives.flag,
        'tab-width': int,
        'language': directives.unchanged_required,
        'encoding': directives.encoding,
        'pyobject': directives.unchanged_required,
        'lines': directives.unchanged_required,
        'start-after': directives.unchanged_required,
        'end-before': directives.unchanged_required,
        'start-at': directives.unchanged_required,
        'end-at': directives.unchanged_required,
        'prepend': directives.unchanged_required,
        'append': directives.unchanged_required,
        'emphasize-lines': directives.unchanged_required,
        'caption': directives.unchanged,
        'class': directives.class_option,
        'name': directives.unchanged,
        'diff': directives.unchanged_required,
    }
 
    def find_file(self, filename):
        for path in sys.path:
            target = os.path.abspath(os.path.join(path, filename))
            if os.path.exists(target):
                return target
        return None

    def run(self):
        '''
        As noted above, this is largely cribbed from LiteralIncludeDirective,
        however it does not implement all of the options listed above as we're
        not currently using them.
        '''

        document = self.state.document
        if not document.settings.file_insertion_enabled:
            return [document.reporter.warning('File insertion disabled',
                                              line=self.lineno)]
        env = document.settings.env
        original_filename = self.arguments[0]
        filename = self.find_file(original_filename)
        if filename is None:
            raise Exception("specified Ansible include not found: '%s'" % original_filename)
        env.note_dependency(filename)

        location = self.state_machine.get_source_and_line(self.lineno)
        reader = LiteralIncludeReader(filename, self.options, env.config)
        text, lines = reader.read(location=location)

        retnode = nodes.literal_block(text, text, source=filename)
        if 'language' in self.options:
            retnode['language'] = self.options['language']

        if 'caption' in self.options:
            caption = self.options['caption'] or original_filename
            retnode = container_wrapper(self, retnode, caption)

        self.add_name(retnode)
        return [retnode]

def setup(app):
    app.add_directive('ansible_include', AnsibleIncludeDirective)
