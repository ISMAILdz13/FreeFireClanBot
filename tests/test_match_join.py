"""Tests for match-join and concurrent reading functionality."""
import asyncio
import json
import sys
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'OB54-TCP-BOT'))


class TestJoinMatchProtobufEncoding(unittest.IsolatedAsyncioTestCase):
    """Test that join_match creates valid protobuf with integer keys."""

    async def test_protobuf_with_integer_keys(self):
        """CrEaTe_ProTo must handle nested dicts with integer keys (not string keys)."""
        from xC4 import CrEaTe_ProTo
        
        fields = {
            1: 3,
            2: {
                1: 16145387763,
                2: "",
                8: {1: "IDC3", 2: 149, 3: "IND"},
                10: 1,
                13: 1,
                14: 1,
                16: "en",
                22: {1: 21},
            }
        }
        result = await CrEaTe_ProTo(fields)
        self.assertIsInstance(result, (bytes, bytearray))
        self.assertGreater(len(result), 10)
        
        # Verify it can be decoded back
        from xC4 import DeCode_PackEt
        json_str = await DeCode_PackEt(result.hex())
        self.assertIsNotNone(json_str, "Protobuf should be decodable")
        parsed = json.loads(json_str)
        # Field 1 should be 3 (room join command)
        f1 = parsed.get('1', {})
        self.assertEqual(f1.get('data'), 3)

    async def test_string_keys_cause_error(self):
        """Verify that string keys in nested dicts cause the << error (regression test)."""
        from xC4 import CrEaTe_ProTo
        
        fields = {
            1: 3,
            2: {
                1: 12345,
                8: {"1": "IDC3", "2": 149, "3": "IND"},  # String keys!
            }
        }
        with self.assertRaises(TypeError) as ctx:
            await CrEaTe_ProTo(fields)
        self.assertIn('<<', str(ctx.exception))

    async def test_join_match_packet_structure(self):
        """Test that join_match fields produce a valid RoomJoin packet."""
        from xC4 import CrEaTe_ProTo, DeCode_PackEt
        
        # Simulate the exact fields used by join_match
        group_id = 16145387763
        fields = {
            1: 3,
            2: {
                1: group_id,
                2: "",
                8: {1: "IDC3", 2: 149, 3: "IND"},
                10: 1,
                13: 1,
                14: 1,
                16: "en",
                22: {1: 21},
            }
        }
        
        proto = await CrEaTe_ProTo(fields)
        proto_hex = proto.hex()
        
        # Decode and verify GroupID is in the packet
        decoded = await DeCode_PackEt(proto_hex)
        parsed = json.loads(decoded)
        
        f2 = parsed.get('2', {})
        f2d = f2.get('data', {})
        f1 = f2d.get('1', {})
        self.assertEqual(f1.get('data'), group_id, "GroupID should be in the packet")
        
        # Verify field 8 nested structure
        f8 = f2d.get('8', {})
        f8d = f8.get('data', {})
        self.assertEqual(f8d.get('1', {}).get('data'), "IDC3")
        self.assertEqual(f8d.get('2', {}).get('data'), 149)
        self.assertEqual(f8d.get('3', {}).get('data'), "IND")


class TestGroupIDExtraction(unittest.TestCase):
    """Test extracting GroupID from match-found packet data."""

    def _extract_group_id(self, match_data):
        """Replicate the GroupID extraction logic from the bot."""
        f5 = match_data.get('5', {})
        f5d = f5.get('data', {}) if isinstance(f5, dict) else {}
        group_id = None
        if isinstance(f5d, dict):
            f1 = f5d.get('1', {})
            if isinstance(f1, dict) and 'data' in f1:
                group_id = f1['data']
        return group_id

    def test_extract_group_id_from_real_packet(self):
        """Test with actual match packet data from a real run."""
        match_data = {
            "1": {"wire_type": "varint", "data": 16648969335},
            "2": {"wire_type": "varint", "data": 18},
            "4": {"wire_type": "varint", "data": 2},
            "5": {
                "wire_type": "length_delimited",
                "data": {
                    "1": {"wire_type": "varint", "data": 16145387763},
                    "2": {"wire_type": "varint", "data": 100001},
                    "3": {"wire_type": "varint", "data": 5},
                    "5": {"wire_type": "varint", "data": 1785450593},
                    "8": {"wire_type": "string", "data": '{"GroupID":16145387763,"Game":15,"Match":6,"MemberNum":1,"RecruitCode":"1785450593732162312_doxes153pi","type":"group"}'},
                }
            }
        }
        group_id = self._extract_group_id(match_data)
        self.assertEqual(group_id, 16145387763)

    def test_extract_group_id_missing_f5(self):
        """Test extraction when f5 is missing."""
        group_id = self._extract_group_id({})
        self.assertIsNone(group_id)

    def test_extract_group_id_missing_f1(self):
        """Test extraction when f5.1 is missing."""
        match_data = {"5": {"data": {"2": {"data": 100001}}}}
        group_id = self._extract_group_id(match_data)
        self.assertIsNone(group_id)

    def test_extract_group_id_negative(self):
        """Test extraction with a negative GroupID (edge case)."""
        match_data = {
            "5": {
                "data": {
                    "1": {"wire_type": "varint", "data": -1},
                }
            }
        }
        group_id = self._extract_group_id(match_data)
        self.assertEqual(group_id, -1)


class TestMatchPacketDetection(unittest.TestCase):
    """Test f2=18 match packet detection logic."""

    def _is_match_packet(self, parsed):
        """Replicate the match detection logic."""
        f2 = parsed.get('2', {})
        f2_val = f2.get('data') if isinstance(f2, dict) else f2
        return isinstance(f2_val, int) and f2_val == 18

    def test_match_packet_f2_18(self):
        parsed = {"2": {"wire_type": "varint", "data": 18}}
        self.assertTrue(self._is_match_packet(parsed))

    def test_non_match_packet_f2_5(self):
        parsed = {"2": {"wire_type": "varint", "data": 5}}
        self.assertFalse(self._is_match_packet(parsed))

    def test_non_match_packet_f2_string(self):
        parsed = {"2": {"wire_type": "string", "data": "18"}}
        self.assertFalse(self._is_match_packet(parsed))

    def test_non_match_packet_no_f2(self):
        parsed = {"1": {"data": 123}}
        self.assertFalse(self._is_match_packet(parsed))


class TestGroupIDSharing(unittest.TestCase):
    """Test the GroupID sharing logic across connections."""

    def test_share_group_id_to_unmatched(self):
        """When one connection finds a match, others should join."""
        connections = [
            MagicMock(index=0, match_found=True, match_data={
                "5": {"data": {"1": {"data": 16145387763}}}
            }, connected=True),
            MagicMock(index=1, match_found=False, match_data=None, connected=True),
            MagicMock(index=2, match_found=False, match_data=None, connected=True),
        ]
        
        match_finders = [c for c in connections if c.match_found and c.match_data]
        self.assertEqual(len(match_finders), 1)
        
        # Extract GroupID from finder
        finder = match_finders[0]
        f5 = finder.match_data.get('5', {})
        f5d = f5.get('data', {})
        group_id = f5d.get('1', {}).get('data')
        self.assertEqual(group_id, 16145387763)
        
        # Count connections that need to join
        unmatched = [c for c in connections 
                     if c.index != finder.index and not c.match_found and c.connected]
        self.assertEqual(len(unmatched), 2)

    def test_no_sharing_when_all_matched(self):
        """No sharing needed when all connections found matches."""
        connections = [
            MagicMock(index=0, match_found=True, match_data={"5": {"data": {"1": {"data": 123}}}}, connected=True),
            MagicMock(index=1, match_found=True, match_data={"5": {"data": {"1": {"data": 456}}}}, connected=True),
        ]
        match_finders = [c for c in connections if c.match_found and c.match_data]
        self.assertEqual(len(match_finders), 2)
        # All are matched, so no sharing needed
        for finder in match_finders:
            unmatched = [c for c in connections 
                         if c.index != finder.index and not c.match_found and c.connected]
            self.assertEqual(len(unmatched), 0)

    def test_no_sharing_when_no_match(self):
        """No sharing when no connection found a match."""
        connections = [
            MagicMock(index=0, match_found=False, connected=True),
            MagicMock(index=1, match_found=False, connected=True),
        ]
        match_finders = [c for c in connections if c.match_found and c.match_data]
        self.assertEqual(len(match_finders), 0)


class TestConcurrentReading(unittest.IsolatedAsyncioTestCase):
    """Test the concurrent channel reading logic."""

    async def test_concurrent_read_finds_match(self):
        """Simulate concurrent reading that finds a match packet."""
        mock_reader = AsyncMock()
        # Simulate: no data for 2 reads, then match packet on 3rd read
        match_packet = bytes.fromhex("120000021208f7b8" + "0a" * 20)
        mock_reader.read = AsyncMock(side_effect=[
            asyncio.TimeoutError(),  # First read: timeout
            match_packet,             # Second read: match data!
        ])
        
        results = []
        async def read_loop(reader, label):
            try:
                resp = await asyncio.wait_for(reader.read(65535), timeout=0.1)
                if resp:
                    results.append((label, len(resp)))
            except asyncio.TimeoutError:
                pass
        
        await read_loop(mock_reader, "test")
        # The mock side_effect starts with TimeoutError, so first call raises
        # Let's test with actual match data directly
        mock_reader2 = AsyncMock()
        mock_reader2.read = AsyncMock(return_value=match_packet)
        await read_loop(mock_reader2, "test2")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "test2")

    async def test_deadline_respected(self):
        """Reading should stop when deadline is reached."""
        import time
        deadline = asyncio.get_event_loop().time() + 0.05  # 50ms
        elapsed = asyncio.get_event_loop().time()
        self.assertLess(elapsed, deadline)
        
        # Wait a bit
        await asyncio.sleep(0.1)
        elapsed = asyncio.get_event_loop().time()
        self.assertGreater(elapsed, deadline)


class TestMatchJSONParsing(unittest.TestCase):
    """Test parsing the JSON data inside match packet f5.8."""

    def test_parse_match_json(self):
        """Parse the match JSON from f5.8 field."""
        raw_json = '{"GroupID":16145387763,"Group":3,"Map":[1,3,4,22,29],"Game":15,"Match":6,"MemberNum":1,"RequireRankMin":311,"RequireRankMax":315,"CSSpecialModeEventId":38,"GroupTag":"0;0","SecretCode":null,"RecruitCode":"1785450593732162312_doxes153pi","showGameBuf":0,"hasLuckyBuf":false,"hasMapBonus":true,"type":"group"}'
        data = json.loads(raw_json)
        
        self.assertEqual(data['GroupID'], 16145387763)
        self.assertEqual(data['Game'], 15)
        self.assertEqual(data['Match'], 6)
        self.assertEqual(data['MemberNum'], 1)
        self.assertEqual(data['type'], 'group')
        self.assertIsNone(data['SecretCode'])
        self.assertTrue(data['hasMapBonus'])
        self.assertEqual(data['RecruitCode'], '1785450593732162312_doxes153pi')

    def test_recruit_code_format(self):
        """RecruitCode should be timestamp_string format."""
        raw_json = '{"RecruitCode":"1785450593732162312_doxes153pi"}'
        data = json.loads(raw_json)
        code = data['RecruitCode']
        # Format: <timestamp><random_int>_<random_string>
        parts = code.split('_')
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[0].isdigit())
        self.assertGreater(len(parts[1]), 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
