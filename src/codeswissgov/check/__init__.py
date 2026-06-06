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

"""Link-rot detection: check every curated org URL, never edit ``data/orgs``.

The curated org URLs in ``data/orgs`` go stale when an organization is renamed
or deleted on GitHub. This package checks each one and emits a **read-only**
report (parallel to ``ingest``) so a human can curate the fix. The check is
**tokenless**: it requests the public ``github.com/<login>`` page and reads only
the HTTP status and any redirect target — no API, no auth. Network I/O is
isolated in :func:`fetch_status`; classification and rendering are pure
(:mod:`codeswissgov.check.linkrot`), so tests run offline.
"""

from pathlib import Path

import httpx

from ..build import DEFAULT_ROOT
from ..loader import load_organizations
from .linkrot import ERROR, LinkResult, LinkRotReport, build_report, classify

__all__ = ["fetch_status", "run_check"]


def fetch_status(client: httpx.Client, url: str) -> tuple[int, str | None]:
    """Return ``(status_code, location)`` for ``url`` without following redirects.

    A 404 or a redirect is a meaningful link-rot signal, not an error, so the
    status is returned verbatim. ``location`` is the redirect target header, or
    ``None`` when absent.

    Raises:
        httpx.HTTPError: a transport-level failure (caught by :func:`run_check`).
    """
    response = client.get(
        url,
        follow_redirects=False,
        headers={"User-Agent": "awesome-codeswissgov-check"},
    )
    return response.status_code, response.headers.get("location")


def run_check(
    root: Path = DEFAULT_ROOT,
    *,
    client: httpx.Client | None = None,
) -> LinkRotReport:
    """Check every curated org URL and return a read-only :class:`LinkRotReport`.

    Args:
        root: Repository root containing ``data/orgs``.
        client: Injected ``httpx.Client`` (tests); a default one is created and
            closed here when omitted (same pattern as ``run_ingest``).

    A transport failure on one org becomes an ``ERROR`` result rather than
    aborting the run, so one flaky URL never hides the rest. Nothing is written.
    """
    orgs = load_organizations(root / "data" / "orgs")

    owns_client = client is None
    client = client or httpx.Client(timeout=30.0)
    results: list[LinkResult] = []
    try:
        for org in orgs:
            try:
                status, location = fetch_status(client, org.url)
            except httpx.HTTPError as exc:
                results.append(LinkResult(org, ERROR, str(exc)))
                continue
            results.append(classify(org, status, location))
    finally:
        if owns_client:
            client.close()

    return build_report(results)
