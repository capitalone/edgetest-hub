"""Plugin for hub functionality with ``edgetest``."""
import os
from typing import Dict, List

import pluggy
from edgetest.logger import get_logger
from edgetest.schema import Schema
from edgetest.utils import _run_command

LOG = get_logger(__name__)

hookimpl = pluggy.HookimplMarker("edgetest")

HUB_COMMAND = "hub"
GIT_COMMAND = "git"
GIT_TOKEN_ENVNAME = "GITHUB_TOKEN"


def configure_branch(conf: Dict):
    """Configure the git and the branch before we submit a PR with hub.

    Parameters
    ----------
    conf: Dict


    Returns
    -------
    None
    """
    git_repo_url = (
        f"https://{os.environ[GIT_TOKEN_ENVNAME]}@github.com/"
        f"{conf['hub']['git_repo_org']}/{conf['hub']['git_repo_name']}.git"
    )
    out, _ = _run_command(
        GIT_COMMAND, "config", "user.name", conf["hub"]["git_username"]
    )
    out, _ = _run_command(
        GIT_COMMAND, "config", "user.email", conf["hub"]["git_useremail"]
    )
    out, _ = _run_command(GIT_COMMAND, "remote", "set-url", "origin", git_repo_url)
    out, _ = _run_command(GIT_COMMAND, "config", "--global", "hub.protocol", "https")
    out, _ = _run_command(
        GIT_COMMAND,
        "config",
        "--global",
        "--add",
        "hub.host",
        "github.com",
    )

    try:  # delete any remote updater_branch
        out, _ = _run_command(
            GIT_COMMAND, "push", git_repo_url, "--delete", conf["hub"]["updater_branch"]
        )
    except RuntimeError:
        LOG.info(
            f"Remote branch {conf['hub']['updater_branch']} not found. Continuing on."
        )

    try:  # delete any local updater_branch
        out, _ = _run_command(
            GIT_COMMAND, "branch", "-D", conf["hub"]["updater_branch"]
        )
    except RuntimeError:
        LOG.info(
            f"Local branch {conf['hub']['updater_branch']} not found. Continuing on."
        )

    out, _ = _run_command(GIT_COMMAND, "clean", "-fd")

    try:
        out, _ = _run_command(
            GIT_COMMAND,
            "checkout",
            "-b",
            conf["hub"]["updater_branch"],
            conf["hub"]["pr_to_branch"],
        )
    except RuntimeError:
        out, _ = _run_command(
            GIT_COMMAND,
            "checkout",
            "-b",
            conf["hub"]["updater_branch"],
        )


def push_branch(conf: Dict):
    """Push the branch and submit a PR with hub.

    Parameters
    ----------
    conf: Dict


    Returns
    -------
    None
    """
    try:
        out, _ = _run_command(GIT_COMMAND, "diff-index", "--quiet", "HEAD")
        LOG.info("No changes detected. No pull request opened.")
    except RuntimeError:
        out, _ = _run_command(
            GIT_COMMAND,
            "add",
            "setup.cfg",
            "requirements.txt",
        )
        LOG.info("Adding setup.cfg and requirements.txt")

        os.environ["PRE_COMMIT_ALLOW_NO_CONFIG"] = "1"
        out, _ = _run_command(
            GIT_COMMAND,
            "commit",
            "-m",
            "environmentally friendly",
        )
        LOG.info("Committing changes.")

        out, _ = _run_command(
            GIT_COMMAND,
            "push",
            "origin",
            conf["hub"]["updater_branch"],
        )
        LOG.info("Pushing changes to remote.")

        out, _ = _run_command(
            HUB_COMMAND,
            "pull-request",
            "-b",
            conf["hub"]["pr_to_branch"],
            "-m",
            f"[EDGETEST] Updating {conf['hub']['git_repo_name']} dependency versions",
            "-r",
            conf["hub"]["pr_reviewers"],
            "--push",
        )
        LOG.info("Submitting PR.")


@hookimpl
def addoption(schema: Schema):
    """Add an email global configuration option.

    Parameters
    ----------
    schema : Schema
        The schema class.
    """
    schema.add_globaloption(
        "hub",
        {
            "type": "dict",
            "schema": {
                "git_repo_org": {
                    "type": "string",
                    "coerce": "strip",
                    "required": True,
                },
                "git_repo_name": {
                    "type": "string",
                    "coerce": "strip",
                    "required": True,
                },
                "git_username": {
                    "type": "string",
                    "coerce": "strip",
                    "default": "Jenkins",
                },
                "git_useremail": {
                    "type": "string",
                    "coerce": "strip",
                    "default": "noreply@capitalone.com",
                },
                "updater_branch": {
                    "type": "string",
                    "coerce": "strip",
                    "default": "dep-updates",
                },
                "pr_to_branch": {
                    "type": "string",
                    "coerce": "strip",
                    "default": "develop",
                },
                "pr_reviewers": {
                    "type": "string",
                    "coerce": "strip",
                    "required": True,
                },
            },
        },
    )


@hookimpl
def post_run_hook(testers: List, conf: Dict):
    """Invoke hub after the testing is complete."""
    if (
        testers[-1].status and GIT_TOKEN_ENVNAME in os.environ
    ):  # skip is token not available
        if conf.get("hub"):
            configure_branch(conf)
            push_branch(conf)
    else:
        LOG.info("Environment variable GITHUB_TOKEN not found. Skipping Hub plugin.")
