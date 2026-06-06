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

"""Pure inventory reports: license, staleness, authority coverage, EMBAG.

These turn the curated ``data/orgs`` and the harvested ``inventory.json`` into
the questions an OSPO actually asks — what share of repos carry a license, how
many are stale or archived, which authorities publish nothing, and how the
*federal* picture looks under EMBAG. Everything here is a pure function of its
inputs (orgs, harvest mapping, a reference ``today``), so it is deterministic
and offline-testable; file I/O lives in :func:`codeswissgov.build.run_report`.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from ..cantons import CANTONS, canton_display
from ..models import Organization, Repository
from .inventory import OrgHarvest

# A repo with no push in this window counts as stale (~2 years). Archived and
# never-active repos are reported separately, so this measures dormancy only.
STALE_AFTER_DAYS = 730


@dataclass(frozen=True)
class LicenseReport:
    """License coverage across a set of repositories."""

    total: int
    licensed: int
    unlicensed: int  # compliance flags: a repo with no declared license

    @property
    def coverage_pct(self) -> float | None:
        """Percent of repos carrying a license, or ``None`` when there are none."""
        return None if self.total == 0 else 100 * self.licensed / self.total


@dataclass(frozen=True)
class StalenessReport:
    """Activity lenses over a set of repositories (the lenses may overlap)."""

    total: int
    archived: int
    stale: int  # pushed, but not within STALE_AFTER_DAYS
    no_activity: int  # no recorded last_activity at all


@dataclass(frozen=True)
class CoverageReport:
    """Authority coverage — who has a GitHub org and who publishes nothing."""

    federal_orgs: int
    cantons_present: list[str]  # canton codes with >= 1 org
    cantons_absent: list[str]  # display names of cantons with no GitHub org


@dataclass(frozen=True)
class EmbagReport:
    """Federal publishing visibility (EMBAG: public money -> public code)."""

    federal_orgs: int
    federal_orgs_with_repos: int
    license: LicenseReport


def _all_repos(harvest: dict[str, OrgHarvest]) -> list[Repository]:
    return [repo for entry in harvest.values() for repo in entry.repositories]


def license_report(repos: list[Repository]) -> LicenseReport:
    """Count license coverage and compliance flags across ``repos``."""
    licensed = sum(1 for r in repos if r.license is not None)
    return LicenseReport(
        total=len(repos), licensed=licensed, unlicensed=len(repos) - licensed
    )


def staleness_report(repos: list[Repository], today: date) -> StalenessReport:
    """Count archived, stale, and never-active repos relative to ``today``."""
    cutoff = today - timedelta(days=STALE_AFTER_DAYS)
    archived = stale = no_activity = 0
    for repo in repos:
        if repo.archived:
            archived += 1
        if repo.last_activity is None:
            no_activity += 1
        elif date.fromisoformat(repo.last_activity) < cutoff:
            stale += 1
    return StalenessReport(
        total=len(repos), archived=archived, stale=stale, no_activity=no_activity
    )


def authority_coverage(orgs: list[Organization]) -> CoverageReport:
    """Report federal org count and which cantons have / lack a GitHub org."""
    present = {o.canton_code for o in orgs if not o.is_federal}
    absent = [canton_display(code) for code in CANTONS if code not in present]
    return CoverageReport(
        federal_orgs=sum(1 for o in orgs if o.is_federal),
        cantons_present=sorted(c for c in present if c is not None),
        cantons_absent=sorted(absent),
    )


def embag_report(
    orgs: list[Organization], harvest: dict[str, OrgHarvest]
) -> EmbagReport:
    """Federal-only license/visibility slice (EMBAG applies to federal bodies)."""
    federal_urls = [o.url for o in orgs if o.is_federal]
    federal_repos: list[Repository] = []
    orgs_with_repos = 0
    for url in federal_urls:
        repos = harvest[url].repositories if url in harvest else []
        if repos:
            orgs_with_repos += 1
        federal_repos.extend(repos)
    return EmbagReport(
        federal_orgs=len(federal_urls),
        federal_orgs_with_repos=orgs_with_repos,
        license=license_report(federal_repos),
    )


def _pct(report: LicenseReport) -> str:
    pct = report.coverage_pct
    return "n/a" if pct is None else f"{pct:.0f}%"


def render_reports(
    orgs: list[Organization],
    harvest: dict[str, OrgHarvest],
    *,
    today: date,
) -> str:
    """Render all four reports as a single read-only markdown document."""
    repos = _all_repos(harvest)
    coverage = authority_coverage(orgs)

    lines = [
        "# Inventory report",
        "",
        "Read-only. Repo-level figures come from the harvested inventory.json; "
        "authority coverage comes from data/orgs.",
        "",
        "## Authority coverage",
        "",
        f"- {coverage.federal_orgs} federal organization(s) tracked.",
        f"- {len(coverage.cantons_present)}/{len(CANTONS)} cantons have a known "
        "GitHub org.",
        f"- {len(coverage.cantons_absent)} canton(s) publish nothing on GitHub "
        "(that we know of):",
    ]
    lines.append(
        "  " + (", ".join(coverage.cantons_absent) if coverage.cantons_absent else "—")
    )
    lines += [
        "",
        "> GitHub-only coverage: absence means *no GitHub org found*, **not** "
        '"publishes no open source" — authorities may publish off GitHub '
        "(out of scope).",
        "",
    ]

    if not repos:
        lines += [
            "## Repositories",
            "",
            "No harvested repo data yet — run `python -m codeswissgov harvest "
            "--token $GITHUB_TOKEN` to populate inventory.json.",
            "",
        ]
        return "\n".join(lines) + "\n"

    licenses = license_report(repos)
    staleness = staleness_report(repos, today)
    embag = embag_report(orgs, harvest)
    lines += [
        "## License coverage",
        "",
        f"- {licenses.total} repositories harvested.",
        f"- {licenses.licensed} licensed ({_pct(licenses)}).",
        f"- {licenses.unlicensed} without a license (compliance flags).",
        "",
        "## Staleness",
        "",
        f"- {staleness.archived} archived.",
        f"- {staleness.stale} stale (no push in {STALE_AFTER_DAYS // 365} years).",
        f"- {staleness.no_activity} with no recorded activity.",
        "",
        "## EMBAG visibility (federal)",
        "",
        f"- {embag.federal_orgs_with_repos}/{embag.federal_orgs} federal orgs "
        "have harvested repositories.",
        f"- {embag.license.total} federal repositories, "
        f"{embag.license.licensed} licensed ({_pct(embag.license)}), "
        f"{embag.license.unlicensed} without a license.",
        "",
    ]
    return "\n".join(lines) + "\n"
