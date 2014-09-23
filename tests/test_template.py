import tempfile
import shutil
import os

from voltgrid import TemplateManager, ConfigManager

VG_CFG = 'voltgrid.conf'
VG_TEMPLATE = 'template.test'


def test_template_manager():
    files = ()
    context = {}
    t = TemplateManager(files, context)
    t.render_files()


def test_template_render():
    os.environ['CONFIG'] = '{"foo": "bar"}'  # Context
    template = '%s' % os.path.join(os.path.abspath(os.path.split(__file__)[0]), VG_TEMPLATE)
    c = ConfigManager(VG_CFG)
    files = (template, )
    t = TemplateManager()
    result = '/* This is just an example */\nfoo = bar'
    assert(result == t.render(template, c.config))