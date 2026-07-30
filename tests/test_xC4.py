"""
Tests for xC4.py — Crypto, Protobuf, Varint, AES functions.
These test the core building blocks used by all packet operations.
"""
import sys
import os
import asyncio
import json
import unittest

# Setup paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TCP_DIR = os.path.join(BASE_DIR, "OB54-TCP-BOT")
sys.path.insert(0, TCP_DIR)
sys.path.insert(0, os.path.join(TCP_DIR, "Pb2"))

from xC4 import (
    EnC_AEs, DEc_AEs, EnC_PacKeT, DEc_PacKeT,
    EnC_Vr, DEc_Uid, EnC_Uid,
    CrEaTe_VarianT, CrEaTe_LenGTh, CrEaTe_ProTo,
    DecodE_HeX, DeCode_PackEt, GeneRaTePk,
    Key, Iv,
)


class TestAESEncryption(unittest.IsolatedAsyncioTestCase):
    """Test AES encrypt/decrypt round-trip."""

    async def test_aes_round_trip(self):
        """Encrypt then decrypt should return original."""
        original = "deadbeefcafebabe1234567890abcdef"
        encrypted = await EnC_AEs(original)
        decrypted = await DEc_AEs(encrypted)
        self.assertEqual(decrypted, original)

    async def test_aes_known_key_iv(self):
        """Verify the global Key/Iv are correct."""
        self.assertEqual(Key, b"Yg&tc%DEuh6%Zc^8")
        self.assertEqual(Iv, b"6oyZDr22E3ychjM%")
        self.assertEqual(len(Key), 16, "AES key must be 16 bytes")
        self.assertEqual(len(Iv), 16, "AES IV must be 16 bytes")

    async def test_aes_empty_input(self):
        """AES should handle minimal input."""
        original = "00112233"
        encrypted = await EnC_AEs(original)
        decrypted = await DEc_AEs(encrypted)
        self.assertEqual(decrypted, original)

    async def test_packet_encryption_round_trip(self):
        """Test EnC_PacKeT / DEc_PacKeT with custom keys."""
        key = bytes([0x41] * 16)
        iv = bytes([0x42] * 16)
        original = "aabbccdd" * 4
        encrypted = await EnC_PacKeT(original, key, iv)
        decrypted = await DEc_PacKeT(encrypted, key, iv)
        self.assertEqual(decrypted, original)


class TestVarintEncoding(unittest.IsolatedAsyncioTestCase):
    """Test protobuf varint encoding."""

    async def test_small_values(self):
        """Single-byte varints."""
        self.assertEqual((await EnC_Vr(0)).hex(), b'\x00'.hex())
        self.assertEqual((await EnC_Vr(1)).hex(), b'\x01'.hex())
        self.assertEqual((await EnC_Vr(127)).hex(), b'\x7f'.hex())

    async def test_multi_byte(self):
        """Multi-byte varints (with continuation bit)."""
        result = (await EnC_Vr(128)).hex()
        self.assertEqual(result, "8001")
        result = (await EnC_Vr(300)).hex()
        self.assertEqual(result, "ac02")

    async def test_large_values(self):
        """Large UIDs like Free Fire account IDs."""
        uid = 16648969335
        encoded = (await EnC_Vr(uid)).hex()
        decoded = DEc_Uid(encoded)
        self.assertEqual(decoded, uid)

    async def test_uid_round_trip(self):
        """EnC_Uid should encode and DEc_Uid should decode."""
        test_uids = [1, 100, 5842511863, 16648969335, 16648969338]
        for uid in test_uids:
            encoded = await EnC_Uid(uid, 'Uid')
            self.assertIsNotNone(encoded)
            decoded = DEc_Uid(encoded)
            self.assertEqual(decoded, uid, f"UID {uid} round-trip failed")


class TestProtobufEncoding(unittest.IsolatedAsyncioTestCase):
    """Test CrEaTe_ProTo protobuf builder."""

    async def test_simple_fields(self):
        """Build a simple protobuf with int fields."""
        fields = {1: 9, 2: {1: 12345}}
        proto = await CrEaTe_ProTo(fields)
        # CrEaTe_ProTo returns bytearray, not bytes
        self.assertIsInstance(proto, (bytes, bytearray))
        self.assertGreater(len(proto), 0)

    async def test_string_fields(self):
        """Build protobuf with string fields."""
        fields = {1: 5, 2: {1: "ME", 2: "test"}}
        proto = await CrEaTe_ProTo(fields)
        self.assertIsInstance(proto, (bytes, bytearray))
        self.assertGreater(len(proto), 0)

    async def test_nested_fields(self):
        """Build protobuf with deeply nested fields."""
        fields = {
            1: 269,
            2: {
                1: 8, 2: 8,
                5: "samsung",
                14: {2: 5756, 6: 11, 8: "1.126.2", 9: 2, 10: 4}
            }
        }
        proto = await CrEaTe_ProTo(fields)
        self.assertIsInstance(proto, (bytes, bytearray))
        self.assertGreater(len(proto), 10)

    async def test_encode_decode_round_trip(self):
        """Encode then decode should give back the same structure."""
        fields = {1: 9, 2: {1: 16648969335}}
        proto = await CrEaTe_ProTo(fields)
        hex_str = proto.hex() if isinstance(proto, (bytes, bytearray)) else proto
        decoded_json = await DeCode_PackEt(hex_str)
        self.assertIsNotNone(decoded_json)
        parsed = json.loads(decoded_json)
        self.assertEqual(parsed['1']['data'], 9)
        self.assertEqual(parsed['2']['data']['1']['data'], 16648969335)

    async def test_start_match_packet(self):
        """Test building a start-match packet (field 1=9)."""
        fields = {1: 9, 2: {1: 16648969335}}
        proto = await CrEaTe_ProTo(fields)
        hex_str = proto.hex() if isinstance(proto, (bytes, bytearray)) else proto
        decoded = json.loads(await DeCode_PackEt(hex_str))
        self.assertEqual(decoded['1']['data'], 9)
        self.assertEqual(decoded['2']['data']['1']['data'], 16648969335)

    async def test_open_squad_packet(self):
        """Test building an OpEnSq packet (field 1=1)."""
        fields = {
            1: 1,
            2: {
                2: "\u0001", 3: 1, 4: 1, 5: "en",
                9: 1, 11: 1, 13: 1,
                14: {2: 5756, 6: 11, 8: "1.126.2", 9: 2, 10: 4}
            }
        }
        proto = await CrEaTe_ProTo(fields)
        hex_str = proto.hex() if isinstance(proto, (bytes, bytearray)) else proto
        decoded = json.loads(await DeCode_PackEt(hex_str))
        self.assertEqual(decoded['1']['data'], 1)
        self.assertEqual(decoded['2']['data']['3']['data'], 1)
        self.assertEqual(decoded['2']['data']['14']['data']['8']['data'], "1.126.2")

    async def test_join_team_packet(self):
        """Test building a join-team packet (field 1=4)."""
        fields = {1: 4, 2: {1: 1, 2: 1785439811}}
        proto = await CrEaTe_ProTo(fields)
        hex_str = proto.hex() if isinstance(proto, (bytes, bytearray)) else proto
        decoded = json.loads(await DeCode_PackEt(hex_str))
        self.assertEqual(decoded['1']['data'], 4)
        self.assertEqual(decoded['2']['data']['1']['data'], 1)
        self.assertEqual(decoded['2']['data']['2']['data'], 1785439811)

    async def test_leave_squad_packet(self):
        """Test building a leave-squad packet (field 1=7)."""
        fields = {1: 7, 2: {1: 16648969335}}
        proto = await CrEaTe_ProTo(fields)
        hex_str = proto.hex() if isinstance(proto, (bytes, bytearray)) else proto
        decoded = json.loads(await DeCode_PackEt(hex_str))
        self.assertEqual(decoded['1']['data'], 7)
        self.assertEqual(decoded['2']['data']['1']['data'], 16648969335)


class TestPacketGeneration(unittest.IsolatedAsyncioTestCase):
    """Test GeneRaTePk — full packet with header + encrypted payload."""

    async def test_packet_structure(self):
        """Generated packet should have header + encrypted payload."""
        key = bytes([0x41] * 16)
        iv = bytes([0x42] * 16)
        fields = {1: 9, 2: {1: 12345}}
        proto = await CrEaTe_ProTo(fields)
        packet = await GeneRaTePk(proto.hex(), "0515", key, iv)
        self.assertIsInstance(packet, bytes)
        packet_hex = packet.hex()
        self.assertTrue(packet_hex.startswith("0515"))

    async def test_packet_type_in_header(self):
        """Verify packet type appears in header for different types."""
        key = bytes([0x41] * 16)
        iv = bytes([0x42] * 16)
        fields = {1: 9}
        proto = await CrEaTe_ProTo(fields)
        for pkt_type in ["0514", "0515", "0519"]:
            packet = await GeneRaTePk(proto.hex(), pkt_type, key, iv)
            self.assertTrue(packet.hex().startswith(pkt_type),
                          f"Packet type {pkt_type} not in header: {packet.hex()[:10]}")

    async def test_packet_round_trip_decrypt(self):
        """Encrypt a packet, then decrypt it to verify content."""
        key = bytes([0x41] * 16)
        iv = bytes([0x42] * 16)
        fields = {1: 9, 2: {1: 16648969335}}
        proto = await CrEaTe_ProTo(fields)
        proto_hex = proto.hex()

        # Encrypt the proto
        encrypted = await EnC_PacKeT(proto_hex, key, iv)

        # Decrypt it back
        decrypted = await DEc_PacKeT(encrypted, key, iv)

        # Decode the decrypted data
        decoded = json.loads(await DeCode_PackEt(decrypted))
        self.assertEqual(decoded['1']['data'], 9)
        self.assertEqual(decoded['2']['data']['1']['data'], 16648969335)


class TestHexDecode(unittest.IsolatedAsyncioTestCase):
    """Test DecodE_HeX utility."""

    async def test_small_numbers(self):
        """Small numbers should produce correct hex."""
        self.assertEqual(await DecodE_HeX(0), "00")
        self.assertEqual(await DecodE_HeX(1), "01")
        self.assertEqual(await DecodE_HeX(15), "0f")
        self.assertEqual(await DecodE_HeX(255), "ff")

    async def test_large_numbers(self):
        """Large numbers should produce multi-byte hex (no padding)."""
        result = await DecodE_HeX(256)
        # DecodE_HeX uses hex() which doesn't zero-pad
        self.assertEqual(result, "100")


class TestVersionConsistency(unittest.TestCase):
    """Test that version strings are consistent across files."""

    EXPECTED_VERSION = "1.126.2"

    def test_clan_bot_version(self):
        """clan_glory_bot.py should use version 1.126.2."""
        filepath = os.path.join(BASE_DIR, "clan_glory_bot.py")
        with open(filepath) as f:
            content = f.read()
        self.assertIn(self.EXPECTED_VERSION, content)
        for old_ver in ["1.111.1", "1.111.5", "1.114.18", "1.118"]:
            self.assertNotIn(old_ver, content,
                           f"Old version {old_ver} still in clan_glory_bot.py")

    def test_xC4_version(self):
        """xC4.py should use version 1.126.2."""
        filepath = os.path.join(TCP_DIR, "xC4.py")
        with open(filepath) as f:
            content = f.read()
        self.assertIn(self.EXPECTED_VERSION, content)
        for old_ver in ["1.111.1", "1.111.5", "1.114.18"]:
            self.assertNotIn(old_ver, content,
                           f"Old version {old_ver} still in xC4.py")

    def test_main_py_version(self):
        """main.py should use version 1.126.2."""
        filepath = os.path.join(TCP_DIR, "main.py")
        if os.path.exists(filepath):
            with open(filepath) as f:
                content = f.read()
            self.assertIn(self.EXPECTED_VERSION, content)
            for old_ver in ["1.111.1", "1.111.5", "1.114.18"]:
                self.assertNotIn(old_ver, content,
                               f"Old version {old_ver} still in main.py")


if __name__ == '__main__':
    unittest.main(verbosity=2)
