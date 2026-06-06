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

"""Registry candidates, the source protocol, and pure reconciliation.

A :class:`RegistrySource` fetches :class:`Candidate` org URLs from one external
registry. :func:`reconcile` compares those candidates against the curated
``data/orgs`` and classifies each as missing / matched / extra; nothing here
touches the filesystem or the network, so it is fully unit-testable offline.
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import httpx
from pydantic import BaseModel, ConfigDict, field_validator

from ..models import Organization
from ..orgurl import login_key

# Shared with the org/repo models: only GitHub is in scope (SPEC non-goal).
_GITHUB_PREFIX = "https://github.com/"

FEDERAL_HINT = "federal"
CANTONAL_HINT = "cantonal"


class IngestError(RuntimeError):
    """A registry could not be fetched or parsed."""


class Candidate(BaseModel):
    """A GitHub org URL surfaced by a registry, with its provenance.

    Attributes:
        url: GitHub organization URL (only GitHub is in scope).
        source: Registry that listed it, e.g. ``"swiss/index"``.
        section: The registry's own section/heading the entry sat under, kept
            as a provenance hint (``None`` if the registry is flat).
        authority_hint: Coarse authority guess derived from ``section``
            (``"federal"`` / ``"cantonal"``), or ``None``. A hint only — the
            curator sets the real ``authority`` when adding the org.
    """

    model_config = ConfigDict(extra="forbid")

    url: str
    source: str
    section: str | None = None
    authority_hint: str | None = None

    @field_validator("url")
    @classmethod
    def _url_is_github(cls, value: str) -> str:
        if not value.startswith(_GITHUB_PREFIX):
            raise ValueError(f"url must be a {_GITHUB_PREFIX} URL, got {value!r}")
        return value


@dataclass(frozen=True)
class SourceResult:
    """One registry's fetch outcome.

    ``skipped`` carries entries dropped because they are out of scope (non-GitHub
    forges such as GitLab), so the report can state the GitHub-only under-count
    explicitly rather than hiding it (SPEC coverage-reporting requirement).
    """

    name: str
    candidates: list[Candidate] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


@runtime_checkable
class RegistrySource(Protocol):
    """A pluggable external registry that yields GitHub org candidates."""

    name: str

    def fetch(self, client: httpx.Client) -> SourceResult:
        """Fetch and parse this registry into a :class:`SourceResult`."""
        ...


@dataclass(frozen=True)
class ReconciliationReport:
    """The read-only outcome of reconciling registries against ``data/orgs``.

    Attributes:
        missing: Candidates whose login is absent from ``data/orgs`` — the
            actionable coverage gap a curator should review.
        matched: Candidates already present in ``data/orgs``.
        extra: Curated orgs not listed by any ingested registry (mostly our
            cantonal breadth, since the federal registry omits it) — expected,
            not an error.
        sources: Names of the registries that were ingested.
        skipped: Out-of-scope (non-GitHub) URLs dropped across all sources.
    """

    missing: list[Candidate]
    matched: list[Candidate]
    extra: list[Organization]
    sources: list[str]
    skipped: list[str]


def reconcile(
    results: list[SourceResult], orgs: list[Organization]
) -> ReconciliationReport:
    """Classify registry candidates against the curated ``orgs``.

    Matching is case-insensitive on the GitHub login (:func:`login_key`), since
    GitHub treats logins case-insensitively. Candidates are de-duplicated by
    login (a registry may list the same org with/without a trailing slash, or
    two registries may overlap), keeping the first occurrence.
    """
    known = {login_key(o.url) for o in orgs}

    missing: list[Candidate] = []
    matched: list[Candidate] = []
    seen: set[str] = set()
    candidate_keys: set[str] = set()
    for result in results:
        for candidate in result.candidates:
            key = login_key(candidate.url)
            candidate_keys.add(key)
            if key in seen:
                continue
            seen.add(key)
            (matched if key in known else missing).append(candidate)

    extra = [o for o in orgs if login_key(o.url) not in candidate_keys]
    skipped = [url for result in results for url in result.skipped]
    return ReconciliationReport(
        missing=missing,
        matched=matched,
        extra=extra,
        sources=[r.name for r in results],
        skipped=skipped,
    )


def render_report(report: ReconciliationReport) -> str:
    """Render a reconciliation report as human-readable markdown.

    Output is read-only guidance: the ``missing`` section lists orgs a curator
    should consider adding to ``data/orgs`` (with the registry's authority hint
    and provenance), never an instruction to auto-add.
    """
    sources = ", ".join(report.sources) or "(none)"
    lines = [
        "# Registry reconciliation report",
        "",
        f"Sources ingested: {sources}",
        "",
        f"- {len(report.missing)} in a registry but **missing** from data/orgs",
        f"- {len(report.matched)} already covered",
        f"- {len(report.extra)} in data/orgs but not in any registry "
        "(mostly cantonal breadth; expected)",
        f"- {len(report.skipped)} non-GitHub entries skipped (GitHub-only)",
        "",
        "## Missing from data/orgs (review and curate — never auto-added)",
        "",
    ]
    if report.missing:
        for candidate in report.missing:
            hint = candidate.authority_hint or "?"
            lines.append(f"- {candidate.url} — hint: {hint} (via {candidate.source})")
    else:
        lines.append("- (none)")

    if report.skipped:
        lines += ["", "## Skipped (non-GitHub, out of scope)", ""]
        lines += [f"- {url}" for url in report.skipped]

    return "\n".join(lines) + "\n"
