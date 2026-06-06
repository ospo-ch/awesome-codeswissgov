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

"""Helpers for GitHub organization URLs, shared by harvest and ingest."""


def org_login(url: str) -> str:
    """Extract the GitHub org login from an organization URL.

    ``https://github.com/admin-ch`` and ``.../cdc-si/`` both -> the last
    path segment, tolerating a trailing slash. Case is preserved (the GitHub
    API and display both want the real-case login); use :func:`login_key` when
    comparing logins, since GitHub treats them case-insensitively.
    """
    return url.rstrip("/").rsplit("/", 1)[-1]


def login_key(url: str) -> str:
    """Case-insensitive match key for an org URL's login.

    GitHub logins are case-insensitive, so reconciling two registries (e.g.
    ``KOST-CECO`` vs ``kost-ceco``) must compare on a folded key, not the raw
    login.
    """
    return org_login(url).casefold()
