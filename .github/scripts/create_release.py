from github import Github
import os
import re

# Path to the current script's directory
script_dir = os.path.dirname(os.path.realpath(__file__))

# Path to the setup.py relative to the script's directory
setup_path = os.path.join(script_dir, "../../clients/metatrader-sockets/setup.py")

# Reading the version from setup.py
with open(setup_path, "r") as f:
    setup_contents = f.read()
    print(setup_contents)

match = re.search(r"version\s*=\s*['\"]([^'\"]+)['\"]", setup_contents)
if match:
    setup_version = match.group(1)
else:
    raise ValueError("Could not find version in setup.py")

# Access the current repository
g = Github(os.getenv("GITHUB_TOKEN"))
repo = g.get_repo(os.getenv("GITHUB_REPOSITORY"))

# Fetch the latest release
releases = repo.get_releases()
latest_release = next((release for release in releases), None)

# If the setup.py version is different from the latest release, create a new release
if latest_release is None or latest_release.tag_name != setup_version:
    repo.create_git_ref(ref=f"refs/tags/{setup_version}", sha=os.getenv("GITHUB_SHA"))
    repo.create_git_release(
        tag=setup_version,
        name=f"Release {setup_version}",
        message="",
        draft=False,
        prerelease=False,
        target_commitish=os.getenv("GITHUB_SHA"),
    )
