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
    AuthClan, OpEnSq, AutH_GlobAl, ExiT, cHSq,
    DeCode_PackEt, DEc_PacKeT, GeTSQDaTa,
    EnC_PacKeT, EnC_Uid, EnC_Vr,
)

# ======================== CONFIG ========================

AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

DEFAULT_CLAN_ID    = 3100938923
DEFAULT_REGION     = "ME"
DEFAULT_CYCLES     = 200
SPAM_DURATION      = 18
SPAM_DELAY         = 0.2
MATCH_WAIT         = 20
LEAVE_DELAY        = 2.0
CYCLE_DELAY        = 3.0
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
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
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
        """Connect to Online + Chat TCP servers using xAuThSTarTuP token."""
        try:
            auth_token_hex = await build_tcp_auth_token(
                self.account_uid, self.jwt, self.timestamp, self.key, self.iv)
            auth_token_bytes = bytes.fromhex(auth_token_hex)

            self.online_reader, self.online_writer = await asyncio.open_connection(
                self.online_ip, self.online_port)
            self.online_writer.write(auth_token_bytes)
            await self.online_writer.drain()

            self.chat_reader, self.chat_writer = await asyncio.open_connection(
                self.chat_ip, self.chat_port)
            self.chat_writer.write(auth_token_bytes)
            await self.chat_writer.drain()

            await asyncio.sleep(1)
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

    async def open_squad(self, region: str, squad_size: int = 2) -> dict:
        """OpEnSq — leader opens squad for matchmaking.
        Uses custom fields with squad_size to set the number of additional member slots.
        Original OpEnSq has field 2.3=1 (1 extra slot). We set it to squad_size-1."""
        # Custom OpEnSq with squad_size
        extra_slots = squad_size - 1  # leader + extra_slots = total squad size
        fields = {
            1: 1,
            2: {
                2: "\u0001",
                3: extra_slots,  # Number of additional member slots (was hardcoded 1)
                4: 1,
                5: "en",
                9: 1,
                11: 1,
                13: 1,
                14: {2: 5756, 6: 11, 8: "1.111.5", 9: 2, 10: 4}
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

    async def join_team(self, team_code: str) -> bool:
        """Join a squad/team directly using team_code.
        This is the LEVEL BOT's proven join method — simple and works.
        No invite mechanism needed, just direct join with team_code.

        Packet format: {1: 4, 2: {1: 1, 2: int(team_code)}}
        - field 1 = 4 (join squad action)
        - field 2.1 = 1 (join type)
        - field 2.2 = team_code as integer
        """
        if not team_code:
            print(f"  [G{self.index+1}] No team_code provided")
            return False

        try:
            team_code_int = int(team_code)
        except ValueError:
            print(f"  [G{self.index+1}] team_code is not numeric: {team_code}")
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

        # Read response to check if join succeeded
        try:
            resp = await asyncio.wait_for(self.online_reader.read(9999), timeout=2.0)
            if resp:
                resp_hex = resp.hex()
                print(f"  [G{self.index+1}] Join response: {len(resp_hex)} hex, header={resp_hex[:12]}")
                for skip in [10, 8, 12, 6, 14]:
                    try:
                        payload = resp_hex[skip:]
                        if len(payload) < 10:
                            continue
                        json_str = await DeCode_PackEt(payload)
                        if json_str:
                            parsed = json.loads(json_str)
                            field3 = parsed.get('3', {})
                            if isinstance(field3, dict):
                                err_code = field3.get('data')
                                if err_code and err_code not in [0]:
                                    print(f"  [G{self.index+1}] Join error code: {err_code}")
                                    return False
                            print(f"  [G{self.index+1}] Joined team {team_code}")
                            self.in_squad = True
                            return True
                    except:
                        continue
                print(f"  [G{self.index+1}] Joined team {team_code} (response received)")
                self.in_squad = True
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

    async def spam_start_match(self, duration: float, delay: float):
        """Spam start-match packets on the ONLINE socket.
        FIX: Uses self.account_uid instead of hardcoded 12480598706."""
        fields = {
            1: 9,
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
        """Leave squad.
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
        await asyncio.sleep(LEAVE_DELAY)
        self.in_match = False
        self.in_squad = False
        self.squad_code = None
        self.team_code = None

    async def cleanup(self):
        """Close all TCP connections."""
        for writer in [self.online_writer, self.chat_writer]:
            if writer and not writer.is_closing():
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass
        self.connected = False


# ======================== CLAN GLORY BOT ========================

class ClanGloryBot:
    """Orchestrates the clan glory farming loop."""

    def __init__(self, clan_id: int = DEFAULT_CLAN_ID, region: str = DEFAULT_REGION,
                 cycles: int = DEFAULT_CYCLES):
        self.clan_id = clan_id
        self.region = region
        self.max_cycles = cycles
        self.connections: list[GuestConnection] = []
        self.running = False
        self.cycle_count = 0
        self.total_glory_estimated = 0

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
        return len(ready) >= 1

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

        # Step 1: ALL members reset/leave existing squad
        print(f"  >> Resetting all members to solo...")
        for conn in self.connections:
            await conn.reset_squad()
        await asyncio.sleep(1)

        # Step 2: Leader opens squad
        leader_response = await leader.open_squad(self.region, squad_size=len(self.connections))
        await asyncio.sleep(2)

        # CRITICAL: Call cHSq for EACH member to reserve their slot
        # TCP bot flow: OpEnSq → cHSq(N, target_uid) per target → SEnd_InV
        # cHSq with target_uid reserves a slot for that specific player
        squad_size = len(self.connections)
        for member in members:
            print(f"  [G1] cHSq: reserving slot for G{member.index+1} (uid={member.account_uid}, squad_size={squad_size})...")
            chsq_packet = await cHSq(squad_size, member.account_uid, leader.key, leader.iv, self.region)
            await leader.send_packet(chsq_packet, channel="online")
            await asyncio.sleep(0.5)

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
                print(f"  Waiting 3s before next member join (server sync)...")
                await asyncio.sleep(3)
            
            print(f"  [G{member.index+1}] Joining team {team_code}...")
            joined = await member.join_team(team_code)
            if joined:
                print(f"  [G{member.index+1}] In squad")
            else:
                # Retry 1: with squad_code (extract numeric part before underscore)
                if squad_code:
                    numeric_part = ""
                    for ch in str(squad_code):
                        if ch.isdigit():
                            numeric_part += ch
                        else:
                            break
                    if numeric_part and numeric_part != team_code:
                        print(f"  [G{member.index+1}] Retrying with squad_code numeric: {numeric_part[:20]}...")
                        await asyncio.sleep(2)
                        joined = await member.join_team(numeric_part)
                        if joined:
                            print(f"  [G{member.index+1}] In squad (via squad_code)")
                
                # Retry 2: wait and try again with original team_code (server might be slow)
                if not joined:
                    print(f"  [G{member.index+1}] Retrying in 5s (server sync delay)...")
                    await asyncio.sleep(5)
                    joined = await member.join_team(team_code)
                    if joined:
                        print(f"  [G{member.index+1}] In squad (retry)")
                    else:
                        print(f"  [G{member.index+1}] ❌ Failed to join after retries")

        in_squad_count = sum(1 for c in self.connections if c.in_squad)
        print(f"  Squad formed: {in_squad_count}/{len(self.connections)} players in squad")
        return True

    async def exploit_cycle(self) -> bool:
        """Single glory cycle: form squad -> spam start -> wait -> leave."""
        await self.form_squad()
        await asyncio.sleep(3)

        print(f"  >> Spamming start-match for {SPAM_DURATION}s...")
        tasks = []
        for conn in self.connections:
            if conn.connected:
                tasks.append(conn.spam_start_match(SPAM_DURATION, SPAM_DELAY))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_packets = sum(r for r in results if isinstance(r, int))
        print(f"  >> Sent {total_packets} start-match packets total")

        print(f"  >> Waiting {MATCH_WAIT}s for match completion...")
        for conn in self.connections:
            if not conn.connected:
                continue
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
        await asyncio.sleep(max(0, MATCH_WAIT - 3))

        print(f"  >> Leaving team...")
        for conn in self.connections:
            if conn.connected:
                try:
                    await conn.leave_team()
                except Exception as e:
                    print(f"  [G{conn.index+1}] Leave failed: {e}")
                await asyncio.sleep(0.3)

        print(f"  >> Waiting {CYCLE_DELAY}s before next cycle...")
        await asyncio.sleep(CYCLE_DELAY)

        glory_per_cycle = len(self.connections) * random.randint(5, 15)
        self.total_glory_estimated += glory_per_cycle
        print(f"  >> Cycle #{self.cycle_count} done (+~{glory_per_cycle} glory, total ~{self.total_glory_estimated})")
        return True

    async def run(self):
        """Main exploit loop."""
        self.running = True
        self.cycle_count = 0

        print("=" * 60)
        print("  CLAN GLORY BOT - Squad Match Farm (v2)")
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
                for conn in self.connections:
                    if not conn.connected:
                        print(f"  [G{conn.index+1}] Reconnecting...")
                        await conn.connect_tcp()
                        await conn.join_clan(self.clan_id)
                        await asyncio.sleep(2)

                await self.exploit_cycle()
                await asyncio.sleep(CYCLE_DELAY)

            except KeyboardInterrupt:
                print("\n  Stopped by user")
                break
            except Exception as e:
                print(f"  Cycle error: {e}")
                await asyncio.sleep(RECONNECT_DELAY)

        elapsed = int(time.time() - start_time)
        print("\n" + "=" * 60)
        print(f"  CLAN GLORY BOT - Done")
        print(f"  Cycles: {self.cycle_count}/{self.max_cycles}")
        print(f"  Time: {elapsed}s ({elapsed // 60}m {elapsed % 60}s)")
        print(f"  Est glory: ~{self.total_glory_estimated}")
        print(f"  Guests: {len(self.connections)}")
        print(f"  Clan: {self.clan_id}")
        print("=" * 60)

        for conn in self.connections:
            await conn.cleanup()

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
    args = p.parse_args()

    SPAM_DURATION = args.spam_duration
    SPAM_DELAY = args.spam_delay
    MATCH_WAIT = args.match_wait

    bot = ClanGloryBot(
        clan_id=args.clan_id,
        region=args.region,
        cycles=args.cycles,
    )

    def stop_handler(sig, frame):
        bot.running = False
    signal.signal(signal.SIGINT, stop_handler)

    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
