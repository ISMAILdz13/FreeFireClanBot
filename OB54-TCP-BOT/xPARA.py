# By RedZed PARAHEX

import requests , json , binascii , time , urllib3 , base64 , datetime , re ,socket , threading , random , os , asyncio
from protobuf_decoder.protobuf_decoder import Parser
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad , unpad
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

Key , Iv = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56]) , bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

async def EnC_AEs(HeX):
    cipher = AES.new(Key , AES.MODE_CBC , Iv)
    return cipher.encrypt(pad(bytes.fromhex(HeX), AES.block_size)).hex()
    
async def DEc_AEs(HeX):
    cipher = AES.new(Key , AES.MODE_CBC , Iv)
    return unpad(cipher.decrypt(bytes.fromhex(HeX)), AES.block_size).hex()
    
async def EnC_PacKeT(HeX , K , V): 
    return AES.new(K , AES.MODE_CBC , V).encrypt(pad(bytes.fromhex(HeX) ,16)).hex()
    
async def DEc_PacKeT(HeX , K , V):
    return unpad(AES.new(K , AES.MODE_CBC , V).decrypt(bytes.fromhex(HeX)) , 16).hex()  

async def EnC_Uid(H , Tp):
    e , H = [] , int(H)
    while H:
        e.append((H & 0x7F) | (0x80 if H > 0x7F else 0)) ; H >>= 7
    return bytes(e).hex() if Tp == 'Uid' else None

async def EnC_Vr(N):
    if N < 0: ''
    H = []
    while True:
        RedZed = N & 0x7F ; N >>= 7
        if N: RedZed |= 0x80
        H.append(RedZed)
        if not N: break
    return bytes(H)
    
def DEc_Uid(H):
    n = s = 0
    for b in bytes.fromhex(H):
        n |= (b & 0x7F) << s
        if not b & 0x80: break
        s += 7
    return n
    
async def CrEaTe_VarianT(field_number, value):
    field_header = (field_number << 3) | 0
    return await EnC_Vr(field_header) + await EnC_Vr(value)

async def CrEaTe_LenGTh(field_number, value):
    field_header = (field_number << 3) | 2
    encoded_value = value.encode() if isinstance(value, str) else value
    return await EnC_Vr(field_header) + await EnC_Vr(len(encoded_value)) + encoded_value

async def CrEaTe_ProTo(fields):
    packet = bytearray()
    for field, value in fields.items():
        if isinstance(value, dict):
            nested_packet = await CrEaTe_ProTo(value)  # لازم await
            packet.extend(await CrEaTe_LenGTh(field, nested_packet))
        elif isinstance(value, int):
            packet.extend(await CrEaTe_VarianT(field, value))
        elif isinstance(value, str) or isinstance(value, bytes):
            packet.extend(await CrEaTe_LenGTh(field, value))
    return packet
    
async def DecodE_HeX(H):
    R = hex(H) 
    F = str(R)[2:]
    if len(F) == 1: F = "0" + F ; return F
    else: return F

async def Fix_PackEt(parsed_results):
    result_dict = {}
    for result in parsed_results:
        field_data = {}
        field_data['wire_type'] = result.wire_type
        if result.wire_type == "varint":
            field_data['data'] = result.data
        if result.wire_type == "string":
            field_data['data'] = result.data
        if result.wire_type == "bytes":
            field_data['data'] = result.data
        elif result.wire_type == 'length_delimited':
            field_data["data"] = await Fix_PackEt(result.data.results)
        result_dict[result.field] = field_data
    return result_dict




async def EnC_UiDInFo(uid):
    fields = {1:int(uid)}
    uid = await CrEaTe_ProTo(fields)
    uid = uid.hex()
    print(uid)
    uid = str(uid)[2:]
    return uid



async def SendInFoPaCKeT(uid , key , iv):
    uid = await EnC_UiDInFo(int(uid))
    print(uid)
    hex = f"080112090A05{uid}1005"

    return await GeneRaTePk((hex) , '0F15' , key , iv)

import datetime


async def SendRoomInfo(roomuid , key , iv):
    fields = {
    1: 1,
    2: {
        1: roomuid,
        3: {},
        4: 1,
        6: "en"
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0E15' , key , iv)

def get_room_info(packet):
    parsed_data = json.loads(packet)
    print(parsed_data)
    is_emulator = True
    room_data = parsed_data['5']['data']['1']['data']
    room_id = int(room_data['1']['data'])
    owner_uid = int(room_data['37']['data']['1']['data'])
    room_name = room_data['2']['data']
    mode = room_data['4']['data']
    members = 0
    max_members = room_data['7']['data']
    specs_number = room_data['9']['data']
    
    
    try:
        spectators = room_data['8']['data']
    except KeyError:
        spectators = 0

    try:
        members = room_data['6']['data']
        spectators = room_data['8']['data']
        is_emulator = room_data['17']['data']
        is_emulator = False
    except KeyError:
        is_emulator = True

    if members == 0:
        room_text = f" No Players , Everyone is a spectator  Spectators : {spectators}[FF0000]/[FFFFFF]{specs_number} "
    else:
        room_text = f"{members}/{max_members}"


    if mode == 1:
        mode = "BERMUDA"
    elif mode == 201:
        mode = "BATTLE CAGE"
    elif mode == 15:
        mode = "CLASH SQUAD"
    elif mode == 43:
        mode = "LONE WOLF"
    elif mode == 3:
        mode = "RUSH HOUR"
    elif mode == 27:
        mode = "BOMB SQUAD 5v5"
    elif mode == 24:
        mode = f"{xMsGFixinG('DEATH MATCH')}"

        

    return f"[B][00FF00]- PLAYER IS IN ROOM !\n\n[00FF00]- Room Name : [FFFFFF]{room_name}\n\n[00FF00]- Room Uid : [FFFFFF]{xMsGFixinG(room_id)}\n\n[FFFF00]- Owner Uid : [FFFFFF]{xMsGFixinG(owner_uid)}\n\n[FF0000]- Players In The Room : [FFFFFF]({room_text}) \n\n[FF00FF]- Spectators Count : [FFFFFF]{specs_number}\n\n[FFA500]- MODE SELECTED : [FFFFFF]{mode}\n\n[FF00FF]- Emulator Allowed : [FFFFFF]{is_emulator}\n\n\n\n[FF0000] - DEV => {xMsGFixinG('@redzedking')}"
    


def time_since(timestamp: int) -> str:

    past_time = datetime.datetime.fromtimestamp(timestamp)
    now = datetime.datetime.now()
    diff = now - past_time

    total_seconds = int(diff.total_seconds())
    minutes = (abs(total_seconds) % 3600) // 60
    seconds = abs(total_seconds) % 60

    
    return f"{minutes:02}:{seconds:02}"

def get_player_status(packet):
    parsed_data = json.loads(packet)
    print(parsed_data)
    if "5" not in parsed_data or "data" not in parsed_data["5"]:
        return "OFFLINE"

    json_data = parsed_data["5"]["data"]

    if "1" not in json_data or "data" not in json_data["1"]:
        return "OFFLINE"

    data = json_data["1"]["data"]

    if "3" not in data or "data" not in data["3"]:
        return "OFFLINE"

    status = data["3"]["data"]

    group_count = data.get("9", {}).get("data", 0)
    countmax = data.get("10", {}).get("data", 0) + 1 if "10" in data else 0
    group_owner = data.get("8", {}).get("data", 0)
    time_game_started = data.get("4", {}).get("data", 0)
    if time_game_started == 0:
        pass
    else:
        time_game_started = time_since(time_game_started)
        minutes , seconds = time_game_started.split(":")
    print(time_game_started)
    squad_text = f"{group_count}/{countmax}" if group_count and countmax else None


    mode_id_5 = data.get("5", {}).get("data")
    mode_id_6 = data.get("6", {}).get("data")
    playing = False
    print(status)
    if status == 1:
        base = "SOLO"
    elif status == 2:
        base = "INSQUAD"
    elif status in [3, 5]:
        base = "INGAME"
    elif status == 7:
        base = "MATCHMAKING"
    elif status == 4:
        room_uid = data['15']['data']
        players_count = data['17']['data']
        max_players = data['18']['data']
        room_text = f"{players_count}/{max_players}"
        room_owner = xMsGFixinG(data['1']['data'])
        base = "IN ROOM"
    elif status == 6:
        base = "SOCIAL ISLAND MODE"
    else:
        base = "NOTFOUND"


    parts = []
    mode = None

    if data.get("14") and "data" in data["14"] :
        field14 = data["14"]["data"]
        if field14 == 1:
            mode = "TRAINING"
        elif field14 == 2:
            mode = "SOCIAL ISLAND"
        playing = True
    elif status == 3:
        playing = True

    print(status , mode_id_5 , mode_id_6)
    if mode_id_5 == 2 and mode_id_6 == 1:
        mode = "BR RANK"
    if mode_id_5 == 5 and mode_id_6 == 23:
        mode = "TRAINING"
    elif mode_id_5 == 6 and mode_id_6 == 15:
        mode = "CS RANK"
    elif mode_id_5 == 1 and mode_id_6 == 43:
        mode = "LONE WOLF"
    elif mode_id_5 == 1 and mode_id_6 == 1:
        mode = "BERMUDA"
    elif mode_id_5 == 1 and mode_id_6 == 15:
        mode = "CLASH SQUAD"
    elif mode_id_5 == 1 and mode_id_6 == 29:
        mode = "CONVOY CRUNCH"
    elif mode_id_5 == 1 and mode_id_6 == 61:
        mode = "FREE FOR ALL"


    if base == "INSQUAD" and playing:
        if squad_text:
            parts.append(f"[FFFF00] INSQUAD\n- SQUAD OWNER : {xMsGFixinG(group_owner)}\n[00FF00]- PLAYING ([FFFFFF]{squad_text}) ! \n- [00FF00]PLAYING [FFFFFF]: {mode or 'UNKNOWN'}\n- [FFFF00]For : {minutes} Minutes , {seconds} Seconds ! ")
        else:
            parts.append(f"[FFFF00] INSQUAD\n- SQUAD OWNER : {xMsGFixinG(group_owner)}\n[00FF00]- PLAYING [FFFFFF]: {mode or 'UNKNOWN'}\n- [FFFF00]For : {minutes} Minutes , {seconds} Seconds ! ")


    elif base == "INSQUAD":
        if squad_text:
            parts.append(f"[FFFF00]INSQUAD ([FFFFFF]{squad_text}) \n- SQUAD OWNER : {xMsGFixinG(group_owner)}\n- [00FF00]SELECTED [FFFFFF]: {mode or 'UNKNOWN'}")
        else:
            parts.append(f"[FFFF00]INSQUAD \n- SQUAD OWNER : {xMsGFixinG(group_owner)}\n- SELECTED [FFFFFF]: {mode or 'UNKNOWN'}")


    elif base == "INGAME" or playing:
        parts.append(f"[00FF00] PLAYING [FFFFFF] : {mode or 'UNKNOWN'}\n- [FFFF00]For : {minutes} Minutes , {seconds} Seconds ! ")
    elif base == "IN ROOM":
        return {"IN_ROOM":True,"room_uid":room_uid}
    else:
        parts.append(base)

    return " ".join(parts)

async def DeCode_PackEt(input_text):
    try:
        parsed_results = Parser().parse(input_text)
        parsed_results_objects = parsed_results
        parsed_results_dict = await Fix_PackEt(parsed_results_objects)
        json_data = json.dumps(parsed_results_dict)
        return json_data
    except Exception as e:
        print(f"error {e}")
        return None
                      
def xMsGFixinG(n):
    return '🗿'.join(str(n)[i:i + 3] for i in range(0 , len(str(n)) , 3))
    
async def Ua():
    versions = [
        '4.0.18P6', '4.0.19P7', '4.0.20P1', '4.1.0P3', '4.1.5P2', '4.2.1P8',
        '4.2.3P1', '5.0.1B2', '5.0.2P4', '5.1.0P1', '5.2.0B1', '5.2.5P3',
        '5.3.0B1', '5.3.2P2', '5.4.0P1', '5.4.3B2', '5.5.0P1', '5.5.2P3'
    ]
    models = [
        'SM-A125F', 'SM-A225F', 'SM-A325M', 'SM-A515F', 'SM-A725F', 'SM-M215F', 'SM-M325FV',
        'Redmi 9A', 'Redmi 9C', 'POCO M3', 'POCO M4 Pro', 'RMX2185', 'RMX3085',
        'moto g(9) play', 'CPH2239', 'V2027', 'OnePlus Nord', 'ASUS_Z01QD',
    ]
    android_versions = ['9', '10', '11', '12', '13', '14']
    languages = ['en-US', 'es-MX', 'pt-BR', 'id-ID', 'ru-RU', 'hi-IN']
    countries = ['USA', 'MEX', 'BRA', 'IDN', 'RUS', 'IND']
    version = random.choice(versions)
    model = random.choice(models)
    android = random.choice(android_versions)
    lang = random.choice(languages)
    country = random.choice(countries)
    return f"GarenaMSDK/{version}({model};Android {android};{lang};{country};)"


def Uaa():
    versions = [
        '4.0.18P6', '4.0.19P7', '4.0.20P1', '4.1.0P3', '4.1.5P2', '4.2.1P8',
        '4.2.3P1', '5.0.1B2', '5.0.2P4', '5.1.0P1', '5.2.0B1', '5.2.5P3',
        '5.3.0B1', '5.3.2P2', '5.4.0P1', '5.4.3B2', '5.5.0P1', '5.5.2P3'
    ]
    models = [
        'SM-A125F', 'SM-A225F', 'SM-A325M', 'SM-A515F', 'SM-A725F', 'SM-M215F', 'SM-M325FV',
        'Redmi 9A', 'Redmi 9C', 'POCO M3', 'POCO M4 Pro', 'RMX2185', 'RMX3085',
        'moto g(9) play', 'CPH2239', 'V2027', 'OnePlus Nord', 'ASUS_Z01QD',
    ]
    android_versions = ['9', '10', '11', '12', '13', '14']
    languages = ['en-US', 'es-MX', 'pt-BR', 'id-ID', 'ru-RU', 'hi-IN']
    countries = ['USA', 'MEX', 'BRA', 'IDN', 'RUS', 'IND']
    version = random.choice(versions)
    model = random.choice(models)
    android = random.choice(android_versions)
    lang = random.choice(languages)
    country = random.choice(countries)
    return f"GarenaMSDK/{version}({model};Android {android};{lang};{country};)"

async def ArA_CoLor():
    Tp = ["32CD32" , "00BFFF" , "00FA9A" , "90EE90" , "FF4500" , "FF6347" , "FF69B4" , "FF8C00" , "FF6347" , "FFD700" , "FFDAB9" , "F0F0F0" , "F0E68C" , "D3D3D3" , "A9A9A9" , "D2691E" , "CD853F" , "BC8F8F" , "6A5ACD" , "483D8B" , "4682B4", "9370DB" , "C71585" , "FF8C00" , "FFA07A"]
    return random.choice(Tp)
    
async def xBunnEr():
    bN = [902000306 , 902000305 , 902000003 , 902000016 , 902000017 , 902000019 , 902031010 , 902043025 , 902043024 , 902000020 , 902000021 , 902000023 , 902000070 , 902000087 , 902000108 , 902000011 , 902049020 , 902049018 , 902049017 , 902049016 , 902049015 , 902049003 , 902033016 , 902033017 , 902033018 , 902048018 , 902000306 , 902000305 , 902000079]
    return random.choice(bN)


async def leave_chat(T , L , K , V):
    fields = {1: 4, 2: { 1: T, 3: L}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '1201' , K , V)

async def Send_GhosTs(Uid , Nm , sQ , K , V):
    fields =  {1: 61 , 2: {1: int(Uid) , 2: {1: int(Uid) , 2: 1159, 3: f'{Nm}', 5: 12, 6: 9999999, 7: 1, 8: {2: 1, 3: 1}, 9: 3}, 3: sQ}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V)

async def Join_Sq(T , UiD, sQ , K , I):
    fields = {
  1: 4,
  2: {
    1: UiD,
    4: "\u0001\u0003\u0004\u0007\t\n\u000b\u0012\u000f\u0019\u001a ",
    6: 1,
    8: 1,
    9: {
      4: "y[WW",
      6: 11,
      7: "\u001d`at\u0005d\u001d\u0016",
      8: "1.118.3",
      9: 3,
      10: 2
    },
    13: T,
    15: sQ,
    16: "OR",
    20: {
      1: 21
    }
  }
}

    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0501', K , I)

async def xSEndMsg(Msg , Tp , Tp2 , id , K , V):
    feilds = {1: id , 2: Tp2 , 3: Tp, 4: Msg, 5: 1735129800, 7: 2, 9: {1: "RedZedTOP1", 2: int(await xBunnEr()), 3: 901048018, 4: 330, 5: 909034009, 8: "RedZedTOP1", 10: 1, 11: 1, 13: {1: 2}, 14: {1: 12484827014, 2: 8, 3: "\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"}, 12: 0}, 10: "en", 13: {3: 1}}
    Pk = (await CrEaTe_ProTo(feilds)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return await GeneRaTePk(Pk, '1201', K, V)
    
async def xSEndMsgsQ(Msg , id , K , V):
    fields = {1: id , 2: id , 4: Msg , 5: 1756580149, 7: 2, 8: 904990072, 9: {1: "RedZedTOP1", 2: await xBunnEr(), 4: 330, 5: 827001005, 8: "RedZedTOP1", 10: 1, 11: 1, 13: {1: 2}, 14: {1: 1158053040, 2: 8, 3: "\u0010\u0015\b\n\u000b\u0015\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"}}, 10: "en", 13: {2: 2, 3: 1}}
    Pk = (await CrEaTe_ProTo(fields)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return await GeneRaTePk(Pk, '1201', K, V)     
async def AuthClan(CLan_Uid, AuTh, K, V):
    fields = {1: 3, 2: {1: int(CLan_Uid), 2: 1, 4: str(AuTh)}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '1201' , K , V)
async def AutH_GlobAl(K, V):
    fields = {
    1: 3,
    2: {
        2: 5,
        3: "fr"
    }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '1201' , K , V)

async def RedZedLeaveRoom(uid,key,iv):
    fields = {
        1: 6,
        2: {
            1: uid
        }
        }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0E15', key , iv)



async def RedZedTeamCode(T,key,iv):
    fields = {
  1: 4,
  2: {
    4: "\u0001\u0003\u0004\u0007\t\n\u000b\u0012\u000e\u0016\u0019\u001a \u001d'",
    5: str(T),
    6: 6,
    8: 1,
    9: {
      2: 3140,
      3: "vX\\Q\u0016\u0005\bN\u0006R\b\u0001U\u0002\rR[\u0003TU\u0006\b\u0007U\u0004P\\\u0000RRRT\t\u0007\fP\n\nS\u0000\u0013\u0000\u0001HpYHFN\u001e\u0000\u001d\u0001\u001d\u0016\u0005\nN[U\u0006\u0003cwewhaSdeF^Fr}Q|V\u000edRS\u0000\u0005\t\u001b\u0003K^s`c^\u0005\u001fw\u0003\u0005@Bz\u0006\u0006\\{\bVbSR~J{La\u0005\u0011\u0006\u0005L[UNAwHZ_\u0019s~_Rvdy\u001d_uq\u001aCNRpM{\n\u0015\bMaBR[JQezTvcELuu\u0005_tHdFS\u0006`OY\u0007\u000b\u0013\u0003LYA\u0000AAzPWdqDy~Uj\\\u0005GgovQzrU\r\u0012\tHq[@Dr[\u0000`zS|MIZR\u0005r\u0006g\u0005pM\nPTrS\f\u0013\u0005\rHIwVRhAgfl\u000e]R\u0019EZ\\A@\fLHYN\u001bXW\t\u0016\u0007DjydvuG\u0001]MUO\u0005^[tBcS\u0013J@\u0002\\ZJ\f\b\u0017\fNyNaV}F~\rT\u0006Y\u000fBzyag\u0007@{BxU^WNV\t\u001b\u0000\u0007J\\\u0003d\u0003vBBQ^^\u001bCd\u0005\\M`F@C\t\u0007^sUS\u000f\u0014\u0003LRX`lzm_\u0004ovtxDwPr@`^B_Y\\`Mks\n",
      4: "zW\\R",
      6: 11,
      7: "\u0014twqqq~\u0016\u0013",
      8: "1.120.19",
      9: 3,
      10: 2
    },
    13: "ar",
    16: "7OR\u0019",

  }
}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , key , iv)


async def RedZedTeamJoinChat(cQ,uid,key,iv):
    fields = {
  1: 3,
  2: {
    1: uid,
    3: "ar",
    4: str(cQ)
  }
}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , key , iv)


async def RedZedTeamChat(MsG,Uid,key,iv):
    fields = {
  1: 1,
  2: {
    1: 6728454010,
    2: Uid,
    4: await str(MsG),
    5: 1770940400,
    7: 6,
    9: {
      1: "@RedZedㅤFxp!",
      2: 902038020,
      4: 308,
      8: "PARAHEXBOT?",
      13: {},
      14: {
        1: 6728454010,
        2: 4,
        3: "\t\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011"
      }
    },
    10: "ar",
    13: {
      1: "https://lh3.googleusercontent.com/a/ACg8ocL-nkgE3QDkoih_D5YHMybFA0W-oyRvFhBBSuBgpujrySInbQ=s96-c",
      2: 1,
      3: 1
    },
    14: {}
  }
}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , key , iv)

async def RedZedJoinRomm(uid,password,key,iv):
    fields = {
  1: 3,
  2: {
    1: int(uid),
    2: str(password),
    8: {
      1: "IDC3",
      2: 149,
      3: "BD"
    },
    9: "\u0001\u0003\u0004\u0007\t\n\u000b\u0012\u000e\u0016\u0019 \u001d",
    10: 1,
    12: {},
    13: 1,
    14: 1,
    16: "en",
    22: {
      1: 21
    }
  }
}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0E15' , key , iv)

async def new_lag(K,I):
    fields = {
        1: 15,
        2: {
            1: 804266360,
            2: 1
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , I)


async def RedZedRefuse(owner,uid, K,V):
    fields = {
    1: 5,
    2: {
        1: int(owner),
        2: 1,
        3: int(uid),
        4: "[FF0000][B][C] ERROR , WELCOME TO [FFFFFF]REDZED [00FF00]PARAHEX BOT ! \n[FFFF00]NEW VERSION NEW FUNCTION !\n[FF0000]TELEGRAM : @redzedking\n\n"
    }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V)


async def RedZed_SendInv(uid,K,V):
    fields = fields = {1: 33, 2: {1: int(uid), 2: "BD", 3: 1, 4: 1, 6: "RedZedKing!!", 7: 330, 8: 1000, 9: 100, 10: "DZ", 12: 1, 13: int(uid), 16: 1, 17: {2: 159, 4: "y[WW", 6: 11, 8: "1.118.1", 9: 3, 10: 1}, 18: 306, 19: 18, 24: 902000306, 26: {}, 27: {1: 11, 2: 12999994075, 3: 999}, 28: {}, 31: {1: 1, 2: 32768}, 32: 32768, 34: {1: 12947882969, 2: 8, 3: "\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"}}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V)



async def trydecByRedZed(pack):

    try:
        r = pack['5']['data']['3']['data']['31']['data']
    except KeyError:
        r = pack['5']['data']['31']['data']
    except:
        return None
    return r

async def RedZedAccepted(uid,code,K,V):
    fields = {
        1: 4,
        2: {
            1: uid,
            3: uid,
            8: 1,
            9: {
            2: 161,
            4: "y[WW",
            6: 11,
            8: "1.114.18",
            9: 3,
            10: 1
            },
            10: str(code),
        }
        }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V)

async def LagSquad(K,V):
    fields = {
    1: 15,
    2: {
        1: 1124759936,
        2: 1
    }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V)

async def GeT_Status(PLayer_Uid , K , V):
    PLayer_Uid = await EnC_Uid(PLayer_Uid , Tp = 'Uid')
    if len(PLayer_Uid) == 8: Pk = f'080112080a04{PLayer_Uid}1005'
    elif len(PLayer_Uid) == 10: Pk = f"080112090a05{PLayer_Uid}1005"
    return await GeneRaTePk(Pk , '0f15' , K , V)
           
async def SPam_Room(Uid , Rm , Nm , K , V):
    fields = {1: 78, 2: {1: int(Rm), 2: f"[{ArA_CoLor()}]{Nm}", 3: {2: 1, 3: 1}, 4: 330, 5: 1, 6: 201, 10: xBunnEr(), 11: int(Uid), 12: 1}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0e15' , K , V)
async def GenJoinSquadsPacket(code,  K , V):
    fields = {}
    fields[1] = 4
    fields[2] = {}
    fields[2][4] = bytes.fromhex("01090a0b121920")
    fields[2][5] = str(code)
    fields[2][6] = 6
    fields[2][8] = 1
    fields[2][9] = {}
    fields[2][9][2] = 800
    fields[2][9][6] = 11
    fields[2][9][8] = "1.111.1"
    fields[2][9][9] = 5
    fields[2][9][10] = 1
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V)   
async def GenJoinGlobaL(owner , code , K, V):
    fields = {
    1: 4,
    2: {
        1: owner,
        6: 1,
        8: 1,
        13: "en",
        15: code,
        16: "OR",
    }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V)

async def FS(K,V):
    fields = {
            1: 9,
            2: {
                1: 13250133060
            }
            }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V)




#EMOTES BY PARAHEX X CODEX
async def Emote_k(TarGeT , idT, K, V):
    fields = {
        1: 21,
        2: {
            1: 804266360,
            2: 909000001,
            5: {
                1: TarGeT,
                3: idT,
            }
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V)

#EMOTES BY PARAHEX X CODEX


async def GeTSQDaTa(D):
    try:
        uid = D['5']['data']['1']['data']
        chat_code = D["5"]["data"]["17"]["data"]
        squad_code = D["5"]["data"]["31"]["data"]
        return uid, chat_code , squad_code
    except:
        return None


async def AutH_Chat(T , uid, code , K, V):
    fields = {
  1: T,
  2: {
    1: uid,
    3: "en",
    4: str(code)
  }
}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '1201' , K , V)
async def Msg_Sq(msg, owner, bot, K, V):
    fields = {
    1: 1,
    2: 2,
    2: {
        1: bot,
        2: owner,
        4: msg,
        5: 1757799182,
        7: 2,
        9: {
            1: "Fun1w5a2",
            2: await xBunnEr(),
            3: 909000024,
            4: 330,
            5: 909000024,
            7: 2,
            10: 1,
            11: 1,
            12: 0,
            13: {1: 2},
            14: {
                1: bot,
                2: 8,
                3: "\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
            }
        },
        10: "ar",
        13: {3: 1},
        14: ""
    }
}
    proto_bytes = await CrEaTe_ProTo(fields)
    return await GeneRaTePk(proto_bytes.hex(), '1201', K, V)


async def ghost_pakcet(player_id , secret_code ,K , V):
    fields = {
        1: 61,
        2: {
            1: int(player_id),  
            2: {
                1: int(player_id),  
                2: int(time.time()),  
                3: "MR3SKR",
                5: 12,  
                6: 9999999,
                7: 1,
                8: {
                    2: 1,
                    3: 1,
                },
                9: 3,
            },
            3: secret_code,},}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V)
async def GeneRaTePk(Pk , N , K , V):
    PkEnc = await EnC_PacKeT(Pk , K , V)
    _ = await DecodE_HeX(int(len(PkEnc) // 2))
    if len(_) == 2: HeadEr = N + "000000"
    elif len(_) == 3: HeadEr = N + "00000"
    elif len(_) == 4: HeadEr = N + "0000"
    elif len(_) == 5: HeadEr = N + "000"
    else: print('ErroR => GeneRatinG ThE PacKeT !! ')
    return bytes.fromhex(HeadEr + _ + PkEnc)
async def OpEnSq(K , V):
    fields = {1: 1, 2: {2: "\u0001", 3: 1, 4: 1, 5: "en", 9: 1, 11: 1, 13: 1, 14: {2: 5756, 6: 11, 8: "1.111.5", 9: 2, 10: 4}}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V) 

async def cHSq(Nu , Uid , K , V):
    fields = {1: 17, 2: {1: int(Uid), 2: 1, 3: int(Nu - 1), 4: 62, 5: "\u001a", 8: 5, 13: 329}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V) 

async def SEnd_InV(Nu , Uid , K , V):
    fields = {1: 2 , 2: {1: int(Uid) , 2: "BD" , 4: int(Nu)}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V) 
    
async def ExiT(idT , K , V):
    fields = {
        1: 7,
        2: {
            1: idT,
        }
        }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0501' , K , V) 