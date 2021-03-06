#!/usr/bin/env python

import pwd
import os
import sys
import json
import subprocess
import shutil
import re
import tempfile
from distutils.dir_util import copy_tree


__version__ = '1.0.8'

# Config
VG_CONF_PATH = os.environ.get('VG_CONF_PATH', '/usr/local/etc/voltgrid.conf')

# Default ID for spawning and mounting, override in voltgrid.conf
DEFAULT_UID = 48
DEFAULT_GID = 48

# Magic Vars
CONFIG_EXCEPTION = 64
GIT_EXCEPTION = 128


class ConfigManager(object):
    """ Configuration Manager """

    config = {}
    environment = os.environ

    def __init__(self, cfg_file=None):
        # Assume same dir as voltgrid.py if not specified
        cfg_file = cfg_file or os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'voltgrid.conf')
        self.local_config = self.load_local_config(cfg_file)
        self.spawn_uid = self.local_config.get('user', {}).get('uid', DEFAULT_UID)
        self.spawn_gid = self.local_config.get('user', {}).get('gid', DEFAULT_GID)
        super(self.__class__, self).__init__()

    def load_config(self):
        if os.getenv('CONFIG') is not None:
            self.config = json.loads(os.getenv('CONFIG'))
        else:
            self.config = {}
            for key in self.environment.keys():
                # remove crlf from environment variables
                value = str(os.environ[key])
                value = ''.join(value.splitlines())
                value = value.strip('\r\n')
                self.config[key] = value

    @staticmethod
    def load_local_config(cfg_file):
        # Ignore errors with loading config
        try:
            config = json.load(open(cfg_file))
        except ValueError:
            print('Could not parse config file %s' % cfg_file)
            config = {}
        except IOError:
            print('Could not open config file %s' % cfg_file)
            config = {}
        return config

    @staticmethod
    def write_file(data, path):
        with open(path, 'w') as f:
            for line in data:
                f.write(line + '\n')

    def load_git_conf(self):
        # Allow override git config from environment
        self.git_cfg = self.local_config.get('git', {})
        git = self.local_config.get('git', {})
        for key in self.environment.keys():
            if re.search('^GIT', key, re.IGNORECASE):
                self.git_cfg[key.lower()] = os.environ[key]
        # easier access
        self.git_url = self.git_cfg.get('git_url', None)
        self.git_dst = self.git_cfg.get('git_dst', None)
        self.git_branch = self.git_cfg.get('git_branch', None)
        self.git_tag = self.git_cfg.get('git_tag', None)
        self.git_hash = self.git_cfg.get('git_hash', None)

    def write_envs(self):
        env_file_path = self.local_config.get('env_file_path', None)
        if env_file_path is not None:
            envs = list()
            for key in self.environment.keys():
                # Don't set inherited environment variables that dont need to be configured
                if key not in ['HOME', 'PATH']:
                    envs.append("%s=%s" % (key, os.environ[key]))
            self.write_file(envs, env_file_path)

    def load_envs(self):
        env_file_path = self.local_config.get('env_file_path', None)
        if env_file_path is not None and os.path.exists(env_file_path):
            # Load environment variables from .env file
            reg = re.compile('(?P<key>\w+)(\=(?P<value>.+))')
            for line in open(env_file_path):
                m = reg.match(line)
                if m:
                    key = m.group('key')
                    if m.group('value'):
                        value = m.group('value')
                    else:
                        value = ''
                    os.environ[key] = value


class GitManager(object):
    """ Manager for git operations """

    def __init__(self, url, git_dst, git_branch=None, git_tag=None, git_hash=None):
        self.url = url
        self.git_dst = git_dst
        self.git_branch = git_branch
        self.git_tag = git_tag
        self.git_hash = git_hash
        super(self.__class__, self).__init__()

    class GitException(Exception):
        def getExitCode(self):
            return GIT_EXCEPTION

    def get_commands(self):
        git_commands = list()
        if self.git_hash is not None:
            # It's not possible to do a sparse clone when we need a specific commit hash
            git_commands.append(['git', 'clone', self.url, '.'])
            git_commands.append(['git', 'checkout', self.git_hash])
        elif self.git_tag is not None:
            git_commands.append(['git', 'clone', '--depth=1', '-b', '%s' % self.git_tag, self.url, '.'])  # detached HEAD
        elif self.git_branch is not None:
            git_commands.append(['git', 'clone', '--depth=1', '-b', '%s' % self.git_branch, self.url, '.'])
        else:
            git_commands.append(['git', 'clone', '--depth=1', self.url, '.'])
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
            return_code = self.call(cmd, cwd=self.git_dst)
            if return_code != 0:
                raise self.GitException('Git command failed: %s' % ' '.join(cmd))


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
            # Mount working_dir to remote_dir if empty
            if not os.listdir(self.base):
                mounts_list = list()
                mounts_list.append((self.remote, self.base))
            else:
                return False

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
            # Copy mount_dir to remote, if remote is empty, and mount_dir has files
            if os.path.exists(mount_dir) and os.listdir(mount_dir) and not os.listdir(remote_dir):
                # use copy_tree because shutil.copytree doesn't like it when the dst exists
                copy_tree(mount_dir, remote_dir)
                # Fix permissions recursively in remote_dir
                for root, dirs, files in os.walk(remote_dir):
                    for item in dirs:
                        os.chown(os.path.join(root, item), self.mount_uid, self.mount_gid)
                    for item in files:
                        os.chown(os.path.join(root, item), self.mount_uid, self.mount_gid)
            # Delete mount_dir if exists. Create symlink to remote_dir
            if os.path.isfile(mount_dir) or os.path.islink(mount_dir):
                os.remove(mount_dir)
            elif os.path.isdir(mount_dir):
                shutil.rmtree(mount_dir)
            os.symlink(remote_dir, mount_dir)
            print("Link created %s to %s" % (mount_dir, remote_dir))


class TemplateManager(object):
    """ Templated Config File Manager """

    def __init__(self, files=None, context=None):
            self.files = files
            self.context = context
            super(self.__class__, self).__init__()

    @staticmethod
    def render(file, context):
        from jinja2 import Environment, FileSystemLoader, contextfunction
        environment = Environment(loader=FileSystemLoader(searchpath="/"))
        def from_json(value):
            return json.loads(value)
        @contextfunction
        def get_context(c):
            return c
        environment.filters['from_json'] = from_json
        # fix issue w/ UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3 in position 1: ordinal not in range(128)
        if (sys.version_info < (3, 0)):
            reload(sys)
            sys.setdefaultencoding("UTF-8")
        template = environment.get_template(file)
        template.globals['context'] = get_context
        template.globals['callable'] = callable
        return template.render(context)

    def render_files(self):
        from stat import S_IMODE
        for f in self.files:
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp_f:
                output = self.render(f, self.context)
                if (sys.version_info > (3, 0)):
                    tmp_f.write(bytes(self.render(f, self.context), 'UTF-8'))  # python 3
                else:
                    tmp_f.write(output)  # python 2

            f_st = os.stat(f)
            root, ext = os.path.splitext(f)
            if ext == ".j2":
                f = root
            os.rename(tmp_f.name, f)
            os.chmod(f, S_IMODE(f_st.st_mode))
            os.chown(f, f_st.st_uid, f_st.st_gid)
            print("Rendered template %s with mode %d" % (f, int(oct(f_st.st_mode)[-4:])))


def main(argv):

    def execute(arg, user, group):
        # Update home to correct value incase it was inherited
        home = pwd.getpwuid(user)[5]  # Users home directory
        print("Updating HOME to %s" % home)
        os.environ['HOME'] = home
        print("Replacing current process with: %s" % arg[1])
        os.setgid(group)
        os.setuid(user)
        print("Running as %s:%s" % (os.geteuid(), os.getegid()))
        sys.stdout.flush()
        os.execvpe(arg[1], arg[1:], os.environ)  # replace current process, inherit environment

    def vg_debug():
        debug = bool(os.environ.get('VOLTGRID_PIE_DEBUG', 'False').lower() in ("true", "yes", "t", "1"))
        print("voltgrid.py debug %s" % str(debug))
        if debug:
            for env in os.environ:
                val = os.getenv(env)
                print("Environment: %s='%s'" % (env, val))
        return debug

    # Unset inherited environment variables that dont need to be configured
    for e in ['HOME',]:
        print("Unsetting %s" % e)
        del os.environ[e]

    # Load config
    c = ConfigManager(VG_CONF_PATH)
    c.load_envs()
    c.write_envs()
    c.load_config()
    c.load_git_conf()
    local_config = c.local_config
    files = local_config.get('files', {})
    dirs = local_config.get('dirs', {})

    VOLTGRID_PIE_DEBUG = vg_debug()

    # Checkout Git
    if c.git_url is not None:
        g = GitManager(url=c.git_url, git_dst=c.git_dst, git_branch=c.git_branch, git_tag=c.git_tag, git_hash=c.git_hash)
        g.run()

    # Mount shares
    working_dir = dirs.get('working_dir', None)
    remote_dir = dirs.get('remote_dir', None)
    if working_dir is not None and remote_dir is not None:
        m = MountManager(working_dir, remote_dir, DEFAULT_UID, DEFAULT_GID)
        m.handle()

    # Write config from templates
    if len(files) > 0:
        t = TemplateManager(files, context=c.config)
        t.render_files()

    # Spawn Next Process
    if len(argv) > 1:
        execute(argv, c.spawn_uid, c.spawn_gid)

if __name__ == "__main__":
    main(argv=sys.argv)
