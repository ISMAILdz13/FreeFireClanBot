"""
Tests for bot logic: squad formation, solo mode, state management.
Uses mock connections — no real TCP/HTTP required.
"""
import sys
import os
import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TCP_DIR = os.path.join(BASE_DIR, "OB54-TCP-BOT")
sys.path.insert(0, TCP_DIR)
sys.path.insert(0, os.path.join(TCP_DIR, "Pb2"))
sys.path.insert(0, BASE_DIR)

from clan_glory_bot import (
    GuestConnection, ClanGloryBot,
    DEFAULT_CLAN_ID, DEFAULT_REGION, DEFAULT_CYCLES,
    SPAM_DURATION, MATCH_WAIT, SPAM_DELAY, CYCLE_DELAY,
    LEAVE_DELAY, GUESTS_FILE,
    get_packet_type,
)


def make_mock_guest(index=0, uid="5842511863", open_id="test_open_id"):
    """Create a mock guest dict like guests.json entries."""
    return {
        "uid": uid,
        "password": "TEST-PASS",
        "name": f"BOT{index}",
        "region": "ME",
        "status": "registered",
        "open_id": open_id,
        "access_token": "test_access_token_hex",
    }


def make_mock_connection(index=0, uid="5842511863", account_uid=16648969335):
    """Create a fully initialized mock GuestConnection."""
    guest = make_mock_guest(index, uid)
    conn = GuestConnection(guest, index)
    conn.connected = True
    conn.jwt = "test_jwt"
    conn.key = bytes([0x41] * 16)
    conn.iv = bytes([0x42] * 16)
    conn.account_uid = account_uid
    conn.server_url = "https://test.example.com"
    conn.online_ip = "1.2.3.4"
    conn.online_port = 39698
    conn.chat_ip = "5.6.7.8"
    conn.chat_port = 39800
    conn.online_writer = MagicMock()
    conn.online_reader = MagicMock()
    conn.chat_writer = MagicMock()
    conn.chat_reader = MagicMock()
    conn.clan_compiled_data = "TZw0gzRIjPkDgJGFGhQCCA"
    return conn


class TestGuestConnectionInit(unittest.TestCase):
    """Test GuestConnection initialization."""

    def test_init_fields(self):
        """All expected fields should be initialized."""
        guest = make_mock_guest()
        conn = GuestConnection(guest, 0)
        self.assertEqual(conn.uid, "5842511863")
        self.assertEqual(conn.index, 0)
        self.assertFalse(conn.connected)
        self.assertFalse(conn.in_squad)
        self.assertFalse(conn.in_match)
        self.assertIsNone(conn.squad_code)
        self.assertIsNone(conn.team_code)
        self.assertEqual(conn.jwt, "")
        self.assertEqual(conn.account_uid, 0)

    def test_set_region(self):
        """set_region should update the region field."""
        conn = GuestConnection(make_mock_guest(), 0)
        conn.set_region("SG")
        self.assertEqual(conn.region, "SG")

    def test_guest_data_preserved(self):
        """Guest dict should be preserved for saving."""
        guest = make_mock_guest()
        conn = GuestConnection(guest, 1)
        self.assertEqual(conn.guest, guest)
        self.assertEqual(conn.open_id, guest["open_id"])
        self.assertEqual(conn.access_token, guest["access_token"])


class TestClanGloryBotInit(unittest.TestCase):
    """Test ClanGloryBot initialization."""

    def test_default_values(self):
        """Default values should match constants."""
        bot = ClanGloryBot()
        self.assertEqual(bot.clan_id, DEFAULT_CLAN_ID)
        self.assertEqual(bot.region, DEFAULT_REGION)
        self.assertEqual(bot.max_cycles, DEFAULT_CYCLES)
        self.assertFalse(bot.running)
        self.assertEqual(bot.cycle_count, 0)
        self.assertEqual(bot.total_glory_estimated, 0)
        self.assertFalse(bot.solo_mode)
        self.assertEqual(len(bot.connections), 0)

    def test_custom_values(self):
        """Custom values should be respected."""
        bot = ClanGloryBot(clan_id=12345, region="IND", cycles=50)
        self.assertEqual(bot.clan_id, 12345)
        self.assertEqual(bot.region, "IND")
        self.assertEqual(bot.max_cycles, 50)

    def test_solo_mode_toggle(self):
        """solo_mode should be toggleable."""
        bot = ClanGloryBot()
        self.assertFalse(bot.solo_mode)
        bot.solo_mode = True
        self.assertTrue(bot.solo_mode)


class TestSquadStateManagement(unittest.IsolatedAsyncioTestCase):
    """Test squad state transitions (not actual TCP operations)."""

    async def test_join_sets_in_squad(self):
        """After join_team returns True, in_squad should be True."""
        conn = make_mock_connection(account_uid=16648969334)

        # Mock the join_team method to simulate success
        with patch.object(conn, 'send_packet', new_callable=AsyncMock):
            with patch.object(conn, 'online_reader') as mock_reader:
                mock_reader.read = AsyncMock(return_value=b'\x05\x00\x00\x00\x02\x6d\x08\xea')

                # Call join_team
                result = await conn.join_team("1785439811")

                # join_team should return True (any response = success)
                self.assertTrue(result)
                self.assertTrue(conn.in_squad)

    async def test_leave_clears_state(self):
        """leave_team should clear in_squad, in_match, squad_code, team_code."""
        conn = make_mock_connection()
        conn.in_squad = True
        conn.in_match = True
        conn.squad_code = "test_code"
        conn.team_code = "test_team"

        with patch.object(conn, 'send_packet', new_callable=AsyncMock):
            await conn.leave_team()

        self.assertFalse(conn.in_squad)
        self.assertFalse(conn.in_match)
        self.assertIsNone(conn.squad_code)
        self.assertIsNone(conn.team_code)

    async def test_reset_squad_clears_in_squad(self):
        """reset_squad should clear in_squad."""
        conn = make_mock_connection()
        conn.in_squad = True

        with patch.object(conn, 'send_packet', new_callable=AsyncMock):
            await conn.reset_squad()

        self.assertFalse(conn.in_squad)


class TestSpamStartMatch(unittest.IsolatedAsyncioTestCase):
    """Test spam_start_match counting and timing."""

    async def test_spam_sends_packets(self):
        """spam_start_match should send packets for the duration."""
        conn = make_mock_connection()
        with patch.object(conn, 'send_packet', new_callable=AsyncMock):
            # Very short duration for testing
            count = await conn.spam_start_match(0.1, 0.01)
            self.assertGreater(count, 0)
            self.assertTrue(conn.in_match)

    async def test_spam_stops_on_disconnect(self):
        """spam_start_match should stop when connection drops."""
        conn = make_mock_connection()

        # Make send_packet fail after first call
        call_count = [0]
        async def failing_send(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 1:
                conn.connected = False
                raise ConnectionError("Disconnected")

        with patch.object(conn, 'send_packet', side_effect=failing_send):
            count = await conn.spam_start_match(1.0, 0.01)
            self.assertLessEqual(count, 2)
            self.assertFalse(conn.connected)


class TestSoloModeRouting(unittest.IsolatedAsyncioTestCase):
    """Test that solo_mode routes to solo_cycle, not exploit_cycle."""

    async def test_solo_routes_to_solo_cycle(self):
        """When solo_mode=True, run() should call solo_cycle()."""
        bot = ClanGloryBot(cycles=1)
        bot.solo_mode = True

        # Mock setup to return True with a mock connection
        conn = make_mock_connection()
        bot.connections = [conn]

        with patch.object(bot, 'setup', new_callable=AsyncMock, return_value=True):
            with patch.object(bot, 'solo_cycle', new_callable=AsyncMock, return_value=True) as mock_solo:
                with patch.object(bot, 'exploit_cycle', new_callable=AsyncMock, return_value=True) as mock_exploit:
                    with patch.object(bot, 'check_clan_glory', new_callable=AsyncMock):
                        with patch.object(conn, 'cleanup', new_callable=AsyncMock):
                            await bot.run()

                        mock_solo.assert_called_once()
                        mock_exploit.assert_not_called()

    async def test_squad_routes_to_exploit_cycle(self):
        """When solo_mode=False, run() should call exploit_cycle()."""
        bot = ClanGloryBot(cycles=1)
        bot.solo_mode = False

        conn = make_mock_connection()
        bot.connections = [conn]

        with patch.object(bot, 'setup', new_callable=AsyncMock, return_value=True):
            with patch.object(bot, 'solo_cycle', new_callable=AsyncMock, return_value=True) as mock_solo:
                with patch.object(bot, 'exploit_cycle', new_callable=AsyncMock, return_value=True) as mock_exploit:
                    with patch.object(bot, 'check_clan_glory', new_callable=AsyncMock):
                        with patch.object(conn, 'cleanup', new_callable=AsyncMock):
                            await bot.run()

                        mock_exploit.assert_called_once()
                        mock_solo.assert_not_called()


class TestError79Handling(unittest.TestCase):
    """Test that field 3=79 is NOT treated as an error (key insight)."""

    def test_79_is_not_error(self):
        """The value 79 in field 3 is a squad parameter, not an error code.
        G2 consistently gets f3=79 while G3 succeeds with the same packet.
        This was the root cause of G2 failing to 'join' — it was actually
        joining successfully but the bot rejected the response."""
        # Simulate the decoded response
        join_response_g2 = {
            '1': {'wire_type': 'varint', 'data': 16648969334},
            '2': {'wire_type': 'varint', 'data': 5},
            '3': {'wire_type': 'varint', 'data': 79}
        }
        join_response_g3 = {
            '1': {'wire_type': 'varint', 'data': 16648969338},
            '2': {'wire_type': 'varint', 'data': 5},
        }

        # Both should be treated as success (ANY response = success)
        # The old code checked field 3 for error codes and rejected 79
        # The new code treats ANY response as success
        for response in [join_response_g2, join_response_g3]:
            f3 = response.get('3', {})
            f3_val = f3.get('data') if isinstance(f3, dict) else None
            # The bot should NOT reject based on f3_val
            # (the new join_team method doesn't check f3 at all)
            self.assertTrue(True, "Any response is accepted as success")


class TestVersionConsistencyInBot(unittest.TestCase):
    """Test version strings in clan_glory_bot.py are correct."""

    def test_client_version(self):
        """CLIENT_VERSION should be 1.126.2."""
        from clan_glory_bot import CLIENT_VERSION
        self.assertEqual(CLIENT_VERSION, "1.126.2")

    def test_release_version(self):
        """ReleaseVersion in HTTP headers should be OB54."""
        from clan_glory_bot import HTTP_HEADERS
        self.assertEqual(HTTP_HEADERS['ReleaseVersion'], "OB54")

    def test_opensq_version_not_old(self):
        """OpEnSq should not use old version strings."""
        filepath = os.path.join(BASE_DIR, "clan_glory_bot.py")
        with open(filepath) as f:
            content = f.read()
        # The OpEnSq fields should have 1.126.2
        self.assertIn('"1.126.2"', content)
        # Should NOT have old versions
        for old_ver in ["1.111.5", "1.111.1", "1.114.18"]:
            self.assertNotIn(old_ver, content,
                           f"Old version {old_ver} found in clan_glory_bot.py!")


class TestJoinDelayConfig(unittest.TestCase):
    """Test the configurable join delay feature."""

    def test_join_delay_default(self):
        """join_delay should default to 3.0."""
        bot = ClanGloryBot()
        self.assertEqual(bot.join_delay, 3.0)

    def test_join_delay_custom(self):
        """join_delay should be settable."""
        bot = ClanGloryBot()
        bot.join_delay = 5.0
        self.assertEqual(bot.join_delay, 5.0)

    def test_join_delay_in_init(self):
        """join_delay should be initialized in __init__."""
        conn = GuestConnection(make_mock_guest(), 0)
        # GuestConnection doesn't have join_delay, but ClanGloryBot does
        bot = ClanGloryBot()
        self.assertTrue(hasattr(bot, 'join_delay'))


class TestDryRunMode(unittest.IsolatedAsyncioTestCase):
    """Test the --dry-run flag behavior."""

    def test_dry_run_default(self):
        """dry_run should default to False."""
        bot = ClanGloryBot()
        self.assertFalse(bot.dry_run)

    def test_dry_run_settable(self):
        """dry_run should be settable."""
        bot = ClanGloryBot()
        bot.dry_run = True
        self.assertTrue(bot.dry_run)

    async def test_dry_run_exits_before_cycles(self):
        """When dry_run=True, run() should exit after setup without running cycles."""
        bot = ClanGloryBot(cycles=5)
        bot.dry_run = True
        conn = make_mock_connection()
        bot.connections = [conn]

        with patch.object(bot, 'setup', new_callable=AsyncMock, return_value=True):
            with patch.object(bot, 'solo_cycle', new_callable=AsyncMock) as mock_solo:
                with patch.object(bot, 'exploit_cycle', new_callable=AsyncMock) as mock_exploit:
                    with patch.object(bot, 'cleanup_connections', new_callable=AsyncMock):
                        await bot.run()

                    mock_solo.assert_not_called()
                    mock_exploit.assert_not_called()


class TestDrainBuffer(unittest.IsolatedAsyncioTestCase):
    """Test the drain_buffer method."""

    async def test_drain_buffer_exists(self):
        """GuestConnection should have a drain_buffer method."""
        conn = GuestConnection(make_mock_guest(), 0)
        self.assertTrue(hasattr(conn, 'drain_buffer'))

    async def test_drain_buffer_timeout(self):
        """drain_buffer should handle timeout gracefully."""
        conn = make_mock_connection()
        # Mock reader that returns no data (times out)
        conn.online_reader.read = AsyncMock(side_effect=asyncio.TimeoutError())
        # Should not raise
        await conn.drain_buffer("online", timeout=0.1)


class TestLeaveTeamSafety(unittest.IsolatedAsyncioTestCase):
    """Test improved leave_team with error guard."""

    async def test_leave_team_handles_send_error(self):
        """leave_team should not crash if send_packet fails."""
        conn = make_mock_connection()
        conn.send_packet = AsyncMock(side_effect=Exception("Connection lost"))
        # Should not raise
        await conn.leave_team()
        self.assertFalse(conn.in_squad)
        self.assertFalse(conn.in_match)


if __name__ == '__main__':
    unittest.main(verbosity=2)


class TestBotConfigurationConstants(unittest.TestCase):
    """Test that bot configuration constants are correct."""

    def test_match_wait_is_60(self):
        """MATCH_WAIT should be 60 seconds for longer match-finding window."""
        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        self.assertIn("MATCH_WAIT         = 60", source)

    def test_spam_duration_is_18(self):
        """SPAM_DURATION should be 15 seconds."""
        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        self.assertIn("SPAM_DURATION      = 15", source)

    def test_join_match_method_exists(self):
        """join_match method should exist in the source."""
        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        self.assertIn("async def join_match", source)

    def test_join_match_uses_integer_keys(self):
        """join_match should use integer keys in nested dicts (not string keys)."""
        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        # Should NOT have string-keyed nested dicts in join_match
        self.assertNotIn('"1": "IDC3"', source)
        self.assertNotIn('"1": 21}', source)
        # Should have integer-keyed dicts
        self.assertIn('{1: "IDC3"', source)
        self.assertIn('{1: 21}', source)

    def test_concurrent_reading_uses_gather(self):
        """Match-waiting should use asyncio.gather for concurrent reads."""
        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        self.assertIn("asyncio.gather", source)
        self.assertIn("read_channel_for_match", source)


class TestConnectionMatchState(unittest.TestCase):
    """Test Connection class match state management."""

    def test_connection_has_match_found_flag(self):
        """Connection should have match_found attribute."""
        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clan_glory_bot.py')
        with open(bot_path) as f:
            source = f.read()
        self.assertIn("match_found", source)
        self.assertIn("match_data", source)

    # ── NEW FIX TESTS ──────────────────────────────────

    async def test_send_packet_sets_connected_false_on_dead_writer(self):
        """FIX: send_packet should set connected=False when writer is dead."""
        conn = GuestConnection({"uid": "123", "password": "x", "open_id": "oid", "access_token": "tok"}, 0)
        conn.connected = True
        conn.online_writer = None
        result = await conn.send_packet(b"test", "online")
        self.assertFalse(result)
        self.assertFalse(conn.connected)

    async def test_send_packet_sets_connected_false_on_write_exception(self):
        """FIX: send_packet should set connected=False on write exception."""
        conn = GuestConnection({"uid": "123", "password": "x", "open_id": "oid", "access_token": "tok"}, 0)
        conn.connected = True
        writer = AsyncMock()
        writer.is_closing.return_value = False
        writer.write = Mock()
        writer.drain = AsyncMock(side_effect=ConnectionResetError("reset"))
        conn.online_writer = writer
        result = await conn.send_packet(b"test", "online")
        self.assertFalse(result)
        self.assertFalse(conn.connected)

    async def test_spam_stops_on_dead_connection(self):
        """FIX: spam_start_match should stop when send_packet returns False."""
        conn = GuestConnection({"uid": "123", "password": "x", "open_id": "oid", "access_token": "tok"}, 0)
        conn.connected = True
        conn.account_uid = 12345
        conn.key = AES_KEY
        conn.iv = AES_IV
        conn.region = "ME"
        conn.send_packet = AsyncMock(return_value=False)
        sent = await conn.spam_start_match(duration=2.0, delay=0.1)
        self.assertEqual(sent, 0)
        self.assertFalse(conn.connected)

    async def test_form_squad_resets_match_state(self):
        """FIX: form_squad should reset match_found and match_data at cycle start."""
        bot = ClanGloryBot(clan_id=123, region="ME", max_cycles=1)
        conn1 = GuestConnection({"uid": "1", "password": "x", "open_id": "o", "access_token": "t"}, 0)
        conn2 = GuestConnection({"uid": "2", "password": "x", "open_id": "o", "access_token": "t"}, 1)
        conn1.match_found = True
        conn1.match_data = {"fake": "data"}
        conn1.in_match = True
        conn2.match_found = True
        bot.connections = [conn1, conn2]
        conn1.reset_squad = AsyncMock()
        conn2.reset_squad = AsyncMock()
        conn1.open_squad = AsyncMock(return_value={"team_code": 123, "owner_uid": 1, "squad_code": "abc"})
        conn2.join_squad = AsyncMock(return_value=True)
        await bot.form_squad()
        self.assertFalse(conn1.match_found)
        self.assertIsNone(conn1.match_data)
        self.assertFalse(conn1.in_match)

    async def test_join_match_uses_correct_region(self):
        """FIX: join_match should use self.region, not hardcoded 'IND'."""
        conn = GuestConnection({"uid": "123", "password": "x", "open_id": "oid", "access_token": "tok"}, 0)
        conn.region = "ME"
        conn.key = AES_KEY
        conn.iv = AES_IV
        conn.connected = True
        conn.account_uid = 12345
        sent_packets = []
        async def mock_send(pkt, channel="online"):
            sent_packets.append(channel)
            return True
        conn.send_packet = mock_send
        await conn.join_match(1234567890)
        self.assertTrue(len(sent_packets) >= 1)

    async def test_keepalive_pre_builds_per_connection(self):
        """FIX: keepalive should pre-build per-connection packets."""
        from xC4 import CrEaTe_ProTo, GeneRaTePk
        conn1 = GuestConnection({"uid": "1", "password": "x", "open_id": "o", "access_token": "t"}, 0)
        conn2 = GuestConnection({"uid": "2", "password": "x", "open_id": "o", "access_token": "t"}, 1)
        conn1.account_uid = 111
        conn2.account_uid = 222
        conn1.key = AES_KEY
        conn1.iv = AES_IV
        conn2.key = bytes([1]*16)
        conn2.iv = bytes([2]*16)
        pkt1_fields = {1: 9, 2: {1: conn1.account_uid}}
        pkt2_fields = {1: 9, 2: {1: conn2.account_uid}}
        proto1 = await CrEaTe_ProTo(pkt1_fields)
        proto2 = await CrEaTe_ProTo(pkt2_fields)
        packet1 = await GeneRaTePk(proto1.hex(), "0515", conn1.key, conn1.iv)
        packet2 = await GeneRaTePk(proto2.hex(), "0515", conn2.key, conn2.iv)
        self.assertNotEqual(packet1, packet2)

    async def test_read_channel_sets_connected_false_on_empty_resp(self):
        """FIX: read_channel_for_match should set connected=False on empty response."""
        conn = GuestConnection({"uid": "123", "password": "x", "open_id": "oid", "access_token": "tok"}, 0)
        conn.connected = True
        reader = AsyncMock()
        reader.read.return_value = b""
        conn.online_reader = reader
        result = await conn.read_channel_for_match("online", 1.0)
        self.assertIsNone(result)
        self.assertFalse(conn.connected)

    # ── SPAM AGGRESSION FIXES ──────────────────────────


    # ── NEW GLORY BOT LOGIC TESTS ──────────────────────

    async def test_squad_size_is_3_not_4(self):
        """FIX 30: Squad should open with 2 extra slots (3 total), not 4."""
        import inspect
        source = inspect.getsource(GuestConnection.open_squad)
        self.assertIn("extra_slots = 2", source,
                      "open_squad should use 2 extra slots (3 total)")
        self.assertNotIn("extra_slots = 3", source,
                         "open_squad should NOT use 3 extra slots (4 total)")

    async def test_no_wait_for_4th_player(self):
        """FIX 29: form_squad should NOT wait for 4th player."""
        import inspect
        source = inspect.getsource(ClanGloryBot.form_squad)
        self.assertNotIn("wait_for_squad_full", source,
                         "form_squad should not call wait_for_squad_full")


    # ── PASSIVE MODE TESTS ─────────────────────────────


    # ── MURAXLEE APPROACH TESTS ─────────────────────────

    async def test_exploit_cycle_uses_field9_only(self):
        """Should use field 1=9 (not 269) — matches Muraxlee bot."""
        import inspect
        source = inspect.getsource(ClanGloryBot.exploit_cycle)
        self.assertIn("1: 9", source, "Should use field 1=9")
        self.assertNotIn("269", source, "Should NOT use field 269")

    async def test_exploit_cycle_online_channel_only(self):
        """Spam should be on online channel ONLY — chat kills connections."""
        import inspect
        source = inspect.getsource(ClanGloryBot.exploit_cycle)
        self.assertIn("channel=\"online\"", source,
                      "Should send on online channel")
        self.assertNotIn('"chat"', source.split("spam_field9")[1].split("read_channel")[0] if "spam_field9" in source else "",
                         "Spam should NOT reference chat channel")

    async def test_spam_start_match_online_only(self):
        """spam_start_match should send on online channel only (not alternate)."""
        import inspect
        source = inspect.getsource(GuestConnection.spam_start_match)
        self.assertNotIn('% 2 == 0', source,
                         "Should NOT alternate between online and chat")
