import os
from time import sleep
from travispy import TravisPy as TravisCI
from travispy.errors import TravisError


def enable_continuous_integration(repository):
    r"""
    Enable continuous integration on a repository using Travis.

    :param repository:
        The repository in the form of {owner}/{repo}.
    """

    travis = TravisCI.github_auth(os.environ.get("GITHUB_TOKEN"))
    
    for attempt in range(3):
        travis.user().sync()

        try:
            return travis.repo(repository).enable()

        except TravisError:
            sleep(3)

    raise