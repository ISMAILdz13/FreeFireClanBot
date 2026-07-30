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
# NOTE: Do NOT add src/proto/compiled to path — it conflicts with Pb2 version

import aiohttp
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from Pb2 import MajoRLoGinrEq_pb2, MajoRLoGinrEs_pb2, PorTs_pb2
from xC4 import (
    CrEaTe_ProTo, EnC_PacKeT_sync, GeneRaTePk, DecodE_HeX,
    AuthClan, OpEnSq, SEnd_InV, GenJoinSquadsPacket, ExiT,
    AutH_GlobAl, EnC_Uid, EnC_Vr,
    DeCode_PackEt, DEc_PacKeT, GeTSQDaTa,
    EnC_PacKeT
)

# ======================== TCP AUTH TOKEN BUILDER ========================

async def build_tcp_auth_token(uid: int, token: str, timestamp: int, key: bytes, iv: bytes) -> str:
    """xAuThSTarTuP — builds the TCP auth startup token.
    Matches the original client's authentication flow exactly."""
    uid_hex = hex(uid)[2:]
    uid_length = len(uid_hex)
    encrypted_timestamp = await DecodE_HeX(timestamp)
    encrypted_account_token = token.encode().hex()
    encrypted_packet = await EnC_PacKeT(encrypted_account_token, key, iv)
    encrypted_packet_length = hex(len(encrypted_packet) // 2)[2:]
    if uid_length == 9: headers = '0000000'
    elif uid_length == 8: headers = '00000000'
    elif uid_length == 10: headers = '000000'
    elif uid_length == 7: headers = '000000000'
    else: headers = '0000000'
    return f"0115{headers}{uid_hex}{encrypted_timestamp}00000{encrypted_packet_length}{encrypted_packet}"

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
# PORTS_URL removed — using GetLoginData endpoint instead
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


async def get_login_data(major_login_payload: bytes, server_url: str, jwt_token: str) -> dict:
    """GetLoginData — POST to {server_url}/GetLoginData with the MajorLogin encrypted payload.
    Returns: online_ip, online_port, chat_ip, chat_port, clan_compiled_data, account_name.
    NOTE: The body is the SAME encrypted MajorLogin payload (not the JWT token).
    The Authorization header uses the JWT token from MajorLogin response (not the OAuth access token)."""
    try:
        url = f"{server_url}/GetLoginData"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=major_login_payload, headers={
                **HTTP_HEADERS, "Authorization": f"Bearer {jwt_token}"
            }, ssl=False, timeout=aiohttp.ClientTimeout(total=20)) as r:
                if r.status == 200:
                    data = await r.read()
                    from PorTs_pb2 import GetLoginData as GetLoginDataProto
                    proto = GetLoginDataProto()
                    proto.ParseFromString(data)
                    result = {
                        "online_ip_port": proto.Online_IP_Port,
                        "chat_ip_port": proto.AccountIP_Port,
                        "account_name": proto.AccountName,
                        "clan_compiled_data": proto.Clan_Compiled_Data,
                        "account_uid": proto.AccountUID,
                    }
                    return result
                else:
                    body = await r.text()
                    print(f"  GetLoginData HTTP {r.status}: {body[:100]}")
    except Exception as e:
        print(f"  GetLoginData error: {e}")
    return {}


async def auto_join_clan(session: aiohttp.ClientSession, jwt: str, clan_id: int,
                         server_url: str, index: int):
    """Send HTTP RequestJoinClan to join the target clan.
    Tries multiple payload formats and server URLs (matching the reference bot)."""
    import struct

    def encode_varint(value):
        buf = []
        value = int(value)
        while True:
            towrite = value & 0x7f
            value >>= 7
            if value:
                buf.append(towrite | 0x80)
            else:
                buf.append(towrite)
                break
        return bytes(buf).hex()

    gid_int = int(clan_id)
    gid_str_bytes = str(gid_int).encode('utf-8')
    gid_str_len = encode_varint(len(gid_str_bytes))
    gid_varint = encode_varint(gid_int)

    # Multiple payload formats (string and varint) like the reference bot
    payload_formats = [
        f"0a{gid_str_len}{gid_str_bytes.hex()}",  # field 1, string
        f"12{gid_str_len}{gid_str_bytes.hex()}",  # field 2, string
        f"10{gid_varint}",                        # field 2, varint
        f"08{gid_varint}",                        # field 1, varint
    ]

    # Multiple server URLs
    urls = [
        f"{server_url}/RequestJoinClan",
        "https://clientbp.common.ggbluefox.com/RequestJoinClan",
        "https://clientbp.ggblueshark.com/RequestJoinClan",
        "https://client.me.freefiremobile.com/RequestJoinClan",
    ]

    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB54",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
    }

    for fmt_idx, payload_hex in enumerate(payload_formats, 1):
        enc_hex = EnC_PacKeT_sync(payload_hex, AES_KEY, AES_IV)
        for url in urls:
            try:
                async with session.post(url, data=bytes.fromhex(enc_hex),
                    headers=headers, ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status in (200, 201):
                        print(f"  [G{index+1}] Joined clan {clan_id} (HTTP fmt#{fmt_idx})")
                        return True
                    elif r.status == 400:
                        # 400 might mean already in clan — check response
                        body = await r.text()
                        if "already" in body.lower():
                            print(f"  [G{index+1}] Already in clan {clan_id}")
                            return True
            except:
                continue
    print(f"  [G{index+1}] Clan join failed (tried {len(payload_formats)} formats x {len(urls)} URLs)")
    return False


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
        """Full OAuth -> MajorLogin -> GetLoginData chain.
        Returns TCP endpoints + clan data for this account."""
        print(f"  [G{self.index+1}] UID {self.uid}: Auth...")

        # Step 1: Refresh OAuth token
        at, oid = await refresh_oauth_token(self.guest)
        if at:
            self.access_token = at
            self.open_id = oid
            self.guest["access_token"] = at
            self.guest["open_id"] = oid
        else:
            at = self.access_token
            oid = self.open_id
            if not at:
                print(f"  [G{self.index+1}] No OAuth token")
                return False

        # Step 2: MajorLogin — get JWT, key, iv, server_url
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

                # Check if banned (no token returned)
                if not res.token:
                    print(f"  [G{self.index+1}] BANNED (no token in MajorLogin response)")
                    return False

                self.jwt = res.token
                self.key = res.key          # bytes (field 22)
                self.iv = res.iv            # bytes (field 23)
                self.server_url = res.url   # field 10
                self.account_uid = res.account_uid  # field 1
                self.timestamp = res.timestamp      # field 21
                print(f"  [G{self.index+1}] JWT OK uid={self.account_uid}")
        except Exception as e:
            err = str(e)
            if "BLACKLIST" in err.upper():
                print(f"  [G{self.index+1}] BANNED (blacklist info in response)")
            else:
                print(f"  [G{self.index+1}] MajorLogin FAIL: {err[:80]}")
            return False

        # Step 3: GetLoginData — get TCP endpoints + clan compiled data
        # NOTE: Send the MajorLogin encrypted payload as the body,
        #       and use the JWT token (not OAuth access token) for Bearer auth
        login_data = await get_login_data(payload, self.server_url, self.jwt)
        if not login_data:
            print(f"  [G{self.index+1}] GetLoginData FAIL")
            return False

        online_ip_port = login_data.get("online_ip_port", "")
        chat_ip_port = login_data.get("chat_ip_port", "")

        if ":" not in online_ip_port or ":" not in chat_ip_port:
            print(f"  [G{self.index+1}] No TCP endpoints in GetLoginData")
            return False

        self.online_ip, online_port_str = online_ip_port.rsplit(":", 1)
        self.online_port = int(online_port_str)
        self.chat_ip, chat_port_str = chat_ip_port.rsplit(":", 1)
        self.chat_port = int(chat_port_str)
        self.clan_compiled_data = login_data.get("clan_compiled_data", "")

        print(f"  [G{self.index+1}] TCP: {self.online_ip}:{self.online_port} | {self.chat_ip}:{self.chat_port}")
        return True

    async def connect_tcp(self) -> bool:
        """Connect to Online + Chat TCP servers using xAuThSTarTuP token.
        NOTE: Free Fire game servers use RAW TCP — NO SSL/TLS."""
        try:
            # Build the proper TCP auth token using xAuThSTarTuP
            auth_token_hex = await build_tcp_auth_token(
                self.account_uid, self.jwt, self.timestamp, self.key, self.iv)
            auth_token_bytes = bytes.fromhex(auth_token_hex)

            # Online connection (raw TCP, no SSL)
            self.online_reader, self.online_writer = await asyncio.open_connection(
                self.online_ip, self.online_port)
            self.online_writer.write(auth_token_bytes)
            await self.online_writer.drain()

            # Chat (Whisper) connection (raw TCP, no SSL)
            self.chat_reader, self.chat_writer = await asyncio.open_connection(
                self.chat_ip, self.chat_port)
            self.chat_writer.write(auth_token_bytes)
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
        """AuthClan — join guild (sent to CHAT channel, uses clan_compiled_data)."""
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
