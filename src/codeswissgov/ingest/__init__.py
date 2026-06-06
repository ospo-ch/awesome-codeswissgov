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
