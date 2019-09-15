from termcolor import cprint
from shutil import which
from pathlib import Path
from setuptools import find_packages

import semver

from invoke import run as invoke_run
from invoke import task

VERSION_TEMPLATE = """__version__ = "{version_string}"
"""

HERE = Path(__file__).parent

@task(help={"version": "Version number to release"})
def prerelease(_ctx, version):
    """
    Release a pre-release version
    Running this task will:
     - Bump the version number
     - Push a release to pypi
    """
    check_prerequisites()
    info(f"Releasing version {version} as prerelease")
    build_publish(version)


@task(help={"version": "Version number to release"})
def release(_ctx, version):
    """
    Release a new version
    Running this task will:
     - Prompt the user for a changelog and write it to
       the release notes
     - Commit the release notes
     - Bump the version number
     - Push a release to pypi
     - commit the version changes to source control
     - tag the commit
    """
    check_prerequisites()
    info(f"Releasing version {version} as full release")

    build_publish(version)

    info("Committing version changes")

    run(f"git checkout -b release-{version}")
    run(f"git add {package_name()}/_version.py")
    run(f'git commit -m "Bump version to {version}"')
    info(f"Tagging version {version} and pushing to GitHub")
    run(f"git push origin release-{version} --tags")


@task(help={
    "version": "Version number to finalize. Must be "
               "the same version number that was used in the release."})
def postrelease(_ctx, version):
    """
    Finalise the release
    Running this task will:
     - bump the version to the next dev version
     - push changes to master
    """
    new_version = semver.bump_patch(version) + "-dev"
    info(f"Bumping version numbers to {new_version} and committing")
    set_pyversion(new_version)
    run(f"git checkout -b postrelease-{version}")
    run(f"git add {package_name()}/_version.py")
    run('git commit -m "Back to dev"')
    run(f"git push origin postrelease-{version}")


def build_publish(version):

    def clean():
        paths_to_clean = []
        for path in paths_to_clean:
            run(f"rm -rf {path}")

    def release_python_sdist():
        run("rm -f dist/*")
        run("python setup.py sdist")
        invoke_run("twine upload dist/*")


    info("Cleaning")
    clean()
    info("Updating versions")
    set_pyversion(version)
    info("Building and uploading Python source distribution")
    info("PyPI credentials:")
    release_python_sdist()


def set_pyversion(version):

    def normalize_version(version):
        version_info = semver.parse_version_info(version)
        version_string = str(version_info)
        return version_string

    version = normalize_version(version)
    version_path = HERE / package_name() / "_version.py"
    with version_path.open("w") as f:
        f.write(VERSION_TEMPLATE.format(version_string=version))

def package_name():
    packages = find_packages()
    return packages[0]

def check_prerequisites():
    for executable in ["twine"]:
        if which(executable) is None:
            error(
                f"{executable} executable not found. "
                f"You must have {executable} to release "
                "test."
            )
            exit(127)

def run(command, **kwargs):
    result = invoke_run(command, hide=True, warn=True, **kwargs)
    print('{} : {}'.format(command, result))
    if result.exited != 0:
        error(f"Error running {command}")
        print(result.stdout)
        print()
        print(result.stderr)
        exit(result.exited)


def error(text):
    cprint(text, "red")

def info(text):
    print(text)
