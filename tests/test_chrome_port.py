"""Chrome picks its own DevTools port (port 0) and we read it back: no port collision possible."""

import pytest

from account_state_check import agent, chrome


def test_active_port_reads_first_line(tmp_path):
    (tmp_path / "DevToolsActivePort").write_text("41234\n/devtools/browser/abc\n")
    assert chrome.active_port(tmp_path) == 41234


@pytest.mark.parametrize("content", [None, "", "not-a-port\n/x\n"])
def test_active_port_missing_or_garbage(tmp_path, content):
    if content is not None:
        (tmp_path / "DevToolsActivePort").write_text(content)
    assert chrome.active_port(tmp_path) is None


def test_wait_ready_with_port_zero_uses_the_file(tmp_path, monkeypatch):
    (tmp_path / "DevToolsActivePort").write_text("41234\n/devtools/browser/abc\n")
    monkeypatch.setattr(chrome, "endpoint", lambda port: f"ws://127.0.0.1:{port}/x" if port == 41234 else None)
    assert chrome.wait_ready(0, profile_dir=tmp_path, timeout=2) == (41234, "ws://127.0.0.1:41234/x")


def test_wait_ready_times_out_with_auto_port(tmp_path):
    with pytest.raises(RuntimeError, match="auto"):
        chrome.wait_ready(0, profile_dir=tmp_path, timeout=0.5)


def test_start_browser_retries_when_chrome_does_not_come_up(tmp_path, monkeypatch):
    calls = {"launch": [], "stop": 0}

    class FakeChrome:
        free_port = staticmethod(lambda start: start)

        @staticmethod
        def launch(profile, port, **kw):
            calls["launch"].append(port)
            return object()

        @staticmethod
        def wait_ready(port, proc, timeout, profile_dir):
            if len(calls["launch"]) < 3:
                raise RuntimeError("Chrome did not open the DevTools port")
            return 5555, "ws://x"

        @staticmethod
        def stop(proc):
            calls["stop"] += 1

    monkeypatch.setattr(agent, "ensure_daemon", lambda: None)
    agent.start_browser(FakeChrome, tmp_path, headed=False)
    assert calls["launch"] == [0, 0, 0] and calls["stop"] == 2


def test_cdp_port_is_tried_first_then_auto(tmp_path, monkeypatch):
    calls = []

    class FakeChrome:
        free_port = staticmethod(lambda start: start)
        launch = staticmethod(lambda profile, port, **kw: calls.append(port) or object())
        stop = staticmethod(lambda proc: None)

        @staticmethod
        def wait_ready(port, proc, timeout, profile_dir):
            if port:
                raise RuntimeError("busy")
            return 6000, "ws://x"

    monkeypatch.setattr(agent, "ensure_daemon", lambda: None)
    agent.start_browser(FakeChrome, tmp_path, headed=False, port_start=9506)
    assert calls == [9506, 0]


def test_gives_up_after_all_attempts(tmp_path):
    class FakeChrome:
        free_port = staticmethod(lambda start: start)
        launch = staticmethod(lambda profile, port, **kw: object())
        stop = staticmethod(lambda proc: None)

        @staticmethod
        def wait_ready(port, proc, timeout, profile_dir):
            raise RuntimeError("never")

    with pytest.raises(RuntimeError, match="never"):
        agent.start_browser(FakeChrome, tmp_path, headed=False)
