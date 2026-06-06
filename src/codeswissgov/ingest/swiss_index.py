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

"""The ``swiss/index`` registry source: the federal index of GitHub orgs.

``swiss/index`` is a plain markdown README — sectioned ``## headings`` with one
``* <url>`` bullet per organization. Network I/O (:func:`fetch_readme`) is kept
separate from the pure :func:`parse_index`, so parsing is tested offline against
a recorded fixture. Only GitHub orgs are in scope (SPEC non-goal): GitLab and
other forges are recorded as ``skipped`` so the GitHub-only under-count is
stated, not hidden.
"""

import re
from dataclasses import dataclass

import httpx

from .registry import (
    CANTONAL_HINT,
    FEDERAL_HINT,
    Candidate,
    IngestError,
    SourceResult,
)

SOURCE_NAME = "swiss/index"
# HEAD resolves the default branch, so we are not pinned to "main" vs "master".
SWISS_INDEX_URL = "https://raw.githubusercontent.com/swiss/index/HEAD/README.md"

_GITHUB_PREFIX = "https://github.com/"
_SECTION_RE = re.compile(r"^#+\s+(.*\S)\s*$")
# First http(s) URL on a bullet line; stop at whitespace or markdown delimiters.
_URL_RE = re.compile(r"https?://[^\s)>\]]+")


def fetch_readme(client: httpx.Client, url: str = SWISS_INDEX_URL) -> str:
    """Fetch the raw ``swiss/index`` README. No token needed (public raw file).

    Raises:
        IngestError: the request failed or returned a non-2xx status.
    """
    try:
        response = client.get(
            url, headers={"User-Agent": "awesome-codeswissgov-ingest"}
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise IngestError(f"failed to fetch {url}: {exc}") from exc
    return response.text


def _authority_hint(section: str | None) -> str | None:
    """Map a section heading to a coarse authority hint (a guess, not truth)."""
    if section is None:
        return None
    return CANTONAL_HINT if "cantonal" in section.casefold() else FEDERAL_HINT


def parse_index(markdown: str, source: str = SOURCE_NAME) -> SourceResult:
    """Parse a ``swiss/index``-style README into a :class:`SourceResult`.

    Walks the document tracking the current ``## section``; each bulleted URL
    becomes a GitHub :class:`Candidate` (with the section as a provenance hint)
    or, if it points at another forge, is recorded in ``skipped``.
    """
    candidates: list[Candidate] = []
    skipped: list[str] = []
    section: str | None = None
    for line in markdown.splitlines():
        heading = _SECTION_RE.match(line)
        if heading:
            section = heading.group(1)
            continue
        match = _URL_RE.search(line)
        if not match:
            continue
        url = match.group(0)
        if url.startswith(_GITHUB_PREFIX):
            candidates.append(
                Candidate(
                    url=url,
                    source=source,
                    section=section,
                    authority_hint=_authority_hint(section),
                )
            )
        else:
            skipped.append(url)
    return SourceResult(name=source, candidates=candidates, skipped=skipped)


@dataclass
class SwissIndexSource:
    """The federal ``swiss/index`` registry as a :class:`RegistrySource`."""

    name: str = SOURCE_NAME
    url: str = SWISS_INDEX_URL

    def fetch(self, client: httpx.Client) -> SourceResult:
        """Fetch and parse ``swiss/index`` into a :class:`SourceResult`."""
        return parse_index(fetch_readme(client, self.url), source=self.name)
