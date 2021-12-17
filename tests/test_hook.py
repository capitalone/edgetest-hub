"""Test the hub hook."""
import os
from pathlib import Path
from unittest.mock import PropertyMock, call, patch

import pytest
from click.testing import CliRunner
from edgetest.interface import cli
from edgetest.schema import EdgetestValidator, Schema
from edgetest.utils import parse_cfg

from edgetest_hub.plugin import addoption

CFG = """
[edgetest.envs.myenv]
upgrade =
    myupgrade
command =
    pytest tests -m 'not integration'
"""

CFG_HUB = """
[edgetest.hub]
git_repo_org = test-org
git_repo_name = test-repo
pr_reviewers = abc123,efg456
[edgetest.envs.myenv]
upgrade =
    myupgrade
command =
    pytest tests -m 'not integration'
"""

PIP_LIST = """
[{"name": "myupgrade", "version": "0.2.0"}]
"""

TABLE_OUTPUT = """

============= =============== =================== =================
 Environment   Passing tests   Upgraded packages   Package version
------------- --------------- ------------------- -----------------
 myenv         True            myupgrade           0.2.0
============= =============== =================== =================

"""


@pytest.mark.parametrize("config", [CFG, CFG_HUB])
def test_addoption(config, tmpdir):
    """Test the addoption hook."""
    location = tmpdir.mkdir("mylocation")
    conf_loc = Path(str(location), "myconfig.ini")
    with open(conf_loc, "w") as outfile:
        outfile.write(config)

    schema = Schema()
    addoption(schema=schema)

    cfg = parse_cfg(filename=conf_loc)
    validator = EdgetestValidator(schema=schema.schema)

    assert validator.validate(cfg)


@patch("edgetest_hub.plugin._run_command", autospec=True)
@patch("edgetest.lib.EnvBuilder", autospec=True)
@patch("edgetest.core.Popen", autospec=True)
@patch("edgetest.utils.Popen", autospec=True)
def test_hub_notoken(mock_popen, mock_cpopen, mock_builder, mock_run_command):
    """Test hub and git in setting up PR of changes."""
    mock_popen.return_value.communicate.return_value = (PIP_LIST, "error")
    type(mock_popen.return_value).returncode = PropertyMock(return_value=0)
    mock_cpopen.return_value.communicate.return_value = ("output", "error")
    type(mock_cpopen.return_value).returncode = PropertyMock(return_value=0)

    runner = CliRunner()

    with runner.isolated_filesystem() as loc:
        with open("setup.cfg", "w") as outfile:
            outfile.write(CFG_HUB)

        result = runner.invoke(cli, ["--config=setup.cfg"])

    assert result.exit_code == 0
    assert mock_run_command.called is False


@patch.dict(os.environ, {"GITHUB_TOKEN": "abcd1234"})
@patch("edgetest_hub.plugin._run_command", autospec=True)
@patch("edgetest.lib.EnvBuilder", autospec=True)
@patch("edgetest.core.Popen", autospec=True)
@patch("edgetest.utils.Popen", autospec=True)
def test_hub_withtoken_nopr(mock_popen, mock_cpopen, mock_builder, mock_run_command):
    """Test hub and git in setting up PR of changes."""
    mock_popen.return_value.communicate.return_value = (PIP_LIST, "error")
    type(mock_popen.return_value).returncode = PropertyMock(return_value=0)
    mock_cpopen.return_value.communicate.return_value = ("output", "error")
    type(mock_cpopen.return_value).returncode = PropertyMock(return_value=0)

    mock_run_command.side_effect = [(None, None)] * 10  # 10 calls
    expected_calls_no_pr = [
        call("git", "config", "user.name", "Jenkins"),
        call("git", "config", "user.email", "noreply@capitalone.com"),
        call(
            "git",
            "remote",
            "set-url",
            "origin",
            "https://abcd1234@github.com/test-org/test-repo.git",
        ),
        call("git", "config", "--global", "hub.protocol", "https"),
        call(
            "git",
            "config",
            "--global",
            "--add",
            "hub.host",
            "github.com",
        ),
        call(
            "git",
            "push",
            "https://abcd1234@github.com/test-org/test-repo.git",
            "--delete",
            "dep-updates",
        ),
        call("git", "branch", "-D", "dep-updates"),
        call("git", "clean", "-fd"),
        call("git", "checkout", "-b", "dep-updates", "develop"),
        call("git", "diff-index", "--quiet", "HEAD"),
    ]

    runner = CliRunner()

    with runner.isolated_filesystem() as loc:
        with open("setup.cfg", "w") as outfile:
            outfile.write(CFG_HUB)

        result = runner.invoke(cli, ["--config=setup.cfg"])

    assert mock_run_command.called is True
    assert mock_run_command.mock_calls == expected_calls_no_pr


@patch.dict(os.environ, {"GITHUB_TOKEN": "abcd1234"})
@patch("edgetest_hub.plugin._run_command", autospec=True)
@patch("edgetest.lib.EnvBuilder", autospec=True)
@patch("edgetest.core.Popen", autospec=True)
@patch("edgetest.utils.Popen", autospec=True)
def test_hub_withtoken_withpr(mock_popen, mock_cpopen, mock_builder, mock_run_command):
    """Test hub and git in setting up PR of changes."""
    mock_popen.return_value.communicate.return_value = (PIP_LIST, "error")
    type(mock_popen.return_value).returncode = PropertyMock(return_value=0)
    mock_cpopen.return_value.communicate.return_value = ("output", "error")
    type(mock_cpopen.return_value).returncode = PropertyMock(return_value=0)

    mock_run_command.side_effect = (
        [(None, None)] * 9 + [RuntimeError()] + [(None, None)] * 4
    )  # 14 calls
    expected_calls_with_pr = [
        call("git", "config", "user.name", "Jenkins"),
        call("git", "config", "user.email", "noreply@capitalone.com"),
        call(
            "git",
            "remote",
            "set-url",
            "origin",
            "https://abcd1234@github.com/test-org/test-repo.git",
        ),
        call("git", "config", "--global", "hub.protocol", "https"),
        call(
            "git",
            "config",
            "--global",
            "--add",
            "hub.host",
            "github.com",
        ),
        call(
            "git",
            "push",
            "https://abcd1234@github.com/test-org/test-repo.git",
            "--delete",
            "dep-updates",
        ),
        call("git", "branch", "-D", "dep-updates"),
        call("git", "clean", "-fd"),
        call("git", "checkout", "-b", "dep-updates", "develop"),
        call("git", "diff-index", "--quiet", "HEAD"),
        call("git", "add", "setup.cfg", "requirements.txt"),
        call("git", "commit", "-m", "environmentally friendly"),
        call("git", "push", "origin", "dep-updates"),
        call(
            "hub",
            "pull-request",
            "-b",
            "develop",
            "-m",
            "[EDGETEST] Updating test-repo dependency versions",
            "-r",
            "abc123,efg456",
            "--push",
        ),
    ]

    runner = CliRunner()

    with runner.isolated_filesystem() as loc:
        with open("setup.cfg", "w") as outfile:
            outfile.write(CFG_HUB)

        result = runner.invoke(cli, ["--config=setup.cfg"])

    assert mock_run_command.called is True
    assert mock_run_command.mock_calls == expected_calls_with_pr
