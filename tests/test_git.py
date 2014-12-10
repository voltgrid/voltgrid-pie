import tempfile
import shutil

from voltgrid import GitManager


def git_checkout(git_url, git_branch=None, git_tag=None, git_hash=None):
    git_dst = tempfile.mkdtemp()
    g = GitManager(url=git_url, destination=git_dst, branch=git_branch, tag=git_tag, hash=git_hash)
    g.run()
    shutil.rmtree(git_dst)


def test_git_tag():
    """ Test checkout w/ Tag """
    git_checkout(git_url='https://github.com/voltgrid/voltgrid-pie.git', git_branch=None, git_tag='v0.1.0')


def test_git_branch():
    """ Test checkout w/ Branch """
    git_checkout(git_url='https://github.com/voltgrid/voltgrid-pie.git', git_branch='master', git_tag=None)


def test_git_hash():
    """ Test checkout w/ Commit Hash """
    git_checkout(git_url='https://github.com/voltgrid/voltgrid-pie.git', git_hash='ab052369c675057dccc90a75fb92317e9b689a56')
