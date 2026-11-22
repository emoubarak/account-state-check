"""jev-check was renamed account-state-check: old installs must keep working."""

import subprocess
import sys
import warnings

import pytest

from account_state_check import config

TOML = '[target]\nbase = "http://localhost:8081"\nallowed_hosts = ["localhost"]\n'


def test_new_config_name_found(tmp_path):
    (tmp_path / "account-state-check.toml").write_text(TOML)
    assert config.find(tmp_path).name == "account-state-check.toml"


def test_legacy_config_name_still_found_from_a_subfolder(tmp_path):
    (tmp_path / "jevcheck.toml").write_text(TOML)
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    assert config.find(sub).name == "jevcheck.toml"


def test_new_config_wins_over_legacy(tmp_path):
    (tmp_path / "jevcheck.toml").write_text(TOML)
    (tmp_path / "account-state-check.toml").write_text(TOML)
    assert config.find(tmp_path).name == "account-state-check.toml"


def test_artifacts_default_follows_existing_legacy_folder(tmp_path):
    (tmp_path / "jevcheck.toml").write_text(TOML)
    assert config.load(tmp_path / "jevcheck.toml").artifacts.name == ".account-state-check"
    (tmp_path / ".jevcheck").mkdir()
    assert config.load(tmp_path / "jevcheck.toml").artifacts.name == ".jevcheck"
    (tmp_path / ".account-state-check").mkdir()
    assert config.load(tmp_path / "jevcheck.toml").artifacts.name == ".account-state-check"


def test_explicit_artifacts_setting_is_respected(tmp_path):
    (tmp_path / "jevcheck.toml").write_text(TOML + '[run]\nartifacts = ".mine"\n')
    (tmp_path / ".jevcheck").mkdir()
    assert config.load(tmp_path / "jevcheck.toml").artifacts.name == ".mine"


def test_old_import_forwards_with_a_deprecation_warning():
    code = (
        "import warnings; warnings.simplefilter('error', DeprecationWarning)\n"
        "try:\n    import jevcheck\nexcept DeprecationWarning as w:\n    print('WARN', w)\n"
        "else:\n    print('NOWARN')\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout
    assert out.startswith("WARN") and "account_state_check" in out
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        import account_state_check
        import jevcheck
    assert jevcheck.Check is account_state_check.Check
    assert jevcheck.result is account_state_check.result


def test_old_command_warns_then_runs_the_new_one():
    run = subprocess.run([sys.executable, "-m", "jevcheck", "--help"], capture_output=True, text=True)
    assert run.returncode == 0
    assert "deprecated" in run.stderr and "account-state-check" in run.stderr
    assert "usage: account-state-check" in run.stdout


def test_new_command_does_not_warn():
    run = subprocess.run([sys.executable, "-m", "account_state_check", "--help"], capture_output=True, text=True)
    assert run.returncode == 0 and "deprecated" not in run.stderr


def test_init_scaffolds_new_names_and_respects_a_legacy_config(tmp_path):
    new, old = tmp_path / "new", tmp_path / "old"
    old.mkdir()
    (old / "jevcheck.toml").write_text(TOML)
    for d in (new, old):
        subprocess.run([sys.executable, "-m", "account_state_check", "init", "--dir", str(d)],
                       capture_output=True, text=True, check=True)
    assert sorted(p.name for p in new.iterdir()) == [
        "account-state-check.toml", "account_state_check_checks.py", "account_state_check_hooks.py"]
    assert [p.name for p in old.iterdir()] == ["jevcheck.toml"]


def test_templates_import_the_new_package():
    from account_state_check import cli
    checks = (cli.TEMPLATES / "account_state_check_checks.py").read_text()
    assert "from account_state_check import" in checks and "jevcheck" not in checks


@pytest.mark.parametrize("branch,legacy,new,expected", [
    (None, True, False, "jevcheck-assets"),
    (None, True, True, "account-state-check-assets"),
    (None, False, False, "account-state-check-assets"),
    ("custom", True, False, "custom"),
])
def test_screenshot_branch_choice(monkeypatch, branch, legacy, new, expected):
    from account_state_check import shots

    def fake_gh(repo, method, path, payload=None, ok_404=False):
        name = path.rsplit("/", 1)[-1]
        return {"ref": name} if (name == "jevcheck-assets" and legacy) or (name == "account-state-check-assets" and new) else None

    monkeypatch.setattr(shots, "_gh", fake_gh)
    assert shots.pick_branch("o/r", branch) == expected
