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

"""Typed models for the inventory source of truth.

``Organization`` is the curated, ``publiccode.yml``-compatible record stored in
``data/orgs/*.yaml`` (SPEC decision #9). Harvested repo-level fields are *not*
modelled here — they arrive in ``inventory.json`` in Epic 2 (decision #7).
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .cantons import CANTON_CODES

FEDERAL = "federal"
CANTON_PREFIX = "canton:"

# URLs are rendered verbatim into README.md, so we keep them as exact strings
# (validated below) rather than coupling byte-stability to URL canonicalization.
_GITHUB_PREFIX = "https://github.com/"


class Organization(BaseModel):
    """A curated Swiss public-sector GitHub organization (or a known gap).

    Attributes:
        name: Display name. For federal entries this is the service name; for
            cantonal entries it is the unit/org name (the README link label).
        authority: ``"federal"`` or ``"canton:<CODE>"`` (e.g. ``"canton:ZH"``).
        url: GitHub organization URL. Required: only real organizations are
            stored. Cantons with no known org are *not* records here — the
            renderer derives ``— none known yet`` from the canton list.
        official: Verified-official flag. Only ``True`` with recorded
            ``provenance`` (SPEC decision #5); otherwise the entry is a
            candidate.
        provenance: Evidence backing ``official`` (registry listing, verified
            domain match, explicit confirmation). ``None`` = unverified.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    authority: str
    url: str
    official: bool = False
    provenance: str | None = None

    @field_validator("name")
    @classmethod
    def _name_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty")
        return value

    @field_validator("authority")
    @classmethod
    def _authority_well_formed(cls, value: str) -> str:
        if value == FEDERAL:
            return value
        if value.startswith(CANTON_PREFIX):
            code = value[len(CANTON_PREFIX) :]
            if code in CANTON_CODES:
                return value
            raise ValueError(f"unknown canton code in authority: {value!r}")
        raise ValueError(
            f"authority must be 'federal' or 'canton:<CODE>', got {value!r}"
        )

    @field_validator("url")
    @classmethod
    def _url_is_github(cls, value: str) -> str:
        if not value.startswith(_GITHUB_PREFIX):
            raise ValueError(f"url must be a {_GITHUB_PREFIX} URL, got {value!r}")
        return value

    @model_validator(mode="after")
    def _check_cross_field_rules(self) -> "Organization":
        if self.official and not self.provenance:
            raise ValueError(
                "official=true requires non-empty provenance (SPEC decision #5)"
            )
        return self

    @property
    def is_federal(self) -> bool:
        """True for a federal-level organization."""
        return self.authority == FEDERAL

    @property
    def canton_code(self) -> str | None:
        """The canton code (e.g. ``ZH``) for a cantonal org, else ``None``."""
        if self.authority.startswith(CANTON_PREFIX):
            return self.authority[len(CANTON_PREFIX) :]
        return None


class Repository(BaseModel):
    """A harvested source repository belonging to an organization.

    Repo-level records are *not* curated in ``data/orgs`` (SPEC decision #7);
    they are produced by ``harvest`` from real GitHub API responses and live
    only in the generated ``inventory.json``, nested under their organization.
    ``authority`` is therefore omitted here (derivable from the parent org).

    Attributes:
        name: Repository name (within the org).
        url: GitHub repository URL.
        license: SPDX identifier, or ``None`` when no license is declared.
            ``None`` is a compliance flag, not missing data.
        language: Primary language reported by GitHub, or ``None``.
        topics: Repository topics (may be empty).
        archived: Whether GitHub marks the repo as archived.
        last_activity: ISO-8601 date of the last push, or ``None``.
        has_publiccode_yml: Whether a ``publiccode.yml`` exists at the repo root.
        has_security_md: Whether a ``SECURITY.md`` exists at the repo root.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    url: str
    license: str | None = None
    language: str | None = None
    topics: list[str] = Field(default_factory=list)
    archived: bool = False
    last_activity: str | None = None
    has_publiccode_yml: bool = False
    has_security_md: bool = False

    @field_validator("name")
    @classmethod
    def _name_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty")
        return value

    @field_validator("url")
    @classmethod
    def _url_is_github(cls, value: str) -> str:
        if not value.startswith(_GITHUB_PREFIX):
            raise ValueError(f"url must be a {_GITHUB_PREFIX} URL, got {value!r}")
        return value

    @property
    def is_compliance_flag(self) -> bool:
        """True when the repo lacks a declared license."""
        return self.license is None
