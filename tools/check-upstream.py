"""Detect when an upstream source a reference file was distilled from has moved.

`skills/ducat/references/data-sources.md` and `.../opportunity-catalog.md` are distilled
from sources that keep moving, and each carries a distillation date and nothing else.
That date says when somebody last read the source. It never says whether the source has
changed since, so a re-read that is owed looks exactly like one that is not.

This script pins the change signal each source publishes and compares it against the
live one. A re-distillation is then triggered by the source actually moving rather than
by a calendar, and a source that publishes no signal is named here as such, so its
absence is a visible fact instead of an omission.

Not a commit hook. Every other checker in tools/ is offline and deterministic; this one
reaches the network and is neither. Committing must never depend on a third party being
reachable, so this runs on a schedule in CI instead.

Exit codes are distinct on purpose: a moved source is a finding somebody must act on, a
source that cannot be reached is a broken run, and the two must not raise the same alarm.

    0  every pinned source still matches
    1  at least one source has moved — re-read it and re-pin
    2  at least one source could not be checked, and none had moved

Usage:
    uv run tools/check-upstream.py
"""

import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Literal

USER_AGENT = "ducat-upstream-check"
TIMEOUT_SECONDS = 30

# learn.microsoft.com serves the content commit of every article in its head. Pin that,
# not `ms.date` or `updated_at`: `ms.date` is author-declared and drifts from reality
# (the pricing article's is over a year behind its own publish), and `updated_at` moves
# on template rebuilds that change no prose. Only the commit id tracks the content.
LEARN_COMMIT_RX = re.compile(r'<meta name="git_commit_id" content="([0-9a-f]{40})"')

Kind = Literal["learn-page", "github-release", "unversioned", "unnamed"]


@dataclass(frozen=True)
class Source:
    """One upstream source a reference file was distilled from.

    Attributes:
        id: Stable short name, used in findings and as the sort key.
        kind: How the source publishes change, which selects the live-signal reader.
        distils_into: Repository-relative files whose content depends on this source.
        url: Where to read the live signal. Empty for `unversioned` and `unnamed`.
        signal: The pinned signal, as read when the source was last distilled. Empty
            when the kind publishes none.
        note: Why a source publishes no signal, or what is still unresolved about it.
    """

    id: str
    kind: Kind
    distils_into: tuple[str, ...]
    url: str = ""
    signal: str = ""
    note: str = ""


# The starting authorities `skills/ducat/references/data-sources.md` names, which that file asks a
# reader to "follow ... when Microsoft moves them", plus the two licensed sources
# `NOTICE.md` records. Signals pinned 2026-09-07.
SOURCES: tuple[Source, ...] = (
    Source(
        id="learn-system-tables-overview",
        kind="learn-page",
        url="https://learn.microsoft.com/en-us/azure/databricks/admin/usage/system-tables",
        signal="f684e9e50a753ff1341f9cd3adc12e0af4881c4a",
        distils_into=("skills/ducat/references/data-sources.md",),
    ),
    Source(
        id="learn-billing-system-table",
        kind="learn-page",
        url="https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing",
        signal="9d69f24dbb22d6ad38df4b95845a050fb1ee59bd",
        distils_into=("skills/ducat/references/data-sources.md",),
    ),
    Source(
        id="learn-pricing-system-table",
        kind="learn-page",
        url="https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/pricing",
        signal="0df2cf97dfb033d25e332ccfd462c803b0dd7619",
        distils_into=(
            "skills/ducat/references/data-sources.md",
            "skills/ducat/references/opportunity-catalog.md",
        ),
    ),
    Source(
        id="learn-jobs-cost",
        kind="learn-page",
        url="https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost",
        signal="0df2cf97dfb033d25e332ccfd462c803b0dd7619",
        distils_into=("skills/ducat/references/data-sources.md",),
    ),
    Source(
        id="learn-azure-cost-data",
        kind="learn-page",
        url="https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/review-subscription-billing",
        signal="981d4c7a114a9026e67c1ac75226043c035d2ab5",
        distils_into=("skills/ducat/references/data-sources.md",),
    ),
    Source(
        id="learn-retail-prices-api",
        kind="learn-page",
        url="https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices",
        signal="de6b152c15ece5c9525b925fce0240f31547c02a",
        distils_into=("skills/ducat/references/data-sources.md",),
    ),
    Source(
        id="focus-spec",
        kind="github-release",
        url="https://api.github.com/repos/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec/releases/latest",
        signal="v1.4",
        distils_into=("skills/ducat/references/data-sources.md",),
        note="NOTICE.md pins tag v1.4, commit f1eeb30a78f7c141ef1237d589355296a2761c1c.",
    ),
    Source(
        id="finops-framework",
        kind="unversioned",
        distils_into=("skills/ducat/references/opportunity-catalog.md",),
        note=(
            "Published as a live site with no version or changelog, per NOTICE.md. "
            "Nothing here can detect its movement; it needs a review date instead."
        ),
    ),
    Source(
        id="databricks-cost-component-matrix",
        kind="unnamed",
        distils_into=(
            "skills/ducat/references/data-sources.md",
            "skills/ducat/references/opportunity-catalog.md",
        ),
        note="Named as a distillation source in both files, but no URL is recorded anywhere.",
    ),
    Source(
        id="databricks-cost-tracking-guide",
        kind="unnamed",
        distils_into=(
            "skills/ducat/references/data-sources.md",
            "skills/ducat/references/opportunity-catalog.md",
        ),
        note="Named as a distillation source in both files, but no URL is recorded anywhere.",
    ),
)


@dataclass
class Report:
    """What one run found, split by what each outcome should cause.

    Attributes:
        moved: Sources whose live signal differs from the pinned one.
        unreachable: Sources that could not be read, for any reason.
        uncheckable: Sources that publish no signal, or have no URL to read.
        matched: Ids of sources whose pinned signal still holds.
    """

    moved: list[str] = field(default_factory=list)
    unreachable: list[str] = field(default_factory=list)
    uncheckable: list[str] = field(default_factory=list)
    matched: list[str] = field(default_factory=list)


def read_learn_signal(html: str) -> str:
    """Extracts the content commit id a learn.microsoft.com article publishes.

    Args:
        html: The article's full HTML.

    Returns:
        The 40-character commit id.

    Raises:
        LookupError: If the meta tag is absent, which means the page shape changed and
            this reader is blind rather than reassuring.
    """
    match = LEARN_COMMIT_RX.search(html)
    if match is None:
        raise LookupError("no git_commit_id meta tag — the page shape changed")
    return match.group(1)


def read_github_release_signal(body: str) -> str:
    """Extracts the tag name from a GitHub latest-release response.

    The `releases/latest` endpoint already excludes drafts and prereleases, so no
    ordering is assumed here — FOCUS publishes a `latest-draft` prerelease that any
    date-ordered reading of the tag list would eventually pick up by mistake.

    Args:
        body: The endpoint's JSON response.

    Returns:
        The tag name of the newest full release.

    Raises:
        LookupError: If the response carries no `tag_name`.
    """
    payload = json.loads(body)
    tag = payload.get("tag_name") if isinstance(payload, dict) else None
    if not isinstance(tag, str) or not tag:
        raise LookupError("no tag_name in the release response")
    return tag


def fetch(url: str) -> str:
    """Reads a URL as text.

    Args:
        url: The address to read.

    Returns:
        The response body, decoded as UTF-8 with undecodable bytes replaced.

    Raises:
        urllib.error.URLError: On any transport or HTTP failure.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return bytes(response.read()).decode("utf-8", errors="replace")


def live_signal(source: Source) -> str:
    """Reads the signal a source publishes right now.

    Args:
        source: The source to read. Must be of a kind that publishes a signal.

    Returns:
        The live signal, comparable to `source.signal`.

    Raises:
        ValueError: If the source's kind publishes nothing to read.
        LookupError: If the response carries no signal where one was expected.
        urllib.error.URLError: If the source could not be reached.
    """
    if source.kind == "learn-page":
        return read_learn_signal(fetch(source.url))
    if source.kind == "github-release":
        return read_github_release_signal(fetch(source.url))
    raise ValueError(f"{source.kind} publishes no signal")


def check(sources: tuple[Source, ...]) -> Report:
    """Compares every source's pinned signal against its live one.

    Args:
        sources: The sources to check, normally `SOURCES`.

    Returns:
        A `Report` splitting the outcome by what each case should cause.
    """
    report = Report()
    for source in sorted(sources, key=lambda s: s.id):
        if source.kind in ("unversioned", "unnamed"):
            report.uncheckable.append(f"{source.id}: {source.note}")
            continue
        try:
            live = live_signal(source)
        except (urllib.error.URLError, LookupError, ValueError, OSError) as error:
            report.unreachable.append(f"{source.id}: {source.url} — {error}")
            continue
        if live == source.signal:
            report.matched.append(source.id)
        else:
            report.moved.append(
                f"{source.id}: pinned {source.signal}, live {live} — re-read "
                f"{source.url} and re-pin, then re-distil "
                f"{' and '.join(source.distils_into)}"
            )
    return report


def main() -> int:
    """Checks every source and reports what moved.

    Returns:
        0 when every pinned source still matches, 1 when at least one has moved, and 2
        when none had moved but at least one could not be checked.
    """
    report = check(SOURCES)

    if report.uncheckable:
        print("check-upstream: publishing no signal, so not checked here\n", file=sys.stderr)
        for line in report.uncheckable:
            print(f"  {line}", file=sys.stderr)
        print("", file=sys.stderr)

    if report.moved:
        print("check-upstream: these sources have moved\n", file=sys.stderr)
        for line in report.moved:
            print(f"  {line}", file=sys.stderr)
        return 1

    if report.unreachable:
        print("check-upstream: these sources could not be read\n", file=sys.stderr)
        for line in report.unreachable:
            print(f"  {line}", file=sys.stderr)
        return 2

    print(f"check-upstream: {len(report.matched)} sources checked, none have moved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
