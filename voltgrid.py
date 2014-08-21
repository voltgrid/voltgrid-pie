#!/usr/bin/env python

import os
import sys
import json
import subprocess
import shutil
import re
import tempfile


# Default ID for spawning and mounting, override in voltgrid.conf
DEFAULT_UID = 48
DEFAULT_GID = 48

# Magic Vars
CONFIG_EXCEPTION = 64
GIT_EXCEPTION = 128


class ConfigManager(object):
    """ Configuration Manager """

    def __init__(self, cfg_file=None):
        # Assume same dir as voltgrid.py if not specified
        cfg_file = cfg_file or os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'voltgrid.conf')
        self.environment = os.environ
        self.config = json.loads(os.getenv('CONFIG', '{}'))  # defaults
        self.local_config = self.load_local_config(cfg_file)
        self.spawn_uid = self.local_config.get('user', {}).get('uid', DEFAULT_UID)
        self.spawn_gid = self.local_config.get('user', {}).get('gid', DEFAULT_GID)
        self.git_url = self.local_config.get('git', {}).get('git_url')
        self.git_dst = self.local_config.get('git', {}).get('git_dst')
        self.git_branch = self.local_config.get('git', {}).get('git_branch', None)
        self.git_tag = self.local_config.get('git', {}).get('git_tag', None)
        super(self.__class__, self).__init__()

    @staticmethod
    def load_local_config(cfg_file):
        # Ignore errors with loading config
        try:
            config = json.load(open(cfg_file))
        except ValueError:
            config = {}
        except FileNotFoundError:
            config = {}
        return config

    @staticmethod
    def write_file(data, path):
        with open(path, 'w') as f:
            for line in data:
                f.write(line + '\n')

    def write_envs(self):
        env_file_path = self.local_config.get('env_file_path', None)
        if env_file_path is not None:
            # Allow override git config from environment
            git = self.local_config.get('git', None)
            envs = list()
            for key in self.environment.keys():
                envs.append("%s=%s" % (key, os.environ[key]))
                if re.search('^GIT', key, re.IGNORECASE):
                    git[key.lower()] = os.environ[key]
            self.write_file(envs, env_file_path)


class GitManager(object):
    """ Manager for git operations """

    def __init__(self, url, destination, branch=None, tag=None):
        self.url = url
        self.destination = destination
        self.branch = branch
        self.tag = tag
        super(self.__class__, self).__init__()

    class GitException(Exception):
        def getExitCode(self):
            return GIT_EXCEPTION

    def get_commands(self):
        git_commands = list()
        # Initialise clone
        git_commands.append(['git', 'clone', self.url, '.'])
        # Update to branch or tag
        if self.tag is not None:
            git_commands.append(['git', 'checkout', 'tags/%s' % self.tag])
        elif self.branch is not None:
            git_commands.append(['git', 'checkout', self.branch])
        # Update submodules
        git_commands.append(['git', 'submodule', 'update', '--init'])
        return git_commands

    @staticmethod
    def call(cmd, cwd):
        p = subprocess.Popen(cmd, cwd=cwd)
        return_code = p.wait()
        return return_code

    def run(self):
        for cmd in self.get_commands():
            return_code = self.call(cmd, cwd=self.destination)
            if return_code != 0:
                raise self.GitException('Git command failed')


class MountManager(object):
    """ Mountfile mounts manager """

    def __init__(self, base, remote, mount_uid, mount_gid, mount_file='Mountfile'):
        self.base = base
        self.remote = remote
        self.mount_uid = mount_uid
        self.mount_gid = mount_gid
        self.mount_file = mount_file
        super(self.__class__, self).__init__()

    @staticmethod
    def parse_mountfile_line(line):
        r = re.compile(r'^\s*/?([\.\-\w]*[ \.\-/\w]*[\.\-\w]+)/?\s*:\s*/?([\.\-\w]*[ \.\-/\w]*[\.\-\w]+)/?\s*(#.*)?$')
        match = r.search(line.strip())
        if match:
            remote = str(match.group(1))
            mount = str(match.group(2))
            match = True
        else:
            remote = None
            mount = None
            match = False
        return remote, mount, match

    def find_mount_file(self):
        if os.path.exists(os.path.join(self.base, self.mount_file)):
            return os.path.join(self.base, self.mount_file)
        elif os.path.exists(os.path.join(self.remote, self.mount_file)):
            return os.path.join(self.remote, self.mount_file)
        else:
            return False

    def get_mounts(self, mount_file):
        mounts_list = list()
        with open(mount_file, 'r') as mount_file:
            for line in mount_file:
                remote, mount, match = self.parse_mountfile_line(line)
                if match:
                    if remote == 'ephemeral':
                        remote_dir = tempfile.mkdtemp()
                        os.chown(remote_dir, self.mount_uid, self.mount_gid)
                        print("Using temporary remote %s" % remote_dir)
                    else:
                        remote_dir = os.path.join(self.remote, remote)
                    mount_dir = os.path.join(self.base, mount)
                    mounts_list.append((str(remote_dir), str(mount_dir)))
        return mounts_list

    def handle(self):
        # This creates symlinks to link share (or remote) content into the local code base.
        # Performs a number of checks to ensure we are not leaving the remote and local directories.
        # Will create folders on the remote side but will not delete anything.
        # Will not allow a link to be created in another link.
        # Will not create parent directories on the local side.
        mount_file_path = self.find_mount_file()
        if mount_file_path:
            mounts_list = self.get_mounts(mount_file_path)
        else:
            mounts_list = None

        for (remote_dir, mount_dir) in mounts_list:
            # Some check to ensure mount_dir (local) is not going into a remote dir
            real_mount_dir = os.path.realpath(os.path.dirname(mount_dir))
            if re.match(self.remote, real_mount_dir):
                print("Looks like %s is in the remote" % mount_dir)
                continue
            # Create remote directories if they don't exist, set ownership
            if not os.path.exists(remote_dir):
                os.makedirs(remote_dir)
                if remote_dir != self.remote:
                    os.chown(remote_dir, self.mount_uid, self.mount_gid)
            # Delete mount_dir if exists. Create symlink to remote_dir
            if os.path.isfile(mount_dir) or os.path.islink(mount_dir):
                os.remove(mount_dir)
            elif os.path.isdir(mount_dir):
                shutil.rmtree(mount_dir)
            os.symlink(remote_dir, mount_dir)
            print("Link created %s to %s" % (mount_dir, remote_dir))


class TemplateManager(object):
    """ Templated Config File Manager """

    def __init__(self, files, context):
            self.files = list(files)
            self.context = context
            super(self.__class__, self).__init__()

    def render_files(self):
        from jinja2 import Environment, FileSystemLoader
        environment = Environment(loader=FileSystemLoader(searchpath="/"))
        for f in self.files:
            template = environment.get_template(f)
            with tempfile.TemporaryFile(mode='w') as tmp_f:
                tmp_f.write(template.render(self.context))
            os.rename(tmp_f, f)


def main(argv):

    def execute(arg, user, group):
        print("Replacing current process with: %s" % arg[1])
        os.setgid(group)
        os.setuid(user)
        print("Running as %s:%s" % (os.geteuid(), os.getegid()))
        os.execvp(arg[1], arg[1:])  # replace current process

    # Load config
    c = ConfigManager()
    c.write_envs()
    config = c.config
    local_config = c.local_config
    files = local_config.get('files', [])
    dirs = local_config.get('dirs', [])

    # Checkout Git
    if c.git_url:
        g = GitManager(url=c.git_url, destination=c.git_dst, branch=c.git_branch, tag=c.git_tag)
        g.run()

    # Mount shares
    working_dir = dirs.get('working_dir')
    remote_dir = dirs.get('remote_dir')
    m = MountManager(working_dir, remote_dir, DEFAULT_UID, DEFAULT_GID)
    m.handle()

    # Write config from templates
    if len(files) > 0:
        t = TemplateManager(files, context=config)
        t.render_files()

    # Spawn Next Process
    sys.stdout.flush()
    if len(argv) > 1:
        execute(argv, c.spawn_uid, c.spawn_gid)

if __name__ == "__main__":
    main(argv=sys.argv)