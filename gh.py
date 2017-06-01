import os
import subprocess
from glob import glob
from tempfile import mkdtemp
from github import Github as GitHub

from travis import enable_continuous_integration


def create_repository(organization_name, repository_name, 
    template_repository=None, travis_ci=True):
    r"""
    Create a new GitHub organizational repository using an existing repository
    as a template.

    :param organization_name:
        The name of the organization to create the new GitHub repository in.

    :param repository_name:
        The name of the new repository.

    :param template_repository: [optional]
        The name of the repository to use as a template. This can be a single
        repository name if it is owned by the same organization, or a repository
        in the form of {owner}/{repo}.

    :param travis_ci: [optional]
        Automagically enable continuous integration on Travis for the new 
        repository.
    """

    # Create a GitHub repository.
    github_client = GitHub(os.environ.get("GITHUB_TOKEN"))

    organization = github_client.get_organization(organization_name)
    new_repository = organization.create_repo(repository_name)
    new_repository_uri = "/".join([organization_name, repository_name])

    # Enable continuous integration.
    if travis_ci:
        enable_continuous_integration(new_repository_uri)

    # Copy from a template.
    if template_repository:        
        template = github_client.get_repo(template_repository)

        temp_folder = mkdtemp()
        subprocess.Popen(
            ["git", "clone", template.clone_url], cwd=temp_folder).wait()

        # Remove .git directory, create new one, add files, commit and push
        commands = [
            "rm -Rf .git/",
            "git init",
            "git add -f -A",
            "git remote add origin git@github.com:{uri}.git"\
                .format(uri=new_repository_uri),
            ("git", "commit", "-m", "Initial commit using {} template"\
                .format(template_repository)),
            "git push -u origin master"
        ]

        cwd = glob(os.path.join(temp_folder, "*"))[0]
        for command in commands:
            args = command.split() if isinstance(command, str) else command
            subprocess.Popen(args, cwd=cwd).wait()

    return new_repository

