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

"""CLI entry point: ``python -m codeswissgov <command>``.

Commands are wired up in Epic 1 task T5 (``build`` | ``validate``). This stub
exists so the package is runnable as a module from the start of the epic.
"""

import sys


def main(argv: list[str] | None = None) -> int:
    """Dispatch a subcommand. Returns a process exit code."""
    argv = sys.argv[1:] if argv is None else argv
    command = argv[0] if argv else None

    if command in {None, "-h", "--help"}:
        print("usage: python -m codeswissgov <build|validate>")
        return 0

    print(f"codeswissgov: command {command!r} is not implemented yet")
    return 2


if __name__ == "__main__":
    sys.exit(main())
