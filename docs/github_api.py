#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
github_api.py -- Authenticate with Github.com

Written by Tony Pearson, IBM, 2020
"""

import logging
import sys

from github import Github

# API for Github Enterprise in IBM
ENTERPRISE = "https://api.github.com/"

# Personal Access Token
TOKENFILE = "github_api.token"

# Github Repository name.
REPONAME = "Call-for-Code-for-Racial-Justice/Legit-Info"


class GithubError(RuntimeError):
    """ Customized Error for this class """
    pass


class GithubConnect():
    """
    Class for processing Github.ibm.com Repo

    """

    def __init__(self, logger):
        """ Save Repository information """
        self.logger = logger
        self.reponame = REPONAME
        self.baseurl = ENTERPRISE
        self.tokenfile = TOKENFILE
        self.gith = None
        self.repo = None

    def authenticate(self):
        """ Use personal access token to access Github via API """
        token = None

        try:
            with open(self.tokenfile, 'r') as token_file:
                token = token_file.readline().splitlines()[0]
        except FileNotFoundError as e:
            print(e)
            print('To access github.ibm.com you will need to have a local')
            print('file that contains your "Personal Access Token".')
            print('')
            print('To get this key, sign in to your Github.com account,')
            print('select "Settings" under right pulldown, select ')
            print('"Developer Settings" on left panel, then choose ')
            print('"Personal Access Token".')
            print('')
            print('This will generate a 40-character token.  Create a ')
            print('one-line file called "github.token" with this token')
            print('in the first line, and put in your app directory')
            sys.exit()

        print('Accessing Github.com Repository: ', self.reponame)

        self.gith = Github(token)
        if self.logger:
            self.logger.info('Authenticated with Github')

        try:
            self.repo = self.gith.get_repo(self.reponame)
        except Exception as exc:
            if self.logger:
                self.logger.critical(f"Github error {self.reponame}: {exc}",
                                     exc_info=True)
            raise GithubError(f"GithubError {self.reponame}") from exc

        return self


def get_message(commit):
    """ Get message for this commit """

    msg = ''
    if commit.commit is not None:
        msg = commit.commit.message
        msg = ' '.join(msg.splitlines())
    return msg


if __name__ == "__main__":
    print('Testing: ', sys.argv[0])
    logger = logging.getLogger(__name__)

    # Authenticate with Github.ibm.com and fetch repo details.
    con = GithubConnect(logger)
    con.authenticate()
    print("Congratulations, you have connected to:", con.repo.name)

    commits = con.repo.get_commits()
    for commit in commits:
        sha = commit.sha[:7]
        msg = get_message(commit)
        cdate = commit.commit.committer.date
        weeknum = cdate.isocalendar()[1]
        parents = commit.parents
        pstring, connector = "", ""
        for parent in parents:
            pstring += connector + parent.sha[:7]
            connector = ", "

        print(weeknum, cdate, sha, msg, pstring)
