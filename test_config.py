import tempfile
import shutil

from voltgrid import ConfigManager


def test_config_manager():
    c = ConfigManager('voltgrid.conf.example')
    c.write_envs()