import tempfile
import shutil
import os

from voltgrid import ConfigManager

VG_CFG = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'voltgrid.conf')


def test_config_manager():
    c = ConfigManager(VG_CFG)
    c.write_envs()


def test_config_is_empty():
    with tempfile.NamedTemporaryFile() as tmp_f:
        c = ConfigManager(tmp_f.name)


def test_config_not_exist():
    c = ConfigManager('does-not-exist')


def test_git_config():
    git_url = 'git@github.com:voltgrid/voltgrid-pie.git'
    os.environ['GIT_URL'] = git_url
    c = ConfigManager(VG_CFG)
    c.load_git_conf()
    assert(c.git_url == git_url)


def test_git_config_no_vgconf():
    git_url = 'git@github.com:voltgrid/voltgrid-pie.git'
    git_dst = '/tmp/git'
    os.environ['GIT_URL'] = git_url
    os.environ['GIT_DST'] = git_dst
    c = ConfigManager('does-not-exist')
    c.load_git_conf()
    assert(c.git_url == git_url)
    assert(c.git_dst == git_dst)


def test_strip_crlf():
    os.environ['VG_CONF_PATH'] = VG_CFG
    os.environ['MYVARIABLE'] = '\r\nfoo \nbar\r'  # Context
    c = ConfigManager(VG_CFG)
    c.load_config()
    assert(c.config['MYVARIABLE'] == 'foo bar')
