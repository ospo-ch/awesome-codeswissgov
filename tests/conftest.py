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

"""Shared fixtures for the test suite."""

from pathlib import Path

import pytest

from codeswissgov.loader import load_organizations


@pytest.fixture
def repo_root() -> Path:
    """Path to the repository root (tests/ lives directly under it)."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def organizations(repo_root):
    """All committed organizations, loaded from data/orgs."""
    return load_organizations(repo_root / "data" / "orgs")
