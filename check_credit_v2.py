#!/usr/bin/env python3
"""Check Credit/Honour Score using the bot's own auth flow."""

import sys
import json
import asyncio
import aiohttp
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, 'OB54-TCP-BOT')
sys.path.insert(0, 'OB54-TCP-BOT/Pb2')

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import google.protobuf.json_format as json_format
from Pb2 import dev_generator_pb2, data_pb2

OAUTH_V2_URL = "https://ffmconnect.live.gop.garenanow.com/api/v2/oauth/guest/token:grant"
OAUTH_V1_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
OPEN_ID = "100067"
CLIENT_SECRET = "66ecd8d2eaf64751b352db7985d70650"

API_KEY = b'Yg&tc%DEuh6%Zc^8'
API_IV  = b'6oyZDr22E3ychjM%'

HTTP_HEADERS = {
    "User-Agent": "Dalvik/2.1.0",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "X-Unity-Version": "2018.4.11f1",
    "X-GA": "v1 1",
    "ReleaseVersion": "OB54",
}

def enc_uid(uid):
    msg = dev_generator_pb2.dev_generator()
    msg.saturn_ = int(uid)
    msg.garena = 1
    pb = msg.SerializeToString()
    cipher = AES.new(API_KEY, AES.MODE_CBC, API_IV)
    return cipher.encrypt(pad(pb, AES.block_size)).hex()

async def get_guest_token(guest_key):
    """Get OAuth guest token."""
    payload = {
        "guest_id": guest_key,
        "client_id": "100067",
        "client_secret": CLIENT_SECRET,
        "open_id": OPEN_ID,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(OAUTH_V1_URL, json=payload, headers=HTTP_HEADERS, ssl=False, timeout=15) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("access_token")
            return None

async def check_credit_score(uid, guest_key):
    """Get credit score for a single account."""
    token = await get_guest_token(guest_key)
    if not token:
        return None, "Failed to get OAuth token"
    
    url = "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"
    encrypted_uid = enc_uid(uid)
    edata = bytes.fromhex(encrypted_uid)
    headers = {**HTTP_HEADERS, "Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=edata, headers=headers, ssl=False, timeout=15) as resp:
            if resp.status != 200:
                return None, f"HTTP {resp.status}"
            content = await resp.read()
            try:
                info = data_pb2.AccountPersonalShowInfo()
                info.ParseFromString(content)
                d = json.loads(json_format.MessageToJson(info))
                
                basic = d.get('basicInfo', {})
                credit = d.get('creditScoreInfo', {})
                clan = d.get('clanBasicInfo', {})
                
                return {
                    'nickname': basic.get('nickname', 'N/A'),
                    'level': basic.get('level', 'N/A'),
                    'region': basic.get('region', 'N/A'),
                    'credit_score': credit.get('score', 'N/A'),
                    'credit_status': credit.get('status', 'N/A'),
                    'clan_name': clan.get('clanName', 'N/A'),
                    'clan_level': clan.get('clanLevel', 'N/A'),
                }, None
            except Exception as e:
                return None, f"Parse: {e}"

# Guest keys from the bot
GUESTS = [
    {"uid": "16648969335", "key": "g16648969335"},
    {"uid": "16648969334", "key": "g16648969334"},
    {"uid": "16648969338", "key": "g16648969338"},
]

async def main():
    print("=" * 60)
    print("  CREDIT/HONOUR SCORE CHECK (via OAuth + GetPlayerPersonalShow)")
    print("=" * 60)
    
    for g in GUESTS:
        info, err = await check_credit_score(g['uid'], g['key'])
        if err:
            print(f"\n  [{g['uid']}] ERROR: {err}")
        else:
            print(f"\n  [{g['uid']}] {info['nickname']} (Lv.{info['level']}, {info['region']})")
            print(f"    Credit Score: {info['credit_score']} | Status: {info['credit_status']}")
            print(f"    Clan: {info['clan_name']} (Lv.{info['clan_level']})")
            
            score = info['credit_score']
            if score != 'N/A':
                s = int(score)
                if s < 90:
                    print(f"    ⚠️  SCORE < 90! CANNOT play Clash Squad!")
                elif s < 100:
                    print(f"    ⚠️  Score low — approaching lockout")
                else:
                    print(f"    ✅ Score healthy")
    
    print("\n" + "=" * 60)

asyncio.run(main())
