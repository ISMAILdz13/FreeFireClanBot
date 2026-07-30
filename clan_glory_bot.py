"""
Clan Glory Bot — Clash Squad Exit Glitch Exploit
==================================================
Exploit: Enter Clash Squad match with clan members, immediately exit after
match starts. System awards glory points for participation even on exit/loss.
Repeat hundreds of times for fast glory farming.

Flow per cycle (~30-60 seconds):
  1. Squad leader opens squad -> server returns squad_code
  2. Members join using squad_code (NOT leader UID)
  3. Squad leader queues Clash Squad match
  4. Wait for match to start (matchmaking delay)
  5. ALL members immediately exit/withdraw
  6. Glory points credited for participation
  7. Re-queue immediately

Usage:
  python3 clan_glory_bot.py --clan-id 3100938923 --region ME --cycles 200

Requirements:
  - 2+ guest accounts in data/guests.json
  - All guests must be members of the target clan
  - Termux: pip install pycryptodome aiohttp
"""

import asyncio
import json
import os
import sys
import time
import random
import ssl
import signal
from datetime import datetime
from typing import Optional, List

# ======================== PATH SETUP ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TCP_DIR = os.path.join(BASE_DIR, "OB54-TCP-BOT")
sys.path.insert(0, TCP_DIR)
sys.path.insert(0, os.path.join(TCP_DIR, "Pb2"))
sys.path.insert(0, os.path.join(BASE_DIR, "src", "proto", "compiled"))

import aiohttp
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from Pb2 import MajoRLoGinrEq_pb2, MajoRLoGinrEs_pb2, PorTs_pb2
from xC4 import (
    CrEaTe_ProTo, EnC_PacKeT_sync, GeneRaTePk, DecodE_HeX,
    AuthClan, OpEnSq, SEnd_InV, GenJoinSquadsPacket, ExiT,
    AutH_GlobAl, EnC_Uid, EnC_Vr,
    DeCode_PackEt, DEc_PacKeT, GeTSQDaTa
)

# ======================== CONFIG ========================

AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

DEFAULT_CLAN_ID    = 3100938923
DEFAULT_REGION     = "ME"
DEFAULT_CYCLES     = 200
MATCHMAKING_WAIT   = 15   # seconds to wait for match to start
POST_EXIT_WAIT     = 5    # seconds after exit for glory to credit
REQUEUE_DELAY      = 3    # seconds between cycles
RECONNECT_DELAY    = 3
PACKET_INTERVAL    = 0.5  # seconds between TCP packets

# Region to packet type mapping
REGION_PACKETS = {"ind": "0514", "bd": "0519"}
DEFAULT_PACKET = "0515"

GUESTS_FILE = os.path.join(BASE_DIR, "data", "guests.json")

# ======================== HTTP API ========================

HTTP_HEADERS = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    'Connection': "Keep-Alive", 'Accept-Encoding': "gzip",
    'Content-Type': "application/octet-stream", 'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1", 'X-GA': "v1 1", 'ReleaseVersion': "OB54",
}

OAUTH_CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
OAUTH_V2_URL = "https://ffmconnect.live.gop.garenanow.com/api/v2/oauth/guest/token:grant"
OAUTH_V1_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
PORTS_URL = "https://loginbp.ggpolarbear.com/api/ports"
MAJOR_LOGIN_URL = "https://loginbp.ggpolarbear.com/MajorLogin"
CLAN_JOIN_URL = "https://clientbp.ggpolarbear.com/RequestClan"


def get_packet_type(region: str) -> str:
    r = region.lower()
    if r in REGION_PACKETS:
        return REGION_PACKETS[r]
    return DEFAULT_PACKET


async def refresh_oauth_token(guest: dict) -> tuple:
    """Refresh OAuth access_token + open_id via v2, fallback to v1."""
    uid = guest["uid"]
    password = guest["password"]
    try:
        async with aiohttp.ClientSession() as session:
            # Try v2
            async with session.post(OAUTH_V2_URL, json={
                "client_id": 100067, "client_secret": OAUTH_CLIENT_SECRET,
                "client_type": 2, "password": password,
                "response_type": "token", "uid": int(uid)
            }, headers={"Content-Type": "application/json; charset=utf-8",
                        "User-Agent": "GarenaMSDK/4.0.19P10(I2404 ;Android 15;en;US;)"},
                       ssl=False, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    odata = data.get("data", data)
                    at = odata.get("access_token")
                    oid = odata.get("open_id")
                    if at and oid:
                        return at, oid
            # Fallback to v1
            async with session.post(OAUTH_V1_URL, data={
                "uid": uid, "password": password, "response_type": "token",
                "client_type": "2", "client_secret": OAUTH_CLIENT_SECRET,
                "client_id": "100067"
            }, headers={"Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "GarenaMSDK/4.0.19P8(ASUS_Z01QD ;Android 12;en;US;)"},
                       ssl=False, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    at = data.get("access_token")
                    oid = data.get("open_id")
                    if at and oid:
                        return at, oid
    except Exception as e:
        print(f"  OAuth error: {e}")
    return None, None


async def build_major_login(open_id: str, access_token: str) -> bytes:
    """Build encrypted MajorLogin request."""
    from MajoRLoGinrEq_pb2 import MajorLogin
    ml = MajorLogin()
    ml.event_time = str(datetime.now())[:-7]
    ml.game_name = "free fire"
    ml.platform_id = 2
    ml.client_version = "1.126.2"
    ml.client_version_code = "2024010012"
    ml.system_software = "Android OS 11 / API-30"
    ml.system_hardware = "Handheld"
    ml.device_type = "Handheld"
    ml.open_id = open_id
    ml.open_id_type = "4"
    ml.access_token = access_token
    ml.platform_sdk_id = 2
    ml.login_by = 3
    ml.login_open_id_type = 4
    ml.origin_platform_type = "4"
    ml.primary_platform_type = "4"
    enc = AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(ml.SerializeToString(), 16))
    return enc


async def get_login_data(jwt: str, server_url: str, access_token: str) -> dict:
    """Get login data (whisper_ip:port + online_ip:port) via HTTP."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(server_url, data=jwt, headers={
                **HTTP_HEADERS, "Authorization": f"Bearer {access_token}"
            }, ssl=False, timeout=aiohttp.ClientTimeout(total=20)) as r:
                if r.status == 200:
                    data = await r.read()
                    from MajoRLoGinrEs_pb2 import MajorLoginRes
                    res = MajorLoginRes()
                    res.ParseFromString(data)
                    return {
                        "whisper_ip": res.whisper_server_ip,
                        "whisper_port": res.whisper_server_port,
                        "online_ip": res.online_server_ip,
                        "online_port": res.online_server_port,
                        "server_url": server_url,
                    }
    except Exception as e:
        print(f"  Login data error: {e}")
    return {}


async def auto_join_clan(session: aiohttp.ClientSession, jwt: str, clan_id: int,
                         server_url: str, index: int):
    """Send HTTP RequestClan to join the target clan."""
    try:
        # Build a simple protobuf: field 1 = clan_id
        fields = {1: int(clan_id)}
        proto = await CrEaTe_ProTo(fields)
        enc_hex = EnC_PacKeT_sync(proto.hex(), AES_KEY, AES_IV)
        async with session.post("https://clientbp.ggpolarbear.com/RequestClan",
            data=bytes.fromhex(enc_hex),
            headers={**HTTP_HEADERS, "Authorization": f"Bearer {jwt}"},
            ssl=False, timeout=aiohttp.ClientTimeout(total=15)) as r:
            status = r.status
            if status == 200:
                print(f"  [G{index+1}] Joined clan {clan_id} (HTTP)")
            else:
                print(f"  [G{index+1}] Clan join HTTP {status}")
    except Exception as e:
        print(f"  [G{index+1}] Clan join error: {e}")


# ======================== TCP CONNECTION ========================

class GuestConnection:
    """Manages TCP connections (Online + Chat) for a single guest account."""

    def __init__(self, guest: dict, index: int):
        self.guest = guest
        self.index = index
        self.uid = guest["uid"]
        self.password = guest.get("password", "")
        self.access_token = guest.get("access_token", "")
        self.open_id = guest.get("open_id", "")
        self.jwt = ""
        self.key = b""
        self.iv = b""
        self.account_uid = 0
        self.server_url = ""
        self.whisper_ip = ""
        self.whisper_port = 0
        self.online_ip = ""
        self.online_port = 0
        self.online_writer = None
        self.online_reader = None
        self.chat_writer = None
        self.chat_reader = None
        self.connected = False
        self.in_squad = False
        self.in_match = False
        self.match_started = False
        self.squad_code = None
        self._listen_task = None

    async def authenticate(self, session: aiohttp.ClientSession) -> bool:
        """Full OAuth -> MajorLogin -> GetLoginData chain."""
        print(f"  [G{self.index+1}] UID {self.uid}: Auth...")

        # Refresh OAuth token
        at, oid = await refresh_oauth_token(self.guest)
        if at:
            self.access_token = at
            self.open_id = oid
            self.guest["access_token"] = at
            self.guest["open_id"] = oid
        else:
            at = self.access_token
            oid = self.open_id

        # MajorLogin
        payload = await build_major_login(oid, at)
        try:
            async with session.post(MAJOR_LOGIN_URL, data=payload, headers={
                **HTTP_HEADERS, "Authorization": f"Bearer {at}"
            }, ssl=False, timeout=aiohttp.ClientTimeout(total=20)) as r:
                if r.status != 200:
                    print(f"  [G{self.index+1}] MajorLogin FAIL (HTTP {r.status})")
                    return False
                data = await r.read()
                from MajoRLoGinrEs_pb2 import MajorLoginRes
                res = MajorLoginRes()
                res.ParseFromString(data)
                self.jwt = res.token
                self.key = bytes(res.secret_key, 'utf-8')
                self.iv = bytes(res.secret_iv, 'utf-8')
                self.server_url = res.server
                # Parse account UID from JWT (it's encoded in the token)
                self.account_uid = res.uid if hasattr(res, 'uid') else 0
                print(f"  [G{self.index+1}] JWT OK uid={self.account_uid}")
        except Exception as e:
            print(f"  [G{self.index+1}] MajorLogin FAIL: {e}")
            return False

        # Get login data (ports + IPs)
        login_data = await get_login_data(self.jwt, self.server_url, at)
        if not login_data:
            print(f"  [G{self.index+1}] No login data")
            return False

        self.whisper_ip = login_data.get("whisper_ip", "")
        self.whisper_port = login_data.get("whisper_port", 0)
        self.online_ip = login_data.get("online_ip", "")
        self.online_port = login_data.get("online_port", 0)

        if not self.online_ip:
            # Parse ports from PorTs_pb2
            try:
                async with session.post(PORTS_URL, data=self.jwt, headers={
                    **HTTP_HEADERS, "Authorization": f"Bearer {at}"
                }, ssl=False, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status == 200:
                        from PorTs_pb2 import Ports
                        ports = Ports()
                        ports.ParseFromString(await r.read())
                        self.whisper_ip = ports.whisper_server_ip
                        self.whisper_port = ports.whisper_server_port
                        self.online_ip = ports.online_server_ip
                        self.online_port = ports.online_server_port
            except:
                pass

        if not self.online_ip:
            print(f"  [G{self.index+1}] No TCP endpoints")
            return False

        print(f"  [G{self.index+1}] TCP: {self.online_ip}:{self.online_port} | {self.whisper_ip}:{self.whisper_port}")
        return True

    async def connect_tcp(self) -> bool:
        """Connect to Online + Chat TCP servers."""
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        try:
            # Online connection
            self.online_reader, self.online_writer = await asyncio.open_connection(
                self.online_ip, self.online_port, ssl=ssl_ctx)
            # Chat (Whisper) connection
            self.chat_reader, self.chat_writer = await asyncio.open_connection(
                self.whisper_ip, self.whisper_port, ssl=ssl_ctx)

            # Send auth token on both
            if self.jwt:
                token_bytes = bytes.fromhex(self.jwt) if all(c in '0123456789abcdef' for c in self.jwt) else self.jwt.encode()
                self.online_writer.write(token_bytes)
                await self.online_writer.drain()
                self.chat_writer.write(token_bytes)
                await self.chat_writer.drain()

            await asyncio.sleep(1)

            # Send global auth
            await self.send_global_auth()

            self.connected = True
            print(f"  [G{self.index+1}] TCP OK")
            return True
        except Exception as e:
            print(f"  [G{self.index+1}] TCP connect FAIL: {e}")
            self.connected = False
            return False

    async def send_packet(self, packet: bytes, channel: str = "online"):
        """Send a raw TCP packet."""
        writer = self.online_writer if channel == "online" else self.chat_writer
        if writer and not writer.is_closing():
            writer.write(packet)
            await writer.drain()
            return True
        return False

    async def send_global_auth(self):
        """Send AutH_GlobAl packet — required after TCP connect."""
        packet = await AutH_GlobAl(self.key, self.iv)
        await self.send_packet(packet, "chat")
        await asyncio.sleep(PACKET_INTERVAL)

    async def join_clan(self, clan_id: int):
        """AuthClan — join guild (sent to CHAT channel)."""
        auth_data = self.clan_compiled_data if hasattr(self, 'clan_compiled_data') and self.clan_compiled_data else self.jwt
        packet = await AuthClan(clan_id, auth_data, self.key, self.iv)
        await self.send_packet(packet, channel="chat")
        await asyncio.sleep(PACKET_INTERVAL)

    async def open_squad(self, region: str) -> str:
        """
        OpEnSq — leader opens squad for matchmaking.
        READS the server response to extract the squad_code.
        Returns the squad_code or None on failure.
        """
        packet = await OpEnSq(self.key, self.iv, region)
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)
        self.in_squad = True

        # Read the server response to get the squad_code
        squad_code = await self.read_squad_code()
        if squad_code:
            self.squad_code = squad_code
            print(f"  [G{self.index+1}] Squad opened, code: {squad_code[:20]}...")
        else:
            print(f"  [G{self.index+1}] Squad opened but no code in response — using UID fallback")
            self.squad_code = str(self.account_uid)
        return self.squad_code

    async def read_squad_code(self, timeout: float = 5.0) -> Optional[str]:
        """
        Read TCP response from Online channel, decode it, extract squad_code.
        Tries both raw parse and decrypted parse.
        """
        try:
            data = await asyncio.wait_for(self.online_reader.read(9999), timeout=timeout)
            if not data:
                return None
            data_hex = data.hex()

            # Skip header (first 10 hex chars = 5 bytes: packet_type + length)
            payload_hex = data_hex[10:]

            # Try 1: parse without decryption (some packets may be unencrypted)
            try:
                json_str = await DeCode_PackEt(payload_hex)
                if json_str:
                    packet_json = json.loads(json_str)
                    # Check if this has squad data (field 5 with nested data)
                    if '5' in packet_json and 'data' in packet_json.get('5', {}):
                        try:
                            uid, chat_code, squad_code = await GeTSQDaTa(packet_json)
                            return str(squad_code)
                        except:
                            pass
                    # Also check for field 1 = 1 (OpEnSq response)
                    if packet_json.get('1') == 1 and '2' in packet_json:
                        # May contain squad info
                        pass
            except:
                pass

            # Try 2: decrypt first, then parse
            try:
                decrypted_hex = await DEc_PacKeT(payload_hex, self.key, self.iv)
                json_str = await DeCode_PackEt(decrypted_hex)
                if json_str:
                    packet_json = json.loads(json_str)
                    if '5' in packet_json and 'data' in packet_json.get('5', {}):
                        try:
                            uid, chat_code, squad_code = await GeTSQDaTa(packet_json)
                            return str(squad_code)
                        except:
                            pass
            except:
                pass

            return None
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            return None

    async def send_invite(self, target_uid: int, region: str):
        """SEnd_InV — invite a player to squad."""
        packet = await SEnd_InV(1, target_uid, self.key, self.iv, region)
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)

    async def join_squad(self, squad_code: str):
        """GenJoinSquadsPacket — join existing squad using the squad_code."""
        packet = await GenJoinSquadsPacket(squad_code, self.key, self.iv)
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)
        self.in_squad = True

    async def start_clash_squad(self, region: str):
        """
        Queue for Clash Squad match.
        Uses FS packet (field 1=9) which starts matchmaking.
        """
        # Build match start packet — field 1 = 9 (start match)
        fields = {
            1: 9,
            2: {
                1: self.account_uid,
            }
        }
        proto_bytes = await CrEaTe_ProTo(fields)
        pkt_type = get_packet_type(region)
        packet = await GeneRaTePk(proto_bytes.hex(), pkt_type, self.key, self.iv)
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)
        self.in_match = True

    async def exit_match(self):
        """ExiT — immediately withdraw from match (the exploit)."""
        packet = await ExiT(self.account_uid, self.key, self.iv)
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)
        self.in_match = False

    async def listen_online(self):
        """Background reader for Online TCP — detect match start/end + squad data."""
        while self.connected and self.online_reader:
            try:
                data = await asyncio.wait_for(self.online_reader.read(9999), timeout=120)
                if not data:
                    print(f"  [G{self.index+1}] Online closed by server")
                    self.connected = False
                    break
                hex_data = data.hex()
                # Match start detection
                if hex_data.startswith("0500"):
                    self.match_started = False
                elif hex_data.startswith("0515") and not self.match_started:
                    self.match_started = True
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                print(f"  [G{self.index+1}] Listen err: {e}")
                self.connected = False
                break

    async def cleanup(self):
        """Close all TCP connections."""
        for writer in [self.online_writer, self.chat_writer]:
            if writer and not writer.is_closing():
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass
        self.online_writer = self.online_reader = None
        self.chat_writer = self.chat_reader = None


# ======================== CLAN GLORY BOT ========================

class ClanGloryBot:
    """
    Clash Squad Exit Glitch exploit bot.

    Each cycle (~30-60s):
      1. Leader opens squad + gets squad_code from server
      2. Members join using squad_code
      3. Leader queues Clash Squad
      4. Wait for matchmaking
      5. ALL members immediately exit/withdraw
      6. Wait POST_EXIT_WAIT for glory to credit
      7. Re-queue
    """

    def __init__(self, clan_id: int = DEFAULT_CLAN_ID, region: str = DEFAULT_REGION,
                 cycles: int = DEFAULT_CYCLES,
                 matchmaking_wait: int = MATCHMAKING_WAIT,
                 post_exit_wait: int = POST_EXIT_WAIT):
        self.clan_id = clan_id
        self.region = region
        self.max_cycles = cycles
        self.matchmaking_wait = matchmaking_wait
        self.post_exit_wait = post_exit_wait
        self.connections: List[GuestConnection] = []
        self.running = False
        self.cycle_count = 0
        self.total_glory_estimated = 0

    async def load_guests(self) -> List[dict]:
        with open(GUESTS_FILE) as f:
            return json.load(f)

    async def setup(self) -> bool:
        """Authenticate all guests, connect TCP, join clan."""
        guests = await self.load_guests()
        if len(guests) < 2:
            print("Need at least 2 guest accounts!")
            return False

        guests = guests[:4]
        print(f"\n  Guest accounts: {len(guests)}")

        async with aiohttp.ClientSession() as session:
            for i, guest in enumerate(guests):
                conn = GuestConnection(guest, i)

                if not await conn.authenticate(session):
                    continue

                # Auto-join target clan via HTTP API
                await auto_join_clan(session, conn.jwt, self.clan_id, conn.server_url, i)
                await asyncio.sleep(1)

                if not await conn.connect_tcp():
                    continue

                # Start listener
                asyncio.create_task(conn.listen_online())

                # Join clan (sends AuthClan to chat channel)
                await conn.join_clan(self.clan_id)

                self.connections.append(conn)
                await asyncio.sleep(2)

        if len(self.connections) < 2:
            print(f"  Only {len(self.connections)} connected — need 2+")
            return False

        print(f"\n  {len(self.connections)} guests ready in clan {self.clan_id}")
        return True

    async def form_squad(self) -> bool:
        """
        Leader opens squad -> gets squad_code from server response.
        Leader invites members.
        Members join using the REAL squad_code (not leader UID!).
        """
        if not self.connections:
            return False

        leader = self.connections[0]
        members = self.connections[1:]

        print(f"  Squad: Leader=G1({leader.account_uid}) -> {len(members)} members")

        # Leader opens squad and READS the response to get squad_code
        squad_code = await leader.open_squad(self.region)
        await asyncio.sleep(2)

        if not squad_code:
            print(f"  ⚠ No squad_code received — squad may not form properly")
            squad_code = str(leader.account_uid)  # fallback

        # Leader invites each member
        for member in members:
            await leader.send_invite(member.account_uid, self.region)
            await asyncio.sleep(1)

        # Wait for invites to process
        await asyncio.sleep(2)

        # Members join using the REAL squad_code
        for member in members:
            try:
                await member.join_squad(squad_code)
                print(f"  [G{member.index+1}] Joined squad with code: {squad_code[:20]}...")
            except Exception as e:
                print(f"  [G{member.index+1}] Join squad failed: {e}")
            await asyncio.sleep(1)

        print(f"  Squad formed: {len(self.connections)} players (code: {squad_code[:20]}...)")
        return True

    async def exploit_cycle(self) -> bool:
        """
        Single exploit cycle:
          1. Form squad (with proper squad_code)
          2. Queue Clash Squad
          3. Wait for matchmaking
          4. ALL exit immediately
          5. Wait for glory credit
        """
        # Form squad (if not already)
        if not all(c.in_squad for c in self.connections):
            await self.form_squad()
            await asyncio.sleep(3)

        # Queue Clash Squad — leader starts match
        leader = self.connections[0]
        print(f"  >> Queueing Clash Squad...")

        # All members send match start
        for conn in self.connections:
            await conn.start_clash_squad(self.region)
            await asyncio.sleep(0.3)

        # Wait for matchmaking
        print(f"  >> Waiting {self.matchmaking_wait}s for match...")
        await asyncio.sleep(self.matchmaking_wait)

        # EXPLOIT: ALL members exit immediately
        print(f"  >> EXITING MATCH (exploit)...")
        for conn in self.connections:
            await conn.exit_match()
            await asyncio.sleep(0.2)

        # Reset squad state (exiting match disbands squad)
        for conn in self.connections:
            conn.in_squad = False
            conn.in_match = False
            conn.squad_code = None

        # Wait for glory to credit
        print(f"  >> Waiting {self.post_exit_wait}s for glory credit...")
        await asyncio.sleep(self.post_exit_wait)

        # Estimate glory (varies, but participation gives some points)
        glory_per_cycle = len(self.connections) * random.randint(5, 15)
        self.total_glory_estimated += glory_per_cycle

        print(f"  >> Cycle #{self.cycle_count} done (+~{glory_per_cycle} glory, total ~{self.total_glory_estimated})")
        return True

    async def run(self):
        """Main exploit loop."""
        self.running = True
        self.cycle_count = 0

        print("=" * 60)
        print("  CLAN GLORY BOT — Clash Squad Exit Exploit")
        print(f"  Clan: {self.clan_id}")
        print(f"  Region: {self.region}")
        print(f"  Max cycles: {self.max_cycles}")
        print(f"  Per cycle: ~{self.matchmaking_wait + self.post_exit_wait + REQUEUE_DELAY}s")
        print(f"  Est total time: ~{(self.max_cycles * (self.matchmaking_wait + self.post_exit_wait + REQUEUE_DELAY)) // 60} min")
        print("=" * 60)

        if not await self.setup():
            print("  Setup FAILED")
            return

        start_time = time.time()

        while self.running and self.cycle_count < self.max_cycles:
            self.cycle_count += 1
            print(f"\n  --- CYCLE #{self.cycle_count}/{self.max_cycles} ---")

            try:
                # Reconnect if needed
                for conn in self.connections:
                    if not conn.connected:
                        print(f"  [G{conn.index+1}] Reconnecting...")
                        await conn.connect_tcp()
                        await conn.join_clan(self.clan_id)
                        await asyncio.sleep(2)

                # Run exploit
                await self.exploit_cycle()

                # Inter-cycle delay
                await asyncio.sleep(REQUEUE_DELAY)

            except KeyboardInterrupt:
                print("\n  Stopped by user")
                break
            except Exception as e:
                print(f"  Cycle error: {e}")
                await asyncio.sleep(RECONNECT_DELAY)

        elapsed = int(time.time() - start_time)
        print("\n" + "=" * 60)
        print(f"  CLAN GLORY BOT — Done")
        print(f"  Cycles: {self.cycle_count}/{self.max_cycles}")
        print(f"  Time: {elapsed}s ({elapsed // 60}m {elapsed % 60}s)")
        print(f"  Est glory: ~{self.total_glory_estimated}")
        print(f"  Guests: {len(self.connections)}")
        print(f"  Clan: {self.clan_id}")
        print("=" * 60)

        # Cleanup
        for conn in self.connections:
            await conn.cleanup()

        # Save updated guests
        with open(GUESTS_FILE, "w") as f:
            json.dump([c.guest for c in self.connections], f, indent=2)


# ======================== ENTRY POINT ========================

def main():
    import argparse
    p = argparse.ArgumentParser(description="Clan Glory Bot — Clash Squad Exit Exploit")
    p.add_argument("--clan-id", type=int, default=DEFAULT_CLAN_ID, help="Target clan ID")
    p.add_argument("--region", type=str, default=DEFAULT_REGION, help="Region (ME, IND, BR, SG, etc.)")
    p.add_argument("--cycles", type=int, default=DEFAULT_CYCLES, help="Max exploit cycles")
    p.add_argument("--match-wait", type=int, default=MATCHMAKING_WAIT, help="Matchmaking wait (seconds)")
    p.add_argument("--post-exit-wait", type=int, default=POST_EXIT_WAIT, help="Post-exit wait (seconds)")
    args = p.parse_args()

    bot = ClanGloryBot(
        clan_id=args.clan_id, region=args.region, cycles=args.cycles,
        matchmaking_wait=args.match_wait, post_exit_wait=args.post_exit_wait
    )

    # Handle Ctrl+C
    def stop_handler(sig, frame):
        bot.running = False
    signal.signal(signal.SIGINT, stop_handler)

    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
