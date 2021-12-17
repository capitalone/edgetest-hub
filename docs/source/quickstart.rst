Quick Start
===========

Install
-------

Installation from PyPI:

.. code:: console

    $ python -m pip install edgetest-hub


Installation from conda-forge:

.. code:: console

    $ conda install -c conda-forge edgetest-hub


Usage
-----
The primary use case is Jenkins to automate PRs with the latest versions for dependency testing, but can be
used from any machine with ``git`` and ``hub`` installed.

To automatically update your package with ``edgetest-hub``, and auto generate Pull Requests add the following
to your configuration:

.. code-block:: ini

    [edgetest.hub]
    git_repo_org = org-name
    git_repo_name = repo-name
    git_username = Jenkins  # optional
    git_useremail = noreply@capitalone.com  # optional
    updater_branch = dep-updates  # optional
    pr_to_branch = develop  # optional
    pr_reviewers = fdosani  # comma seperated github ids

- ensure you have an environment variable ``GITHUB_TOKEN`` set. This token should have permissions to interact with the
  GitHub repo in question.
- ``git`` is installed.
- ``hub`` is installed. See `here <https://hub.github.com/>`_.

That's it! the plugin will automatically be called after the tests finish.

- It will check for ``GITHUB_TOKEN`` before continuing.
- The first step configures ``git`` and the ``updater_branch``.
  - will delete the ``updater_branch`` if it exists remotely or locally.
- Then commits ``setup.cfg`` and ``requirements.txt`` and submits a PR for review.
