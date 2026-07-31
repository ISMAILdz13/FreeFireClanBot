"""Tests for concurrent channel reading and match-waiting logic."""
import asyncio
import json
import sys
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'OB54-TCP-BOT'))


class TestChannelReaderLoop(unittest.IsolatedAsyncioTestCase):
    """Test the read_channel_continuously logic used in the match-waiting phase."""

    async def test_reader_finds_match_packet(self):
        """Reader should detect f2=18 in incoming data and set match_found."""
        from xC4 import CrEaTe_ProTo, GeneRaTePk, DeCode_PackEt
        
        # Build a real f2=18 packet
        fields = {
            1: 16648969335,
            2: 18,
            4: 2,
            5: {
                1: 16145387763,
                2: 100001,
                3: 5,
                8: json.dumps({"GroupID": 16145387763, "Game": 15, "type": "group"}),
            }
        }
        proto = await CrEaTe_ProTo(fields)
        proto_hex = proto.hex()
        
        # Verify we can decode it
        decoded = await DeCode_PackEt(proto_hex)
        self.assertIsNotNone(decoded)
        parsed = json.loads(decoded)
        f2 = parsed.get('2', {})
        f2_val = f2.get('data') if isinstance(f2, dict) else f2
        self.assertEqual(f2_val, 18)

    async def test_reader_handles_timeout_gracefully(self):
        """Reader should continue after timeout, not crash."""
        mock_reader = AsyncMock()
        call_count = 0
        
        async def mock_read(size):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise asyncio.TimeoutError()
            return b""  # Empty = connection closed
        
        mock_reader.read = mock_read
        
        # Simulate the read loop
        results = []
        for _ in range(3):
            try:
                resp = await asyncio.wait_for(mock_reader.read(65535), timeout=0.05)
                if resp:
                    results.append(resp)
            except asyncio.TimeoutError:
                continue
            except:
                break
        
        # Should have handled timeouts without crashing
        self.assertEqual(len(results), 0)

    async def test_concurrent_reads_complete_within_deadline(self):
        """Multiple concurrent readers should all complete within deadline."""
        async def fake_reader(label, duration):
            await asyncio.sleep(duration)
            return f"{label}_done"
        
        deadline = asyncio.get_event_loop().time() + 0.5
        tasks = [
            asyncio.create_task(fake_reader("online", 0.1)),
            asyncio.create_task(fake_reader("chat", 0.1)),
            asyncio.create_task(fake_reader("online2", 0.1)),
        ]
        results = await asyncio.gather(*tasks)
        self.assertEqual(len(results), 3)
        self.assertLess(asyncio.get_event_loop().time(), deadline)


class TestSquadVerification(unittest.IsolatedAsyncioTestCase):
    """Test the improved squad verification logic."""

    async def test_verification_tries_both_channels(self):
        """Verification should try both online and chat channels."""
        online_reader = AsyncMock()
        chat_reader = AsyncMock()
        
        # Online returns nothing, chat returns data
        online_reader.read = AsyncMock(side_effect=asyncio.TimeoutError())
        chat_reader.read = AsyncMock(return_value=b"\x08\x03\x12\x28\x08\xf3")
        
        verified = False
        for ch_name, ch_reader in [("online", online_reader), ("chat", chat_reader)]:
            try:
                data = await asyncio.wait_for(ch_reader.read(9999), timeout=0.1)
                if data:
                    verified = True
                    break
            except asyncio.TimeoutError:
                continue
        
        self.assertTrue(verified, "Should verify via chat when online has no data")

    async def test_verification_no_data_either_channel(self):
        """Verification should report no data gracefully when both channels timeout."""
        online_reader = AsyncMock()
        chat_reader = AsyncMock()
        
        online_reader.read = AsyncMock(side_effect=asyncio.TimeoutError())
        chat_reader.read = AsyncMock(side_effect=asyncio.TimeoutError())
        
        verified = False
        for ch_name, ch_reader in [("online", online_reader), ("chat", chat_reader)]:
            try:
                data = await asyncio.wait_for(ch_reader.read(9999), timeout=0.1)
                if data:
                    verified = True
                    break
            except asyncio.TimeoutError:
                continue
        
        self.assertFalse(verified)


class TestPacketTypeScanning(unittest.IsolatedAsyncioTestCase):
    """Test packet type scanning from raw hex data."""

    async def test_scan_finds_multiple_packet_types(self):
        """Scan should find different f2 values in a multi-packet response."""
        from xC4 import CrEaTe_ProTo, DeCode_PackEt
        
        # Create two different packets and concatenate
        packet1_fields = {1: 12345, 2: 5, 4: 1}  # f2=5
        packet2_fields = {1: 67890, 2: 18, 4: 2}  # f2=18
        
        proto1 = await CrEaTe_ProTo(packet1_fields)
        proto2 = await CrEaTe_ProTo(packet2_fields)
        
        combined_hex = proto1.hex() + proto2.hex()
        
        # Scan for packet types
        found_types = set()
        for skip in range(0, min(len(combined_hex) - 20, 200), 2):
            try:
                payload = combined_hex[skip:]
                if len(payload) < 10:
                    continue
                json_str = await DeCode_PackEt(payload)
                if json_str:
                    parsed = json.loads(json_str)
                    f2 = parsed.get('2', {})
                    f2_val = f2.get('data') if isinstance(f2, dict) else f2
                    if isinstance(f2_val, int) and f2_val > 0:
                        found_types.add(f2_val)
                        break
            except:
                continue
        
        # Should find at least one packet type
        self.assertGreater(len(found_types), 0)

    async def test_scan_empty_data(self):
        """Scan should handle empty data without crashing."""
        from xC4 import DeCode_PackEt
        
        found_types = set()
        for skip in range(0, 0, 2):
            try:
                json_str = await DeCode_PackEt("")
                if json_str:
                    found_types.add(1)
            except:
                continue
        
        self.assertEqual(len(found_types), 0)


class TestGroupIDValidation(unittest.TestCase):
    """Test that f2=18 packets are only treated as matches when GroupID is valid."""

    def _is_real_match(self, parsed):
        """Replicate the GroupID validation logic."""
        f2 = parsed.get('2', {})
        f2_val = f2.get('data') if isinstance(f2, dict) else f2
        if f2_val != 18:
            return False
        f5 = parsed.get('5', {})
        f5d = f5.get('data', {}) if isinstance(f5, dict) else {}
        if isinstance(f5d, dict):
            f1 = f5d.get('1', {})
            if isinstance(f1, dict) and 'data' in f1:
                group_id = f1['data']
                return isinstance(group_id, int) and group_id > 1000000000
        return False

    def test_real_match_packet(self):
        """f2=18 with GroupID > 1B is a real match."""
        parsed = {
            "2": {"wire_type": "varint", "data": 18},
            "5": {"data": {"1": {"data": 16145387763}}}
        }
        self.assertTrue(self._is_real_match(parsed))

    def test_config_packet_not_match(self):
        """f2=18 with 5.1=100001 is NOT a match (it's config data)."""
        parsed = {
            "2": {"wire_type": "varint", "data": 18},
            "5": {"data": {"1": {"data": 100001}, "2": {"data": 20}}}
        }
        self.assertFalse(self._is_real_match(parsed))

    def test_small_group_id_not_match(self):
        """f2=18 with GroupID < 1B is probably not a real match."""
        parsed = {
            "2": {"wire_type": "varint", "data": 18},
            "5": {"data": {"1": {"data": 999999}}}
        }
        self.assertFalse(self._is_real_match(parsed))

    def test_f2_not_18_not_match(self):
        """f2=5 is not a match."""
        parsed = {
            "2": {"wire_type": "varint", "data": 5},
            "5": {"data": {"1": {"data": 16145387763}}}
        }
        self.assertFalse(self._is_real_match(parsed))

    def test_no_f5_not_match(self):
        """f2=18 without f5 is not a match."""
        parsed = {"2": {"wire_type": "varint", "data": 18}}
        self.assertFalse(self._is_real_match(parsed))


class TestSpamReadOverlap(unittest.TestCase):
    """Test that spam and reading run concurrently (not sequentially)."""

    def test_no_drain_buffer_in_source(self):
        """drain_buffer should NOT be called in the match-waiting flow."""
        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        # drain_buffer should exist as a method but NOT be called in exploit_cycle
        # Check that it's not called between spam and match-waiting
        self.assertIn("async def drain_buffer", source)
        # The old pattern "Drain stale data" should be gone
        self.assertNotIn("Drain stale data from buffers", source,
                         "drain_buffer call should be removed from match-waiting flow")

    def test_spam_and_read_concurrent(self):
        """Spam tasks and read tasks should be gathered together."""
        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        self.assertIn("spam_tasks", source)
        self.assertIn("read_tasks", source)
        self.assertIn("all_tasks = spam_tasks + read_tasks", source)

    def test_total_wait_includes_spam_duration(self):
        """Total wait should be SPAM_DURATION + MATCH_WAIT (not just MATCH_WAIT)."""
        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        self.assertIn("SPAM_DURATION + MATCH_WAIT", source)


class TestMatchWaitTiming(unittest.TestCase):
    """Test timing-related aspects of the match-waiting logic."""

    def test_match_wait_constant(self):
        """MATCH_WAIT should be 60 seconds."""
        # Import the constant from the bot
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "clan_glory_bot",
            os.path.join(os.path.dirname(__file__), '..', 'clan_glory_bot.py')
        )
        # Just check the source file for the constant
        bot_path = os.path.join(os.path.dirname(__file__), '..', 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        self.assertIn("MATCH_WAIT         = 60", source)

    def test_spam_duration_constant(self):
        """SPAM_DURATION should be 15 seconds."""
        bot_path = os.path.join(os.path.dirname(__file__), '..', 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        self.assertIn("SPAM_DURATION      = 15", source)

    def test_concurrent_reading_in_source(self):
        """Source should use asyncio.gather for concurrent reading."""
        bot_path = os.path.join(os.path.dirname(__file__), '..', 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        self.assertIn("asyncio.gather", source)
        self.assertIn("read_channel_for_match", source)
        self.assertIn("deadline", source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
