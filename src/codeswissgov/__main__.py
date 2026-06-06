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

"""CLI entry point: ``python -m codeswissgov <build|validate|harvest|ingest>``.

``build``    regenerate README.md + inventory.json from data/orgs.
``validate`` schema-check data/orgs and assert the generated views are current.
``harvest``  enrich inventory.json with repo-level data from the GitHub API.
``ingest``   reconcile sibling registries (swiss/index) against data/orgs.
"""

import os
import sys

from .build import build, validate
from .harvest import run_harvest
from .ingest import run_ingest
from .ingest.registry import IngestError, render_report

USAGE = "usage: python -m codeswissgov <build|validate|harvest [--token TOKEN]|ingest>"


def _cmd_build(args: list[str]) -> int:
    result = build()
    print(f"built {result.readme_path.name} and {result.inventory_path.name}")
    return 0


def _cmd_validate(args: list[str]) -> int:
    try:
        stale = validate()
    except ValueError as exc:
        print(f"validate: schema error in data/orgs\n{exc}", file=sys.stderr)
        return 1
    if stale:
        print(
            f"validate: {', '.join(stale)} out of date — "
            "run `python -m codeswissgov build` and commit the result.",
            file=sys.stderr,
        )
        return 1
    print("validate: data/orgs is valid and README.md + inventory.json are up to date")
    return 0


def _cmd_harvest(args: list[str]) -> int:
    token = _token(args)
    if not token:
        print(
            "harvest: a read-only token is required "
            "(--token TOKEN or $GITHUB_TOKEN).",
            file=sys.stderr,
        )
        return 2
    summary = run_harvest(token)
    print(
        f"harvest: refreshed {summary.orgs_refreshed}/{summary.orgs_total} orgs, "
        f"{summary.repos_total} repos in inventory.json"
    )
    if summary.orgs_failed:
        print(
            f"harvest: {len(summary.orgs_failed)} org(s) kept cached data: "
            f"{', '.join(summary.orgs_failed)}",
            file=sys.stderr,
        )
    # Non-zero only when nothing could be refreshed (e.g. a bad token).
    return 1 if summary.orgs_failed and summary.orgs_refreshed == 0 else 0


def _cmd_ingest(args: list[str]) -> int:
    """Reconcile registries against data/orgs and print a read-only report.

    Tokenless (the registry README is a public raw file) and never mutates
    data/orgs — it only surfaces the coverage gap for a human to curate.
    """
    try:
        report = run_ingest()
    except IngestError as exc:
        print(f"ingest: {exc}", file=sys.stderr)
        return 1
    print(render_report(report), end="")
    return 0


def _token(args: list[str]) -> str | None:
    """Resolve a token from ``--token VALUE``/``--token=VALUE`` or env."""
    for i, arg in enumerate(args):
        if arg == "--token" and i + 1 < len(args):
            return args[i + 1]
        if arg.startswith("--token="):
            return arg[len("--token=") :]
    return os.environ.get("GITHUB_TOKEN")


COMMANDS = {
    "build": _cmd_build,
    "validate": _cmd_validate,
    "harvest": _cmd_harvest,
    "ingest": _cmd_ingest,
}


def main(argv: list[str] | None = None) -> int:
    """Dispatch a subcommand. Returns a process exit code."""
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else None

    if command in {"-h", "--help"}:
        print(USAGE)
        return 0

    handler = COMMANDS.get(command)
    if handler is None:
        print(USAGE, file=sys.stderr)
        return 2
    return handler(argv[1:])


if __name__ == "__main__":
    sys.exit(main())
