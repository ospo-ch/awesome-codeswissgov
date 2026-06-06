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

"""Registry ingestion: reconcile sibling registries against ``data/orgs``.

Epic 3 closes a live drift: the org list is meant to be synced from the federal
``github.com/swiss/index`` registry, but that sync is manual and has fallen
behind. This package ingests such registries and emits a **read-only**
reconciliation report — it never mutates ``data/orgs`` (a human reviews the
report and curates). The :class:`RegistrySource` protocol keeps it pluggable so
further sources slot in without touching the reconciliation core.
"""

from pathlib import Path

import httpx

from ..build import DEFAULT_ROOT
from ..loader import load_organizations
from .registry import ReconciliationReport, RegistrySource, reconcile
from .swiss_index import SwissIndexSource

# The registries ingested by default. swiss/index is the federal source
# (SPEC decision #1); the list is the single place to register more sources.
SOURCES: list[RegistrySource] = [SwissIndexSource()]


def run_ingest(
    root: Path = DEFAULT_ROOT,
    *,
    sources: list[RegistrySource] | None = None,
    client: httpx.Client | None = None,
) -> ReconciliationReport:
    """Fetch every registry source and reconcile it against ``data/orgs``.

    Args:
        root: Repository root containing ``data/orgs``.
        sources: Registries to ingest; defaults to :data:`SOURCES`.
        client: Injected ``httpx.Client`` (tests); a default one is created and
            closed here when omitted.

    Returns:
        A read-only :class:`ReconciliationReport`. Nothing is written to disk.
    """
    sources = SOURCES if sources is None else sources
    orgs = load_organizations(root / "data" / "orgs")

    owns_client = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        results = [source.fetch(client) for source in sources]
    finally:
        if owns_client:
            client.close()

    return reconcile(results, orgs)
