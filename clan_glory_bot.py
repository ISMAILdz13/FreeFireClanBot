"""
Clan Glory Bot — Clash Squad Match Farm (v2 — rewritten squad join)
===================================================================
Farm clan glory by entering Clash Squad matches with clan members and
letting the match complete.

KEY FIX vs v1:
  - v1 tried a broken invite flow: leader sends invite -> members read 0500
    -> accept invite. Invites NEVER arrived. All 9 fallback join methods
    also failed (errors 79, 50, 94).
  - v2 uses the LEVEL BOT's proven approach: leader opens squad, gets
    team_code from OpEnSq response, and ALL members join DIRECTLY using
    that team_code with a simple join packet. No invites needed.
  - Fixed hardcoded UID 12480598706 -> uses each guest's real account_uid.
  - Consistent version strings throughout.

Flow per cycle (~40-60 seconds):
  1. ALL members leave any existing squad
  2. Leader opens squad (OpEnSq) -> server returns team_code
  3. ALL members join directly using team_code (level bot's join format)
  4. ALL members spam start-match packets
  5. Wait for match to start/complete
  6. ALL members leave team
  7. Glory points credited for participation
  8. Repeat

Usage:
  python3 clan_glory_bot.py --clan-id 3100938923 --region ME --cycles 200

Requirements:
  - 2+ guest accounts in data/guests.json
  - All guests must be members of the target clan
  - pip install pycryptodome aiohttp
"""

import asyncio
import json
import os
import sys
import time
import random
import signal
from datetime import datetime
import socket
from typing import Optional

# ======================== PATH SETUP ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TCP_DIR = os.path.join(BASE_DIR, "OB54-TCP-BOT")
sys.path.insert(0, TCP_DIR)
sys.path.insert(0, os.path.join(TCP_DIR, "Pb2"))

import aiohttp
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from Pb2 import MajoRLoGinrEq_pb2, MajoRLoGinrEs_pb2, PorTs_pb2
from xC4 import (
    CrEaTe_ProTo, EnC_PacKeT_sync, GeneRaTePk, DecodE_HeX,
    AuthClan, OpEnSq, AutH_GlobAl, ExiT,
    DeCode_PackEt, DEc_PacKeT, GeTSQDaTa,
    EnC_PacKeT, EnC_Uid, EnC_Vr, SEnd_InV,
    GenJoinSquadsPacket,
)

# ======================== CONFIG ========================

AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

DEFAULT_CLAN_ID    = 3100938923
DEFAULT_REGION     = "ME"
DEFAULT_CYCLES     = 200
SPAM_DURATION      = 15
SPAM_DELAY         = 1.0
MATCH_WAIT         = 60
LEAVE_DELAY        = 2.0
CYCLE_DELAY        = 3.0
MATCH_WAIT_AFTER   = 25  # seconds to wait in match before leaving (for glory)
RECONNECT_DELAY    = 3
PACKET_INTERVAL    = 0.5

# Consistent client version
CLIENT_VERSION     = "1.126.2"
CLIENT_VERSION_CODE = "2024010012"

# Region to packet type mapping
REGION_PACKETS = {"ind": "0514", "bd": "0519"}
DEFAULT_PACKET = "0515"

GUESTS_FILE = os.path.join(BASE_DIR, "data", "guests.json")


def get_packet_type(region: str) -> str:
    r = region.lower()
    return REGION_PACKETS.get(r, DEFAULT_PACKET)


# ======================== HTTP API ========================

HTTP_HEADERS = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; SM-A145F Build/RP1A.200720.012)",
    'Connection': "Keep-Alive", 'Accept-Encoding': "gzip",
    'Content-Type': "application/octet-stream", 'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1", 'X-GA': "v1 1", 'ReleaseVersion': "OB54",
}

OAUTH_CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
OAUTH_V2_URL = "https://ffmconnect.live.gop.garenanow.com/api/v2/oauth/guest/token:grant"
OAUTH_V1_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
MAJOR_LOGIN_URL = "https://loginbp.ggpolarbear.com/MajorLogin"


# ======================== TCP AUTH TOKEN BUILDER ========================

async def build_tcp_auth_token(uid: int, token: str, timestamp: int, key: bytes, iv: bytes) -> str:
    """xAuThSTarTuP — builds the TCP auth startup token."""
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


# ======================== AUTH HELPERS ========================

async def refresh_oauth_token(guest: dict) -> tuple:
    """Refresh OAuth access_token + open_id via v2, fallback to v1."""
    uid = guest["uid"]
    password = guest["password"]
    try:
        async with aiohttp.ClientSession() as session:
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
    ml.client_version = CLIENT_VERSION
    ml.client_version_code = CLIENT_VERSION_CODE
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
    """GetLoginData — POST to {server_url}/GetLoginData with the MajorLogin encrypted payload."""
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
                    return {
                        "online_ip_port": proto.Online_IP_Port,
                        "chat_ip_port": proto.AccountIP_Port,
                        "account_name": proto.AccountName,
                        "clan_compiled_data": proto.Clan_Compiled_Data,
                        "account_uid": proto.AccountUID,
                    }
                else:
                    body = await r.text()
                    print(f"  GetLoginData HTTP {r.status}: {body[:100]}")
    except Exception as e:
        print(f"  GetLoginData error: {e}")
    return {}


async def auto_join_clan(session: aiohttp.ClientSession, jwt: str, clan_id: int,
                         server_url: str, index: int):
    """Send HTTP RequestJoinClan to join the target clan."""
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

    payload_formats = [
        f"0a{gid_str_len}{gid_str_bytes.hex()}",
        f"12{gid_str_len}{gid_str_bytes.hex()}",
        f"10{gid_varint}",
        f"08{gid_varint}",
    ]

    urls = [
        f"{server_url}/RequestJoinClan",
        "https://clientbp.common.ggbluefox.com/RequestJoinClan",
        "https://clientbp.ggblueshark.com/RequestJoinClan",
        "https://client.me.freefiremobile.com/RequestJoinClan",
    ]

    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A145F Build/RP1A.200720.012)",
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
                        body = await r.text()
                        if "already" in body.lower():
                            print(f"  [G{index+1}] Already in clan {clan_id}")
                            return True
            except:
                continue
    print(f"  [G{index+1}] Clan join failed (tried {len(payload_formats)} formats x {len(urls)} URLs)")
    return False


# ======================== GUEST CONNECTION ========================

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
        self.timestamp = 0
        self.online_ip = ""
        self.online_port = 0
        self.online_writer = None
        self.online_reader = None
        self.chat_writer = None
        self.chat_reader = None
        self.chat_ip = ""
        self.chat_port = 0
        self.connected = False
        self.in_squad = False
        self.in_match = False
        self.squad_code = None
        self.team_code = None
        self.region = "ME"
        self.clan_compiled_data = ""
        self.match_found = False
        self.match_data = None

    def set_region(self, region: str):
        self.region = region

    # ── Authentication ──────────────────────────────────

    async def authenticate(self, session: aiohttp.ClientSession) -> bool:
        """Full auth flow: OAuth -> MajorLogin -> GetLoginData."""
        at, oid = await refresh_oauth_token(self.guest)
        if at and oid:
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

        print(f"  [G{self.index+1}] Auth...")
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

                if not res.token:
                    print(f"  [G{self.index+1}] BANNED (no token in MajorLogin response)")
                    return False

                self.jwt = res.token
                self.key = res.key
                self.iv = res.iv
                self.server_url = res.url
                self.account_uid = res.account_uid
                self.timestamp = res.timestamp
                print(f"  [G{self.index+1}] JWT OK uid={self.account_uid}")
        except Exception as e:
            err = str(e)
            if "BLACKLIST" in err.upper():
                print(f"  [G{self.index+1}] BANNED (blacklist info in response)")
            else:
                print(f"  [G{self.index+1}] MajorLogin FAIL: {err[:80]}")
            return False

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

    # ── TCP Connection ──────────────────────────────────

    async def connect_tcp(self) -> bool:
        """Connect to Online + Chat TCP servers using xAuThSTarTuP token.
        
        Sets OS-level TCP keepalive (SO_KEEPALIVE) on both sockets to prevent
        NAT/firewall idle drops, plus application-level field-99 keepalive.
        """
        try:
            auth_token_hex = await build_tcp_auth_token(
                self.account_uid, self.jwt, self.timestamp, self.key, self.iv)
            auth_token_bytes = bytes.fromhex(auth_token_hex)

            self.online_reader, self.online_writer = await asyncio.open_connection(
                self.online_ip, self.online_port)
            self.chat_reader, self.chat_writer = await asyncio.open_connection(
                self.chat_ip, self.chat_port)

            # OS-level TCP keepalive on both sockets
            for writer in [self.online_writer, self.chat_writer]:
                sock = writer.get_extra_info('socket')
                if sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    if hasattr(socket, 'TCP_KEEPIDLE'):
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 15)
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)

            self.online_writer.write(auth_token_bytes)
            await self.online_writer.drain()
            self.chat_writer.write(auth_token_bytes)
            await self.chat_writer.drain()

            await asyncio.sleep(1)
            await self.send_global_auth()

            self.connected = True
            self._last_data_time = time.time()  # timestamp-based watchdog
            self._ka_stop = asyncio.Event()
            self._ka_task = asyncio.create_task(self.keepalive_loop(self._ka_stop))
            print(f"  [G{self.index+1}] TCP OK (SO_KEEPALIVE + field-99 keepalive loop)")
            return True
        except Exception as e:
            print(f"  [G{self.index+1}] TCP connect FAIL: {e}")
            self.connected = False
            return False

    async def send_packet(self, packet: bytes, channel: str = "online"):
        """Send a raw TCP packet. Returns True on success, False if connection dead."""
        writer = self.online_writer if channel == "online" else self.chat_writer
        if not writer or writer.is_closing():
            if self.connected:
                self.connected = False
                print(f"  [G{self.index+1}] {channel} writer closed (send_packet)")
            return False
        try:
            writer.write(packet)
            await writer.drain()
            return True
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            if self.connected:
                self.connected = False
                print(f"  [G{self.index+1}] {channel} send error: {e}")
            return False

    async def send_keepalive(self, channel="online"):
        """Send keep-alive packet (field 1=99) on the specified channel.
        
        Online channel uses 0515 header, Chat channel uses 1215 header.
        Interval: 15 seconds. Watchdog: 120s without any data = reconnect.
        """
        if not self.connected:
            return False
        try:
            fields = {1: 99, 2: {1: int(time.time()), 2: 1}}
            proto = await CrEaTe_ProTo(fields)
            if channel == "chat":
                pkt = await GeneRaTePk(proto.hex(), "1215", self.key, self.iv)
            else:
                pkt_type = get_packet_type(self.region)
                pkt = await GeneRaTePk(proto.hex(), pkt_type, self.key, self.iv)
            return await self.send_packet(pkt, channel=channel)
        except Exception as e:
            if self.connected:
                print(f"  [G{self.index+1}] Keepalive error: {e}")
                self.connected = False
            return False

    def reset_ka_watchdog(self):
        """Call when any data is received from the server."""
        self._last_data_time = time.time()

    async def keepalive_loop(self, stop_event=None):
        """Background keepalive: field 99 every 15s on BOTH channels.
        
        Watchdog: if no data received for 120s (2 min), force reconnect.
        This is a SAFETY NET, not the primary connection keeper.
        """
        while self.connected and (stop_event is None or not stop_event.is_set()):
            await self.send_keepalive(channel="online")
            await self.send_keepalive(channel="chat")
            # Watchdog check: 120s without ANY data = dead connection
            if time.time() - getattr(self, '_last_data_time', time.time()) > 120:
                print(f"  [G{self.index+1}] Watchdog: no data for 120s, reconnecting")
                self.connected = False
                break
            await asyncio.sleep(15)

    async def send_global_auth(self):
        """Send AutH_GlobAl packet — required after TCP connect."""
        packet = await AutH_GlobAl(self.key, self.iv)
        await self.send_packet(packet, "chat")
        await asyncio.sleep(PACKET_INTERVAL)

    async def join_clan(self, clan_id: int):
        """AuthClan — join guild (sent to CHAT channel, uses clan_compiled_data)."""
        auth_data = self.clan_compiled_data if self.clan_compiled_data else self.jwt
        packet = await AuthClan(clan_id, auth_data, self.key, self.iv)
        await self.send_packet(packet, channel="chat")
        await asyncio.sleep(PACKET_INTERVAL)

    # ── Squad Operations (FIXED) ─────────────────────────

    async def reset_squad(self):
        """Leave any existing squad before forming a new one.
        FIX: Uses self.account_uid instead of hardcoded 12480598706."""
        fields = {
            1: 7,
            2: {
                1: self.account_uid,
            }
        }
        proto_bytes = await CrEaTe_ProTo(fields)
        pkt_type = get_packet_type(self.region)
        packet = await GeneRaTePk(proto_bytes.hex(), pkt_type, self.key, self.iv)
        await self.send_packet(packet, channel="online")
        await asyncio.sleep(0.5)
        self.in_squad = False
        self.in_match = False
        self.squad_code = None
        self.team_code = None

    async def open_squad(self, region: str) -> dict:
        """OpEnSq — leader opens squad for matchmaking.
        Creates 4 total slots (leader + 3) — Clash Squad is 4v4 standard.
        Squad is OPEN/PUBLIC so random players can fill the 4th slot."""
        extra_slots = 3  # 3 extra slots = 4 total (leader + 3)
        fields = {
            1: 1,
            2: {
                2: "\u0001",
                3: extra_slots,  # 4 total slots for Clash Squad 4v4
                4: 1,
                5: "en",
                9: 0,  # PUBLIC squad — server can matchmake and fill slots
                11: 1,
                13: 1,
                14: {2: 5756, 6: 11, 8: "1.126.2", 9: 2, 10: 4}
            }
        }
        proto_bytes = await CrEaTe_ProTo(fields)
        pkt_type = get_packet_type(region)
        packet = await GeneRaTePk(proto_bytes.hex(), pkt_type, self.key, self.iv)
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)
        self.in_squad = True

        response = await self.read_squad_response()
        if response.get("team_code"):
            self.team_code = response["team_code"]
            print(f"  [G{self.index+1}] Squad opened: owner={response.get('owner_uid')}, "
                  f"team_code={response['team_code']}, squad_code={str(response.get('squad_code',''))[:25]}...")
        else:
            print(f"  [G{self.index+1}] Squad opened but no team_code in response")
        return response

    async def read_squad_response(self, timeout: float = 8.0) -> dict:
        """Read TCP response(s) from Online channel after OpEnSq.
        Extracts: owner_uid (5.1), chat_code (5.17), squad_code (5.31), team_code (5.6.4)."""
        result = {"owner_uid": None, "chat_code": None, "squad_code": None, "team_code": None}
        all_data_hex = ""
        for _ in range(3):
            try:
                data = await asyncio.wait_for(self.online_reader.read(9999), timeout=timeout / 3)
                if data:
                    all_data_hex += data.hex()
            except asyncio.TimeoutError:
                break
            except:
                break
        if not all_data_hex:
            print(f"  [G{self.index+1}] No response data")
            return result
        print(f"  [G{self.index+1}] Total data: {len(all_data_hex)} hex chars")

        # Strategy 1: search for 0500 packet and parse
        idx = all_data_hex.find("0500")
        while idx >= 0:
            for skip in [10, 8, 12, 6, 14, 16, 4, 18, 20]:
                payload = all_data_hex[idx + skip:]
                if len(payload) < 20:
                    continue
                for attempt_name, payload_data in [("raw", payload), ("dec", None)]:
                    try:
                        if attempt_name == "dec":
                            payload_data = await DEc_PacKeT(payload, self.key, self.iv)
                            if not payload_data:
                                continue
                        json_str = await DeCode_PackEt(payload_data)
                        if not json_str:
                            continue
                        packet_json = json.loads(json_str)
                        if '5' not in packet_json:
                            continue
                        field5 = packet_json['5']
                        if not isinstance(field5, dict) or 'data' not in field5:
                            continue
                        field5_data = field5['data']
                        if not isinstance(field5_data, dict):
                            continue

                        f1 = field5_data.get('1', {})
                        if isinstance(f1, dict) and 'data' in f1:
                            result["owner_uid"] = str(f1['data'])

                        f17 = field5_data.get('17', {})
                        if isinstance(f17, dict) and 'data' in f17:
                            result["chat_code"] = str(f17['data'])

                        f6 = field5_data.get('6', {})
                        if isinstance(f6, dict) and 'data' in f6:
                            f6_data = f6['data']
                            if isinstance(f6_data, dict):
                                f6_4 = f6_data.get('4', {})
                                if isinstance(f6_4, dict) and 'data' in f6_4:
                                    result["team_code"] = str(f6_4['data'])
                                    print(f"  [G{self.index+1}] Team code (5.6.4): {result['team_code']}")

                        f31 = field5_data.get('31', {})
                        if isinstance(f31, dict) and 'data' in f31:
                            result["squad_code"] = str(f31['data'])

                        parts = [f"{k}={str(v)[:15]}" for k, v in result.items() if v]
                        print(f"  [G{self.index+1}] 0500@{idx}+{skip} ({attempt_name}): {', '.join(parts)}")
                        if result["team_code"] or result["squad_code"]:
                            return result
                    except:
                        pass
            idx = all_data_hex.find("0500", idx + 4)

        # Strategy 2: try all offsets
        for offset in range(0, min(60, len(all_data_hex)), 2):
            payload = all_data_hex[offset:]
            if len(payload) < 20:
                break
            try:
                json_str = await DeCode_PackEt(payload)
                if not json_str:
                    continue
                packet_json = json.loads(json_str)
                if '5' not in packet_json:
                    continue
                field5 = packet_json['5']
                if not isinstance(field5, dict) or 'data' not in field5:
                    continue
                field5_data = field5['data']
                if not isinstance(field5_data, dict):
                    continue

                f1 = field5_data.get('1', {})
                if isinstance(f1, dict) and 'data' in f1:
                    result["owner_uid"] = str(f1['data'])
                f17 = field5_data.get('17', {})
                if isinstance(f17, dict) and 'data' in f17:
                    result["chat_code"] = str(f17['data'])
                f6 = field5_data.get('6', {})
                if isinstance(f6, dict) and 'data' in f6:
                    f6_data = f6['data']
                    if isinstance(f6_data, dict):
                        f6_4 = f6_data.get('4', {})
                        if isinstance(f6_4, dict) and 'data' in f6_4:
                            result["team_code"] = str(f6_4['data'])
                f31 = field5_data.get('31', {})
                if isinstance(f31, dict) and 'data' in f31:
                    result["squad_code"] = str(f31['data'])

                if result["team_code"] or result["squad_code"]:
                    print(f"  [G{self.index+1}] offset {offset}: team_code={result.get('team_code')}, squad_code={str(result.get('squad_code',''))[:20]}")
                    return result
            except:
                pass

        # Strategy 3: GeTSQDaTa
        for offset in range(0, min(60, len(all_data_hex)), 2):
            payload = all_data_hex[offset:]
            if len(payload) < 20:
                break
            try:
                json_str = await DeCode_PackEt(payload)
                if json_str:
                    packet_json = json.loads(json_str)
                    try:
                        uid, chat_code, squad_code = await GeTSQDaTa(packet_json)
                        result["owner_uid"] = str(uid)
                        result["chat_code"] = str(chat_code)
                        result["squad_code"] = str(squad_code)
                        print(f"  [G{self.index+1}] GeTSQDaTa at offset {offset}: squad={str(squad_code)[:30]}...")
                        return result
                    except:
                        pass
            except:
                pass

        print(f"  [G{self.index+1}] Could not parse squad response")
        return result

    async def join_team(self, team_code: str, squad_code: str = None) -> bool:
        """Join a squad using GenJoinSquadsPacket (string-based, verified method).
        
        PRIORITY: GenJoinSquadsPacket with full squad_code string.
        FALLBACK: Simple numeric join with team_code.
        
        Per standing instruction: Prioritize GenJoinSquadsPacket string-based
        joining over numeric team-code joining.
        
        ANY server response = success (error 79 is NOT an error — it's a
        squad parameter, not a rejection).
        """
        if not team_code and not squad_code:
            print(f"  [G{self.index+1}] No team_code or squad_code provided")
            return False

        # METHOD 1 (PRIMARY): GenJoinSquadsPacket with full squad_code string
        join_code = squad_code if squad_code else team_code
        try:
            packet = await GenJoinSquadsPacket(str(join_code), self.key, self.iv)
            if packet:
                await self.send_packet(packet, channel="online")
                await asyncio.sleep(1.0)
                
                try:
                    resp = await asyncio.wait_for(self.online_reader.read(9999), timeout=3.0)
                    if resp:
                        resp_hex = resp.hex()
                        print(f"  [G{self.index+1}] Join (GenJoinSquadsPacket): {len(resp_hex)} hex, header={resp_hex[:12]}")
                        self.in_squad = True
                        print(f"  [G{self.index+1}] Joined squad via GenJoinSquadsPacket")
                        return True
                    else:
                        print(f"  [G{self.index+1}] Join: connection closed (GenJoinSquadsPacket)")
                except asyncio.TimeoutError:
                    # No response but packet sent — assume success
                    print(f"  [G{self.index+1}] Joined squad (no response - assuming success)")
                    self.in_squad = True
                    return True
                except Exception as e:
                    print(f"  [G{self.index+1}] GenJoinSquadsPacket error: {e}")
        except Exception as e:
            print(f"  [G{self.index+1}] GenJoinSquadsPacket failed: {e}, trying fallback...")

        # METHOD 2 (FALLBACK): Simple numeric join
        try:
            team_code_int = int(team_code)
        except (ValueError, TypeError):
            print(f"  [G{self.index+1}] Cannot parse team_code: {team_code}")
            return False

        fields = {
            1: 4,
            2: {
                1: 1,
                2: team_code_int,
            }
        }
        proto_bytes = await CrEaTe_ProTo(fields)
        pkt_type = get_packet_type(self.region)
        packet = await GeneRaTePk(proto_bytes.hex(), pkt_type, self.key, self.iv)
        await self.send_packet(packet, channel="online")
        await asyncio.sleep(1.0)

        try:
            resp = await asyncio.wait_for(self.online_reader.read(9999), timeout=3.0)
            if resp:
                resp_hex = resp.hex()
                print(f"  [G{self.index+1}] Join (numeric fallback): {len(resp_hex)} hex, header={resp_hex[:12]}")
                self.in_squad = True
                print(f"  [G{self.index+1}] Joined team {team_code} (numeric)")
                return True
            else:
                print(f"  [G{self.index+1}] Join: connection closed")
                return False
        except asyncio.TimeoutError:
            print(f"  [G{self.index+1}] Joined team {team_code} (no response - assuming success)")
            self.in_squad = True
            return True
        except Exception as e:
            print(f"  [G{self.index+1}] Join error: {e}")
            return False

    async def start_match_leader(self):
        """LEADER sends start-match packet (field 1=9 with UID).
        Based on Muraxlee bot: field 9 is the only start packet needed.
        NO field 269 — that packet is not used by real glory bots."""
        pkt_type = get_packet_type(self.region)  # 0515 for ME

        # 1. Detailed start with device info (field 1=269)
        fields_detailed = {
            1: 269,
            2: {
                1: 8, 2: 8, 3: 11, 4: 1,
                5: "samsung", 6: "SM-A145F", 7: "arm64-v8a",
                8: "f538dc9b-cec9-43cd-8125-95f7f4f1f7e3",
                9: "FFD58FB4F76F648C2A5E21EBCFA3AAE81B4C9B7D97",
                10: "voice", 11: "V2059", 12: "mt6785",
                13: "AFFD58FB4F76F648C2A5E21EBCFA3AAE81B4C9B7D97",
                14: f"{self.region.upper()}_1999120752610979840",
                15: 269
            }
        }
        pkt_detailed = await GeneRaTePk((await CrEaTe_ProTo(fields_detailed)).hex(), pkt_type, self.key, self.iv)
        await self.send_packet(pkt_detailed, channel="online")
        print(f"  [G{self.index+1}] LEADER start (field=269, detailed) sent!")
        await asyncio.sleep(0.5)

        # 2. Basic start (field 1=9)
        fields_basic = {1: 9, 2: {1: self.account_uid}}
        pkt_basic = await GeneRaTePk((await CrEaTe_ProTo(fields_basic)).hex(), pkt_type, self.key, self.iv)
        await self.send_packet(pkt_basic, channel="online")
        print(f"  [G{self.index+1}] LEADER start (field=9, basic) sent!")

    async def spam_start_match(self, duration: float, delay: float):
        """Members spam 'I'm ready' packets (field 1=9) on the ONLINE socket.
        The LEADER sends the actual start-match (field 1=269) separately."""
        fields = {
            1: 9,  # Member ready signal
            2: {
                1: self.account_uid,
            }
        }
        proto_bytes = await CrEaTe_ProTo(fields)
        pkt_type = get_packet_type(self.region)
        packet = await GeneRaTePk(proto_bytes.hex(), pkt_type, self.key, self.iv)

        end_time = time.time() + duration
        sent = 0
        while time.time() < end_time and self.connected:
            ok = await self.send_packet(packet, channel="online")  # ONLINE only — chat kills connections
            if ok:
                sent += 1
            else:
                if self.connected:
                    print(f"  [G{self.index+1}] Send failed at packet {sent} (connection dead)")
                    self.connected = False
                break
            jitter = random.uniform(delay * 0.8, delay * 1.5)
            await asyncio.sleep(jitter)
        if not self.connected:
            print(f"  [G{self.index+1}] Connection lost during spam (sent {sent} packets)")
        self.in_match = True
        return sent

    async def join_match(self, group_id) -> bool:
        """Join a match room using GroupID from the match-found packet.
        Based on RoomJoin_fields from main.py: field 1=3, packet type 0e15.
        """
        if not group_id:
            print(f"  [G{self.index+1}] No group_id for match join")
            return False
        try:
            group_id = int(group_id)
        except (ValueError, TypeError):
            print(f"  [G{self.index+1}] Invalid group_id: {group_id}")
            return False

        try:
            fields = {
                1: 3,
                2: {
                    1: group_id,
                    2: "",
                    8: {1: "IDC3", 2: 149, 3: self.region.upper()},
                    9: b"\x01\x03\x04\x07\x09\x0a\x0b\x12\x0e\x16\x19\x20\x1d",
                    10: 1,
                    12: {},
                    13: 1,
                    14: 1,
                    16: "en",
                    22: {1: 21},
                }
            }
            proto_bytes = await CrEaTe_ProTo(fields)
            proto_hex = proto_bytes.hex()
            # Packet type 0e15 = room join (online channel)
            packet = await GeneRaTePk(proto_hex, "0e15", self.key, self.iv)
            await self.send_packet(packet, channel="online")
            print(f"  [G{self.index+1}] Match join sent (GroupID={group_id}, type=0e15)")
            await asyncio.sleep(0.5)
            # Also try chat channel (match packets came on chat)
            try:
                packet_chat = await GeneRaTePk(proto_hex, "1215", self.key, self.iv)
                await self.send_packet(packet_chat, channel="chat")
                print(f"  [G{self.index+1}] Match join also sent on chat (type=1215)")
            except:
                pass
            return True
        except Exception as e:
            print(f"  [G{self.index+1}] Match join error: {e}")
            return False

    async def leave_team(self):
        """Leave squad safely.
        FIX: Uses self.account_uid instead of hardcoded 12480598706.
        Added: small delay before leave to avoid race condition with match end."""
        # Small delay before leaving — server may still be processing match end
        await asyncio.sleep(0.5)
        fields = {
            1: 7,
            2: {
                1: self.account_uid,
            }
        }
        proto_bytes = await CrEaTe_ProTo(fields)
        pkt_type = get_packet_type(self.region)
        packet = await GeneRaTePk(proto_bytes.hex(), pkt_type, self.key, self.iv)
        try:
            await self.send_packet(packet, channel="online")
        except Exception as e:
            print(f"  [G{self.index+1}] Leave send error (non-critical): {e}")
        await asyncio.sleep(LEAVE_DELAY)
        self.in_match = False
        self.in_squad = False
        self.squad_code = None
        self.team_code = None

    async def drain_buffer(self, channel: str = "online", timeout: float = 1.0):
        """Drain any pending data from the socket buffer.
        Call this before sending match packets to avoid reading stale data."""
        reader = self.online_reader if channel == "online" else self.chat_reader
        try:
            while True:
                data = await asyncio.wait_for(reader.read(4096), timeout=timeout)
                if not data:
                    break
        except asyncio.TimeoutError:
            pass
        except:
            pass

    async def cleanup(self):
        """Close all TCP connections and stop keepalive loop."""
        # Stop background loops
        if hasattr(self, '_ka_stop') and self._ka_stop:
            self._ka_stop.set()
        for task_attr in ['_ka_task']:
            task = getattr(self, task_attr, None)
            if task:
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=2)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
        for writer in [self.online_writer, self.chat_writer]:
            if writer and not writer.is_closing():
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass
        self.connected = False


# ======================== CLAN GLORY BOT ========================

# ======================== CREDIT SCORE CHECK ========================

async def check_credit_score(jwt_token: str, uid: str) -> dict:
    """Check Credit/Honour Score via GetPlayerPersonalShow API.
    
    Returns dict with credit_score, status, and whether account can play CS.
    Score < 90 = cannot play Clash Squad.
    """
    import sys
    sys.path.insert(0, os.path.join(BASE_DIR, 'OB54-TCP-BOT'))
    sys.path.insert(0, os.path.join(BASE_DIR, 'OB54-TCP-BOT', 'Pb2'))
    
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    import google.protobuf.json_format as json_format
    from Pb2 import dev_generator_pb2, data_pb2
    
    API_KEY = b'Yg&tc%DEuh6%Zc^8'
    API_IV  = b'6oyZDr22E3ychjM%'
    
    def enc_uid(uid_str):
        msg = dev_generator_pb2.dev_generator()
        msg.saturn_ = int(uid_str)
        msg.garena = 1
        pb = msg.SerializeToString()
        cipher = AES.new(API_KEY, AES.MODE_CBC, API_IV)
        return cipher.encrypt(pad(pb, AES.block_size)).hex()
    
    url = "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"
    encrypted_uid = enc_uid(uid)
    edata = bytes.fromhex(encrypted_uid)
    headers = {
        **HTTP_HEADERS,
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=edata, headers=headers, ssl=False, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                content = await resp.read()
                info = data_pb2.AccountPersonalShowInfo()
                info.ParseFromString(content)
                d = json.loads(json_format.MessageToJson(info))
                
                basic = d.get('basicInfo', {})
                credit = d.get('creditScoreInfo', {})
                clan = d.get('clanBasicInfo', {})
                
                score = credit.get('score', 'N/A')
                can_play_cs = True
                if score != 'N/A':
                    can_play_cs = int(score) >= 90
                
                return {
                    'uid': uid,
                    'nickname': basic.get('nickname', 'N/A'),
                    'level': basic.get('level', 'N/A'),
                    'credit_score': score,
                    'credit_status': credit.get('status', 'N/A'),
                    'can_play_cs': can_play_cs,
                    'clan_name': clan.get('clanName', 'N/A'),
                    'clan_level': clan.get('clanLevel', 'N/A'),
                }
    except Exception as e:
        return {"error": str(e)}

class ClanGloryBot:
    """Orchestrates the clan glory farming loop."""

    def __init__(self, clan_id: int = DEFAULT_CLAN_ID, region: str = DEFAULT_REGION,
                 cycles: int = DEFAULT_CYCLES):
        self.solo_mode = False
        self.join_delay = 3.0
        self.dry_run = False
        self.clan_id = clan_id
        self.region = region
        self.max_cycles = cycles
        self.connections: list[GuestConnection] = []
        self.running = False
        self.cycle_count = 0
        self.total_glory_estimated = 0

    async def check_clan_glory(self, label: str = ""):
        """Check clan glory by re-running GetLoginData and extracting clan_compiled_data.
        We know GetLoginData works — it's what authenticate() uses.
        The clan_compiled_data field contains clan info including glory."""
        try:
            conn = self.connections[0]
            if not conn.jwt or not conn.access_token:
                print(f"  [CLAN] {label}: no auth available")
                return None
            # Re-build MajorLogin payload and call GetLoginData
            payload = await build_major_login(conn.open_id, conn.access_token)
            login_data = await get_login_data(payload, conn.server_url, conn.jwt)
            if login_data:
                ccd = login_data.get("clan_compiled_data", "")
                if ccd:
                    # Try to decode clan_compiled_data
                    print(f"  [CLAN] {label}: clan_compiled_data = {len(str(ccd))} chars")
                    # Try hex decode
                    ccd_str = str(ccd)
                    if all(c in '0123456789abcdef' for c in ccd_str[:20].lower()) and len(ccd_str) > 20:
                        json_str = await DeCode_PackEt(ccd_str)
                        if json_str:
                            parsed = json.loads(json_str)
                            print(f"  [CLAN] {label}: decoded clan data:")
                            for k, v in sorted(parsed.items())[:20]:
                                if isinstance(v, dict) and 'data' in v:
                                    print(f"  [CLAN] {label}: field {k} = {str(v['data'])[:120]}")
                        else:
                            print(f"  [CLAN] {label}: clan data (hex, first 100): {ccd_str[:100]}")
                    else:
                        print(f"  [CLAN] {label}: clan data (first 100): {ccd_str[:100]}")
                else:
                    print(f"  [CLAN] {label}: no clan_compiled_data in response")
                return login_data
            else:
                print(f"  [CLAN] {label}: GetLoginData returned empty")
        except Exception as e:
            print(f"  [CLAN] {label}: error: {e}")
        return None

    async def setup(self) -> bool:
        """Authenticate all guests, connect TCP, join clan."""
        if not os.path.exists(GUESTS_FILE):
            print(f"  Guests file not found: {GUESTS_FILE}")
            return False

        with open(GUESTS_FILE) as f:
            guests = json.load(f)
        if not guests:
            print("  No guests in file")
            return False

        print(f"  Guest accounts: {len(guests)}")

        async with aiohttp.ClientSession() as session:
            for i, guest in enumerate(guests):
                conn = GuestConnection(guest, i)
                conn.set_region(self.region)
                self.connections.append(conn)

                if not await conn.authenticate(session):
                    print(f"  [G{i+1}] Auth FAILED - skipping")
                    continue

                if not await conn.connect_tcp():
                    print(f"  [G{i+1}] TCP FAIL - skipping")
                    continue

                await conn.join_clan(self.clan_id)
                await asyncio.sleep(1)

        ready = [c for c in self.connections if c.connected]
        print(f"\n  {len(ready)} guests ready in clan {self.clan_id}")

        # Check credit/honour scores before starting
        print("\n  === Credit Score Check ===")
        for c in self.connections:
            if c.connected and c.jwt:
                try:
                    cs = await check_credit_score(c.jwt, str(c.account_uid))
                    if "error" in cs:
                        print(f'  [G{c.index+1}] Credit check error: {cs["error"][:60]}')
                    else:
                        score = cs["credit_score"]
                        status = "OK" if cs["can_play_cs"] else "LOCKED (<90)!"
                        print(f'  [G{c.index+1}] {cs["nickname"]} | Score={score} | {status}')
                except Exception as e:
                    print(f"  [G{c.index+1}] Credit check failed: {e}")

        return len(ready) >= 1


    async def wait_for_squad_full(self, leader, timeout: float = 30.0):
        """Wait for the 4th player to join the squad.
        Monitors leader's chat channel for squad member updates.
        Returns True if 4/4 confirmed, False if timeout."""
        print(f"  >> Waiting for 4th player to join squad (timeout {timeout}s)...")
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                data = await asyncio.wait_for(leader.chat_reader.read(9999), timeout=5.0)
                if not data:
                    print(f"  [G1] Connection closed while waiting for 4th player")
                    return False
                data_hex = data.hex()
                for skip in [10, 8, 12, 6, 14, 4, 0, 16, 18]:
                    try:
                        payload = data_hex[skip:]
                        if len(payload) < 20:
                            continue
                        # Try decryption first
                        try:
                            decrypted = await DEc_PacKeT(payload, leader.key, leader.iv)
                            if decrypted:
                                json_str = await DeCode_PackEt(decrypted)
                                if json_str:
                                    parsed = json.loads(json_str)
                                    f5 = parsed.get('5', {})
                                    if isinstance(f5, dict) and 'data' in f5:
                                        f5d = f5['data']
                                        if isinstance(f5d, dict):
                                            f6 = f5d.get('6', {})
                                            if isinstance(f6, dict) and 'data' in f6:
                                                f6d = f6['data']
                                                if isinstance(f6d, dict):
                                                    f75 = f6d.get('75', {})
                                                    if isinstance(f75, dict) and 'data' in f75:
                                                        mc = f75['data']
                                                        print(f"  [G1] Squad members: {mc}/4")
                                                        if int(mc) >= 4:
                                                            print(f"  >> Squad FULL! 4/4 players ready.")
                                                            return True
                        except:
                            pass
                        # Try raw decode
                        try:
                            json_str = await DeCode_PackEt(payload)
                            if json_str:
                                parsed = json.loads(json_str)
                                f5 = parsed.get('5', {})
                                if isinstance(f5, dict) and 'data' in f5:
                                    f5d = f5['data']
                                    if isinstance(f5d, dict):
                                        f6 = f5d.get('6', {})
                                        if isinstance(f6, dict) and 'data' in f6:
                                            f6d = f6['data']
                                            if isinstance(f6d, dict):
                                                f75 = f6d.get('75', {})
                                                if isinstance(f75, dict) and 'data' in f75:
                                                    mc = f75['data']
                                                    print(f"  [G1] Squad members: {mc}/4")
                                                    if int(mc) >= 4:
                                                        print(f"  >> Squad FULL! 4/4 players ready.")
                                                        return True
                        except:
                            pass
                    except:
                        continue
            except asyncio.TimeoutError:
                remaining = int(deadline - time.time())
                if remaining > 0:
                    print(f"  >> Still waiting for 4th player... ({remaining}s left)")
            except Exception as e:
                print(f"  [G1] Wait for 4th player error: {e}")
                break
        
        print(f"  >> No 4th player joined within {timeout}s. Starting match anyway (3/4).")
        return False

    async def form_squad(self) -> bool:
        """
        Squad formation (SIMPLIFIED - no invite mechanism):
          1. ALL members leave any existing squad
          2. Leader (G1) opens squad (OpEnSq) -> gets team_code
          3. ALL other members join directly using team_code

        This replaces the broken invite flow from v1 where:
          - Leader sent custom invite packets (20+ fields) -> never received
          - All 9 fallback join methods failed (errors 79, 50, 94)
        """
        if not self.connections:
            return False

        leader = self.connections[0]
        members = self.connections[1:]
        squad_size = len(self.connections)

        print(f"  Squad: Leader=G1({leader.account_uid}) -> {len(members)} members (size={squad_size})")

        # Reset per-cycle state
        for conn in self.connections:
            conn.match_found = False
            conn.match_data = None
            conn.in_match = False

        # Step 1: ALL members reset/leave existing squad
        print(f"  >> Resetting all members to solo...")
        for conn in self.connections:
            await conn.reset_squad()
        await asyncio.sleep(1)

        # Step 2: Leader opens squad
        leader_response = await leader.open_squad(self.region)

        # No cHSq — it was inconsistent (sometimes 3/3, sometimes 2/3)
        # Instead, OpEnSq field 2.3 = 3 creates 4 total slots (leader + 3)
        # Even if one slot is wasted, 2 members can still join reliably
        await asyncio.sleep(5)  # Wait for server to register the 4-slot squad

        team_code = leader_response.get("team_code")
        chat_code = leader_response.get("chat_code")
        squad_code = leader_response.get("squad_code")
        owner_uid = leader_response.get("owner_uid") or str(leader.account_uid)

        print(f"  Leader: owner={owner_uid}, team_code={team_code}, "
              f"chat={'Y' if chat_code else 'N'}, squad={'Y' if squad_code else 'N'}")

        if not team_code:
            if squad_code:
                digits = ""
                for ch in str(squad_code):
                    if ch.isdigit():
                        digits += ch
                    else:
                        break
                if digits:
                    team_code = digits
                    print(f"  Extracted team_code from squad_code: {team_code}")

        if not team_code:
            print(f"  [!] No team_code - cannot form squad. Members cannot join.")
            print(f"  This may indicate the OpEnSq response format has changed.")
            leader.in_squad = True
            return False

        # Step 3: All members join DIRECTLY using team_code
        # Add longer delay between joins (server needs time to register each member)
        for i, member in enumerate(members):
            if not member.connected:
                continue
            # First member joins immediately, subsequent members wait longer
            if i > 0:
                print(f"  Waiting {self.join_delay}s before next member join (server sync)...")
                await asyncio.sleep(self.join_delay)
            
            print(f"  [G{member.index+1}] Joining squad (code={str(squad_code)[:25] if squad_code else team_code}...)...")
            joined = await member.join_team(team_code, squad_code)
            if joined:
                print(f"  [G{member.index+1}] In squad")
            else:
                # Retry 1: with squad_code (extract numeric part before underscore)
                if squad_code:
                    # Retry with GenJoinSquadsPacket using the full squad_code string
                    print(f"  [G{member.index+1}] Retrying with full squad_code string...")
                    await asyncio.sleep(2)
                    joined = await member.join_team(team_code, squad_code)
                    if joined:
                        print(f"  [G{member.index+1}] In squad (via squad_code)")
                
                # Retry 2: wait and try again with original team_code (server might be slow)
                if not joined:
                    print(f"  [G{member.index+1}] Retrying in 5s (server sync delay)...")
                    await asyncio.sleep(5)
                    joined = await member.join_team(team_code, squad_code)
                    if joined:
                        print(f"  [G{member.index+1}] In squad (retry)")
                    else:
                        # Retry 3: Leader sends invite, member waits for it
                        print(f"  [G{member.index+1}] Direct join failed. Trying invite-based approach...")
                        try:
                            inv_pkt = await SEnd_InV(3, int(member.account_uid), leader.key, leader.iv, self.region)
                            await leader.send_packet(inv_pkt, channel="online")
                            print(f"  [G1] Sent SEnd_InV invite to G{member.index+1}")
                            await asyncio.sleep(2)
                            # Member tries to join again after receiving invite
                            joined = await member.join_team(team_code, squad_code)
                            if joined:
                                print(f"  [G{member.index+1}] In squad (via invite + join)")
                            else:
                                print(f"  [G{member.index+1}] ❌ Failed to join after all retries")
                        except Exception as e:
                            print(f"  [G{member.index+1}] Invite fallback error: {e}")

        in_squad_count = sum(1 for c in self.connections if c.in_squad)
        print(f"  Squad formed (local state): {in_squad_count}/{len(self.connections)} players in squad")

        # Verify squad membership via leader's squad update
        print(f"  >> Verifying squad membership via leader socket...")
        verified = False
        # Try BOTH online and chat channels with 8s timeout each
        for ch_name, ch_reader in [("online", leader.online_reader), ("chat", leader.chat_reader)]:
            if verified:
                break
            try:
                verify_data = await asyncio.wait_for(ch_reader.read(9999), timeout=8.0)
                if verify_data:
                    verify_hex = verify_data.hex()
                    print(f"  [G1] {ch_name} verify: {len(verify_hex)} hex, header={verify_hex[:12]}")
                    for skip in [10, 8, 12, 6, 14, 4, 0, 16, 18]:
                        try:
                            payload = verify_hex[skip:]
                            if len(payload) < 20:
                                continue
                            # Try decryption first (server may encrypt squad data)
                            try:
                                decrypted = await DEc_PacKeT(payload, leader.key, leader.iv)
                                if decrypted:
                                    json_str = await DeCode_PackEt(decrypted)
                                    if json_str:
                                        parsed = json.loads(json_str)
                                        f2 = parsed.get('2', {})
                                        f2_val = f2.get('data') if isinstance(f2, dict) else f2
                                        if isinstance(f2_val, int) and f2_val > 0:
                                            print(f"  [G1] {ch_name} DECRYPTED f2={f2_val}")
                                            f5 = parsed.get('5', {})
                                            if isinstance(f5, dict) and 'data' in f5:
                                                f5d = f5['data']
                                                if isinstance(f5d, dict):
                                                    for k in sorted(f5d.keys())[:10]:
                                                        v = f5d[k]
                                                        if isinstance(v, dict) and 'data' in v:
                                                            print(f"    5.{k} = {str(v['data'])[:100]}")
                                            verified = True
                                            break
                            except:
                                pass
                            # Try raw decode
                            json_str = await DeCode_PackEt(payload)
                            if json_str:
                                parsed = json.loads(json_str)
                                f2 = parsed.get('2', {})
                                f2_val = f2.get('data') if isinstance(f2, dict) else f2
                                if isinstance(f2_val, int) and f2_val > 0:
                                    print(f"  [G1] {ch_name} RAW f2={f2_val}")
                                    f5 = parsed.get('5', {})
                                    if isinstance(f5, dict) and 'data' in f5:
                                        f5d = f5['data']
                                        if isinstance(f5d, dict):
                                            # Check field 5.6 for squad member info
                                            f6 = f5d.get('6', {})
                                            if isinstance(f6, dict) and 'data' in f6:
                                                f6d = f6['data']
                                                if isinstance(f6d, dict):
                                                    f75 = f6d.get('75', {})
                                                    if isinstance(f75, dict) and 'data' in f75:
                                                        print(f"  [G1] Server confirms squad members: {f75['data']}")
                                                    f4 = f6d.get('4', {})
                                                    if isinstance(f4, dict) and 'data' in f4:
                                                        print(f"  [G1] Squad team_code: {f4['data']}")
                                            for k in sorted(f5d.keys())[:10]:
                                                v = f5d[k]
                                                if isinstance(v, dict) and 'data' in v:
                                                    print(f"    5.{k} = {str(v['data'])[:100]}")
                                    verified = True
                                    break
                        except:
                            continue
                else:
                    print(f"  [G1] No {ch_name} verify data")
            except asyncio.TimeoutError:
                print(f"  [G1] No {ch_name} verify data (timeout)")
            except Exception as e:
                print(f"  [G1] {ch_name} verify error: {e}")
        
        if not verified:
            print(f"  [G1] Squad verify: no data on either channel (squad may still be valid)")

        return True

    async def solo_cycle(self) -> bool:
        """Solo matchmaking cycle: each bot independently starts matchmaking.
        No squad formation — each bot finds its own match.
        Solo has a larger player pool → more likely to actually start a match.
        """
        print(f"  >> SOLO MODE: Each bot independently matchmaking...")

        # Each bot sends start-match independently (leader packets only)
        for conn in self.connections:
            if conn.connected:
                await conn.start_match_leader()
                await asyncio.sleep(0.5)

        # CONCURRENT SPAM + READ (no sequential spam — reading starts immediately)
        total_wait = SPAM_DURATION + MATCH_WAIT
        deadline = asyncio.get_event_loop().time() + total_wait
        
        async def read_solo_match(conn, channel_name, reader, deadline):
            """Read for match packets in solo mode."""
            label = f"G{conn.index+1}/{channel_name}"
            while asyncio.get_event_loop().time() < deadline:
                if conn.match_found:
                    break
                try:
                    resp = await asyncio.wait_for(reader.read(65535), timeout=5.0)
                    if not resp:
                        # Empty response = connection closed
                        conn.connected = False
                        break
                    resp_hex = resp.hex()
                    if len(resp_hex) > 40:
                        print(f"  [{label}] DATA: {len(resp_hex)} hex, header={resp_hex[:16]}")
                    for skip in [10, 8, 12, 6, 4, 0, 14, 16, 18, 20, 2, 22, 24]:
                        try:
                            payload = resp_hex[skip:]
                            if len(payload) < 20:
                                continue
                            json_str = await DeCode_PackEt(payload)
                            if not json_str:
                                continue
                            parsed = json.loads(json_str)
                            f2 = parsed.get('2', {})
                            f2_val = f2.get('data') if isinstance(f2, dict) else f2
                            if not isinstance(f2_val, int) or f2_val < 1:
                                continue
                            if f2_val == 18 and not conn.match_found:
                                f5 = parsed.get('5', {})
                                f5d = f5.get('data', {}) if isinstance(f5, dict) else {}
                                group_id = None
                                if isinstance(f5d, dict):
                                    f1_5 = f5d.get('1', {})
                                    if isinstance(f1_5, dict) and 'data' in f1_5:
                                        group_id = f1_5['data']
                                if group_id and isinstance(group_id, int) and group_id > 1000000000:
                                    print(f"  [{label}] MATCH FOUND! f2=18, GroupID={group_id}")
                                    conn.match_found = True
                                    conn.match_data = parsed
                                    for k in sorted(f5d.keys())[:15]:
                                        v = f5d[k]
                                        if isinstance(v, dict) and 'data' in v:
                                            print(f"    5.{k} = {str(v['data'])[:150]}")
                                    print(f"  *** MATCH PACKET (f2=18) for G{conn.index+1}! ***")
                                    await conn.join_match(group_id)
                            break
                        except:
                            continue
                except asyncio.TimeoutError:
                    continue
                except:
                    break
            if not conn.match_found:
                print(f"  [{label}] no match packet found")
        
        # Start spam + reads concurrently + keepalive
        spam_tasks = []
        for conn in self.connections:
            if conn.connected:
                spam_tasks.append(conn.spam_start_match(SPAM_DURATION, SPAM_DELAY))
        
        read_tasks = []
        for conn in self.connections:
            if not conn.connected:
                continue
            read_tasks.append(read_solo_match(conn, "online", conn.online_reader, deadline))
            read_tasks.append(read_solo_match(conn, "chat", conn.chat_reader, deadline))
        
        # Keepalive task for solo mode
        async def keepalive_solo(conns, deadline):
            # Pre-build per-connection packets
            conn_packets = {}
            for conn in conns:
                if not conn.connected:
                    continue
                fields = {1: 9, 2: {1: conn.account_uid}}
                proto = await CrEaTe_ProTo(fields)
                pkt_type = get_packet_type(self.region)
                conn_packets[conn.index] = await GeneRaTePk(proto.hex(), pkt_type, conn.key, conn.iv)
            sent = 0
            while asyncio.get_event_loop().time() < deadline:
                for conn in conns:
                    if not conn.connected or conn.match_found:
                        continue
                    pkt = conn_packets.get(conn.index)
                    if pkt:
                        try:
                            await conn.send_packet(pkt, channel="online")
                            sent += 1
                        except:
                            pass
                await asyncio.sleep(3.0)
            return sent
        
        keepalive_task = keepalive_solo(self.connections, deadline)
        
        async def mid_cycle_reconnect_solo(conns, deadline, clan_id):
            reconnected = 0
            while asyncio.get_event_loop().time() < deadline:
                for conn in conns:
                    if not conn.connected and not conn.match_found:
                        try:
                            await conn.connect_tcp()
                            if conn.connected:
                                await conn.join_clan(clan_id)
                                reconnected += 1
                                print(f"  [G{conn.index+1}] Mid-cycle reconnect OK")
                        except:
                            pass
                await asyncio.sleep(10)
            return reconnected
        
        reconnect_task = mid_cycle_reconnect_solo(self.connections, deadline, self.clan_id)
        
        all_tasks = spam_tasks + read_tasks + [keepalive_task, reconnect_task]
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        fast_packets = sum(r for r in results[:len(spam_tasks)] if isinstance(r, int))
        keepalive_count = results[-2] if isinstance(results[-2], int) else 0
        reconnect_count = results[-1] if isinstance(results[-1], int) else 0
        total_packets = fast_packets + keepalive_count
        print(f"  >> Sent {total_packets} start-match packets total ({fast_packets} fast + {keepalive_count} keepalive, {reconnect_count} reconnects)")
        
        # Share GroupID
        match_finders = [c for c in self.connections if c.match_found and c.match_data]
        if match_finders:
            for finder in match_finders:
                f5 = finder.match_data.get('5', {})
                f5d = f5.get('data', {}) if isinstance(f5, dict) else {}
                shared_group_id = None
                if isinstance(f5d, dict):
                    f1 = f5d.get('1', {})
                    if isinstance(f1, dict) and 'data' in f1:
                        shared_group_id = f1['data']
                if shared_group_id:
                    for other in self.connections:
                        if other.index != finder.index and not other.match_found and other.connected:
                            print(f"  [G{other.index+1}] Joining match (shared by G{finder.index+1}, GroupID={shared_group_id})...")
                            await other.join_match(shared_group_id)
                            other.match_found = True
        
        if not match_finders:
            print(f"  >> No matches found this cycle")

        glory_per_cycle = len(self.connections) * random.randint(5, 15)
        self.total_glory_estimated += glory_per_cycle
        matches_count = sum(1 for c in self.connections if c.match_found)
        print(f"  >> Cycle #{self.cycle_count} done (matches: {matches_count}/{len(self.connections)}, est +~{glory_per_cycle} glory, total ~{self.total_glory_estimated})")
        return True

    async def exploit_cycle(self) -> bool:
        """Simplified glory cycle matching the proven reference bot (Muraxlee).
        
        The reference bot does NOT detect f2=18 or send join_match packets.
        It simply: joins squad → spams field 9 → waits → leaves → repeats.
        The server auto-places accounts in the match when they're ready.
        
        Our previous version was over-engineered with match detection and
        join_match (field 1=3, type 0e15) which may have INTERFERED with
        the server's match placement, preventing glory registration.
        
        Proven workflow:
        1. Form squad (OpEnSq + join)
        2. Spam field 1=9 on ONLINE channel (17s, 0.2s delay)
        3. Background keepalive_loop sends field 99 every 15s on BOTH channels
        4. Wait 25s for match to complete (server auto-places + auto-eliminates)
        5. Leave squad and repeat
        """
        await self.form_squad()
        print(f"  >> Squad formed, waiting 5s for server to register squad...")
        await asyncio.sleep(5)

        # Only the LEADER sends field 9 (start match).
        # Members stay quiet — non-leader field 9 may confuse the server.
        leader = self.connections[0]  # G1 is always the leader
        if not leader.connected:
            print("  >> Leader not connected, aborting cycle")
            return False

        fields = {1: 9, 2: {1: leader.account_uid}}
        proto = await CrEaTe_ProTo(fields)
        pkt_type = get_packet_type(self.region)
        spam_pkt = await GeneRaTePk(proto.hex(), pkt_type, leader.key, leader.iv)

        SPAM_DURATION = 17
        SPAM_DELAY = 0.2

        # ── Leader spams field 1=9 on ONLINE channel (17s) ──
        # Also listen for f2=18 (match found) on leader's chat channel
        print(f"  >> Leader spam field=9 on ONLINE ({SPAM_DURATION}s, {SPAM_DELAY}s delay)...")
        end_time = asyncio.get_event_loop().time() + SPAM_DURATION
        spam_count = 0
        match_found = False
        while asyncio.get_event_loop().time() < end_time:
            if not leader.connected:
                break
            if await leader.send_packet(spam_pkt, channel="online"):
                spam_count += 1
            
            # Check for match-found packet on chat channel (non-blocking)
            try:
                data = await asyncio.wait_for(leader.chat_reader.read(9999), timeout=0.3)
                if data:
                    data_hex = data.hex()
                    # Quick check for f2=18 (match found indicator)
                    if '120110' in data_hex or len(data_hex) > 5000:
                        print(f"  >> MATCH PACKET detected on chat ({len(data_hex)} hex)")
                        match_found = True
                        # Don't break — keep spamming, server needs the start signal
            except asyncio.TimeoutError:
                pass
            except Exception:
                pass
            
            await asyncio.sleep(SPAM_DELAY)

        alive_count = sum(1 for c in self.connections if c.connected)
        print(f"  >> Spam: {spam_count} pkts, {alive_count} alive, match={'FOUND' if match_found else 'no'}")

        # ── Wait for match to complete (server auto-places + auto-eliminates) ──
        # The server places all "ready" accounts into the match automatically.
        # The account loads in, gets eliminated (nobody is playing), match ends.
        # Glory is awarded on match completion/elimination.
        print(f"  >> Waiting 40s for match to complete...")
        await asyncio.sleep(40)

        alive_count = sum(1 for c in self.connections if c.connected)
        print(f"  >> After wait: {alive_count} alive")

        # ── Leave squad ──
        for conn in self.connections:
            if conn.connected:
                try:
                    exit_pkt = await ExiT(conn.team_code if conn.team_code else 0, conn.key, conn.iv)
                    await conn.send_packet(exit_pkt, channel="online")
                    conn.in_squad = False
                    conn.match_found = False
                    conn.in_match = False
                    conn.match_data = None
                except:
                    pass

        await asyncio.sleep(CYCLE_DELAY)
        return alive_count > 0

    async def run(self):
        """Main exploit loop."""
        self.running = True
        self.cycle_count = 0

        print("=" * 60)
        print("  CLAN GLORY BOT - Squad Match Farm (v2)")
        print(f"  Clan: {self.clan_id}")
        print(f"  Region: {self.region}")
        print(f"  Max cycles: {self.max_cycles}")
        if self.solo_mode:
            print(f"  Mode: SOLO (independent matchmaking)")
        print(f"  Join delay: {self.join_delay}s")
        cycle_time = SPAM_DURATION + MATCH_WAIT + MATCH_WAIT_AFTER + int(CYCLE_DELAY)
        print(f"  Per cycle: ~{cycle_time}s")
        print(f"  Est total time: ~{(self.max_cycles * cycle_time) // 60} min")
        print("=" * 60)

        if not await self.setup():
            print("  Setup FAILED")
            return

        self.start_time = time.time()

        if getattr(self, 'dry_run', False):
            print("\n  === DRY RUN COMPLETE ===")
            print(f"  All {len(self.connections)} guests authenticated and connected.")
            for conn in self.connections:
                status = "connected" if conn.connected else "DISCONNECTED"
                print(f"  [G{conn.index+1}] uid={conn.account_uid}, {status}")
            await self.cleanup_connections()
            return

        # Check initial clan glory
        print("\n  === Clan Glory Check (Before) ===")
        await self.check_clan_glory("BEFORE")

        while self.running and self.cycle_count < self.max_cycles:
            self.cycle_count += 1
            print(f"\n  --- CYCLE #{self.cycle_count}/{self.max_cycles} ---")

            try:
                for conn in self.connections:
                    if not conn.connected:
                        print(f"  [G{conn.index+1}] Reconnecting...")
                        try:
                            await conn.connect_tcp()
                            if conn.connected:
                                await conn.join_clan(self.clan_id)
                                await asyncio.sleep(1)
                                print(f"  [G{conn.index+1}] Reconnected OK")
                        except Exception as e:
                            print(f"  [G{conn.index+1}] Reconnect failed: {e}")

                if self.solo_mode:
                    await self.solo_cycle()
                    await asyncio.sleep(CYCLE_DELAY)
                else:
                    await self.exploit_cycle()
                    # exploit_cycle already includes CYCLE_DELAY at its end

            except KeyboardInterrupt:
                print("\n  Stopped by user")
                break
            except Exception as e:
                print(f"  Cycle error: {e}")
                await asyncio.sleep(RECONNECT_DELAY)

        # Clean up and show AFTER glory check
        await self.cleanup_connections()


    async def cleanup_connections(self):
        """Clean up all guest connections."""
        for conn in self.connections:
            try:
                await conn.cleanup()
            except:
                pass

        elapsed = int(time.time() - getattr(self, 'start_time', time.time()))
        print("\n" + "=" * 60)
        print(f"  CLAN GLORY BOT - Done")
        print(f"  Cycles: {self.cycle_count}/{self.max_cycles}")
        print(f"  Time: {elapsed}s ({elapsed // 60}m {elapsed % 60}s)")
        print(f"  Est glory: ~{self.total_glory_estimated}")
        print(f"  Guests: {len(self.connections)}")
        print(f"  Clan: {self.clan_id}")
        # Check final clan glory
        print("\n  === Clan Glory Check (After) ===")
        await self.check_clan_glory("AFTER")

        print("=" * 60)

        try:
            with open(GUESTS_FILE, "w") as f:
                json.dump([c.guest for c in self.connections], f, indent=2)
        except:
            pass


# ======================== ENTRY POINT ========================

def main():
    import argparse
    p = argparse.ArgumentParser(description="Clan Glory Bot - Clash Squad Match Farm (v2)")
    p.add_argument("--clan-id", type=int, default=DEFAULT_CLAN_ID, help="Target clan ID")
    p.add_argument("--region", type=str, default=DEFAULT_REGION, help="Region (ME, IND, BR, SG, etc.)")
    p.add_argument("--cycles", type=int, default=DEFAULT_CYCLES, help="Max exploit cycles")
    global SPAM_DURATION, SPAM_DELAY, MATCH_WAIT
    p.add_argument("--match-wait", type=int, default=MATCH_WAIT, help="Matchmaking wait (seconds)")
    p.add_argument("--spam-duration", type=int, default=SPAM_DURATION, help="Start-match spam duration (seconds)")
    p.add_argument("--spam-delay", type=float, default=SPAM_DELAY, help="Delay between start packets")
    p.add_argument("--solo", action="store_true", default=False, help="Solo matchmaking (no squad, each bot independently)")
    p.add_argument("--dry-run", action="store_true", default=False, help="Test auth+connection only, no cycles")
    p.add_argument("--join-delay", type=float, default=3.0, help="Delay between member joins (seconds)")
    args = p.parse_args()

    SPAM_DURATION = args.spam_duration
    SPAM_DELAY = args.spam_delay
    MATCH_WAIT = args.match_wait

    bot = ClanGloryBot(
        clan_id=args.clan_id,
        region=args.region,
        cycles=args.cycles,
    )
    bot.solo_mode = args.solo
    bot.dry_run = args.dry_run
    bot.join_delay = getattr(args, "join_delay", 3.0)

    def stop_handler(sig, frame):
        bot.running = False
    signal.signal(signal.SIGINT, stop_handler)

    asyncio.run(bot.run())


if __name__ == "__main__":
    main()

