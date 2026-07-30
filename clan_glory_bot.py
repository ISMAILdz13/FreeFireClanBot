"""
Clan Glory Bot — Clash Squad Match Farm
==================================================
Farm clan glory by entering Clash Squad matches with clan members and
letting the match complete. Based on the working level bot's match engine.
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
SPAM_DURATION      = 18   # seconds to spam start_match packets (like level bot)
SPAM_DELAY         = 0.2  # delay between start_match packets
MATCH_WAIT         = 20   # seconds to wait for match to complete
LEAVE_DELAY        = 2.0  # seconds after leaving team
CYCLE_DELAY        = 3.0  # seconds between cycles
RECONNECT_DELAY    = 3
PACKET_INTERVAL    = 0.5  # seconds between TCP packets

# Region to packet type mapping
REGION_PACKETS = {"ind": "0514", "bd": "0519"}
DEFAULT_PACKET = "0515"

GUESTS_FILE = os.path.join(BASE_DIR, "data", "guests.json")


async def ArohiAccepted(uid, code, K, V):
    """Accept squad invite — field 1=4, includes owner UID + code.
    From TCP bot: field 2.1 = owner UID, 2.3 = owner UID, 2.10 = code."""
    from xC4 import CrEaTe_ProTo, GeneRaTePk
    fields = {
        1: 4,
        2: {
            1: int(uid),
            3: int(uid),
            8: 1,
            9: {
                2: 161,
                4: "y[WW",
                6: 11,
                8: "1.114.18",
                9: 3,
                10: 1,
            },
            10: str(code),
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), "0515", K, V)


async def AutH_Chat(T, uid, code, K, V):
    """Authenticate squad chat — TCP bot calls this after joining squad."""
    from xC4 import CrEaTe_ProTo, GeneRaTePk
    fields = {
        1: T,
        2: {
            1: int(uid),
            3: "en",
            4: str(code),
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), "1215", K, V)

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
        self.region = "ME"
        self._listen_task = None

    def set_region(self, region: str):
        """Set the region for packet type mapping."""
        self.region = region

    async def read_invite_code(self, timeout: float = 8.0) -> dict:
        """
        Read invite packet(s) from Online socket.
        Reads multiple times, searches for '0500' packet type.
        Extracts: owner_uid (5.1) and invite_code (5.8).
        TCP bot flow: field5_data.get('1') = squad_owner, field5_data.get('8') = code.
        """
        result = {"owner_uid": None, "invite_code": None}

        # Read up to 3 times to catch all packets
        all_data_hex = ""
        for read_num in range(3):
            try:
                data = await asyncio.wait_for(self.online_reader.read(9999), timeout=timeout / 3)
                if data:
                    all_data_hex += data.hex()
            except asyncio.TimeoutError:
                break
            except:
                break

        if not all_data_hex:
            print(f"  [G{self.index+1}] No invite data")
            return result

        print(f"  [G{self.index+1}] Invite data: {len(all_data_hex)} hex chars, starts: {all_data_hex[:20]}...")

        # Strategy 1: Search for "0500" and parse from there
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
                        # Field 5.1 = squad owner UID
                        f1 = field5_data.get('1', {})
                        if isinstance(f1, dict) and 'data' in f1:
                            result["owner_uid"] = str(f1['data'])
                        # Field 5.8 = invite code
                        f8 = field5_data.get('8', {})
                        if isinstance(f8, dict) and 'data' in f8:
                            result["invite_code"] = str(f8['data'])
                        if result["invite_code"]:
                            print(f"  [G{self.index+1}] Found at 0500@{idx}+{skip} ({attempt_name}): owner={result['owner_uid']}, invite={result['invite_code'][:25]}...")
                            return result
                    except:
                        pass
            idx = all_data_hex.find("0500", idx + 4)

        # Strategy 2: Try all offsets 0-60
        for offset in range(0, min(60, len(all_data_hex)), 2):
            payload = all_data_hex[offset:]
            if len(payload) < 20:
                break
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
                    f8 = field5_data.get('8', {})
                    if isinstance(f8, dict) and 'data' in f8:
                        result["invite_code"] = str(f8['data'])
                    if result["invite_code"]:
                        print(f"  [G{self.index+1}] Found at offset {offset} ({attempt_name}): owner={result['owner_uid']}, invite={result['invite_code'][:25]}...")
                        return result
                except:
                    pass

        print(f"  [G{self.index+1}] Could not extract invite code (tried 0500 search + all offsets)")
        return result

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

    async def reset_squad(self):
        """Leave any existing squad before forming a new one."""
        fields = {
            1: 7,
            2: {
                1: 12480598706,
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

    async def open_squad(self, region: str) -> dict:
        """
        OpEnSq — leader opens squad for matchmaking.
        READS the server response to extract owner_uid, invite_code, chat_code, squad_code.
        Returns a dict with all extracted fields.
        """
        packet = await OpEnSq(self.key, self.iv, region)
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)
        self.in_squad = True

        # Read the server response
        response = await self.read_squad_response()
        if response.get("squad_code"):
            self.squad_code = response["squad_code"]
            print(f"  [G{self.index+1}] Squad opened: owner={response.get('owner_uid')}, code={response['squad_code'][:30]}...")
        else:
            print(f"  [G{self.index+1}] Squad opened but limited info in response")
        return response

    async def read_squad_response(self, timeout: float = 8.0) -> dict:
        """
        Read TCP response(s) from Online channel after OpEnSq.
        Reads multiple times (up to 3) to find packets.
        Searches for '0500' packet type inside the data.
        Extracts: owner_uid (5.1), invite_code (5.8), chat_code (5.17), squad_code (5.31).
        """
        result = {"owner_uid": None, "invite_code": None, "chat_code": None, "squad_code": None}

        # Read up to 3 times to catch all packets
        all_data_hex = ""
        for read_num in range(3):
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

        # Strategy 1: Search for "0500" in the data and parse from there
        idx = all_data_hex.find("0500")
        while idx >= 0:
            for skip in [10, 8, 12, 6, 14, 16, 4, 18, 20]:
                payload = all_data_hex[idx + skip:]
                if len(payload) < 20:
                    continue
                # Try raw parse
                try:
                    json_str = await DeCode_PackEt(payload)
                    if json_str:
                        packet_json = json.loads(json_str)
                        if '5' in packet_json:
                            field5 = packet_json['5']
                            if isinstance(field5, dict) and 'data' in field5:
                                field5_data = field5['data']
                                if isinstance(field5_data, dict):
                                    self._extract_squad_fields(field5_data, result)
                                    print(f"  [G{self.index+1}] Parsed at 0500@{idx}+{skip} (raw): {self._debug_fields(result)}")
                                    if result["squad_code"] or result["invite_code"]:
                                        return result
                except:
                    pass
                # Try decrypt + parse
                try:
                    dec_hex = await DEc_PacKeT(payload, self.key, self.iv)
                    if dec_hex:
                        json_str = await DeCode_PackEt(dec_hex)
                        if json_str:
                            packet_json = json.loads(json_str)
                            if '5' in packet_json:
                                field5 = packet_json['5']
                                if isinstance(field5, dict) and 'data' in field5:
                                    field5_data = field5['data']
                                    if isinstance(field5_data, dict):
                                        self._extract_squad_fields(field5_data, result)
                                        print(f"  [G{self.index+1}] Parsed at 0500@{idx}+{skip} (dec): {self._debug_fields(result)}")
                                        if result["squad_code"] or result["invite_code"]:
                                            return result
                except:
                    pass
            # Look for next "0500"
            idx = all_data_hex.find("0500", idx + 4)

        # Strategy 2: Try all offsets 0-60 with raw and decrypted
        for offset in range(0, min(60, len(all_data_hex)), 2):
            payload = all_data_hex[offset:]
            if len(payload) < 20:
                break
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
                    self._extract_squad_fields(field5_data, result)
                    print(f"  [G{self.index+1}] Parsed at offset {offset} ({attempt_name}): {self._debug_fields(result)}")
                    if result["squad_code"] or result["invite_code"]:
                        return result
                except:
                    pass

        # Strategy 3: Try GeTSQDaTa at all offsets
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

        print(f"  [G{self.index+1}] Could not parse squad response (tried 0500 search + all offsets)")
        return result

    def _extract_squad_fields(self, field5_data: dict, result: dict):
        """Extract owner_uid (5.1), invite_code (5.8), chat_code (5.17), squad_code (5.31)."""
        f1 = field5_data.get('1', {})
        if isinstance(f1, dict) and 'data' in f1:
            result["owner_uid"] = str(f1['data'])
        f8 = field5_data.get('8', {})
        if isinstance(f8, dict) and 'data' in f8:
            result["invite_code"] = str(f8['data'])
        f17 = field5_data.get('17', {})
        if isinstance(f17, dict) and 'data' in f17:
            result["chat_code"] = str(f17['data'])
        f31 = field5_data.get('31', {})
        if isinstance(f31, dict) and 'data' in f31:
            result["squad_code"] = str(f31['data'])

    def _debug_fields(self, result: dict) -> str:
        parts = []
        for k in ["owner_uid", "invite_code", "chat_code", "squad_code"]:
            v = result.get(k)
            if v:
                parts.append(f"{k}={v[:20]}")
        return ", ".join(parts) if parts else "no fields"


    async def form_squad(self) -> bool:
        """
        Full squad formation (matches TCP bot flow):
        1. ALL members reset/leave existing squad
        2. Leader opens squad (OpEnSq) -> extracts owner_uid, chat_code, squad_code
        3. Leader invites each member (SEnd_InV)
        4. Each member READS their own invite packet -> extracts invite_code (5.8)
        5. Member accepts with ArohiAccepted(owner_uid, invite_code)
        6. Member authenticates squad chat with AutH_Chat(3, owner_uid, chat_code)
        """
        if not self.connections:
            return False

        leader = self.connections[0]
        members = self.connections[1:]

        print(f"  Squad: Leader=G1({leader.account_uid}) -> {len(members)} members")

        # Step 0: ALL members reset/leave any existing squad first
        print(f"  >> Resetting all members to solo...")
        for conn in self.connections:
            await conn.reset_squad()
        await asyncio.sleep(1)

        # Step 1: Leader opens squad and reads response
        leader_response = await leader.open_squad(self.region)
        await asyncio.sleep(2)

        owner_uid = leader_response.get("owner_uid") or str(leader.account_uid)
        chat_code = leader_response.get("chat_code")
        invite_code_from_leader = leader_response.get("invite_code")
        squad_code = leader_response.get("squad_code")

        print(f"  Leader: owner={owner_uid}, invite={'Y' if invite_code_from_leader else 'N'}, chat={'Y' if chat_code else 'N'}, squad={'Y' if squad_code else 'N'}")

        # Step 2: Leader invites each member
        for member in members:
            await leader.send_invite(member.account_uid, self.region)
            await asyncio.sleep(1)
        await asyncio.sleep(2)

        # Step 3: Each member reads invite packet and accepts
        for member in members:
            try:
                invite_code = invite_code_from_leader
                member_owner_uid = owner_uid

                if not invite_code:
                    # Member reads their own invite packet to get invite code (field 5.8)
                    print(f"  [G{member.index+1}] Reading invite packet...")
                    invite_data = await member.read_invite_code(timeout=5.0)
                    if invite_data.get("invite_code"):
                        invite_code = invite_data["invite_code"]
                    if invite_data.get("owner_uid"):
                        member_owner_uid = invite_data["owner_uid"]

                if invite_code:
                    # Accept invite with correct owner UID and invite code
                    accept_packet = await ArohiAccepted(member_owner_uid, invite_code, member.key, member.iv)
                    await member.send_packet(accept_packet)
                    await asyncio.sleep(1)

                    # Authenticate squad chat with chat_code (from leader's response)
                    if chat_code:
                        chat_auth_packet = await AutH_Chat(3, member_owner_uid, chat_code, member.key, member.iv)
                        await member.send_packet(chat_auth_packet, channel="chat")
                        print(f"  [G{member.index+1}] ✅ Accepted + chat auth (invite: {str(invite_code)[:25]}...)")
                    else:
                        print(f"  [G{member.index+1}] ✅ Accepted invite (no chat code)")

                    member.in_squad = True
                elif squad_code:
                    # Fallback: try squad code from field 5.31
                    accept_packet = await ArohiAccepted(member_owner_uid, squad_code, member.key, member.iv)
                    await member.send_packet(accept_packet)
                    member.in_squad = True
                    print(f"  [G{member.index+1}] ⚠ Accepted with squad_code fallback: {str(squad_code)[:25]}...")
                else:
                    print(f"  [G{member.index+1}] ❌ No invite code — cannot join squad")
            except Exception as e:
                print(f"  [G{member.index+1}] Join squad failed: {e}")
            await asyncio.sleep(1)

        in_squad_count = sum(1 for c in self.connections if c.in_squad)
        print(f"  Squad formed: {in_squad_count}/{len(self.connections)} players in squad")
        return True

    async def exploit_cycle(self) -> bool:
        """
        Single glory cycle (based on the level bot's working approach):
          1. Form squad (if not already)
          2. ALL members spam start_match on online socket for SPAM_DURATION seconds
          3. Wait MATCH_WAIT seconds for match to complete
          4. ALL members leave team
          5. Wait CYCLE_DELAY before next cycle
        """
        # Always form fresh squad each cycle
        await self.form_squad()
        await asyncio.sleep(3)

        # All members spam start_match packets (like the level bot)
        print(f"  >> Spamming start-match for {SPAM_DURATION}s...")
        tasks = []
        for conn in self.connections:
            tasks.append(conn.spam_start_match(SPAM_DURATION, SPAM_DELAY))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_packets = sum(r for r in results if isinstance(r, int))
        print(f"  >> Sent {total_packets} start-match packets total")

        # Wait for match to complete
        print(f"  >> Waiting {MATCH_WAIT}s for match completion...")
        await asyncio.sleep(MATCH_WAIT)

        # ALL members leave team
        print(f"  >> Leaving team...")
        for conn in self.connections:
            try:
                await conn.leave_team()
            except Exception as e:
                print(f"  [G{conn.index+1}] Leave failed: {e}")
            await asyncio.sleep(0.3)

        # Wait for glory to credit
        print(f"  >> Waiting {CYCLE_DELAY}s before next cycle...")
        await asyncio.sleep(CYCLE_DELAY)

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
        print("  CLAN GLORY BOT — Squad Match Farm")
        print(f"  Clan: {self.clan_id}")
        print(f"  Region: {self.region}")
        print(f"  Max cycles: {self.max_cycles}")
        cycle_time = SPAM_DURATION + MATCH_WAIT + int(CYCLE_DELAY)
        print(f"  Per cycle: ~{cycle_time}s")
        print(f"  Est total time: ~{(self.max_cycles * cycle_time) // 60} min")
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
                await asyncio.sleep(CYCLE_DELAY)

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
    p = argparse.ArgumentParser(description="Clan Glory Bot — Clash Squad Match Farm")
    p.add_argument("--clan-id", type=int, default=DEFAULT_CLAN_ID, help="Target clan ID")
    p.add_argument("--region", type=str, default=DEFAULT_REGION, help="Region (ME, IND, BR, SG, etc.)")
    p.add_argument("--cycles", type=int, default=DEFAULT_CYCLES, help="Max exploit cycles")
    p.add_argument("--match-wait", type=int, default=15, help="Matchmaking wait (seconds)")
    p.add_argument("--post-exit-wait", type=int, default=5, help="Post-exit wait (seconds)")
    args = p.parse_args()

    bot = ClanGloryBot(
        clan_id=args.clan_id, region=args.region, cycles=args.cycles,

    )

    # Handle Ctrl+C
    def stop_handler(sig, frame):
        bot.running = False
    signal.signal(signal.SIGINT, stop_handler)

    asyncio.run(bot.run())


if __name__ == "__main__":
    main()

