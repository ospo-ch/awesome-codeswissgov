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
#

"""
This script generates yaml files from the README content
"""

import yaml
import unicodedata
import re


def read_readme():
    """
    Read the default README file, extract the data from the federal services table
    and the cantonal service table. Returns the content from both tables.
    """
    with open("./README.md", "r", encoding="utf-8") as f:
        content = f.readlines()

        fed_table_start = "|Service|Link|\n"
        fed_table_end = "<!-- END FEDERAL LIST -->\n"

        canton_table_start = "|Canton|Link|\n"
        canton_table_end = "<!-- END CANTONAL LIST -->\n"

        fed_idx_start = content.index(fed_table_start) + 2
        fed_idx_end = content.index(fed_table_end) - 1

        canton_idx_start = content.index(canton_table_start) + 2
        canton_idx_end = content.index(canton_table_end) - 1

    return content[fed_idx_start:fed_idx_end], content[canton_idx_start:canton_idx_end]


def parse_row(row: str):
    """
    Parse the markdown content from a row based on the structure:

    row
        A markdown row with the format

        name | \[link_title\](link_url)

    """
    row_data = row.split("|")
    name = row_data[0]
    link_title = ""
    link_url = ""

    if len(row_data) > 1:
        title, url = row_data[1].strip().split("]", maxsplit=1)
        link_title = title[1:]

        if "(" in url and ")" in url:
            link_url = url[1:-1]

    return dict(
        name=name,
        link_title=link_title,
        link_url=link_url,
    )


def convert_to_filename(name: str):
    """
    Convert to ASCII, remove characters which aren't alphanumeric or underscore.
    Strip leading and trailing whitespace. Convert to lowercase. Converts spaces
    and dashes to single underscore.

    This code is based on:
    https://github.com/django/django/blob/cdcd604ef8f650533eff6bd63a517ebb4ffddf96/django/utils/text.py#L452
    """
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = re.sub("[^\w\s]", "", name.lower())
    name = re.sub("[-\s]+", "_", name).strip("_")
    return name


def create_yaml_files():
    """
    Extract data from the README file and create yaml files for each entry.
    """
    fed, canton = read_readme()

    # process federal service data
    for row in fed:
        data = parse_row(row)
        file_name = convert_to_filename("_".join(("admin", data["name"])))
        with open(f"data/{file_name}.yaml", "w") as file:
            yaml.dump(
                data,
                file,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    # process canton data
    for row in canton:
        data = parse_row(row)
        file_name = convert_to_filename("_".join((data["name"], data["link_title"])))
        with open(f"data/{file_name}.yaml", "w") as file:
            yaml.dump(
                data,
                file,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )


if __name__ == "__main__":
    import sys

    sys.exit(create_yaml_files())
