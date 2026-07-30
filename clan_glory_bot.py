"""
Clan Glory Bot — Clash Squad Exit Glitch Exploit
==================================================
Exploit: Enter Clash Squad match with clan members, immediately exit after
match starts. System awards glory points for participation even on exit/loss.
Repeat hundreds of times for fast glory farming.

Flow per cycle (~30-60 seconds):
  1. Squad leader queues Clash Squad
  2. Wait for match to start (matchmaking delay)
  3. ALL members immediately exit/withdraw
  4. Glory points credited for participation
  5. Re-queue immediately

Usage:
  python3 clan_glory_bot.py --clan-id 3100938923 --region ME --cycles 200

Requirements:
  - 4 guest accounts in data/guests.json
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

HTTP_HEADERS = {
    'User-Agent':      "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    'Connection':      "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type':    "application/octet-stream",
    'Expect':          "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA':            "v1 1",
    'ReleaseVersion':  "OB54",
}

GUESTS_FILE = os.path.join(BASE_DIR, "data", "guests.json")
GARENA_CLIENT_ID = "100067"
GARENA_CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
OAUTH_V2_URL = "https://ffmconnect.live.gop.garenanow.com/api/v2/oauth/guest/token:grant"
OAUTH_V1_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
UA_OAUTH = "GarenaMSDK/4.0.19P10(I2404 ;Android 15;en;US;)"


async def refresh_guest_token(session, uid: str, password: str) -> tuple:
    """Refresh OAuth access_token + open_id (tries v2 then v1)."""
    # v2 JSON
    try:
        resp = await session.post(OAUTH_V2_URL, json={
            "client_id": int(GARENA_CLIENT_ID),
            "client_secret": GARENA_CLIENT_SECRET,
            "client_type": 2,
            "password": password,
            "response_type": "token",
            "uid": int(uid),
        }, headers={
            "User-Agent": UA_OAUTH,
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", resp.json())
            at = data.get("access_token")
            oid = data.get("open_id")
            if at and oid:
                return at, oid
    except Exception:
        pass
    # v1 form-urlencoded
    try:
        resp = await session.post(OAUTH_V1_URL, data={
            "uid": uid, "password": password,
            "response_type": "token", "client_type": "2",
            "client_secret": GARENA_CLIENT_SECRET,
            "client_id": GARENA_CLIENT_ID,
        }, headers={
            "User-Agent": UA_OAUTH,
            "Content-Type": "application/x-www-form-urlencoded",
        }, timeout=15)
        if resp.status_code == 200:
            d = resp.json()
            if d.get("access_token") and d.get("open_id"):
                return d["access_token"], d["open_id"]
    except Exception:
        pass
    return None, None

# ======================== AUTH ========================

async def build_major_login(open_id: str, access_token: str) -> bytes:
    """Build encrypted MajorLogin protobuf payload."""
    ml = MajoRLoGinrEq_pb2.MajorLogin()
    ml.event_time = str(datetime.now())[:-7]
    ml.game_name = "free fire"
    ml.platform_id = 2
    ml.client_version = "1.126.2"
    ml.client_version_code = "2024010012"
    ml.system_software = "Android OS 11 / API-30 (RQ3A.210805.001)"
    ml.system_hardware = "Handheld"
    ml.device_type = "Handheld"
    ml.telecom_operator = "Verizon"
    ml.network_operator_a = "Verizon"
    ml.network_type = "WIFI"
    ml.network_type_a = "WIFI"
    ml.screen_width = 1080
    ml.screen_height = 2400
    ml.screen_dpi = "440"
    ml.processor_details = "ARMv8"
    ml.cpu_type = 2
    ml.cpu_architecture = "64"
    ml.memory = 6144
    ml.gpu_renderer = "Adreno (TM) 650"
    ml.gpu_version = "OpenGL ES 3.2 V@1.50"
    ml.graphics_api = "OpenGLES3"
    ml.unique_device_id = f"Google|{random.randint(10**30, 10**31):x}"
    ml.client_ip = ""
    ml.language = "en"
    ml.open_id = open_id
    ml.open_id_type = "4"
    ml.login_open_id_type = 4
    ml.access_token = access_token
    ml.login_by = 3
    ml.platform_sdk_id = 2
    ml.origin_platform_type = "4"
    ml.primary_platform_type = "4"
    ml.memory_available.version = 55
    ml.memory_available.hidden_value = 81
    ml.external_storage_total = 128512
    ml.external_storage_available = random.randint(38000, 52000)
    ml.internal_storage_total = 110731
    ml.internal_storage_available = random.randint(18000, 32000)
    ml.game_disk_storage_total = 26628
    ml.game_disk_storage_available = random.randint(18000, 25000)
    ml.external_sdcard_total_storage = 119234
    ml.external_sdcard_avail_storage = random.randint(25000, 60000)
    ml.library_path = "/data/app/~~random/base.apk"
    ml.library_token = "hash|base.apk"
    ml.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    ml.supported_astc_bitset = 16383
    ml.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    ml.loading_time = random.randint(9000, 18000)
    ml.release_channel = "android"
    ml.channel_type = 3
    ml.reg_avatar = 1
    ml.if_push = 1
    ml.is_vpn = 0
    ml.android_engine_init_flag = 110009

    raw = ml.SerializeToString()
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(raw, AES.block_size))


async def do_major_login(session, open_id: str, access_token: str) -> Optional[dict]:
    """MajorLogin -> JWT + server info."""
    payload = await build_major_login(open_id, access_token)
    headers = {**HTTP_HEADERS, "Authorization": f"Bearer {access_token}"}

    for url in ["https://loginbp.ggwhitehawk.com/MajorLogin",
                "https://loginbp.ggpolarbear.com/MajorLogin",
                "https://loginbp.ggblueshark.com/MajorLogin",
                "https://loginbp.ggblueshark.com/MajorLogin"]:
        try:
            async with session.post(url, data=payload, headers=headers, ssl=False,
                                     timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    res = MajoRLoGinrEs_pb2.MajorLoginRes()
                    res.ParseFromString(data)
                    return {
                        "jwt": res.token,
                        "url": res.url,
                        "key": res.key if res.key else AES_KEY,
                        "iv": res.iv if res.iv else AES_IV,
                        "timestamp": res.timestamp,
                        "account_uid": res.account_uid,
                        "region": res.region,
                    }
        except Exception as e:
            print(f"  MajorLogin err: {e}")
    return None


async def get_login_data(session, base_url: str, login_payload: bytes, jwt: str) -> Optional[dict]:
    """GetLoginData -> TCP server IPs."""
    url = f"{base_url}/GetLoginData"
    headers = {**HTTP_HEADERS, "Authorization": f"Bearer {jwt}"}
    try:
        async with session.post(url, data=login_payload, headers=headers, ssl=False,
                                timeout=aiohttp.ClientTimeout(total=20)) as resp:
            if resp.status == 200:
                data = await resp.read()
                proto = PorTs_pb2.GetLoginData()
                proto.ParseFromString(data)
                online_ip, online_port = proto.Online_IP_Port.split(":")
                chat_ip, chat_port = proto.AccountIP_Port.split(":")
                return {
                    "online_ip": online_ip,
                    "online_port": int(online_port),
                    "chat_ip": chat_ip,
                    "chat_port": int(chat_port),
                    "account_uid": proto.AccountUID,
                    "account_name": proto.AccountName,
                    "clan_id": proto.Clan_ID,
                    "region": proto.Region,
                }
    except Exception as e:
        print(f"  GetLoginData err: {e}")
    return None


def build_tcp_auth_token(account_uid: int, jwt: str, timestamp: int, key: bytes, iv: bytes) -> str:
    """Build TCP auth startup token (xAuThSTarTuP equivalent)."""
    uid_hex = hex(account_uid)[2:]
    uid_length = len(uid_hex)

    ts = timestamp
    ts_bytes = []
    while ts > 0:
        b = ts & 0x7F
        ts >>= 7
        if ts > 0:
            b |= 0x80
        ts_bytes.append(b)
    encrypted_timestamp = bytes(ts_bytes).hex()

    token_hex = jwt.encode().hex()
    encrypted_packet = EnC_PacKeT_sync(token_hex, key, iv)
    encrypted_packet_length = hex(len(encrypted_packet) // 2)[2:]

    if uid_length == 9:    headers = '0000000'
    elif uid_length == 8: headers = '00000000'
    elif uid_length == 10: headers = '000000'
    elif uid_length == 7:  headers = '000000000'
    else:                  headers = '0000000'

    return f"0115{headers}{uid_hex}{encrypted_timestamp}00000{encrypted_packet_length}{encrypted_packet}"


def get_packet_type(region: str) -> str:
    """Get TCP packet type prefix for region."""
    return REGION_PACKETS.get(region.lower(), DEFAULT_PACKET)


# ======================== GUEST CONNECTION ========================

class GuestConnection:
    """Manages TCP connections for a single guest account."""

    def __init__(self, guest: dict, index: int):
        self.guest = guest
        self.index = index
        self.uid = guest["uid"]
        self.open_id = guest["open_id"]
        self.access_token = guest["access_token"]

        self.jwt: str = ""
        self.server_url: str = ""
        self.key: bytes = AES_KEY
        self.iv: bytes = AES_IV
        self.timestamp: int = 0
        self.account_uid: int = 0
        self.account_name: str = ""

        self.online_ip: str = ""
        self.online_port: int = 0
        self.chat_ip: str = ""
        self.chat_port: int = 0

        self.online_writer = None
        self.online_reader = None
        self.chat_writer = None
        self.chat_reader = None

        self.connected = False
        self.in_squad = False
        self.in_match = False
        self.match_started = False

    async def authenticate(self, session):
        """Full auth: MajorLogin -> GetLoginData."""
        print(f"  [G{self.index+1}] UID {self.uid}: Auth...")


        login_payload = await build_major_login(self.open_id, self.access_token)
        auth = await do_major_login(session, self.open_id, self.access_token)
        if not auth:
            print(f"  [G{self.index+1}] MajorLogin FAIL")
            return False

        self.jwt = auth["jwt"]
        self.server_url = auth["url"].rstrip("/")
        self.key = auth["key"]
        self.iv = auth["iv"]
        self.timestamp = auth["timestamp"]
        self.account_uid = auth["account_uid"]

        print(f"  [G{self.index+1}] JWT OK uid={self.account_uid}")

        login_data = await get_login_data(session, self.server_url, login_payload, self.jwt)
        if not login_data:
            print(f"  [G{self.index+1}] GetLoginData FAIL")
            return False

        self.online_ip = login_data["online_ip"]
        self.online_port = login_data["online_port"]
        self.chat_ip = login_data["chat_ip"]
        self.chat_port = login_data["chat_port"]
        self.account_name = login_data.get("account_name", "")

        print(f"  [G{self.index+1}] TCP: {self.online_ip}:{self.online_port} | {self.chat_ip}:{self.chat_port}")
        return True

    async def connect_tcp(self):
        """Connect to TCP Online + Chat servers."""
        if self.connected:
            return True
        try:
            print(f"  [G{self.index+1}] TCP connect Online {self.online_ip}:{self.online_port}...")
            self.online_reader, self.online_writer = await asyncio.open_connection(
                self.online_ip, self.online_port)

            auth_token = build_tcp_auth_token(self.account_uid, self.jwt, self.timestamp,
                                              self.key, self.iv)
            self.online_writer.write(bytes.fromhex(auth_token))
            await self.online_writer.drain()

            print(f"  [G{self.index+1}] TCP connect Chat {self.chat_ip}:{self.chat_port}...")
            self.chat_reader, self.chat_writer = await asyncio.open_connection(
                self.chat_ip, self.chat_port)
            self.chat_writer.write(bytes.fromhex(auth_token))
            await self.chat_writer.drain()

            print(f"  [G{self.index+1}] TCP OK")
            self.connected = True
            return True
        except Exception as e:
            print(f"  [G{self.index+1}] TCP FAIL: {e}")
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
        """AuthClan — join guild."""
        packet = await AuthClan(clan_id, self.jwt, self.key, self.iv)
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)

    async def open_squad(self, region: str):
        """OpEnSq — leader opens squad for matchmaking."""
        packet = await OpEnSq(self.key, self.iv, region)
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)
        self.in_squad = True

    async def send_invite(self, target_uid: int, region: str):
        """SEnd_InV — invite a player to squad."""
        packet = await SEnd_InV(1, target_uid, self.key, self.iv, region)
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)

    async def join_squad(self, code: str):
        """GenJoinSquadsPacket — join existing squad."""
        packet = await GenJoinSquadsPacket(code, self.key, self.iv)
        await self.send_packet(packet)
        await asyncio.sleep(PACKET_INTERVAL)
        self.in_squad = True

    async def start_clash_squad(self, region: str):
        """
        Queue for Clash Squad match.
        Uses FS packet (field 1=9) which starts matchmaking.
        For Clash Squad, the squad mode must be set to CS via OpEnSq.
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
        """Background reader for Online TCP — detect match start/end."""
        while self.connected and self.online_reader:
            try:
                data = await asyncio.wait_for(self.online_reader.read(4096), timeout=1.0)
                if not data:
                    print(f"  [G{self.index+1}] Online closed by server")
                    self.connected = False
                    break
                hex_data = data.hex()
                # Match start detection: packets starting with 0515 with specific patterns
                # Match end detection: 0500 packets
                if hex_data.startswith("0500"):
                    self.match_started = False
                elif hex_data.startswith("0515") and not self.match_started:
                    # Potential match start notification
                    self.match_started = True
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"  [G{self.index+1}] Listen err: {e}")
                self.connected = False
                break

    async def disconnect(self):
        """Close all TCP connections."""
        self.connected = False
        for writer in [self.online_writer, self.chat_writer]:
            if writer and not writer.is_closing():
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass
        self.online_writer = self.online_reader = None
        self.chat_writer = self.chat_reader = None


# ======================== CLAN GLORY BOT (EXPLOIT) ========================

class ClanGloryBot:
    """
    Clash Squad Exit Glitch exploit bot.

    Each cycle (~30-60s):
      1. Squad leader opens squad + invites members
      2. All members join squad
      3. Leader queues Clash Squad
      4. Wait for matchmaking (MATCHMAKING_WAIT seconds)
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
                if not await conn.connect_tcp():
                    continue

                # Start listener
                asyncio.create_task(conn.listen_online())

                # Send global auth
                await conn.send_global_auth()

                # Join clan
                await conn.join_clan(self.clan_id)

                self.connections.append(conn)
                await asyncio.sleep(2)

        if len(self.connections) < 2:
            print(f"  Only {len(self.connections)} connected — need 2+")
            return False

        print(f"\n  {len(self.connections)} guests ready in clan {self.clan_id}")
        return True

    async def form_squad(self) -> bool:
        """Leader opens squad, invites members, members join."""
        if not self.connections:
            return False

        leader = self.connections[0]
        members = self.connections[1:]

        print(f"  Squad: Leader=G1({leader.account_uid}) -> {len(members)} members")

        # Leader opens squad
        await leader.open_squad(self.region)
        await asyncio.sleep(2)

        # Leader invites each member
        for member in members:
            await leader.send_invite(member.account_uid, self.region)
            await asyncio.sleep(1)

        # Wait for invites
        await asyncio.sleep(2)

        # Members join
        for member in members:
            try:
                await member.join_squad(str(leader.account_uid))
            except:
                pass
            await asyncio.sleep(1)

        print(f"  Squad formed: {len(self.connections)} players")
        return True

    async def exploit_cycle(self) -> bool:
        """
        Single exploit cycle:
          1. Form squad
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
                        await conn.send_global_auth()
                        await conn.join_clan(self.clan_id)
                        await asyncio.sleep(2)

                # Run exploit
                await self.exploit_cycle()

                # Brief delay before re-queue
                await asyncio.sleep(REQUEUE_DELAY)

            except KeyboardInterrupt:
                print("\n  STOPPING...")
                break
            except Exception as e:
                print(f"  Cycle error: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(10)

        elapsed = time.time() - start_time

        # Cleanup
        print(f"\n{'='*60}")
        print(f"  CLAN GLORY BOT — Done")
        print(f"  Cycles: {self.cycle_count}/{self.max_cycles}")
        print(f"  Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
        print(f"  Est glory: ~{self.total_glory_estimated}")
        print(f"  Guests: {len(self.connections)}")
        print(f"  Clan: {self.clan_id}")
        print(f"{'='*60}")

        for conn in self.connections:
            await conn.disconnect()

    def stop(self):
        self.running = False


# ======================== CLI ========================

def main():
    import argparse
    p = argparse.ArgumentParser(description="Clan Glory Bot — Clash Squad Exit Exploit")
    p.add_argument("--clan-id", type=int, default=DEFAULT_CLAN_ID,
                   help=f"Clan ID (default: {DEFAULT_CLAN_ID})")
    p.add_argument("--region", type=str, default=DEFAULT_REGION,
                   help=f"Region (default: {DEFAULT_REGION})")
    p.add_argument("--cycles", type=int, default=DEFAULT_CYCLES,
                   help=f"Max cycles (default: {DEFAULT_CYCLES})")
    p.add_argument("--match-wait", type=int, default=MATCHMAKING_WAIT,
                   help=f"Matchmaking wait seconds (default: {MATCHMAKING_WAIT})")
    p.add_argument("--exit-wait", type=int, default=POST_EXIT_WAIT,
                   help=f"Post-exit wait seconds (default: {POST_EXIT_WAIT})")
    args = p.parse_args()

    bot = ClanGloryBot(
        clan_id=args.clan_id,
        region=args.region,
        cycles=args.cycles,
        matchmaking_wait=args.match_wait,
        post_exit_wait=args.exit_wait,
    )

    def sig_handler(sig, frame):
        bot.stop()
    signal.signal(signal.SIGINT, sig_handler)

    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
