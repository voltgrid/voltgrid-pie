import tempfile
import shutil
import os

from voltgrid import ConfigManager


def test_config_manager():
    c = ConfigManager('voltgrid.conf.example')
    c.write_envs()


def test_config_is_empty():
    with tempfile.NamedTemporaryFile() as tmp_f:
        c = ConfigManager(tmp_f.name)


def test_config_not_exist():
    c = ConfigManager('does-not-exist')


def test_git_config():
    git_url = 'git@github.com:voltgrid/voltgrid-pie.git'
    os.environ['GIT_URL'] = git_url
    c = ConfigManager()
    assert(c.git_url == git_url)