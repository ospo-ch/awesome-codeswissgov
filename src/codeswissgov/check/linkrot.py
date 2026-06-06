# Copyright 2024 ospo.ch authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Pure link-rot classification and report rendering.

An org URL in ``data/orgs`` can rot three ways: the org is **renamed** (GitHub
301-redirects the old login to a new one), **deleted** (404), or temporarily
uncheckable (network error). :func:`classify` turns one HTTP outcome into a
:class:`LinkResult`; :func:`render_report` renders the aggregate as read-only
guidance. Nothing here touches the network or the filesystem, so it is fully
unit-testable offline (the HTTP fetch lives in :mod:`codeswissgov.check`).
"""

from dataclasses import dataclass

from ..models import Organization
from ..orgurl import login_key

# Outcome states for a single org URL.
ALIVE = "alive"
RENAMED = "renamed"
GONE = "gone"
ERROR = "error"

# GitHub answers an org rename with a permanent redirect; cover the temporary
# ones too so a transient redirect is not misread as a 404.
_REDIRECTS = frozenset({301, 302, 307, 308})


@dataclass(frozen=True)
class LinkResult:
    """The outcome of checking one organization's URL.

    Attributes:
        org: The curated organization that was checked.
        state: One of :data:`ALIVE`, :data:`RENAMED`, :data:`GONE`, :data:`ERROR`.
        detail: The new URL for a rename, or a message for an error; ``None``
            when the state needs no elaboration.
    """

    org: Organization
    state: str
    detail: str | None = None


@dataclass(frozen=True)
class LinkRotReport:
    """The aggregate of one ``check`` run, grouped by outcome."""

    alive: list[LinkResult]
    renamed: list[LinkResult]
    gone: list[LinkResult]
    errors: list[LinkResult]

    @property
    def checked(self) -> int:
        """Total number of org URLs checked."""
        return len(self.alive) + len(self.renamed) + len(self.gone) + len(self.errors)


def classify(org: Organization, status: int, location: str | None) -> LinkResult:
    """Classify one HTTP outcome for ``org.url`` into a :class:`LinkResult`.

    Args:
        org: The organization whose URL was requested.
        status: The HTTP status code (redirects are *not* followed).
        location: The ``Location`` header on a redirect, else ``None``.

    A redirect to the *same* login (GitHub normalizing case or a trailing slash)
    is :data:`ALIVE`, not a rename — compared via :func:`login_key`.
    """
    if status == 200:
        return LinkResult(org, ALIVE)
    if status in _REDIRECTS:
        if location is None:
            return LinkResult(org, ERROR, f"redirect ({status}) without Location")
        if login_key(location) == login_key(org.url):
            return LinkResult(org, ALIVE)  # slash/case normalization, same org
        return LinkResult(org, RENAMED, location)
    if status == 404:
        return LinkResult(org, GONE)
    return LinkResult(org, ERROR, f"unexpected status {status}")


def build_report(results: list[LinkResult]) -> LinkRotReport:
    """Group flat :class:`LinkResult` records by their state."""
    buckets: dict[str, list[LinkResult]] = {
        ALIVE: [],
        RENAMED: [],
        GONE: [],
        ERROR: [],
    }
    for result in results:
        buckets[result.state].append(result)
    return LinkRotReport(
        alive=buckets[ALIVE],
        renamed=buckets[RENAMED],
        gone=buckets[GONE],
        errors=buckets[ERROR],
    )


def render_report(report: LinkRotReport) -> str:
    """Render a link-rot report as read-only markdown guidance.

    The renamed/gone/error sections name the org and the action a curator should
    take in ``data/orgs`` — the tool never edits it.
    """
    lines = [
        "# Link-rot report",
        "",
        f"Checked {report.checked} org URL(s) against github.com "
        "(read-only; data/orgs is never edited).",
        "",
        f"- {len(report.alive)} alive",
        f"- {len(report.renamed)} renamed (org moved — update the url in data/orgs)",
        f"- {len(report.gone)} gone (404 — remove or replace in data/orgs)",
        f"- {len(report.errors)} could not be checked",
        "",
        "## Renamed (update the url in data/orgs)",
        "",
    ]
    lines += _section(
        report.renamed, lambda r: f"{r.org.name}: {r.org.url} → {r.detail}"
    )
    lines += ["", "## Gone — 404 (review and curate)", ""]
    lines += _section(report.gone, lambda r: f"{r.org.name}: {r.org.url}")
    if report.errors:
        lines += ["", "## Could not be checked", ""]
        lines += _section(
            report.errors, lambda r: f"{r.org.name}: {r.org.url} ({r.detail})"
        )
    return "\n".join(lines) + "\n"


def _section(results, fmt) -> list[str]:
    """Render one report section's bullet lines, or a ``(none)`` placeholder."""
    if not results:
        return ["- (none)"]
    return [f"- {fmt(r)}" for r in results]
