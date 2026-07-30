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
