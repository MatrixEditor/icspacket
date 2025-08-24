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
import pathlib
import json


def asn1_decode(asn1_cls: type, expected: str, data: str):
    """
    Decode ASN.1 BER-encoded data and compare textual output
    against an expected reference.

    :param asn1_cls: ASN.1 class implementing ``ber_decode`` and
                     ``to_text`` methods.
    :type asn1_cls: type
    :param expected: Reference text representation for comparison.
    :type expected: str
    :param data: Hex string of BER-encoded input to decode.
    :type data: str
    :raises AssertionError: If decoded text does not match the
                            expected output line by line.
    """
    parsed = asn1_cls.ber_decode(bytes.fromhex(data))
    parsed_text = parsed.to_text().decode()
    for expected_line, parsed_line in zip(
        expected.splitlines(), parsed_text.splitlines()
    ):
        assert expected_line.strip() == parsed_line.strip(), (
            f"Failed to decode {asn1_cls.__name__}: {expected_line} != {parsed_line}"
        )


def asn1_encode(asn1_cls: type, data: str):
    """
    Encode and re-encode ASN.1 data to verify round-trip consistency.

    Ensures that parsing a BER-encoded value and serializing it again
    produces the identical byte stream.

    :param asn1_cls: ASN.1 class implementing ``ber_decode`` and
                     ``ber_encode`` methods.
    :type asn1_cls: type
    :param data: Hex string of BER-encoded input to check.
    :type data: str
    :raises AssertionError: If re-encoding does not exactly match
                            the original byte stream.
    """
    raw_data = bytes.fromhex(data)
    parsed = asn1_cls.ber_decode(raw_data)
    assert parsed.ber_encode() == raw_data, f"Failed to encode {asn1_cls.__name__}"


def asset_dir() -> pathlib.Path:
    """
    Return the base directory containing test asset files.

    :return: Path to the asset directory.
    :rtype: pathlib.Path
    """
    return pathlib.Path(__file__).parent / "assets"


def load_asset_cases(name: str) -> dict[str, list[str]]:
    """
    Load a named test case set from an asset JSON file.

    Asset files are JSON documents where the top-level keys
    correspond to test categories (e.g. ``"cotp"``). Each entry
    is expected to map to a list of hex-encoded packet strings.

    :param name: Asset case name to retrieve (key in the JSON).
    :type name: str
    :return: Mapping of subcase identifiers to lists of packets.
    :rtype: dict[str, list[str]]
    :raises FileNotFoundError: If the JSON file for ``name`` is missing.
    :raises KeyError: If the JSON file does not contain the requested key.
    """
    path = asset_dir() / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Asset file {path} does not exist")

    with path.open() as f:
        asset_data = json.load(f)

    if name not in asset_data:
        raise KeyError(f"Asset file {path} does not contain {name}")

    return asset_data[name]


class faketpktsock:
    """
    Fake TPKT socket implementation for deterministic testing.

    Provides a minimal interface compatible with Python's socket
    API (``connect``, ``close``, ``recv``, ``sendall``), but driven
    by a predefined set of hex-encoded packets from asset files.
    TPKT headers (first 4 bytes) are automatically stripped so
    that higher protocol layers (e.g. COTP, ACSE) see raw payloads.

    This class is primarily used for simulating protocol exchanges
    in unit tests without requiring an actual network connection.

    Example JSON configuration::

        {
            "cotp": {
                "connect_success": [
                    "0300001611d00001000100c1020000c2020001c0010a"
                ],
                "connect_reject": [
                    "0300000b06800001000080"
                ],
                "recv_single_data": [
                    "0300001611d00001000100c1020000c2020001c0010a",
                    "..."
                ]
            }
        }

    .. note::

        Currently, packets send by a connection implementation won't
        be checked.

    :param asset_data: Preloaded hex-encoded packets (including TPKT header).
    :type asset_data: list[str]
    """

    FAKE_ADDRESS = ("", 0)
    """Placeholder address tuple to mimic a socket endpoint."""

    def __init__(self, asset_data: list[str]) -> None:
        self.__asset_data = asset_data
        self.index = 0

    @property
    def current_packet(self) -> bytes:
        """
        Return the current decoded packet without advancing.

        Removes the first 4 bytes (TPKT header) so that only
        protocol payload remains.

        :return: Current packet payload or empty bytes if exhausted.
        :rtype: bytes
        """
        if self.index >= len(self.__asset_data):
            return b""
        # remove TPKT header first
        return bytes.fromhex(self.__asset_data[self.index])[4:]

    def next_packet(self):
        """
        Retrieve the next decoded packet and advance the cursor.

        :return: Next packet payload.
        :rtype: bytes
        """
        packet = self.current_packet
        self.index += 1
        return packet

    def connect(self, address):
        """
        Reset packet cursor to start when "connecting".

        :param address: Socket-like address (ignored).
        """
        self.index = 0

    def close(self):
        """
        Reset packet cursor to start when "closing".
        """
        self.index = 0

    def recv(self, size):
        """
        Retrieve the next available packet.

        :param size: Maximum size to receive (ignored).
        :return: Next packet payload.
        :rtype: bytes
        """
        return self.next_packet()

    def sendall(self, data):
        """
        No-op method to satisfy socket API compatibility.

        :param data: Data to "send" (ignored).
        """
        pass

    def sendto(self, data, address):
        """
        No-op method to satisfy socket API compatibility.

        :param data: Data to "send" (ignored).
        :param address: Socket-like address (ignored).
        """
        pass

    def send(self, data):
        """
        No-op method to satisfy socket API compatibility.

        :param data: Data to "send" (ignored).
        """
        pass
