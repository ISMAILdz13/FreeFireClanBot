#!/usr/bin/env python3
"""Check Credit/Honour Score of Free Fire accounts via GetPlayerPersonalShow API."""

import sys
import json
import requests
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, 'OB54-TCP-BOT')
sys.path.insert(0, 'OB54-TCP-BOT/Pb2')

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import google.protobuf.json_format as json_format

# Import protobuf modules
from Pb2 import dev_generator_pb2, data_pb2, devxt_count_pb2

# AES key/iv for API encryption
API_KEY = b'Yg&tc%DEuh6%Zc^8'
API_IV  = b'6oyZDr22E3ychjM%'

def enc_uid(uid):
    """Encrypt UID for GetPlayerPersonalShow API."""
    msg = dev_generator_pb2.dev_generator()
    msg.saturn_ = int(uid)
    msg.garena = 1
    pb = msg.SerializeToString()
    cipher = AES.new(API_KEY, AES.MODE_CBC, API_IV)
    encrypted = cipher.encrypt(pad(pb, AES.block_size))
    return encrypted.hex()

def get_player_info(uid, token=None):
    """Fetch player info including credit score."""
    url = "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"
    encrypted_uid = enc_uid(uid)
    edata = bytes.fromhex(encrypted_uid)
    headers = {
        'User-Agent': "Dalvik/2.1.0",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/x-www-form-urlencoded",
        'X-Unity-Version': "2018.4.11f1",
        'X-GA': "v1 1",
        'ReleaseVersion': "OB54"
    }
    if token:
        headers['Authorization'] = f"Bearer {token}"
    
    response = requests.post(url, data=edata, headers=headers, verify=False, timeout=15)
    if response.status_code != 200:
        return None, f"HTTP {response.status_code}"
    
    try:
        info = data_pb2.AccountPersonalShowInfo()
        info.ParseFromString(response.content)
        data = json.loads(json_format.MessageToJson(info))
        
        basic = data.get('basicInfo', {})
        credit = data.get('creditScoreInfo', {})
        clan = data.get('clanBasicInfo', {})
        
        return {
            'uid': uid,
            'nickname': basic.get('nickname', 'N/A'),
            'level': basic.get('level', 'N/A'),
            'region': basic.get('region', 'N/A'),
            'cs_rank': basic.get('csRank', 'N/A'),
            'cs_points': basic.get('csRankingPoints', 'N/A'),
            'credit_score': credit.get('score', 'N/A'),
            'credit_status': credit.get('status', 'N/A'),
            'credit_reason': credit.get('reason', 'N/A'),
            'clan_name': clan.get('clanName', 'N/A'),
            'clan_id': clan.get('clanId', 'N/A'),
            'clan_level': clan.get('clanLevel', 'N/A'),
        }, None
    except Exception as e:
        return None, f"Parse error: {e}"

if __name__ == '__main__':
    uids = sys.argv[1:] if len(sys.argv) > 1 else ['16648969335', '16648969334', '16648969338']
    
    print("=" * 60)
    print("  CREDIT/HONOUR SCORE CHECK")
    print("=" * 60)
    
    for uid in uids:
        info, err = get_player_info(uid)
        if err:
            print(f"\n  [{uid}] ERROR: {err}")
        else:
            print(f"\n  [{uid}] {info['nickname']} (Lv.{info['level']}, {info['region']})")
            print(f"    CS Rank: {info['cs_rank']} | CS Points: {info['cs_points']}")
            print(f"    Credit Score: {info['credit_score']} | Status: {info['credit_status']}")
            if info['credit_reason'] != 'N/A':
                print(f"    Deduct Reason: {info['credit_reason']}")
            print(f"    Clan: {info['clan_name']} (Lv.{info['clan_level']})")
            
            score = info['credit_score']
            if score != 'N/A':
                if int(score) < 90:
                    print(f"    ⚠️  SCORE < 90! Cannot play Clash Squad!")
                elif int(score) < 100:
                    print(f"    ⚠️  Score low — approaching lockout threshold")
                else:
                    print(f"    ✅ Score healthy")
    
    print("\n" + "=" * 60)
