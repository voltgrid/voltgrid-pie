import tempfile
import shutil

from voltgrid import GitManager, ConfigManager, TemplateManager, MountManager


def git_checkout(git_url, git_branch=None, git_tag=None):
    git_dst = tempfile.mkdtemp()
    g = GitManager(url=git_url, destination=git_dst, branch=git_branch, tag=git_tag)
    g.run()
    shutil.rmtree(git_dst)


def test_git_tag():
    """ Test checkout w/ Tag """
    git_checkout(git_url='https://github.com/adlibre/python-bureaucrat.git', git_branch=None, git_tag='v0.2.0')


def test_git_branch():
    """ Test checkout w/ Branch """
    git_checkout(git_url='https://github.com/adlibre/python-bureaucrat.git', git_branch='master', git_tag=None)


def test_config_manager():
    c = ConfigManager('voltgrid.conf', '/tmp/env')
    c.write_envs()


def test_template_manager():
    files = ()
    context = {}
    t = TemplateManager(files, context)
    t.render_files()


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