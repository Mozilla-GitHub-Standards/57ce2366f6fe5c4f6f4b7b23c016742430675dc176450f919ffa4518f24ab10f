#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import os
import re
import sh
import pwd
import sys
import time
import logging

from shlex import shlex
from decouple import Csv, AutoConfig, config

LOG_LEVELS = [
    'DEBUG',
    'INFO',
    'WARNING',
    'ERROR',
    'CRITICAL',
]

LOG_LEVEL = config('LOG_LEVEL', logging.WARNING, cast=int)

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    format='%(asctime)s %(name)s %(message)s')
logging.Formatter.converter = time.gmtime
log = logging.getLogger(__name__)

def git(*args, strip=True, **kwargs):
    try:
        result = str(sh.contrib.git(*args, **kwargs))
        if strip:
            result = result.strip()
        return result
    except sh.ErrorReturnCode as e:
        log.error(e)

class AutoConfigPlus(AutoConfig):
    def __init__(self, *args, **kwargs):
        super(AutoConfigPlus, self).__init__(*args, **kwargs)

    @property
    def BOT_UID(self):
        return os.getuid()

    @property
    def BOT_GID(self):
        return pwd.getpwuid(self.BOT_UID).pw_gid

    @property
    def BOT_USER(self):
        return pwd.getpwuid(self.BOT_UID).pw_name

    @property
    def BOT_PORT(self):
        return config('BOT_PORT', 5000, cast=int)

    @property
    def BOT_TIMEOUT(self):
        return config('BOT_TIMEOUT', 120, cast=int)

    @property
    def BOT_WORKERS(self):
        return config('BOT_WORKERS', 2, cast=int)

    @property
    def BOT_MODULE(self):
        return config('BOT_MODULE', 'main:app')

    @property
    def BOT_REPOROOT(self):
        return git('rev-parse', '--show-toplevel')

    @property
    def BOT_TAGNAME(self):
        return git('describe', '--abbrev=0', '--always')

    @property
    def BOT_VERSION(self):
        return git('describe', '--abbrev=7', '--always')

    @property
    def BOT_BRANCH(self):
        return git('rev-parse', '--abbrev-ref', 'HEAD')

    @property
    def BOT_REVISION(self):
        return git('rev-parse', 'HEAD')

    @property
    def BOT_REMOTE_ORIGIN_URL(self):
        return git('config', '--get', 'remote.origin.url')

    @property
    def BOT_REPONAME(self):
        pattern = '(ssh|https)://([A-Za-z0-9\-_]+@)?github.com/(?P<reponame>[A-Za-z0-9\/\-_]+)(.git)?'
        match = re.search(pattern, self.BOT_REMOTE_ORIGIN_URL)
        return match.group('reponame')

    @property
    def BOT_PROJNAME(self):
        return os.path.basename(self.BOT_REPONAME)

    @property
    def BOT_PROJPATH(self):
        return os.path.join(self.BOT_REPOROOT, self.BOT_PROJNAME)

    @property
    def BOT_TESTPATH(self):
        return os.path.join(self.BOT_REPOROOT, 'tests')

    @property
    def BOT_LS_REMOTE(self):
        url = 'https://github.com/' + self.BOT_REPONAME
        result = git('ls-remote', url)
        return {refname: revision for revision, refname in [line.split() for line in result.split('\n')]}

    @property
    def BOT_GSM_STATUS(self):
        result = git('submodule', 'status', strip=False)
        pattern = '([ +-])([a-f0-9]{40}) ([A-Za-z0-9\/\-_.]+)( .*)?'
        matches = re.findall(pattern, result)
        states = {
            ' ': True,  # submodule is checked out the correct revision
            '+': False, # submodule is checked out to a different revision
            '-': None,  # submodule is not checked out
        }
        return {repopath: [revision, states[state]] for state, revision, repopath, _ in matches}

    def __getattr__(self, attr):
        log.info('attr = {attr}'.format(**locals()))
        result = self.__call__(attr)
        try:
            return int(result)
        except ValueError as ve:
            return result

CFG = AutoConfigPlus()
