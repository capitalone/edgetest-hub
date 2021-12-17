# Edgetest hub plugin

![python-3.7](https://img.shields.io/badge/python-3.7-green.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

[Full Documentation](https://capitalone.github.io/edgetest-hub/)

Table Of Contents
-----------------

- [Install](#install)
- [Getting Started](#getting-started)
- [Contributing](#contributing)
- [License](#license)

Install
-------

Installation from PyPI:

```console
$ python -m pip install edgetest-hub
```


Installation from conda-forge:

```console
$ conda install -c conda-forge edgetest-hub
```


Getting Started
---------------

This plugin uses [hub](https://github.com/github/hub) to enable automating Pull Requests from the results of
[edgetest](https://github.com/capitalone/edgetest). This is intended to be used on Jenkins, but can be
used from any machine with `git` and `hub` installed.

To use this plugin, add an ``edgetest.hub`` section to your configuration:

```ini
[edgetest.hub]
git_repo_org = org-name
git_repo_name = repo-name
git_username = Jenkins  # optional
git_useremail = noreply@capitalone.com  # optional
updater_branch = dep-updates  # optional
pr_to_branch = develop  # optional
pr_reviewers = fdosani  # comma seperated github ids
```
- ensure you have an environment variable `GITHUB_TOKEN` set. This token should have permissions to interact with the
  GitHub repo in question.
- `git` is installed.
- `hub` is installed. See [here](https://hub.github.com/).

That's it! the plugin will automatically be called after the tests finish.

- It will check for `GITHUB_TOKEN`before continuing.
- The first step configures `git` and the `updater_branch`.
  - will delete the `updater_branch` if it exists remotely or locally.
- Then commits `setup.cfg` and `requirements.txt` and submits a PR for review.


Contributing
------------

See our [developer documentation](https://capitalone.github.io/edgetest-hub/developer.html).

We welcome and appreciate your contributions! Before we can accept any contributions, we ask that you please be sure to
sign the [Contributor License Agreement (CLA)](https://cla-assistant.io/capitalone/edgetest-hub)

This project adheres to the [Open Source Code of Conduct](https://developer.capitalone.com/resources/code-of-conduct/).
By participating, you are expected to honor this code.

License
-------

Apache-2.0
