import tempfile
import shutil

from voltgrid import MountManager


def test_mount_manager():
    # This is a hard one to test due to current monolithic design
    m = MountManager('/tmp/base', '/tmp/remote', mount_uid=48, mount_gid=48, mount_file='Mountfile')

    remote, mount, match = m.parse_mountfile_line('  www/media : www/media  ')
    assert remote == 'www/media'
    assert mount == 'www/media'
    assert match is True

    remote, mount, match = m.parse_mountfile_line('ephemeral:www/static')
    assert remote == 'ephemeral'
    assert mount == 'www/static'
    assert match is True

    remote, mount, match = m.parse_mountfile_line('# this is a comment')
    assert match is False

    remote, mount, match = m.parse_mountfile_line('#www/media:www/media')
    assert match is False