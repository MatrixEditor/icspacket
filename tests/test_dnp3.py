# This file is part of icspacket.
# Copyright (C) 2025-present  MatrixEditor @ github
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import pytest

from icspacket.proto.dnp3.objects.coding import (
    DNP3Objects,
    pack_objects,
    unpack_objects,
)
from icspacket.proto.dnp3.application import APDU
from icspacket.proto.dnp3.objects.util import get_octet_string, new_octet_string


@pytest.mark.parametrize(
    "message_hex,expected_objects",
    [
        (
            "c78100000101000005190a020000058101818101011405000000200000001509000000"
            + "000000001e03000006ca000000cb000000c9000000ffffffff66210000592100004b"
            + "210000",
            {
                1: [1],
                10: [2],
                20: [5],
                21: [9],
                30: [3],
            },
        ),
        (
            "c38100040c012801009f860301640000006400000004",
            {
                12: [1],  # with prefix and range
            },
        ),
        (
            "e88100006f0c000000656d7265206e616269796f6e",
            {
                111: [12],  # octet string of length 12
            },
        ),
        (
            "c4013c02063c03063c0406",
            {
                60: [2, 3, 4],  # read class 1-3
            },
        ),
    ],
)
def test_parse_message(
    message_hex: str,
    expected_objects: dict[int, list[int] | None],
):
    apdu = APDU.from_octets(bytes.fromhex(message_hex))
    objects = unpack_objects(apdu.objects)
    if len(objects) != len(expected_objects):
        raise ValueError(
            f"Expected {len(expected_objects)} objects, got {len(objects)}"
        )

    for object_id, expected_variations in expected_objects.items():
        if object_id not in objects:
            raise ValueError(f"Object {object_id} not found")

        variations = objects[object_id]
        if expected_variations is not None:
            if len(variations) != len(expected_variations):
                raise ValueError(
                    f"Expected {len(expected_variations)} variations for object {object_id}, got {len(variations)}"
                )

            assert list(variations.keys()) == expected_variations, (
                f"Expected variations {expected_variations} for object {object_id}, got {list(variations.keys())}"
            )

    packed = pack_objects(objects)
    assert packed == apdu.objects, (
        f"Failed to pack objects: {packed.hex()} != {apdu.objects.hex()}"
    )


def test_empty_objects():
    objects = DNP3Objects()
    objects.add_empty(60, 1)  # object 60, variation 1 (Class 0)
    objects.add_empty(60, 2)  # object 60, variation 2 (Class 1)
    objects.add_empty(60, 3)  # object 60, variation 3 (Class 2)
    objects.add_empty(60, 4)  # object 60, variation 4 (Class 3)

    encoded = pack_objects(objects)
    assert encoded.hex() == "3c01063c02063c03063c0406"


def test_variation0():
    objects = DNP3Objects()
    objects.add_variation0(2)  # default variation for object 02

    encoded = pack_objects(objects)
    assert encoded.hex() == "020006"


def test_octet_string():
    objects = new_octet_string(b"hello world")
    assert get_octet_string(objects) == b"hello world"

    objects = new_octet_string(b"hello world", group=112)
    assert get_octet_string(objects, 112) == b"hello world"

    encoded = pack_objects(objects)
    assert encoded.hex() == "700b0668656c6c6f20776f726c64"
