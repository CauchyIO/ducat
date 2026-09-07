"""Tests for tools/check-upstream.py, the checker for upstream sources that have moved.

Nothing here reaches the network. The two readers are pure functions over a response
body, and `check` is exercised with its signal reader replaced, so the suite says what
the script does with an answer rather than what the internet says today.
"""

from types import ModuleType

import pytest

LEARN_HEAD = (
    '<meta name="ms.date" content="2026-08-28T00:00:00.0000000Z" />'
    '<meta name="git_commit_id" content="9d69f24dbb22d6ad38df4b95845a050fb1ee59bd" />'
    '<meta name="updated_at" content="2026-08-28T23:01:00.0000000Z" />'
)


def _source(check_upstream: ModuleType, **overrides: object) -> object:
    """Builds a Source with sensible defaults, overridden per test.

    Args:
        check_upstream: The loaded script module.
        **overrides: Fields to set on the Source.

    Returns:
        A Source instance.
    """
    fields: dict[str, object] = {
        "id": "probe",
        "kind": "learn-page",
        "url": "https://example.invalid/page",
        "signal": "pinned",
        "distils_into": ("references/data-sources.md",),
    }
    fields.update(overrides)
    return check_upstream.Source(**fields)


def test_learn_signal_is_the_commit_id_not_the_dates(check_upstream: ModuleType) -> None:
    """The reader picks git_commit_id, never ms.date or updated_at.

    Both dates sit in the same head block and both are wrong for this purpose: ms.date
    is author-declared and drifts, updated_at moves on rebuilds that change no prose.
    """
    assert (
        check_upstream.read_learn_signal(LEARN_HEAD) == "9d69f24dbb22d6ad38df4b95845a050fb1ee59bd"
    )


def test_a_learn_page_without_the_meta_tag_raises(check_upstream: ModuleType) -> None:
    """A page whose shape changed is an error, never a silent pass.

    Returning "no signal" here would compare nothing against the pin and look like
    agreement, which is the failure this whole script exists to remove.
    """
    with pytest.raises(LookupError):
        check_upstream.read_learn_signal("<html><head></head></html>")


def test_github_release_signal_is_the_tag_name(check_upstream: ModuleType) -> None:
    """The reader takes tag_name from the latest-release response."""
    assert check_upstream.read_github_release_signal('{"tag_name": "v1.4"}') == "v1.4"


def test_a_release_response_without_a_tag_raises(check_upstream: ModuleType) -> None:
    """A response carrying no tag_name is an error, not an empty signal."""
    with pytest.raises(LookupError):
        check_upstream.read_github_release_signal('{"message": "Not Found"}')


def test_an_unchanged_source_is_reported_as_matched(
    check_upstream: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A live signal equal to the pinned one produces no finding."""
    monkeypatch.setattr(check_upstream, "live_signal", lambda source: "pinned")
    report = check_upstream.check((_source(check_upstream),))
    assert report.matched == ["probe"]
    assert report.moved == []


def test_a_moved_source_names_what_to_re_read_and_re_distil(
    check_upstream: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A changed signal names the source, both signals, and the file that depends on it."""
    monkeypatch.setattr(check_upstream, "live_signal", lambda source: "moved")
    report = check_upstream.check((_source(check_upstream),))
    assert len(report.moved) == 1
    finding = report.moved[0]
    assert "pinned pinned, live moved" in finding
    assert "references/data-sources.md" in finding
    assert report.matched == []


def test_an_unreachable_source_is_not_reported_as_moved(
    check_upstream: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed read is a broken run, not a finding somebody must act on.

    Conflating the two would raise a re-distillation alarm every time the network
    hiccupped, and the alarm would stop being believed.
    """

    def boom(source: object) -> str:
        raise OSError("connection reset")

    monkeypatch.setattr(check_upstream, "live_signal", boom)
    report = check_upstream.check((_source(check_upstream),))
    assert report.moved == []
    assert len(report.unreachable) == 1
    assert "connection reset" in report.unreachable[0]


def test_sources_publishing_no_signal_are_listed_not_skipped(
    check_upstream: ModuleType,
) -> None:
    """An unversioned or unnamed source is reported, so its absence stays visible."""
    sources = (
        _source(
            check_upstream, id="live-site", kind="unversioned", url="", signal="", note="no version"
        ),
        _source(
            check_upstream, id="no-url", kind="unnamed", url="", signal="", note="no URL recorded"
        ),
    )
    report = check_upstream.check(sources)
    assert len(report.uncheckable) == 2
    assert report.matched == [] and report.moved == [] and report.unreachable == []


def test_live_signal_refuses_a_kind_that_publishes_nothing(check_upstream: ModuleType) -> None:
    """Asking an unversioned source for a signal is a programming error, not an empty string."""
    with pytest.raises(ValueError):
        check_upstream.live_signal(_source(check_upstream, kind="unversioned", url="", signal=""))


def test_exit_codes_separate_a_move_from_a_broken_run(
    check_upstream: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0 when everything matches, 1 when a source moved, 2 when one could not be read.

    The workflow keys off these: 1 raises an issue for a human to act on, 2 fails the
    run without inventing a re-distillation that may not be owed.
    """
    monkeypatch.setattr(check_upstream, "SOURCES", (_source(check_upstream),))

    monkeypatch.setattr(check_upstream, "live_signal", lambda source: "pinned")
    assert check_upstream.main() == 0

    monkeypatch.setattr(check_upstream, "live_signal", lambda source: "moved")
    assert check_upstream.main() == 1

    def boom(source: object) -> str:
        raise OSError("unreachable")

    monkeypatch.setattr(check_upstream, "live_signal", boom)
    assert check_upstream.main() == 2


def test_the_shipped_source_list_is_coherent(check_upstream: ModuleType) -> None:
    """Every shipped source has what its kind requires, and ids are unique.

    A source with the wrong shape — a checkable kind with no URL, an unnamed one with a
    pin — would be checked wrongly or skipped silently.
    """
    sources = check_upstream.SOURCES
    assert len({s.id for s in sources}) == len(sources)
    for source in sources:
        assert source.distils_into, source.id
        if source.kind in ("learn-page", "github-release"):
            assert source.url and source.signal, source.id
        else:
            assert not source.url and not source.signal, source.id
            assert source.note, source.id


def test_live_signal_sends_each_kind_to_its_own_reader(
    check_upstream: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A learn page is read for its commit id, a GitHub release for its tag.

    Without this the two readers can be swapped and every other test still passes: both
    take a response body and return a string, so only the pairing distinguishes them.
    The wrong pairing reports a spurious move on the next run.
    """
    monkeypatch.setattr(check_upstream, "fetch", lambda url: bodies[url])
    bodies = {
        "https://learn/page": LEARN_HEAD,
        "https://api/release": '{"tag_name": "v1.4"}',
    }

    page = _source(check_upstream, kind="learn-page", url="https://learn/page")
    release = _source(check_upstream, kind="github-release", url="https://api/release")

    assert check_upstream.live_signal(page) == "9d69f24dbb22d6ad38df4b95845a050fb1ee59bd"
    assert check_upstream.live_signal(release) == "v1.4"


def test_fetch_identifies_itself_and_survives_odd_bytes(
    check_upstream: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The reader sends a User-Agent and a timeout, and never raises on undecodable bytes.

    Decoding strictly would turn one stray byte on a docs page into an unreachable
    source, which is a red run for a reason that has nothing to do with the content.
    """
    seen: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def read(self) -> bytes:
            return b"ok \xff"

    def fake_urlopen(request: object, timeout: int) -> FakeResponse:
        seen["headers"] = request.headers
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(check_upstream.urllib.request, "urlopen", fake_urlopen)

    assert check_upstream.fetch("https://example.invalid/x").startswith("ok ")
    assert seen["timeout"] == check_upstream.TIMEOUT_SECONDS
    assert check_upstream.USER_AGENT in str(seen["headers"])
