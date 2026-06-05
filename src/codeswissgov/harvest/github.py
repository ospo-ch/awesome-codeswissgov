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

"""GitHub GraphQL client: expand an org into :class:`Repository` records.

GraphQL keeps the harvest to one paginated request per org (SPEC decision #4),
fetching license, language, topics, archived state, last activity, and the
presence of ``publiccode.yml`` / ``SECURITY.md`` in a single round trip. All
network I/O is confined here; the ``httpx.Client`` is injected so tests run
offline against recorded fixtures.
"""

from dataclasses import dataclass

import httpx

from ..models import Repository

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# One page of an org's source repositories with everything Epic 2 needs. Forks
# are excluded (ownership/curation noise). File presence uses HEAD:<path>, which
# resolves to null when the file is absent.
_QUERY = """
query($login: String!, $cursor: String) {
  organization(login: $login) {
    repositories(
      first: 100
      after: $cursor
      isFork: false
      ownerAffiliations: OWNER
      orderBy: {field: NAME, direction: ASC}
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        url
        isArchived
        pushedAt
        primaryLanguage { name }
        licenseInfo { spdxId }
        repositoryTopics(first: 100) { nodes { topic { name } } }
        publiccode: object(expression: "HEAD:publiccode.yml") { __typename }
        security: object(expression: "HEAD:SECURITY.md") { __typename }
      }
    }
  }
}
"""


class GitHubError(RuntimeError):
    """A GraphQL request failed, returned errors, or the org was not found."""


@dataclass
class GitHubClient:
    """Thin GraphQL client for harvesting one org's repositories.

    Attributes:
        token: Read-only fine-grained PAT (decision #4); sent as a bearer token.
        client: Injected ``httpx.Client`` so callers/tests control transport.
        url: GraphQL endpoint (overridable for testing).
    """

    token: str
    client: httpx.Client
    url: str = GITHUB_GRAPHQL_URL

    def fetch_org_repositories(self, login: str) -> list[Repository]:
        """Return every source repository for ``login`` (paginated, ordered).

        Raises:
            GitHubError: transport failure, GraphQL errors, or unknown org.
        """
        repositories: list[Repository] = []
        cursor: str | None = None
        while True:
            organization = self._post(login, cursor)["data"]["organization"]
            if organization is None:
                raise GitHubError(f"organization not found or inaccessible: {login}")
            connection = organization["repositories"]
            repositories.extend(_repository(node) for node in connection["nodes"])
            page = connection["pageInfo"]
            if not page["hasNextPage"]:
                return repositories
            cursor = page["endCursor"]

    def _post(self, login: str, cursor: str | None) -> dict:
        try:
            response = self.client.post(
                self.url,
                json={
                    "query": _QUERY,
                    "variables": {"login": login, "cursor": cursor},
                },
                headers={
                    "Authorization": f"bearer {self.token}",
                    "User-Agent": "awesome-codeswissgov-harvester",
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GitHubError(f"GitHub request failed for {login}: {exc}") from exc
        payload = response.json()
        if payload.get("errors"):
            raise GitHubError(f"GraphQL errors for {login}: {payload['errors']}")
        return payload


def _repository(node: dict) -> Repository:
    """Build a :class:`Repository` from one GraphQL repository node."""
    license_info = node.get("licenseInfo") or {}
    language = node.get("primaryLanguage") or {}
    topics = [edge["topic"]["name"] for edge in node["repositoryTopics"]["nodes"]]
    pushed_at = node.get("pushedAt")
    return Repository(
        name=node["name"],
        url=node["url"],
        # null = no license = compliance flag; spdxId verbatim otherwise.
        license=license_info.get("spdxId"),
        language=language.get("name"),
        topics=topics,
        archived=node["isArchived"],
        # Date only: pushedAt is a timestamp, but per-second churn would make
        # every harvest diff noisy. ISO-8601 date matches the model's semantics.
        last_activity=pushed_at[:10] if pushed_at else None,
        has_publiccode_yml=node.get("publiccode") is not None,
        has_security_md=node.get("security") is not None,
    )
