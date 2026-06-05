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

"""CLI entry point: ``python -m codeswissgov <build|validate>``.

``build``    regenerate README.md + inventory.json from data/orgs.
``validate`` schema-check data/orgs and assert the generated views are current.
"""

import sys

from .build import build, validate

USAGE = "usage: python -m codeswissgov <build|validate>"


def _cmd_build() -> int:
    result = build()
    print(f"built {result.readme_path.name} and {result.inventory_path.name}")
    return 0


def _cmd_validate() -> int:
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


COMMANDS = {"build": _cmd_build, "validate": _cmd_validate}


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
    return handler()


if __name__ == "__main__":
    sys.exit(main())
