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

"""Unit tests for registry candidates and pure reconciliation."""

import pytest

from codeswissgov.ingest.registry import (
    Candidate,
    ReconciliationReport,
    SourceResult,
    reconcile,
    render_report,
)
from codeswissgov.models import Organization


def _org(url: str, authority: str = "federal") -> Organization:
    return Organization(name="x", authority=authority, url=url)


def _cand(url: str, **kw) -> Candidate:
    return Candidate(url=url, source=kw.pop("source", "swiss/index"), **kw)


def test_candidate_rejects_non_github_url():
    with pytest.raises(ValueError, match="github.com"):
        _cand("https://gitlab.com/foo")


def test_reconcile_classifies_missing_matched_extra():
    orgs = [
        _org("https://github.com/admin-ch"),
        _org("https://github.com/canton-zh", "canton:ZH"),
    ]
    result = SourceResult(
        name="swiss/index",
        candidates=[
            _cand("https://github.com/admin-ch"),  # matched
            _cand("https://github.com/govcert-ch"),  # missing
        ],
    )
    report = reconcile([result], orgs)

    assert [c.url for c in report.missing] == ["https://github.com/govcert-ch"]
    assert [c.url for c in report.matched] == ["https://github.com/admin-ch"]
    # canton-zh is curated but absent from the federal registry -> extra.
    assert [o.url for o in report.extra] == ["https://github.com/canton-zh"]
    assert report.sources == ["swiss/index"]


def test_reconcile_matches_case_insensitively_and_trailing_slash():
    orgs = [_org("https://github.com/KOST-CECO")]
    result = SourceResult(
        name="swiss/index",
        candidates=[
            _cand("https://github.com/kost-ceco/"),  # same org, folded + slash
            _cand("https://github.com/cdc-si/"),  # missing, trailing slash
        ],
    )
    report = reconcile([result], orgs)

    assert [c.url for c in report.matched] == ["https://github.com/kost-ceco/"]
    assert [c.url for c in report.missing] == ["https://github.com/cdc-si/"]
    assert report.extra == []


def test_reconcile_dedupes_candidates_by_login():
    result = SourceResult(
        name="swiss/index",
        candidates=[
            _cand("https://github.com/govcert-ch"),
            _cand("https://github.com/govcert-ch/"),  # duplicate by login
        ],
    )
    report = reconcile([result], [])
    assert [c.url for c in report.missing] == ["https://github.com/govcert-ch"]


def test_reconcile_carries_skipped_non_github():
    result = SourceResult(
        name="swiss/index",
        candidates=[],
        skipped=["https://gitlab.com/swiss-armed-forces"],
    )
    report = reconcile([result], [])
    assert report.skipped == ["https://gitlab.com/swiss-armed-forces"]


def test_render_report_lists_missing_with_hint_and_counts():
    report = ReconciliationReport(
        missing=[_cand("https://github.com/govcert-ch", authority_hint="federal")],
        matched=[],
        extra=[],
        sources=["swiss/index"],
        skipped=["https://gitlab.com/x"],
    )
    text = render_report(report)

    assert text.endswith("\n")
    assert "Sources ingested: swiss/index" in text
    assert "1 in a registry but **missing**" in text
    assert "https://github.com/govcert-ch — hint: federal (via swiss/index)" in text
    assert "1 non-GitHub entries skipped" in text
    assert "https://gitlab.com/x" in text


def test_render_report_handles_no_missing():
    report = ReconciliationReport(
        missing=[], matched=[], extra=[], sources=["swiss/index"], skipped=[]
    )
    text = render_report(report)
    assert "- (none)" in text
