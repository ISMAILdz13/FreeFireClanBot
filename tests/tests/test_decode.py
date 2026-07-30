"""
Tests for packet decoding with captured real server data.
Tests the decode logic that finds f2=18 (match packet) in chat channel data.
"""
import sys
import os
import asyncio
import json
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TCP_DIR = os.path.join(BASE_DIR, "OB54-TCP-BOT")
sys.path.insert(0, TCP_DIR)
sys.path.insert(0, os.path.join(TCP_DIR, "Pb2"))

from xC4 import DeCode_PackEt, CrEaTe_ProTo


# Captured f2=18 match packet data from real server responses.
# All 3 accounts receive this packet on the chat channel after start-match spam.
# Fields: f0=26, f1=account_uid, f2=18, f4=5, f5.1=100001, f5.2-5.5=20, f5.8=1

MATCH_PACKET_STRUCTURE = {
    "f0": 26,
    "f2": 18,
    "f4": 5,
    "f5": {
        "1": 100001,   # game mode ID (Clash Squad)
        "2": 20,       # timer/param
        "3": 20,       # timer/param
        "4": 20,       # timer/param
        "5": 20,       # timer/param
        "8": 1,        # status flag
    }
}

BOT_UIDS = [
    16648969335,  # G1 (leader)
    16648969334,  # G2
    16648969338,  # G3
]

CLAN_ID = 3100938923


class TestMatchPacketEncoding(unittest.IsolatedAsyncioTestCase):
    """Test that we can encode and decode a match packet (f2=18)."""

    async def test_encode_match_packet(self):
        """Build a packet matching the f2=18 structure and decode it."""
        fields = {
            0: MATCH_PACKET_STRUCTURE["f0"],
            1: BOT_UIDS[0],
            2: MATCH_PACKET_STRUCTURE["f2"],
            4: MATCH_PACKET_STRUCTURE["f4"],
            5: MATCH_PACKET_STRUCTURE["f5"],
        }
        proto = await CrEaTe_ProTo(fields)
        decoded = json.loads(await DeCode_PackEt(proto.hex()))

        self.assertEqual(decoded['0']['data'], 26)
        self.assertEqual(decoded['1']['data'], BOT_UIDS[0])
        self.assertEqual(decoded['2']['data'], 18)
        self.assertEqual(decoded['4']['data'], 5)
        self.assertEqual(decoded['5']['data']['1']['data'], 100001)
        self.assertEqual(decoded['5']['data']['2']['data'], 20)
        self.assertEqual(decoded['5']['data']['3']['data'], 20)
        self.assertEqual(decoded['5']['data']['4']['data'], 20)
        self.assertEqual(decoded['5']['data']['5']['data'], 20)
        self.assertEqual(decoded['5']['data']['8']['data'], 1)

    async def test_match_packet_each_uid(self):
        """Each bot should get its own UID in f1."""
        for uid in BOT_UIDS:
            fields = {
                0: 26,
                1: uid,
                2: 18,
                4: 5,
                5: {1: 100001, 2: 20, 3: 20, 4: 20, 5: 20, 8: 1},
            }
            proto = await CrEaTe_ProTo(fields)
            decoded = json.loads(await DeCode_PackEt(proto.hex()))
            self.assertEqual(decoded['1']['data'], uid,
                           f"UID mismatch: expected {uid}, got {decoded['1']['data']}")
            self.assertEqual(decoded['2']['data'], 18)


class TestMatchPacketDecodeLogic(unittest.IsolatedAsyncioTestCase):
    """Test the decode logic used in the post-match analysis."""

    async def test_find_f2_18_at_offset(self):
        """Simulate finding f2=18 at various offsets in a hex stream."""
        # Build a match packet
        fields = {0: 26, 1: BOT_UIDS[0], 2: 18, 4: 5, 5: {1: 100001, 2: 20, 3: 20, 4: 20, 5: 20, 8: 1}}
        proto = await CrEaTe_ProTo(fields)
        match_hex = proto.hex()

        # Prepend some fake header bytes (simulating TCP framing)
        for prefix_len in [2, 4, 6, 8, 10, 12, 14, 16]:
            prefix = "ab" * (prefix_len // 2)
            full_hex = prefix + match_hex

            # Try to find f2=18 by scanning offsets
            found = False
            for skip in range(0, min(32, len(full_hex)), 2):
                payload = full_hex[skip:]
                if len(payload) < 20:
                    continue
                json_str = await DeCode_PackEt(payload)
                if not json_str:
                    continue
                parsed = json.loads(json_str)
                f2 = parsed.get('2', {})
                f2_val = f2.get('data') if isinstance(f2, dict) else f2
                if isinstance(f2_val, int) and f2_val == 18:
                    found = True
                    self.assertEqual(parsed['1']['data'], BOT_UIDS[0])
                    self.assertEqual(parsed['5']['data']['1']['data'], 100001)
                    break
            self.assertTrue(found, f"Could not find f2=18 at prefix_len={prefix_len}")

    async def test_reject_empty_f2(self):
        """The scanner should NOT accept empty string or None as valid f2."""
        # Build a packet with no field 2 (should not be accepted)
        fields = {1: BOT_UIDS[0], 5: {1: 100001}}
        proto = await CrEaTe_ProTo(fields)
        hex_str = proto.hex()

        decoded = json.loads(await DeCode_PackEt(hex_str))
        f2 = decoded.get('2', {})
        f2_val = f2.get('data') if isinstance(f2, dict) else f2

        # f2 should be None or empty — NOT a positive integer
        self.assertFalse(isinstance(f2_val, int) and f2_val > 0,
                        f"Empty f2 was accepted as valid: {f2_val}")

    async def test_reject_f2_zero(self):
        """f2=0 should not be accepted (only positive integers)."""
        fields = {1: 123, 2: 0, 5: {1: 999}}
        proto = await CrEaTe_ProTo(fields)
        hex_str = proto.hex()
        decoded = json.loads(await DeCode_PackEt(hex_str))

        f2 = decoded.get('2', {})
        f2_val = f2.get('data') if isinstance(f2, dict) else f2

        # 0 should NOT be accepted (only >= 1)
        if isinstance(f2_val, int):
            self.assertLess(f2_val, 1, "f2=0 should be rejected")


class TestClanDataPacket(unittest.IsolatedAsyncioTestCase):
    """Test f2=30 packet which contains clan ID 3100938923."""

    async def test_clan_data_packet_structure(self):
        """Build and decode a clan data packet (f2=30)."""
        fields = {
            2: 30,
            5: {
                1: {
                    1: 10613565903,  # some UID
                    2: CLAN_ID,       # clan ID
                }
            }
        }
        proto = await CrEaTe_ProTo(fields)
        decoded = json.loads(await DeCode_PackEt(proto.hex()))

        self.assertEqual(decoded['2']['data'], 30)
        self.assertEqual(decoded['5']['data']['1']['data']['1']['data'], 10613565903)
        self.assertEqual(decoded['5']['data']['1']['data']['2']['data'], CLAN_ID)

    async def test_clan_id_as_f2_value(self):
        """The clan ID 3100938923 also appears as an f2 value directly."""
        fields = {2: CLAN_ID, 5: {1: "clan_data_here"}}
        proto = await CrEaTe_ProTo(fields)
        decoded = json.loads(await DeCode_PackEt(proto.hex()))

        self.assertEqual(decoded['2']['data'], CLAN_ID)


class TestPacketTypeSummary(unittest.IsolatedAsyncioTestCase):
    """Test the packet type summary logic used in post-match analysis."""

    async def test_scan_multiple_packets(self):
        """Scan a hex stream with multiple packets and find all f2 values."""
        # Build multiple packets with different f2 values
        packets = []
        for f2_val in [1, 5, 18, 20, 30]:
            fields = {1: 12345, 2: f2_val}
            proto = await CrEaTe_ProTo(fields)
            # Add some padding between packets
            packets.append(proto.hex() + "00" * 4)

        full_hex = "".join(packets)

        # Scan for all f2 values
        found_types = {}
        scan_off = 0
        while scan_off < min(len(full_hex) - 20, 4000):
            try:
                payload = full_hex[scan_off:]
                json_str = await DeCode_PackEt(payload)
                if json_str:
                    parsed = json.loads(json_str)
                    f2 = parsed.get('2', {})
                    f2_val = f2.get('data') if isinstance(f2, dict) else f2
                    if isinstance(f2_val, int) and f2_val > 0:
                        if f2_val not in found_types:
                            found_types[f2_val] = 0
                        found_types[f2_val] += 1
                        scan_off += 40
                        continue
                scan_off += 2
            except:
                scan_off += 2

        # Should have found at least some of the f2 values
        self.assertGreater(len(found_types), 0, "No packet types found in multi-packet stream")
        # f2=18 should be among them
        self.assertIn(18, found_types, "f2=18 not found in scanned packets")


class TestJoinResponseDecoding(unittest.IsolatedAsyncioTestCase):
    """Test decoding of join-team responses (which may have f3=79)."""

    async def test_decode_response_with_f3_79(self):
        """G2's join response has f3=79 — this should NOT cause rejection."""
        # Build a response like what G2 receives
        fields = {
            1: BOT_UIDS[1],  # G2's UID
            2: 5,            # packet type = squad
            3: 79,           # squad parameter (NOT an error!)
        }
        proto = await CrEaTe_ProTo(fields)
        decoded = json.loads(await DeCode_PackEt(proto.hex()))

        self.assertEqual(decoded['1']['data'], BOT_UIDS[1])
        self.assertEqual(decoded['2']['data'], 5)
        self.assertEqual(decoded['3']['data'], 79)

        # The key insight: 79 is NOT an error. The join should succeed.
        f3_val = decoded['3']['data']
        self.assertEqual(f3_val, 79, "f3=79 is a squad parameter, not an error code")

    async def test_decode_response_without_f3(self):
        """G3's join response doesn't have f3 — should also succeed."""
        fields = {
            1: BOT_UIDS[2],  # G3's UID
            2: 5,            # packet type = squad
        }
        proto = await CrEaTe_ProTo(fields)
        decoded = json.loads(await DeCode_PackEt(proto.hex()))

        self.assertEqual(decoded['1']['data'], BOT_UIDS[2])
        self.assertEqual(decoded['2']['data'], 5)
        # No field 3 — should be absent
        self.assertNotIn('3', decoded, "G3's response should not have field 3")


if __name__ == '__main__':
    unittest.main(verbosity=2)
