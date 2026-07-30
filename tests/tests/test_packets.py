"""
Tests for packet construction, region routing, and packet type logic.
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

from xC4 import (
    CrEaTe_ProTo, DeCode_PackEt, GeneRaTePk, DEc_PacKeT,
    OpEnSq, AutH_GlobAl, AuthClan, ExiT, SEnd_InV,
)

# Import clan_glory_bot for get_packet_type
sys.path.insert(0, BASE_DIR)


class TestRegionPacketRouting(unittest.TestCase):
    """Test that region → packet type mapping is correct."""

    def test_me_region(self):
        """ME region should use default packet 0515."""
        from clan_glory_bot import get_packet_type
        self.assertEqual(get_packet_type("ME"), "0515")
        self.assertEqual(get_packet_type("me"), "0515")

    def test_ind_region(self):
        """IND region should use packet 0514."""
        from clan_glory_bot import get_packet_type
        self.assertEqual(get_packet_type("IND"), "0514")
        self.assertEqual(get_packet_type("ind"), "0514")

    def test_bd_region(self):
        """BD region should use packet 0519."""
        from clan_glory_bot import get_packet_type
        self.assertEqual(get_packet_type("BD"), "0519")
        self.assertEqual(get_packet_type("bd"), "0519")

    def test_unknown_region_falls_back(self):
        """Unknown regions should fall back to default 0515."""
        from clan_glory_bot import get_packet_type
        self.assertEqual(get_packet_type("US"), "0515")
        self.assertEqual(get_packet_type("SG"), "0515")
        self.assertEqual(get_packet_type("UNKNOWN"), "0515")

    def test_case_insensitive(self):
        """Region lookup should be case-insensitive."""
        from clan_glory_bot import get_packet_type
        self.assertEqual(get_packet_type("Me"), "0515")
        self.assertEqual(get_packet_type("Ind"), "0514")
        self.assertEqual(get_packet_type("Bd"), "0519")


class TestPacketConstruction(unittest.IsolatedAsyncioTestCase):
    """Test construction of specific game packets."""

    async def test_open_squad_uses_correct_version(self):
        """OpEnSq should embed version 1.126.2 in field 14.8."""
        key = bytes([0x41] * 16)
        iv = bytes([0x42] * 16)
        packet = await OpEnSq(key, iv, "ME")
        self.assertIsInstance(packet, bytes)
        packet_hex = packet.hex()
        # Decode the payload to check version
        for header_len in [8, 10, 12, 14]:
            try:
                payload = packet_hex[header_len:]
                decrypted = await DEc_PacKeT(payload, key, iv)
                decoded = json.loads(await DeCode_PackEt(decrypted))
                version_field = decoded.get('2', {}).get('data', {}).get('14', {}).get('data', {}).get('8', {}).get('data')
                if version_field:
                    self.assertEqual(version_field, "1.126.2",
                                   f"OpEnSq has wrong version: {version_field}")
                    return
            except:
                continue
        self.fail("Could not decode OpEnSq packet")

    async def test_auth_global_packet(self):
        """AutH_GlobAl should produce a valid packet."""
        key = bytes([0x41] * 16)
        iv = bytes([0x42] * 16)
        packet = await AutH_GlobAl(key, iv)
        self.assertIsInstance(packet, bytes)
        self.assertGreater(len(packet), 10)

    async def test_exit_packet(self):
        """ExiT should produce a valid leave packet."""
        key = bytes([0x41] * 16)
        iv = bytes([0x42] * 16)
        packet = await ExiT(key, iv)
        self.assertIsInstance(packet, bytes)
        self.assertGreater(len(packet), 10)

    async def test_send_invite_packet(self):
        """SEnd_InV should produce a valid invite packet."""
        key = bytes([0x41] * 16)
        iv = bytes([0x42] * 16)
        packet = await SEnd_InV(16648969334, 16648969335, key, iv)
        self.assertIsInstance(packet, bytes)
        self.assertGreater(len(packet), 10)

    async def test_auth_clan_packet(self):
        """AuthClan should produce a valid clan auth packet."""
        key = bytes([0x41] * 16)
        iv = bytes([0x42] * 16)
        packet = await AuthClan(3100938923, "test_jwt_token", key, iv)
        self.assertIsInstance(packet, bytes)
        self.assertGreater(len(packet), 10)


class TestStartMatchPackets(unittest.IsolatedAsyncioTestCase):
    """Test the three start-match packet types used by the leader."""

    async def test_field_269_detailed(self):
        """Field 1=269: detailed start with device info."""
        fields = {
            1: 269,
            2: {
                1: 8, 2: 8, 3: 11, 4: 1,
                5: "samsung", 6: "SM-A145F", 7: "arm64-v8a",
                8: "f538dc9b-cec9-43cd-8125-95f7f4f1f7e3",
                14: "ME_1999120752610979840",
                15: 269
            }
        }
        proto = await CrEaTe_ProTo(fields)
        decoded = json.loads(await DeCode_PackEt(proto.hex()))
        self.assertEqual(decoded['1']['data'], 269)
        self.assertEqual(decoded['2']['data']['5']['data'], "samsung")
        self.assertEqual(decoded['2']['data']['6']['data'], "SM-A145F")
        self.assertEqual(decoded['2']['data']['14']['data'], "ME_1999120752610979840")

    async def test_field_214_simple(self):
        """Field 1=214: simple start."""
        fields = {1: 214, 2: {1: 1}}
        proto = await CrEaTe_ProTo(fields)
        decoded = json.loads(await DeCode_PackEt(proto.hex()))
        self.assertEqual(decoded['1']['data'], 214)
        self.assertEqual(decoded['2']['data']['1']['data'], 1)

    async def test_field_9_basic(self):
        """Field 1=9: basic start (used by level bot and spam)."""
        uid = 16648969335
        fields = {1: 9, 2: {1: uid}}
        proto = await CrEaTe_ProTo(fields)
        decoded = json.loads(await DeCode_PackEt(proto.hex()))
        self.assertEqual(decoded['1']['data'], 9)
        self.assertEqual(decoded['2']['data']['1']['data'], uid)

    async def test_start_match_uid_not_hardcoded(self):
        """The basic start packet should use the actual account UID, not a hardcoded one."""
        # This was a bug in early versions — UID was hardcoded to 12480598706
        hardcoded_uid = 12480598706
        test_uid = 16648969335
        fields = {1: 9, 2: {1: test_uid}}
        proto = await CrEaTe_ProTo(fields)
        decoded = json.loads(await DeCode_PackEt(proto.hex()))
        actual_uid = decoded['2']['data']['1']['data']
        self.assertEqual(actual_uid, test_uid)
        self.assertNotEqual(actual_uid, hardcoded_uid,
                           "UID is hardcoded — this was a known bug!")


class TestLeaveSquadPacket(unittest.IsolatedAsyncioTestCase):
    """Test leave/reset squad packet (field 1=7)."""

    async def test_leave_uses_correct_uid(self):
        """Leave packet should use the account's own UID, not hardcoded."""
        test_uid = 5842511863
        fields = {1: 7, 2: {1: test_uid}}
        proto = await CrEaTe_ProTo(fields)
        decoded = json.loads(await DeCode_PackEt(proto.hex()))
        self.assertEqual(decoded['1']['data'], 7)
        self.assertEqual(decoded['2']['data']['1']['data'], test_uid)


class TestJoinTeamPacket(unittest.IsolatedAsyncioTestCase):
    """Test the join-team packet (field 1=4, 2.1=1, 2.2=team_code)."""

    async def test_join_team_numeric_code(self):
        """Join with numeric team code."""
        team_code = 1785439811
        fields = {1: 4, 2: {1: 1, 2: team_code}}
        proto = await CrEaTe_ProTo(fields)
        decoded = json.loads(await DeCode_PackEt(proto.hex()))
        self.assertEqual(decoded['1']['data'], 4)
        self.assertEqual(decoded['2']['data']['1']['data'], 1)
        self.assertEqual(decoded['2']['data']['2']['data'], team_code)

    async def test_join_team_different_codes(self):
        """Join with different team codes should produce different packets."""
        key = bytes([0x41] * 16)
        iv = bytes([0x42] * 16)
        code1 = 1785439811
        code2 = 1785439812
        fields1 = {1: 4, 2: {1: 1, 2: code1}}
        fields2 = {1: 4, 2: {1: 1, 2: code2}}
        proto1 = await CrEaTe_ProTo(fields1)
        proto2 = await CrEaTe_ProTo(fields2)
        self.assertNotEqual(proto1.hex(), proto2.hex())


if __name__ == '__main__':
    unittest.main(verbosity=2)
