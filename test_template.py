import tempfile
import shutil

from voltgrid import TemplateManager


def test_template_manager():
    files = ()
    context = {}
    t = TemplateManager(files, context)
    t.render_files()