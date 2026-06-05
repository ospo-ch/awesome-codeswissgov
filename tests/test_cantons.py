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

"""Unit tests for the canton reference map."""

from codeswissgov import cantons


def test_all_26_cantons_present():
    assert len(cantons.CANTONS) == 26
    assert len(cantons.CANTON_CODES) == 26


def test_known_mappings_match_readme_spelling():
    assert cantons.canton_display("ZH") == "Zürich"
    assert cantons.canton_display("GR") == "Graubünden"
    assert cantons.canton_display("NE") == "Neuchâtel"
    assert cantons.canton_display("SG") == "St. Gallen"
    assert cantons.canton_display("BL") == "Basel-Land"


def test_reverse_lookup_is_a_bijection():
    # Every display name maps back to its code, with no collisions.
    assert len(cantons.CODE_BY_DISPLAY) == 26
    for code, name in cantons.CANTONS.items():
        assert cantons.CODE_BY_DISPLAY[name] == code
