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
    AuthClan, OpEnSq, SEnd_InV, GenJoinSquadsPacket, ExiT, cHSq,
    AutH_GlobAl, EnC_Uid, EnC_Vr,
    DeCode_PackEt, DEc_PacKeT, GeTSQDaTa,
    EnC_PacKeT, GenJoinGlobaL
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
                2: 159,
                4: "y[WW",
                6: 11,
                8: "1.120.2",
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

    async def read_invite_code(self, timeout: float = 12.0) -> dict:
        """
        Read packets from BOTH online and chat channels.
        For each chunk, check if it starts with '0500' (like TCP bot).
        If yes, decode from offset 10 and extract field 5.1 (owner) and 5.8 (invite code).
        """
        result = {"owner_uid": None, "invite_code": None}
        deadline = asyncio.get_event_loop().time() + timeout
        packets_checked = 0
        chat_chunks = 0
        online_chunks = 0

        while asyncio.get_event_loop().time() < deadline:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break

            # Read from ONLINE channel (small timeout)
            try:
                data = await asyncio.wait_for(self.online_reader.read(9999), timeout=min(remaining, 2.0))
                if data:
                    online_chunks += 1
                    data_hex = data.hex()
                    # Check if THIS chunk starts with 0500 (like TCP bot)
                    if data_hex.startswith("0500"):
                        packets_checked += 1
                        decoded = await self._try_decode_invite(data_hex)
                        if decoded.get("invite_code"):
                            print(f"  [G{self.index+1}] ✅ Found invite on ONLINE channel: owner={decoded['owner_uid']}, code={decoded['invite_code'][:25]}...")
                            return decoded
            except asyncio.TimeoutError:
                pass
            except:
                pass

            # Read from CHAT channel (small timeout)
            if self.chat_reader:
                try:
                    chat_data = await asyncio.wait_for(self.chat_reader.read(9999), timeout=min(remaining, 2.0))
                    if chat_data:
                        chat_chunks += 1
                        data_hex = chat_data.hex()
                        # Check if THIS chunk starts with 0500
                        if data_hex.startswith("0500"):
                            packets_checked += 1
                            decoded = await self._try_decode_invite(data_hex)
                            if decoded.get("invite_code"):
                                print(f"  [G{self.index+1}] ✅ Found invite on CHAT channel: owner={decoded['owner_uid']}, code={decoded['invite_code'][:25]}...")
                                return decoded
                        # Also search for 0500 within the chunk (might be concatenated)
                        idx = data_hex.find("0500", 4)  # skip start
                        while idx >= 0 and idx < len(data_hex) - 20:
                            sub = data_hex[idx:]
                            decoded = await self._try_decode_invite(sub)
                            if decoded.get("invite_code"):
                                print(f"  [G{self.index+1}] ✅ Found invite at offset {idx} in CHAT data: owner={decoded['owner_uid']}, code={decoded['invite_code'][:25]}...")
                                return decoded
                            idx = data_hex.find("0500", idx + 4)
                except asyncio.TimeoutError:
                    pass
                except:
                    pass

        print(f"  [G{self.index+1}] No invite found (online={online_chunks} chunks, chat={chat_chunks} chunks, 0500 packets={packets_checked})")
        return result

    async def _try_decode_invite(self, data_hex: str) -> dict:
        """Try to decode a 0500 packet and extract owner_uid (5.1) + invite_code (5.8)."""
        result = {"owner_uid": None, "invite_code": None}
        # TCP bot decodes from data_hex[10:] — skip first 5 bytes (type + header)
        for skip in [10, 8, 12, 6, 14]:
            try:
                payload = data_hex[skip:]
                if len(payload) < 20:
                    continue
                # Try raw decode first
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
                # Extract owner_uid (5.1)
                f1 = field5_data.get('1', {})
                if isinstance(f1, dict) and 'data' in f1:
                    result["owner_uid"] = str(f1['data'])
                # Extract invite_code (5.8)
                f8 = field5_data.get('8', {})
                if isinstance(f8, dict) and 'data' in f8:
                    val = str(f8['data'])
                    if len(val) > 10:  # Real invite codes are long strings
                        result["invite_code"] = val
                if result["invite_code"]:
                    return result
            except:
                pass
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
        Reads up to 3 times, searches for '0500' packet type.
        Extracts: owner_uid (5.1), invite_code (5.8), chat_code (5.17), squad_code (5.31).
        """
        result = {"owner_uid": None, "invite_code": None, "chat_code": None, "squad_code": None, "team_code": None}
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
        # Strategy 1: search for 0500 and parse from there
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
                        f8 = field5_data.get('8', {})
                        if isinstance(f8, dict) and 'data' in f8:
                            val = str(f8['data'])
                            # Only accept if it looks like a real invite code (long string)
                            if len(val) > 10 and '_' in val:
                                result["invite_code"] = val
                            else:
                                print(f"  [G{self.index+1}] Field 5.8 = '{val}' (not a real invite code, skipping)")
                        f17 = field5_data.get('17', {})
                        if isinstance(f17, dict) and 'data' in f17:
                            result["chat_code"] = str(f17['data'])
                        # Extract team_code from field 5.6.4 (short code for joining)
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
                        parts = [f"{k}={v[:15]}" for k, v in result.items() if v]
                        print(f"  [G{self.index+1}] 0500@{idx}+{skip} ({attempt_name}): {', '.join(parts)}")
                        if result["squad_code"] or result["invite_code"]:
                            return result
                    except:
                        pass
            idx = all_data_hex.find("0500", idx + 4)
        # Strategy 2: try all offsets 0-60
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
                        val = str(f8['data'])
                        if len(val) > 10 and '_' in val:
                            result["invite_code"] = val
                    f17 = field5_data.get('17', {})
                    if isinstance(f17, dict) and 'data' in f17:
                        result["chat_code"] = str(f17['data'])
                    f31 = field5_data.get('31', {})
                    if isinstance(f31, dict) and 'data' in f31:
                        result["squad_code"] = str(f31['data'])
                    parts = [f"{k}={v[:15]}" for k, v in result.items() if v]
                    print(f"  [G{self.index+1}] offset {offset} ({attempt_name}): {', '.join(parts)}")
                    if result["squad_code"] or result["invite_code"]:
                        return result
                except:
                    pass
        # Strategy 3: GeTSQDaTa at all offsets
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
        print(f"  [G{self.index+1}] Could not parse (tried 0500 search + all offsets + GeTSQDaTa)")
        return result

    async def send_invite(self, target_uid: int, region: str, squad_size: int = 3):
        """SEnd_InV — invite a player to squad. Nu = squad size (3 for 3-player)."""
        packet = await SEnd_InV(squad_size, target_uid, self.key, self.iv, region.lower())
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)

    async def configure_squad(self, target_uid: int, region: str, squad_size: int = 3):
        """cHSq — configure squad for N players. Must be called BEFORE SEnd_InV."""
        packet = await cHSq(squad_size, target_uid, self.key, self.iv, region.lower())
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)

    async def _read_join_response(self, label: str = "Join") -> dict:
        """Read and decode a join response packet from the server."""
        await asyncio.sleep(0.5)
        try:
            resp = await asyncio.wait_for(self.online_reader.read(9999), timeout=1.5)
            if resp:
                resp_hex = resp.hex()
                print(f"  [G{self.index+1}] {label} response: {len(resp_hex)} hex, header={resp_hex[:12]}")
                for skip in [10, 12, 8, 14, 6]:
                    try:
                        payload = resp_hex[skip:]
                        if len(payload) < 10:
                            continue
                        json_str = await DeCode_PackEt(payload)
                        if json_str:
                            parsed = json.loads(json_str)
                            print(f"  [G{self.index+1}] {label} decoded: {str(parsed)[:500]}")
                            return parsed
                    except:
                        continue
                print(f"  [G{self.index+1}] {label} response: could not decode")
            else:
                print(f"  [G{self.index+1}] {label}: connection closed")
        except asyncio.TimeoutError:
            print(f"  [G{self.index+1}] {label}: no response (timeout)")
        except Exception as e:
            print(f"  [G{self.index+1}] {label}: {e}")
        return {}

    async def _try_join_method(self, label: str, packet_bytes, channel: str = "online") -> bool:
        """Send a join packet and check the response. Returns True if joined."""
        await self.send_packet(packet_bytes, channel=channel)
        await asyncio.sleep(0.3)
        resp = await self._read_join_response(label)
        if resp and isinstance(resp, dict):
            field3 = None
            for k, v in resp.items():
                if k == '3':
                    field3 = v.get('data') if isinstance(v, dict) else v
            if field3 is None:
                print(f"  [G{self.index+1}] ✅ {label}: accepted (no error field)")
                self.in_squad = True
                return True
            elif field3 not in [79, 50, 94]:
                print(f"  [G{self.index+1}] ✅ {label}: SUCCESS (field 3 = {field3})")
                self.in_squad = True
                return True
            else:
                print(f"  [G{self.index+1}] ❌ {label}: error {field3}")
        return False

    async def try_join_squad(self, owner_uid: str, team_code: str, squad_code: str = None):
        """Try ALL join methods systematically. Returns True if any worked.
        
        Error codes seen:
        - 79: GenJoinSquadsPacket with squad_code (wrong code format)
        - 50: ArohiAccepted (wrong code or no invite pending)  
        - 94: GenJoinGlobaL with team_code (wrong region or squad state)
        """
        methods_tried = 0
        
        # ── Method 1: GenJoinSquadsPacket with SHORT team_code (not squad_code!) ──
        # The TCP bot uses short team codes for GenJoinSquadsPacket
        try:
            print(f"  [G{self.index+1}] M1: GenJoinSquadsPacket(team_code={team_code})")
            packet = await GenJoinSquadsPacket(team_code, self.key, self.iv)
            if await self._try_join_method("GenJoinSquads(team)", packet):
                return True
            methods_tried += 1
        except Exception as e:
            print(f"  [G{self.index+1}] M1 error: {e}")

        # ── Method 2: GenJoinSquadsPacket with full squad_code ──
        if squad_code:
            try:
                print(f"  [G{self.index+1}] M2: GenJoinSquadsPacket(squad_code={str(squad_code)[:25]}...)")
                packet = await GenJoinSquadsPacket(squad_code, self.key, self.iv)
                if await self._try_join_method("GenJoinSquads(squad)", packet):
                    return True
                methods_tried += 1
            except Exception as e:
                print(f"  [G{self.index+1}] M2 error: {e}")

        # ── Method 3: ArohiAccepted with team_code ──
        try:
            print(f"  [G{self.index+1}] M3: ArohiAccepted(owner={owner_uid}, team_code={team_code})")
            packet = await ArohiAccepted(owner_uid, team_code, self.key, self.iv)
            if await self._try_join_method("ArohiAccepted(team)", packet):
                return True
            methods_tried += 1
        except Exception as e:
            print(f"  [G{self.index+1}] M3 error: {e}")

        # ── Method 4: ArohiAccepted with squad_code ──
        if squad_code:
            try:
                print(f"  [G{self.index+1}] M4: ArohiAccepted(squad_code={str(squad_code)[:25]}...)")
                packet = await ArohiAccepted(owner_uid, squad_code, self.key, self.iv)
                if await self._try_join_method("ArohiAccepted(squad)", packet):
                    return True
                methods_tried += 1
            except Exception as e:
                print(f"  [G{self.index+1}] M4 error: {e}")

        # ── Method 5: GenJoinGlobaL with team_code ──
        try:
            print(f"  [G{self.index+1}] M5: GenJoinGlobaL(owner={owner_uid}, team_code={team_code})")
            packet = await GenJoinGlobaL(int(owner_uid), team_code, self.key, self.iv)
            if await self._try_join_method("GenJoinGlobaL(team)", packet):
                return True
            methods_tried += 1
        except Exception as e:
            print(f"  [G{self.index+1}] M5 error: {e}")

        # ── Method 6: GenJoinGlobaL with squad_code ──
        if squad_code:
            try:
                print(f"  [G{self.index+1}] M6: GenJoinGlobaL(squad_code={str(squad_code)[:25]}...)")
                packet = await GenJoinGlobaL(int(owner_uid), squad_code, self.key, self.iv)
                if await self._try_join_method("GenJoinGlobaL(squad)", packet):
                    return True
                methods_tried += 1
            except Exception as e:
                print(f"  [G{self.index+1}] M6 error: {e}")

        # ── Method 7: Custom join — owner + team_code + version (hybrid) ──
        try:
            print(f"  [G{self.index+1}] M7: Custom hybrid join (owner + team_code + version)")
            fields = {
                1: 4,
                2: {
                    1: int(owner_uid),
                    4: bytes.fromhex("01090a0b121920"),
                    5: str(team_code),
                    6: 6,
                    8: 1,
                    9: {2: 800, 6: 11, 8: "1.111.1", 9: 5, 10: 1},
                }
            }
            proto_hex = (await CrEaTe_ProTo(fields)).hex()
            packet = await GeneRaTePk(proto_hex, "0515", self.key, self.iv)
            if await self._try_join_method("HybridJoin", packet):
                return True
            methods_tried += 1
        except Exception as e:
            print(f"  [G{self.index+1}] M7 error: {e}")

        # ── Method 8: GenJoinGlobaL with "ME" region instead of "OR" ──
        try:
            print(f"  [G{self.index+1}] M8: GenJoinGlobaL with ME region")
            fields = {
                1: 4,
                2: {
                    1: int(owner_uid),
                    6: 1,
                    8: 1,
                    13: "en",
                    15: str(team_code),
                    16: "ME",
                }
            }
            proto_hex = (await CrEaTe_ProTo(fields)).hex()
            packet = await GeneRaTePk(proto_hex, "0515", self.key, self.iv)
            if await self._try_join_method("GenJoinGlobaL(ME)", packet):
                return True
            methods_tried += 1
        except Exception as e:
            print(f"  [G{self.index+1}] M8 error: {e}")

        # ── Method 9: Try on chat channel with best method ──
        try:
            print(f"  [G{self.index+1}] M9: GenJoinSquadsPacket on chat channel")
            packet = await GenJoinSquadsPacket(team_code, self.key, self.iv)
            if await self._try_join_method("GenJoinSquads(chat)", packet, channel="chat"):
                return True
            methods_tried += 1
        except Exception as e:
            print(f"  [G{self.index+1}] M9 error: {e}")

        print(f"  [G{self.index+1}] ⚠ All {methods_tried} join methods failed")
        self.in_squad = False
        return False

    async def accept_invite(self, owner_uid: str, invite_code: str):
        """Accept squad invite — wrapper for try_join_squad."""
        await self.try_join_squad(owner_uid, invite_code)

    async def spam_start_match(self, duration: float, delay: float):
        """Spam start-match packets on the ONLINE socket for the given duration.
        Uses level bot's EXACT format: field 1=9 (BR match start), field 2={1: 12480598706}.
        """
        import time as _time
        # Level bot's start_match: {1: 9, 2: {1: 12480598706}} — THIS WORKS
        fields = {
            1: 9,
            2: {
                1: 12480598706,
            }
        }
        proto_bytes = await CrEaTe_ProTo(fields)
        pkt_type = get_packet_type(self.region)
        packet = await GeneRaTePk(proto_bytes.hex(), pkt_type, self.key, self.iv)

        end_time = _time.time() + duration
        sent = 0
        while _time.time() < end_time and self.connected:
            try:
                await self.send_packet(packet, channel="online")
                sent += 1
            except Exception as e:
                print(f"  [G{self.index+1}] Send failed at packet {sent}: {e}")
                self.connected = False
                break
            await asyncio.sleep(delay)
        if not self.connected:
            print(f"  [G{self.index+1}] Connection lost during spam (sent {sent} packets)")
        self.in_match = True
        return sent

    async def leave_team(self):
        """Leave squad — field 1=7 (matches level bot's PacketBuilder.leave_team)."""
        fields = {
            1: 7,
            2: {
                1: 12480598706,  # Fixed UID (matches level bot)
            }
        }
        proto_bytes = await CrEaTe_ProTo(fields)
        pkt_type = get_packet_type(self.region if hasattr(self, 'region') else "ME")
        packet = await GeneRaTePk(proto_bytes.hex(), pkt_type, self.key, self.iv)
        await self.send_packet(packet, channel="online")
        await asyncio.sleep(LEAVE_DELAY)
        self.in_match = False
        self.in_squad = False
        self.squad_code = None

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
      6. Wait 5 for glory to credit
      7. Re-queue
    """

    def __init__(self, clan_id: int = DEFAULT_CLAN_ID, region: str = DEFAULT_REGION,
                 cycles: int = DEFAULT_CYCLES,
        ):
        self.clan_id = clan_id
        self.region = region
        self.max_cycles = cycles
        # timing now module-level constants
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
                conn.set_region(self.region)

                if not await conn.authenticate(session):
                    continue

                # Auto-join target clan via HTTP API
                await auto_join_clan(session, conn.jwt, self.clan_id, conn.server_url, i)
                await asyncio.sleep(1)

                if not await conn.connect_tcp():
                    continue

                # NOTE: Do NOT start background listener — it would consume
                # the OpEnSq response before read_squad_code can read it.

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
        Full squad formation (matches TCP bot flow exactly):
        1. ALL members reset/leave existing squad
        2. Leader opens squad (OpEnSq) -> extracts owner_uid, chat_code, squad_code
        3. For each member: Leader sends cHSq (configure squad) + SEnd_InV (invite)
        4. Each member reads 0500 invite packet -> ArohiAccepted(owner_uid, invite_code)
        5. Member authenticates squad chat with AutH_Chat(3, owner_uid, chat_code)
        """
        if not self.connections:
            return False

        leader = self.connections[0]
        members = self.connections[1:]
        squad_size = len(self.connections)  # 3 for 3 guests

        print(f"  Squad: Leader=G1({leader.account_uid}) -> {len(members)} members (size={squad_size})")

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
        squad_code = leader_response.get("squad_code")
        team_code = leader_response.get("team_code")

        print(f"  Leader: owner={owner_uid}, chat={'Y' if chat_code else 'N'}, squad={'Y' if squad_code else 'N'}, team_code={team_code}")

        # Step 2: For each member — cHSq (configure) + RedZed_SendInv (REAL invite)
        # The REAL invite function (RedZed_SendInv) has 20+ fields including:
        # - Sender's UID (2.27, 2.34) — the server needs to know WHO is inviting
        # - Version info (2.17) — client version validation
        # - Rank (2.7), country (2.10), name (2.6)
        # Our old SEnd_InV only had 3 fields — that's why invites never arrived!
        for member in members:
            print(f"  [G1] Configuring squad (leader_uid={leader.account_uid}) for G{member.index+1}...")
            await leader.configure_squad(leader.account_uid, self.region.lower(), squad_size)
            await asyncio.sleep(0.3)

            print(f"  [G1] Inviting G{member.index+1} via RedZed_SendInv (internal_uid={member.account_uid})...")
            # Build the REAL invite packet with all required fields
            invite_fields = {
                1: 2,
                2: {
                    1: int(member.account_uid),     # target UID
                    2: self.region.upper(),          # region (ME)
                    3: 1,
                    4: 1,                            # mode (not squad size)
                    6: "BOT5S8F7S",                  # leader's name
                    7: 330,                          # rank
                    8: 1000,
                    9: 100,
                    10: self.region.upper(),         # country code (ME)
                    12: 1,
                    13: int(member.account_uid),     # target UID repeated
                    16: 1,
                    17: {                            # version info
                        2: 159,
                        4: "y[WW",
                        6: 11,
                        8: "1.120.2",
                        9: 3,
                        10: 1
                    },
                    18: 306,
                    19: 18,
                    24: 902000306,
                    26: {},
                    27: {                            # SENDER's UID — critical!
                        1: 11,
                        2: int(leader.account_uid),
                        3: 99999999999
                    },
                    28: {},
                    31: {1: 1, 2: 32768},
                    32: 32768,
                    34: {                            # SENDER's UID with binary blob
                        1: int(leader.account_uid),
                        2: 8,
                        3: b"\x10\x15\x08\x0A\x0B\x13\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
                    }
                }
            }
            invite_proto = await CrEaTe_ProTo(invite_fields)
            invite_packet = await GeneRaTePk(invite_proto.hex(), "0515", leader.key, leader.iv)
            # Send on online channel
            await leader.send_packet(invite_packet, channel="online")
            await asyncio.sleep(0.5)
            # Also send on chat channel for redundancy
            await leader.send_packet(invite_packet, channel="chat")
            await asyncio.sleep(1)

        # Wait for invite packets to reach members
        print(f"  >> Waiting for invite packets to arrive...")
        await asyncio.sleep(2)

        # Step 3: Each member reads 0500 invite packet and accepts with ArohiAccepted
        # ArohiAccepted sends 0516 packet (not 0515) with owner_uid + invite_code
        for member in members:
            try:
                print(f"  [G{member.index+1}] Reading invite packet...")
                invite_data = await member.read_invite_code(timeout=4.0)

                invite_code = invite_data.get("invite_code")
                inviter_uid = invite_data.get("owner_uid") or owner_uid

                if invite_code:
                    # Accept invite — 0516 packet with owner_uid + invite_code
                    accept_packet = await ArohiAccepted(inviter_uid, invite_code, member.key, member.iv)
                    await member.send_packet(accept_packet)
                    await asyncio.sleep(1)

                    # Authenticate squad chat
                    if chat_code:
                        chat_auth_packet = await AutH_Chat(3, owner_uid, chat_code, member.key, member.iv)
                        await member.send_packet(chat_auth_packet, channel="chat")
                        print(f"  [G{member.index+1}] ✅ Accepted invite (code={str(invite_code)[:20]}...) + chat auth")
                    else:
                        print(f"  [G{member.index+1}] ✅ Accepted invite (no chat code)")

                    member.in_squad = True
                elif team_code or squad_code:
                    # Fallback: try ALL join methods (GenJoinSquadsPacket, ArohiAccepted, etc.)
                    print(f"  [G{member.index+1}] No invite arrived. Trying all join methods...")
                    joined = await member.try_join_squad(owner_uid, team_code or "", squad_code)
                    if joined and chat_code:
                        chat_auth_packet = await AutH_Chat(3, owner_uid, chat_code, member.key, member.iv)
                        await member.send_packet(chat_auth_packet, channel="chat")
                else:
                    print(f"  [G{member.index+1}] ❌ No invite code and no squad code — cannot join")
            except Exception as e:
                print(f"  [G{member.index+1}] Join failed: {e}")
            await asyncio.sleep(1)

        # Leader is already in squad from OpEnSq
        leader.in_squad = True
        in_squad_count = sum(1 for c in self.connections if c.in_squad)
        print(f"  Squad formed: {in_squad_count}/{len(self.connections)} players in squad")
        
        # Check if G1 (leader) received squad member join notifications
        print(f"  >> Checking leader socket for squad updates...")
        try:
            for _ in range(3):
                g1_data = await asyncio.wait_for(leader.online_reader.read(9999), timeout=2.0)
                if g1_data:
                    g1_hex = g1_data.hex()
                    print(f"  [G1] Squad update: {len(g1_hex)} hex, header={g1_hex[:16]}")
                    for skip in [10, 12, 8, 14, 6]:
                        try:
                            payload = g1_hex[skip:]
                            if len(payload) < 10:
                                continue
                            json_str = await DeCode_PackEt(payload)
                            if json_str:
                                parsed = json.loads(json_str)
                                print(f"  [G1] Decoded: {str(parsed)[:3000]}")
                                break
                        except:
                            continue
                else:
                    print(f"  [G1] No squad update data")
        except asyncio.TimeoutError:
            print(f"  [G1] No squad updates received (timeout — join may have failed)")
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
        # Check for server responses
        for conn in self.connections:
            try:
                resp = await asyncio.wait_for(conn.online_reader.read(9999), timeout=3.0)
                if resp:
                    print(f"  [G{conn.index+1}] Post-match data: {len(resp.hex())} hex, header={resp.hex()[:12]}")
                else:
                    print(f"  [G{conn.index+1}] Post-match: connection closed")
            except asyncio.TimeoutError:
                print(f"  [G{conn.index+1}] Post-match: no data (timeout)")
            except Exception as e:
                print(f"  [G{conn.index+1}] Post-match: {e}")
        await asyncio.sleep(MATCH_WAIT - 3)

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
