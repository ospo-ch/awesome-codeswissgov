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

"""Tests for the pure inventory reports and the run_report orchestration."""

import json
from datetime import date

from codeswissgov.build import run_report
from codeswissgov.models import Organization, Repository
from codeswissgov.render.inventory import OrgHarvest
from codeswissgov.render.reports import (
    authority_coverage,
    embag_report,
    license_report,
    render_reports,
    staleness_report,
)

TODAY = date(2026, 6, 6)  # cutoff for staleness is 2024-06-06 (730 days earlier)


def _org(url, authority="federal", name="Org"):
    return Organization(name=name, authority=authority, url=url)


def _repo(name, **kw):
    return Repository(name=name, url=f"https://github.com/o/{name}", **kw)


def _repos():
    return [
        _repo("tool", license="MIT", last_activity="2026-01-15"),  # licensed, fresh
        _repo("legacy", last_activity="2020-01-01", archived=True),  # unlic+stale+arch
        _repo("lib", license="Apache-2.0", last_activity=None),  # licensed, no activity
    ]


# --- license_report ---------------------------------------------------------


def test_license_report_counts_coverage_and_flags():
    report = license_report(_repos())
    assert report.total == 3
    assert report.licensed == 2
    assert report.unlicensed == 1
    assert round(report.coverage_pct) == 67


def test_license_report_empty_has_no_coverage():
    report = license_report([])
    assert report.total == 0 and report.coverage_pct is None


# --- staleness_report -------------------------------------------------------


def test_staleness_report_lenses():
    report = staleness_report(_repos(), TODAY)
    assert report.total == 3
    assert report.archived == 1  # legacy
    assert report.stale == 1  # legacy (2020 push < 2024 cutoff)
    assert report.no_activity == 1  # lib (no last_activity)


def test_staleness_boundary_is_exclusive():
    # A push exactly on the cutoff date is not yet stale (strictly older only).
    cutoff = "2024-06-06"
    report = staleness_report([_repo("edge", last_activity=cutoff)], TODAY)
    assert report.stale == 0


# --- authority_coverage -----------------------------------------------------


def test_authority_coverage_counts_federal_and_absent_cantons():
    orgs = [
        _org("https://github.com/admin-ch"),
        _org("https://github.com/zh-org", "canton:ZH"),
    ]
    report = authority_coverage(orgs)
    assert report.federal_orgs == 1
    assert report.cantons_present == ["ZH"]
    # 25 of 26 cantons publish nothing; Zürich is absent from that list.
    assert len(report.cantons_absent) == 25
    assert "Zürich" not in report.cantons_absent
    assert "Bern" in report.cantons_absent


# --- embag_report -----------------------------------------------------------


def test_embag_report_is_federal_only():
    orgs = [
        _org("https://github.com/fed-a"),
        _org("https://github.com/fed-b"),  # no repos
        _org("https://github.com/zh", "canton:ZH"),
    ]
    harvest = {
        "https://github.com/fed-a": OrgHarvest(
            repositories=[_repo("t", license="MIT"), _repo("u")]
        ),
        "https://github.com/zh": OrgHarvest(repositories=[_repo("z", license="GPL")]),
    }
    report = embag_report(orgs, harvest)
    assert report.federal_orgs == 2
    assert report.federal_orgs_with_repos == 1  # only fed-a
    # Cantonal repo (z) is excluded from the federal EMBAG slice.
    assert report.license.total == 2
    assert report.license.licensed == 1


# --- render_reports ---------------------------------------------------------


def test_render_reports_full_document():
    orgs = [_org("https://github.com/o"), _org("https://github.com/zh", "canton:ZH")]
    harvest = {"https://github.com/o": OrgHarvest(repositories=_repos())}
    text = render_reports(orgs, harvest, today=TODAY)

    assert text.endswith("\n")
    assert "## Authority coverage" in text
    assert "GitHub-only coverage" in text  # the mandated caveat
    assert "## License coverage" in text
    assert "3 repositories harvested" in text
    assert "2 licensed (67%)" in text
    assert "1 archived" in text
    assert "## EMBAG visibility (federal)" in text


def test_render_reports_handles_empty_harvest():
    orgs = [_org("https://github.com/o")]
    text = render_reports(orgs, {}, today=TODAY)

    assert "## Authority coverage" in text  # still works without harvest
    assert "No harvested repo data yet" in text
    assert "## License coverage" not in text


# --- run_report (end-to-end against a temp repo) ----------------------------


def _root(tmp_path, orgs, inventory):
    orgs_dir = tmp_path / "data" / "orgs"
    orgs_dir.mkdir(parents=True)
    for handle, authority in orgs:
        (orgs_dir / f"{handle}.yaml").write_text(
            f"name: {handle}\nauthority: {authority}\n"
            f"url: https://github.com/{handle}\n"
        )
    (tmp_path / "inventory.json").write_text(json.dumps(inventory), encoding="utf-8")
    return tmp_path


def test_run_report_reads_orgs_and_inventory(tmp_path):
    inventory = {
        "schema_version": "2.0",
        "organizations": [
            {
                "name": "fed-a",
                "authority": "federal",
                "url": "https://github.com/fed-a",
                "official": False,
                "provenance": None,
                "harvested_at": "2026-06-01T00:00:00Z",
                "repositories": [
                    {"name": "t", "url": "https://github.com/fed-a/t", "license": "MIT"}
                ],
            }
        ],
    }
    root = _root(tmp_path, [("fed-a", "federal")], inventory)
    text = run_report(root, today=TODAY)
    assert "1 repositories harvested" in text
    assert "1 licensed (100%)" in text
