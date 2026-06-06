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

"""Enrichment harvester: expand curated orgs into repo-level inventory data.

Network I/O is isolated in :mod:`codeswissgov.harvest.github`; this module
orchestrates the harvest and merges the results into ``inventory.json`` — the
single committed carrier of repo-level data (SPEC decision #7).

The harvest is incremental and cache-backed: each org is fetched independently,
and ``inventory.json`` itself is the cache. When an org fetch fails, its prior
repositories are carried forward unchanged rather than dropped, so a transient
error never wipes good data and partial progress always persists.
"""

import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import httpx

from ..build import DEFAULT_ROOT
from ..loader import load_organizations
from ..orgurl import org_login
from ..render.inventory import OrgHarvest, load_harvest, render_inventory
from .github import GitHubClient, GitHubError

__all__ = ["HarvestSummary", "org_login", "run_harvest"]


@dataclass(frozen=True)
class HarvestSummary:
    """Outcome of a harvest run, for CLI reporting."""

    orgs_total: int
    orgs_refreshed: int
    repos_total: int
    orgs_failed: list[str] = field(default_factory=list)


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_harvest(
    token: str,
    root: Path = DEFAULT_ROOT,
    *,
    github: GitHubClient | None = None,
    now: str | None = None,
) -> HarvestSummary:
    """Harvest every org's repositories and rewrite ``inventory.json``.

    Args:
        token: Read-only PAT (used only to build the default client).
        root: Repository root containing ``data/orgs`` and ``inventory.json``.
        github: Injected client (tests); a real one is built from ``token`` if
            omitted.
        now: Timestamp to stamp on refreshed orgs; defaults to UTC now.

    Returns:
        A :class:`HarvestSummary` of what was refreshed, cached, or failed.
    """
    orgs = load_organizations(root / "data" / "orgs")
    inventory_path = root / "inventory.json"
    prior = load_harvest(
        inventory_path.read_text(encoding="utf-8") if inventory_path.exists() else ""
    )
    timestamp = now or _utc_now()

    owns_client = github is None
    http_client = httpx.Client(timeout=30.0) if owns_client else None
    github = github or GitHubClient(token=token, client=http_client)

    harvest: dict[str, OrgHarvest] = {}
    failed: list[str] = []
    try:
        for org in orgs:
            login = org_login(org.url)
            try:
                repositories = github.fetch_org_repositories(login)
            except GitHubError as exc:
                failed.append(login)
                if org.url in prior:
                    harvest[org.url] = prior[org.url]  # keep cached data
                print(
                    f"harvest: {login} failed, keeping cached data: {exc}",
                    file=sys.stderr,
                )
                continue
            harvest[org.url] = OrgHarvest(
                harvested_at=timestamp, repositories=repositories
            )
    finally:
        if owns_client:
            http_client.close()

    inventory_path.write_text(render_inventory(orgs, harvest), encoding="utf-8")
    return HarvestSummary(
        orgs_total=len(orgs),
        orgs_refreshed=len(orgs) - len(failed),
        repos_total=sum(len(h.repositories) for h in harvest.values()),
        orgs_failed=failed,
    )
