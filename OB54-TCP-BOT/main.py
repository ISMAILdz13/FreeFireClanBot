# ======================== IMPORTS =======================
import requests , os , psutil , sys , jwt , pickle , json , binascii , time , urllib3 , base64 , datetime , re , socket , threading , ssl , pytz , aiohttp , traceback , signal , multiprocessing , asyncio
# Add parent directory to sys.path to import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.core.bot import FreeFireBot
except ImportError:
    FreeFireBot = None
from Pb2 import DEcwHisPErMsG_pb2 , MajoRLoGinrEs_pb2 , PorTs_pb2 , MajoRLoGinrEq_pb2 , sQ_pb2 , Team_msg_pb2, RemoveFriend_Req_pb2, GetFriend_Res_pb2, spam_request_pb2, devxt_count_pb2, dev_generator_pb2, kyro_title_pb2, room_join_pb2
from protobuf_decoder.protobuf_decoder import Parser
from xC4 import * ; from xHeaders import *
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from cfonts import render, say
import google.protobuf.json_format as json_format
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
async def handle_infox_command(inPuTMsG: str, sender_uid: int, chat_id: int, chat_type: int,
                               key: bytes, iv: bytes, region: str):
    """
    /infox <uid> – Fetch detailed player info and display in three boxes.
    All numbers (UIDs, levels, likes, etc.) are formatted with 🥀 between digits.
    """
    import aiohttp
    import asyncio

    # 1. Parse the command
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        await safe_send_message(chat_type,
                                "[B][C][FF0000]❌ Usage: /infox <uid>",
                                sender_uid, chat_id, key, iv)
        return

    target_uid = parts[1].strip()
    if not target_uid.isdigit():
        await safe_send_message(chat_type,
                                "[B][C][FF0000]❌ Invalid UID.",
                                sender_uid, chat_id, key, iv)
        return

    # Helper to format numbers with 🥀 between digits
    def format_num(num):
        # Convert to string, then join each digit with '🥀'
        return "🥀".join(str(num))

    # 2. Send initial status
    await safe_send_message(chat_type,
                            f"[B][C][FFFF00]🔍 Fetching infox for {format_num(target_uid)}...",
                            sender_uid, chat_id, key, iv)

    # 3. Call the API
    api_url = f"https://mafuuuu-info-api.vercel.app/mafu-info?uid={target_uid}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=15) as resp:
                if resp.status != 200:
                    await safe_send_message(chat_type,
                                            f"[B][C][FF0000]❌ API error (HTTP {resp.status})",
                                            sender_uid, chat_id, key, iv)
                    return
                data = await resp.json()
    except asyncio.TimeoutError:
        await safe_send_message(chat_type,
                                "[B][C][FF0000]❌ Request timed out.",
                                sender_uid, chat_id, key, iv)
        return
    except Exception as e:
        await safe_send_message(chat_type,
                                f"[B][C][FF0000]❌ Network error: {str(e)[:80]}",
                                sender_uid, chat_id, key, iv)
        return

    # 4. Extract data (using .get() to avoid KeyError)
    basic = data.get('basicInfo', {})
    clan = data.get('clanBasicInfo', {})
    captain = data.get('captainBasicInfo', {})
    social = data.get('socialInfo', {})
    credit = data.get('creditScoreInfo', {})

    # 5. Build the boxes (each sent as a separate message)
    # Box 1 – Player Info
    msg1 = f"""[B][C][00FF00]✅ PLAYER INFO
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━
[FFFF00]Nickname    : [FFFFFF]{basic.get('nickname', 'N/A')}
[FFFF00]Region      : [FFFFFF]{basic.get('region', 'N/A')}
[FFFF00]Level       : [FFFFFF]{format_num(basic.get('level', 'N/A'))}
[FFFF00]Likes       : [FFFFFF]{format_num(basic.get('liked', 'N/A'))}
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━"""
    await safe_send_message(chat_type, msg1, sender_uid, chat_id, key, iv)
    await asyncio.sleep(0.3)

    # Box 2 – Clan Info
    captain_nick = captain.get('nickname', 'N/A')
    clan_name = clan.get('clanName', 'N/A')
    if clan_name != 'N/A':
        msg2 = f"""[B][C][00FF00]✅ CLAN INFO
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━
[FFFF00]Clan Name    : [FFFFFF]{clan_name}
[FFFF00]Clan ID      : [FFFFFF]{format_num(clan.get('clanId', 'N/A'))}
[FFFF00]Captain      : [FFFFFF]{captain_nick}
[FFFF00]Captain UID  : [FFFFFF]{format_num(clan.get('captainId', 'N/A'))}
[FFFF00]Clan Level   : [FFFFFF]{format_num(clan.get('clanLevel', 'N/A'))}
[FFFF00]Members      : [FFFFFF]{format_num(clan.get('memberNum', 'N/A'))} / {format_num(clan.get('capacity', 'N/A'))}
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━"""
    else:
        msg2 = f"""[B][C][00FF00]✅ CLAN INFO
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━
[FFFFFF]No clan information available.
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━"""
    await safe_send_message(chat_type, msg2, sender_uid, chat_id, key, iv)
    await asyncio.sleep(0.3)

    # Box 3 – Extra Info
    gender = social.get('gender', 'N/A')
    if gender.startswith('Gender_'):
        gender = gender[7:]  # Remove "Gender_" prefix
    language = social.get('language', 'N/A')
    if language.startswith('Language_'):
        language = language[9:]  # Remove "Language_" prefix
    signature = social.get('signature', 'N/A')
    credit_score = credit.get('creditScore', 'N/A')

    msg3 = f"""[B][C][00FF00]✅ EXTRA INFO
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━
[FFFF00]Gender      : [FFFFFF]{gender}
[FFFF00]Language    : [FFFFFF]{language}
[FFFF00]BIO   : [FFFFFF]{signature}
[FFFF00]Honour Score: [FFFFFF]{format_num(credit_score) if credit_score != 'N/A' else 'N/A'}
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━"""
    await safe_send_message(chat_type, msg3, sender_uid, chat_id, key, iv)
async def handle_duo_command(inPuTMsG: str, sender_uid: int, chat_id: int, chat_type: int,
                             key: bytes, iv: bytes, region: str):
    """
    /duo <uid> – Fetches duo info and shows a clean box (like the working image).
    UIDs are formatted with 🥀 between digits.
    """
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        await safe_send_message(chat_type,
                                "[B][C][FF0000]❌ Usage: /duo <uid>",
                                sender_uid, chat_id, key, iv)
        return

    target_uid = parts[1].strip()
    if not target_uid.isdigit():
        await safe_send_message(chat_type,
                                "[B][C][FF0000]❌ Invalid UID.",
                                sender_uid, chat_id, key, iv)
        return

    def format_uid(uid_str):
        return "🥀".join(uid_str)

    await safe_send_message(chat_type,
                            f"[B][C][FFFF00]🔍 Fetching duo info for {format_uid(target_uid)}...",
                            sender_uid, chat_id, key, iv)

    api_url = f"https://fuhx-rizer-duo.onrender.com/info?uid={target_uid}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=15) as resp:
                if resp.status != 200:
                    await safe_send_message(chat_type,
                                            f"[B][C][FF0000]❌ সা👽লার DUO নাই :( ",
                                            sender_uid, chat_id, key, iv)
                    return
                data = await resp.json()

        if data.get("status") != "success":
            err = data.get("message", "Unknown error")
            await safe_send_message(chat_type,
                                    f"[B][C][FF0000]❌ {err}",
                                    sender_uid, chat_id, key, iv)
            return

        duo = data.get("data", {})
        if not duo:
            await safe_send_message(chat_type,
                                    f"[B][C][FF0000]❌ No duo data for {format_uid(target_uid)}",
                                    sender_uid, chat_id, key, iv)
            return

        response_uid = data.get("uid", target_uid)
        partner_uid = duo.get("partner_uid", "N/A")

        # Build a clean box message (single string)
        box_msg = f"""[B][C][00FF00]✅ DUO INFORMATION
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[FFFF00]Your UID       : [FFFFFF]{format_uid(response_uid)}
[FFFF00]Partner UID   : [FFFFFF]{format_uid(partner_uid) if partner_uid != 'N/A' else 'N/A'}
[FFFF00]Duo Level     : [FFFFFF]{duo.get('duo_level', 'N/A')}
[FFFF00]Intimacy Score: [FFFFFF]{duo.get('intimacy_score', 'N/A')}
[FFFF00]Created On    : [FFFFFF]{duo.get('created_on', 'N/A')}
[FFFF00]Days Active   : [FFFFFF]{duo.get('days_active', 'N/A')}
[FFFF00]Duo Status    : [FFFFFF]{duo.get('duo_status', 'N/A')}
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

        await safe_send_message(chat_type, box_msg, sender_uid, chat_id, key, iv)

    except asyncio.TimeoutError:
        await safe_send_message(chat_type,
                                "[B][C][FF0000]❌ NO DUO FOUND",
                                sender_uid, chat_id, key, iv)
    except Exception as e:
        await safe_send_message(chat_type,
                                f"[B][C][FF0000]❌ Error: {str(e)[:80]}",
                                sender_uid, chat_id, key, iv)
async def handle_praisa_command(inPuTMsG: str, sender_uid: int, chat_id: int, chat_type: int,
                                key, iv, region):
    """
    /praisa <name> – sends 17 positive messages + rotating emotes every 5 sec.
    """
    # ----- Fix region to string -----
    if not isinstance(region, str):
        region = str(region).upper()
    if region not in ("IND", "BD", "SG", "BR", "US"):
        region = "IND"

    # ----- Fix iv to 16 bytes -----
    if isinstance(iv, str):
        iv = bytes.fromhex(iv)
    if len(iv) != 16:
        if len(iv) < 16:
            iv = iv.ljust(16, b'\x00')
        else:
            iv = iv[:16]

    # ----- Fix key to bytes -----
    if isinstance(key, str):
        key = bytes.fromhex(key)

    # ----- Parse command -----
    parts = inPuTMsG.strip().split(maxsplit=1)
    if len(parts) < 2:
        await safe_send_message(chat_type,
                                "[B][C][FF0000]❌ Usage: /praisa <name>",
                                sender_uid, chat_id, key, iv)
        return

    name = parts[1].strip()
    messages = [
        "🌟 {Name} তুমি সত্যিই অসাধারণ একজন মানুষ!",
        "🔥 {Name} তোমার পরিশ্রম একদিন বড় সফলতা এনে দেবে!",
        "💎 {Name} তুমি ইউনিক, তোমার মতো আর কেউ নেই!",
        "🚀 {Name} তোমার ভবিষ্যৎ অনেক উজ্জ্বল!",
        "👑 {Name} তুমি একজন লিডার হওয়ার যোগ্য!",
        "🌈 {Name} তোমার হাসি সবার দিন সুন্দর করে দেয়!",
        "💖 {Name} সবসময় এমন পজিটিভ থাকো!",
        "🏆 {Name} তুমি যা চাও তা অর্জন করার ক্ষমতা তোমার আছে!",
        "✨ {Name} তুমি অনুপ্রেরণার উৎস!",
        "🌟 {Name} নিজের উপর বিশ্বাস রাখো, তুমি পারবে!",
        "🎯 {Name} তোমার ফোকাসই তোমার শক্তি!",
        "📈 {Name} তুমি প্রতিদিন আরও ভালো হচ্ছো!",
        "🧠 {Name} তোমার চিন্তাভাবনা সত্যিই প্রশংসনীয়!",
        "💫 {Name} তুমি অনেক দূর যাবে ইনশা🤫আ🤫ল্লা🤫হ!",
        "🌍 {Name} পৃথিবী তোমার ট্যালেন্ট দেখার অপেক্ষায়!",
        "🛡️ {Name} তুমি শক্ত, আত্মবিশ্বাসী ও সাহসী!",
        "🏅 {Name} তুমি সত্যিকারের চ্যাম্পিয়ন!"
    ]

    emote_cycle = [909000014, 909000034, 909000039, 909000055, 909000071]
    emote_index = 0
    stop_emotes = False

    async def send_emotes():
        nonlocal emote_index, stop_emotes
        while not stop_emotes:
            try:
                emote_id = emote_cycle[emote_index % len(emote_cycle)]
                pkt = await Emote_k(sender_uid, emote_id, key, iv, region)
                if pkt and online_writer:
                    online_writer.write(pkt)
                    await online_writer.drain()
                emote_index += 1
                await asyncio.sleep(3)
            except Exception as e:
                print(f"[Praisa] Emote error: {e}")
                break

    emote_task = asyncio.create_task(send_emotes())

    try:
        for msg in messages:
            colored = f"[B][C]{get_random_color()} {msg.replace('{Name}', name.title())}"
            await safe_send_message(chat_type, colored, sender_uid, chat_id, key, iv)
            await asyncio.sleep(1)
    finally:
        stop_emotes = True
        emote_task.cancel()
        try:
            await emote_task
        except asyncio.CancelledError:
            pass

    await safe_send_message(chat_type,
                            f"[B][C][00FF00]✅ Praisa completed for {name.title()}!",
                            sender_uid, chat_id, key, iv)
async def join_teamcode_packet(team_code, key, iv, region):
    """Join team using code"""
    fields = {
        1: 4,
        2: {
            4: bytes.fromhex("01090a0b121920"),
            5: str(team_code),
            6: 6,
            8: 1,
            9: {
                2: 800,
                6: 11,
                8: "1.126.2",
                9: 5,
                10: 1
            }
        }
    }
    
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"
        
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet_type, key, iv)
async def xSEndMsg(Msg, Tp, Tp2, id, K, V):
    """
    Send message packet with full payload structure
    Msg: Message text
    Tp: Message type
    Tp2: Target/recipient
    id: Sender ID
    K: Key for encryption
    V: IV for encryption
    """
    feilds = {
        1: id,
        2: Tp2,
        3: Tp,
        4: Msg,
        5: 1735129800,
        9: {
            1: "[FFFFFF]BLACK",
            2: int(await xBunnEr()),
            3: 901048020,
            4: 330,
            5: 1001000001,
            8: "xBesTo - C4",
            10: 1,
            11: 1,
            13: {1: 2},
            14: {
                1: 12484827014,
                2: 8,
                3: "\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
            },
            12: 0
        },
        10: "en",
        13: {3: 1}
    }
    Pk = (await CrEaTe_ProTo(feilds)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return await GeneRaTePk(Pk, '1201', K, V)
async def handle_greeting(inPuTMsG: str, uid: int, chat_id: int, chat_type: int, key: bytes, iv: bytes, region: str):
    """Auto-reply to hi/hello/hey with message + emote"""
    trigger_words = {'hi', 'hello', 'hey'}
    if inPuTMsG.strip().lower() in trigger_words:

        reply = "[B][C][00FF00]বা🥀লের hi তোর বোন কে চাই, বিয়ে করব সংসার গড়বো তারপর আবার বলব তোকে bye bye!!"
        await safe_send_message(chat_type, reply, uid, chat_id, key, iv)

        try:
            emote_pkt = await Emote_k(int(uid), 909000002, key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_pkt)
        except Exception as e:
            print(f"Emote failed: {e}")
async def start_match_spam_loop(uid, chat_id, chat_type, key, iv, region):
    global auto_start_running, stop_auto
    
    auto_start_running = True
    stop_auto = False
    
    print(f"[AUTO] Start spamming match for 17 seconds...")
    
    try:
        # স্টার্ট মেসেজ পাঠানো
        start_msg = f"[B][C][00FF00]✅ ১৭ সেকেন্ডের জন্য ম্যাচ স্টার্ট স্প্যাম শুরু হচ্ছে...\n🎯 Target: {uid}"
        await safe_send_message(chat_type, start_msg, uid, chat_id, key, iv)
        
        # স্টার্ট প্যাকেট তৈরি
        start_packet = await start_auto_packet(key, iv, region)
        end_time = time.time() + start_spam_duration
        
        # স্প্যাম লুপ
        while time.time() < end_time and not stop_auto:
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', start_packet)
            await asyncio.sleep(start_spam_delay)
            
        # সমাপ্তি মেসেজ
        if not stop_auto:
            done_msg = "[B][C][FFFF00]⌛ ১৭ সেকেন্ড পূর্ণ হয়েছে! স্টার্ট স্প্যাম বন্ধ করা হলো।"
            await safe_send_message(chat_type, done_msg, uid, chat_id, key, iv)

    except Exception as e:
        print(f"[ERROR] Spam Loop Error: {e}")
        error_msg = f"[B][C][FF0000]❌ স্প্যামিংয়ে ত্রুটি হয়েছে: {str(e)}"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
    
    auto_start_running = False
    stop_auto = False

async def send_love_with_emotes(name: str, uid: int, chat_id: int, chat_type: int, key: bytes, iv: bytes, region: str):
    """Love messages + periodic emote 909000010 every 5 seconds"""
    messages = [
        "[B][C][FFFFFF]♡ [FF1493]{Name} [FFFFFF]তুই আমার [00FFFF]সেফ জোন [FFFFFF]♡",
        "[B][C][FFFFFF]♡ [FF1493]{Name} [FFFFFF] তোমার ম👽নে কি আমা👽কে এক👽টু[00FFFF] জায়👽গা় দে👽ওয়া যাবে পিও [FFFFFF]♡",
        "[B][C][FFFFFF]♡ [FF1493]{Name} [FFFFFF]তোমা👽কে চু👽দা [00FFFF]আমার আ👽কাশ পরি👽মাণ সখ [FFFFFF]♡",                  
        "[B][C][FFFFFF]♡ [FF1493]{Name} [FFFFFF] তুমি আমা👽র মি👽য়া খলিফা [00FFFF]তোমা👽কে ভরে দেও👽য়া আ👽মার অ👽নেক ই👽চ্ছা [FFFFFF]♡",
        "[B][C][FFFFFF]♡ [FF1493]{Name} [FFFFFF] তুমি আ👽মার আশা [00FFFF] তুমি আমার ভালোব👽াসা [FFFFFF]♡",
        "[B][C][FFFFFF]♡ [00FF00]লবিতে [FFFFFF]শুধু [FFD700]{Name} তোকেই খুঁজি [FFFFFF]♡",
        "[B][C][FFFFFF]♡ [FF1493]{Name} [FFFFFF] তোমার জ👽ন্য আমি রাখ👽তে পা🥰রি বাজি[00FFFF] তো🥰মার জ🥰ন্য সা👽ত সমুদ্র তেরো ন🥰দী পারি দিতেও রাজি[FFFFFF]♡",
        "[B][C][FFFFFF]♡ [00FFFF]এয়ারড্রপের [FFFFFF]চেয়েও [FF1493]তুই দামি [FFFFFF]♡",
        "[B][C][FFFFFF]♡ [FFD700]{Name} তোর হাসিতে [FFFFFF]আমার [00FF00]HP বাড়ে [FFFFFF]♡",
        "[B][C][FFFFFF]♡ [FF00FF]{Name} তুই ছাড়া [FFFFFF]গেম খেলা [00FFFF]পুরোই বৃথা [FFFFFF]♡",
        "[B][C][FFFFFF]♡ [FF1493]{Name} [FFFFFF]তোমার অভাবে [00FFFF]আমি হ্যান্ডে👽ল মারী একা একা [FFFFFF]♡",
        "[B][C][FFFFFF]♡ [FFA500]স্নাইপারের [FFFFFF]একমাত্র [FF1493]লক্ষ্য {Name} তুই [FFFFFF]♡",
        "[B][C][FFFFFF]♡ [FF1493]{Name} [FFFFFF]তোমাকে নিয়ে[00FFFF] বাঁধবো একটা ছোট বাসা[FFFFFF]♡",
        "[B][C][FFFFFF]♡ [32CD32]{Name} তুই আমার [FFFFFF]গ্লু-ওয়ালের [FFD700]কভার [FFFFFF]♡",
        "[B][C][FFFFFF]♡ [FF0000]{Name} চল দুজনে [FFFFFF]মিলে [00FFFF]বুইয়া নিই [FFFFFF]♡"
    ]

    # Background emote loop
    async def emote_loop():
        while not stop_emote.is_set():
            try:
                pkt = await Emote_k(int(uid), 909000010, key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', pkt)
            except Exception as e:
                print(f"Love emote error: {e}")
            await asyncio.sleep(5)

    stop_emote = asyncio.Event()
    emote_task = asyncio.create_task(emote_loop())

    try:
        for msg in messages:
            colored = f"[B][C][FFFFFF][B][C][32CD32][FFFFFF][FFA500][FFFFFF][FF00FF][FFD700][FFFFFF][00FFFF][FF1493][00FF00][FFFFFF][FF0000] {msg.replace('{Name}', name.upper())}"
            await safe_send_message(chat_type, colored, uid, chat_id, key, iv)
            await asyncio.sleep(2)
    finally:
        stop_emote.set()
        emote_task.cancel()
        try:
            await emote_task
        except asyncio.CancelledError:
            pass


async def handle_love_command(inPuTMsG: str, uid: int, chat_id: int, chat_type: int, key: bytes, iv: bytes, region: str):
    """Call this from TcPChaT when /love is detected. It handles everything."""
    if not inPuTMsG.strip().startswith('/love '):
        return
    parts = inPuTMsG.strip().split(maxsplit=1)
    if len(parts) < 2:
        error_msg = "[B][C][FF0000]❌ ERROR! Usage: /love <name>\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    name = parts[1].strip()
    # Fire and forget the long task
    asyncio.create_task(send_love_with_emotes(name, uid, chat_id, chat_type, key, iv, region))
#GALLIIII
async def send_gali_with_emotes(name: str, uid: int, chat_id: int, chat_type: int, key: bytes, iv: bytes, region: str):
    """Send gali messages + emote 909000002 every 1 second"""
    messages = [
        "{Name} খান🤫কির ছেলে !!",
        "{Name} মাদার চো🤫দ, তোর মা🤫কে চু🤫দি !!",
        "{Name} মাদার চো🤫দ, তোর মা🤫কে 5G স্পিডে চু🤫দি !!",
        "{Name} বোকাচো🤫দা, তোর মা🤫কে কন🤫ডম লাগিয়ে চু🤫দি !!",
        "{Name} বোকাচো🤫দা, তোর মা🤫কে প্রতিদিন ১০,০০০ টাকার সার্ভিস দেই !!",
        "F🤫U🤫C🤫K {Name} !!",
        "{Name} মাদার চো🤫দ, পো🤫দ মে🤫রে দিবো !!",
        "{Name} মাদার চো🤫দ !!",
        "{Name} খান🤫কি, আমি তোর বা🤫প !!",
        "{Name} তোর মা🤫কে আমি চু🤫ই🤫দা তোরে জন্মায় ছি !!",
        "{Name} বোকাচো🤫দা, খান🤫কির ছেলে !!",
        "{Name} মাদার চো🤫দ, তোর মা🤫কে ১৮০ কি.মি. স্পিডে চু🤫দি !!",
        "{Name} খা🤫ন🤫কির ছেলে বট, নুব🤫রা প্লেয়ার !!",
        "বাংলাদেশের NO-1 বট PLAYER {Name}",
        "{Name} জুতা চোর !!",
        "{Name} মাদারচো🤫দ, ফ্রি ফায়ার খেলা বাদ দিয়ে লুডু খেল যা !!",
        "{Name} যাই করিস, আমি তোর অব্বা এইডা কখনো ভুলিস না !!"
    ]

    # Background emote loop (every 1 second)
    async def emote_loop():
        while not stop_emote.is_set():
            try:
                pkt = await Emote_k(int(uid), 909000002, key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', pkt)
            except Exception as e:
                print(f"Gali emote error: {e}")
            await asyncio.sleep(1)

    stop_emote = asyncio.Event()
    emote_task = asyncio.create_task(emote_loop())

    try:
        for msg in messages:
            colored = f"[B][C][FFFFFF][B][C][32CD32][FFFFFF][FFA500][FFFFFF][FF00FF][FFD700][FFFFFF][00FFFF][FF1493][00FF00][FFFFFF] {msg.replace('{Name}', name.upper())}"
            await safe_send_message(chat_type, colored, uid, chat_id, key, iv)
            await asyncio.sleep(2)   # original delay between messages
    finally:
        stop_emote.set()
        emote_task.cancel()
        try:
            await emote_task
        except asyncio.CancelledError:
            pass


async def send_gali_with_emotes(name: str, uid: int, chat_id: int, chat_type: int, key: bytes, iv: bytes, region: str):
    """Send gali messages + emote 909000002 every 1 second"""
    messages = [
        "{Name} খান🤫কির ছেলে !!",
        "{Name} মাদার চো🤫দ, তোর মা🤫কে চু🤫দি !!",
        "{Name} মাদার চো🤫দ, তোর মা🤫কে 5G স্পিডে চু🤫দি !!",
        "{Name} বোকাচো🤫দা, তোর মা🤫কে কন🤫ডম লাগিয়ে চু🤫দি !!",
        "{Name} বোকাচো🤫দা, তোর মা🤫কে প্রতিদিন ১০,০০০ টাকার সার্ভিস দেই !!",
        "F🤫U🤫C🤫K {Name} !!",
        "{Name} মাদার চো🤫দ, পো🤫দ মে🤫রে দিবো !!",
        "{Name} মাদার চো🤫দ !!",
        "{Name} খান🤫কি, আমি তোর বা🤫প !!",
        "{Name} তোর মা🤫কে আমি চু🤫ই🤫দা তোরে জন্মায় ছি !!",
        "{Name} বোকাচো🤫দা, খান🤫কির ছেলে !!",
        "{Name} মাদার চো🤫দ, তোর মা🤫কে ১৮০ কি.মি. স্পিডে চু🤫দি !!",
        "{Name} খা🤫ন🤫কির ছেলে বট, নুব🤫রা প্লেয়ার !!",
        "বাংলাদেশের NO-1 বট PLAYER {Name}",
        "{Name} জুতা চোর !!",
        "{Name} মাদারচো🤫দ, ফ্রি ফায়ার খেলা বাদ দিয়ে লুডু খেল যা !!",
        "{Name} যাই করিস, আমি তোর অব্বা এইডা কখনো ভুলিস না !!"
    ]

    # Background emote loop (every 1 second)
    async def emote_loop():
        while not stop_emote.is_set():
            try:
                pkt = await Emote_k(int(uid), 909000002, key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', pkt)
            except Exception as e:
                print(f"Gali emote error: {e}")
            await asyncio.sleep(1)

    stop_emote = asyncio.Event()
    emote_task = asyncio.create_task(emote_loop())

    try:
        for msg in messages:
            colored = f"[B][C][FFFFFF][B][C][32CD32][FFFFFF][FFA500][FFFFFF][FF00FF][FFD700][FFFFFF][00FFFF][FF1493][00FF00][FFFFFF] {msg.replace('{Name}', name.upper())}"
            await safe_send_message(chat_type, colored, uid, chat_id, key, iv)
            await asyncio.sleep(2)   # original delay between messages
    finally:
        stop_emote.set()
        emote_task.cancel()
        try:
            await emote_task
        except asyncio.CancelledError:
            pass


async def handle_gop_command(inPuTMsG: str, uid: int, chat_id: int, chat_type: int, key: bytes, iv: bytes, region: str):
    """Call this from TcPChaT when /gop is detected. Handles everything: validation + gali + emote"""
    if not inPuTMsG.strip().startswith('/gop '):
        return

    parts = inPuTMsG.strip().split(maxsplit=1)
    if len(parts) < 2:
        error_msg = "[B][C][FF0000]❌ ERROR! Usage: /gop <name>\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return

    name = parts[1].strip()

    # Prevent targeting yourself (same as before)
    try:
        BLOCKED_NAMES  # ensure the list exists (import or global)
    except NameError:
        BLOCKED_NAMES = []  # fallback if not defined

    if name.lower() in [n.lower() for n in BLOCKED_NAMES]:
        error_msg = (
            "[B][C][FF0000]⚠️শা🤣লা মাদা🤐রচো🥴দ\n[FFFFFF]তর এই বা🤣পে🤣র নামে গা🥴লি দিতে চাস\n[FF0000]শা🤣লা মাদা🤣রচো😁দ"
        )
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return

    # Fire and forget – starts gali messages + emote spam
    asyncio.create_task(send_gali_with_emotes(name, uid, chat_id, chat_type, key, iv, region))
async def handle_commands(cmd_text, sender_uid, chat_id, chat_type, key, iv, region):
    global auto_start_running, stop_auto

    # আপনার বর্তমান /lw কমান্ডের পর এটি যুক্ত করুন
    if cmd_text.startswith('/start1'):
        print('Processing /start1 command in any chat type')
        if auto_start_running:
            stop_msg = "[B][C][FF0000]⚠️ ইতিমধ্যে একটি স্প্যাম চলছে!"
            await safe_send_message(chat_type, stop_msg, sender_uid, chat_id, key, iv)
        else:
            # আলাদা টাস্কে রান করানো যাতে বট হ্যাং না হয়
            asyncio.create_task(start_match_spam_loop(sender_uid, chat_id, chat_type, key, iv, region))

    elif cmd_text.startswith('/stop1'):
        stop_auto = True
        stop_msg = "[B][C][FF0000]🛑 স্টার্ট স্প্যাম বন্ধ করা হয়েছে।"
        await safe_send_message(chat_type, stop_msg, sender_uid, chat_id, key, iv)
GENDER_RESPONSES = ["G A Y", "T R A N S G E N D E R", "L E S B I A N", "B I S E X U A L", "S T R A I G H T", "A S E X U A L", "P A N S E X U A L", "N O N - B I N A R Y", "Q U E E R", "T R A P", "S I S S Y", "F E M B O Y", "T O M B O Y", "A T T A C K  H E L I C O P T E R", "G A Y"]
async def auto_start_loop(team_code, uid, chat_id, chat_type, key, iv, region):
    """Auto start loop that joins, starts match, waits, leaves, repeats"""
    global auto_start_running, stop_auto
    
    print(f"[AUTO] Auto start loop started for team {team_code}")
    
    while not stop_auto:
        try:
            # Send status message
            status_msg = f"[B][C][FFA500]🤖 Auto Start Bot\n🎯 Team: {team_code}\n⚡ Joining team..."
            await safe_send_message(chat_type, status_msg, uid, chat_id, key, iv)
            
            # Join team
            join_packet = await join_teamcode_packet(team_code, key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
            await asyncio.sleep(2)
            
            # Send start spam status
            start_msg = f"[B][C][00FF00]✅ Joined team {team_code}\n🎯 Starting match for {start_spam_duration} seconds..."
            await safe_send_message(chat_type, start_msg, uid, chat_id, key, iv)
            
            # Start spam
            start_packet = await start_auto_packet(key, iv, region)
            end_time = time.time() + start_spam_duration
            spam_count = 0
            
            while time.time() < end_time and not stop_auto:
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', start_packet)
                spam_count += 1
                await asyncio.sleep(start_spam_delay)
            
            if stop_auto:
                break
            
            # Wait after match
            wait_msg = f"[B][C][FFFF00]⏳ Match started! Bot in lobby waiting {wait_after_match} seconds..."
            await safe_send_message(chat_type, wait_msg, uid, chat_id, key, iv)
            
            waited = 0
            while waited < wait_after_match and not stop_auto:
                await asyncio.sleep(1)
                waited += 1
            
            if stop_auto:
                break
            
            # Leave squad
            leave_msg = f"[B][C][FF0000]🔄 Leaving team {team_code} to rejoin and start again..."
            await safe_send_message(chat_type, leave_msg, uid, chat_id, key, iv)
            
            leave_packet = await leave_squad_packet(key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"[AUTO] Error in auto_start_loop: {e}")
            error_msg = f"[B][C][FF0000]❌ Auto start error: {str(e)}\n"
            await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
            break
    
    auto_start_running = False
    stop_auto = False
    print(f"[AUTO] Auto start loop stopped for team {team_code}")
async def tagx_spam_loop(bot_uid: int, key: bytes, iv: bytes, region: str, chat_type: int, sender_uid: int, chat_id: int):
    """Ultra-fast spam: random emote hijack + keep-alive every 0.3 seconds"""
    global tagx_running

    # Random emote IDs (te ajker best list ta use korte paro)
    emote_pool = [
        909000001, 909000002, 909000003, 909000004, 909000005,
        909000006, 909000007, 909000008, 909000009, 909000010,
        909035003, 909040008, 909050009, 909051015, 909000063
    ]

    print(f"⚡ /tagx started by {sender_uid} – hijack + keep-alive combo")

    while tagx_running:
        try:
            # 1. Keep-Alive packet (rapid burst)
            ka = await send_keep_alive(key, iv, region)
            if ka:
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', ka)

            # 2. Random emote hijack (bot performs emote on itself – makes it look like bot is doing it)
            emote_id = random.choice(emote_pool)
            emote_pkt = await Emote_k(int(bot_uid), emote_id, key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_pkt)

            # optional: log progress
            print(f"   ↪ Keep-Alive OK | Emote {emote_id}")

        except Exception as e:
            print(f"❌ tagx loop error: {e}")

        # 0.3 sec burst interval
        await asyncio.sleep(0.3)

    print("🛑 /tagx stopped")


async def handle_tagx_command(inPuTMsG: str, uid: int, chat_id: int, chat_type: int, key: bytes, iv: bytes, region: str):
    """Handle /tagx command: start/restart the combo spam"""
    global tagx_running, tagx_task

    if not inPuTMsG.strip().startswith('/tagx'):
        return

    # Stop previous instance if running
    if tagx_task and not tagx_task.done():
        tagx_running = False
        tagx_task.cancel()
        await asyncio.sleep(0.5)   # wait for cleanup


    BOT_UID_FOR_TAGX = 13964699117   # Apnar bot er UID

    # Confirmation message
    await safe_send_message(chat_type, "[B][C][FFFF00]⚡ /tagx ACTIVATED!\n[FFFFFF]Hijack + Keep-Alive every 0.3 sec", uid, chat_id, key, iv)

    # Start the loop in background
    tagx_running = True
    tagx_task = asyncio.create_task(
        tagx_spam_loop(BOT_UID_FOR_TAGX, key, iv, region, chat_type, uid, chat_id)
    )
async def xSEndMsgsQ(Msg, id, K, V, region="BD"):
    """
    Send message with region 1 title included
    Msg: Message text
    id: Sender/recipient ID
    K: Key for encryption
    V: IV for encryption
    region: Region code (default BD)
    """
    # Get random avatar
    avatar = await xBunnEr()
    
    fields = {
        1: id,
        2: id,
        4: Msg,
        5: 1756580149,
        8: 904990072,
        9: {
            1: "[FFFFFF]BLACK",
            2: avatar,
            3: 2,
            4: 329,
            5: 1001000001,
            6: 66,
            7: 66,
            8: "xBe4!sTo - C4",
            9: 66,
            10: 66,
            11: 66,
            12: 66,
            13: {1: 68, 2: 67},
            14: {
                1: 1158053040,
                2: 8,
                3: b"\x10\x15\x08\x0A\x0B\x15\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
            }
        },
        10: "en",
        13: {66: 66, 66: 66},
        # ADD REGION 1 TITLE HERE (from second packet field 14)
        14: {
            11: {
                1: 3,          # Field 1
                2: 7,          # Field 2
                3: 170,        # Field 3
                4: 999,        # Field 4
                5: 1,          # Field 5
                6: region,
                8: 2,
                9: 2
            }
        }
    }
    
    Pk = (await CrEaTe_ProTo(fields)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return await GeneRaTePk(Pk, '1201', K, V)

async def start_match_spam(key, iv, duration=17, delay=0.2):
    """Spam start match packet for specified duration (seconds)"""
    start_packet = await FS(key, iv)
    end_time = time.time() + duration
    count = 0
    while time.time() < end_time:
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', start_packet)
        count += 1
        await asyncio.sleep(delay)
    return count
async def FS(key, iv, region="ind"):
    """
    Start match packet - converted from TCP version
    key: Encryption key
    iv: Encryption IV
    region: Region code (default ind)
    """
    try:
        # Your original fields from TCP bot
        fields = {
            1: 9,  # Start match packet type
            2: {
                1: 12480598706,  # Your UID or specific value
            }
        }
        
        # Create protobuf packet
        packet = await CrEaTe_ProTo(fields)
        packet_hex = packet.hex()
        
        # Encrypt the packet
        encrypted_packet = await encrypt_packet(packet_hex, key, iv)
        
        # Calculate header length
        header_length = len(encrypted_packet) // 2
        header_length_final = dec_to_hex(header_length)
        
        # Determine packet type based on region
        if region.lower() == "ind":
            packet_type = '0514'
        elif region.lower() == "bd":
            packet_type = "0519"
        else:
            packet_type = "0515"
        
        # Build final packet based on header length
        if len(header_length_final) == 2:
            final_packet_hex = packet_type + "000000" + header_length_final + encrypted_packet
        elif len(header_length_final) == 3:
            final_packet_hex = packet_type + "00000" + header_length_final + encrypted_packet
        elif len(header_length_final) == 4:
            final_packet_hex = packet_type + "0000" + header_length_final + encrypted_packet
        elif len(header_length_final) == 5:
            final_packet_hex = packet_type + "000" + header_length_final + encrypted_packet
        elif len(header_length_final) == 6:
            final_packet_hex = packet_type + "00" + header_length_final + encrypted_packet
        else:
            final_packet_hex = packet_type + "000000" + header_length_final + encrypted_packet
        
        print(f"✅ Start match packet created: {len(final_packet_hex)//2} bytes")
        return bytes.fromhex(final_packet_hex)
        
    except Exception as e:
        print(f"❌ Error creating start packet: {e}")
        import traceback
        traceback.print_exc()
        return None

#NEW LAG
tagx_running = False
tagx_task = None
# SPAMS
auto_start_running = False
stop_auto = False
start_spam_duration = 17
start_spam_delay = 0.2
# =================== CONFIGURATION ======================
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  

# =================== GLOBAL VARIABLES ===================
online_writer = None
whisper_writer = None
spammer_uid = None
msg_spam_running = False
msg_spam_task = None
mg_spam_task = None
spam_chat_id = None
spam_uid = None
Spy = False
Chat_Leave = False
fast_spam_running = False
fast_spam_task = None
custom_spam_running = False
custom_spam_task = None
spam_request_running = False
spam_request_task = None
evo_fast_spam_running = False
evo_fast_spam_task = None
evo_custom_spam_running = False
evo_custom_spam_task = None
reject_spam_running = False
reject_spam_task = None
emote_hijack = False
BLOCK_EMOTE = False   # True = player এর ইমোজি ব্লক করতে fixed emote পাঠাবেBLOCK_EMOTE = False   # True = player এর ইমোজি ব্লক করতে fixed emote পাঠাবে
BLOCK_EMOTE_UID = 11111111
lag_running = False
lag_task = None
reject_spam_running = False
reject_spam_task = None
evo_cycle_running = False
evo_cycle_task = None
status_response_cache = {} 
pending_status_requests = {}
room_info_cache = {}
last_status_packet = None
insquad = None 
joining_team = False 
online_writer = None 
whisper_writer = None 
last_bot_status_check = 0
senthi = False
bot_status_cache_time = 30
cached_bot_status = None
last_status_packet = None
start_spam_duration = 18
wait_after_match = 20
# =================== RIZER BOT CONSTANTS ===================
RIZER = "RIZER_BOT_2024"

# =================== AI MODE CONTROL ===================
ai_mode_enabled = False  # AI mode starts disabled by default
ai_api_url = ""  # Default AI API URL
ai_api_key = ""  # Set your AI API key here



# =================== AI AUTO-REPLY SYSTEM ===================
ai_auto_reply_enabled = False
ai_last_reply_time = 0
ai_reply_cooldown = 2
ai_conversation_context = {}

magic_loop_running = False
magic_loop_task = None
magic_current_bundle_index = 0
magic_team_code = None
# Global bot UID (will be set in MaiiiinE)
TarGeT = None

# =================== LAGC SYSTEM ===================
lagc_running = False
lagc_task = None
lagc_team_code = None
LAGC_DURATION = 120  # 2 minutes auto-stop
# FUCK YOU BRADAR ( RIZER x64 defin i fuck u bruh )
auto_start_teamcode = None
auto_start_task = None
async def magic_loop_function(team_code, key, iv, region, chat_type, sender_uid, chat_id):
    global magic_loop_running
    bundle_list = list(BUNDLE.items())
    while magic_loop_running:
        try:
            join_packet = await GenJoinSquadsPacket(team_code, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
            await asyncio.sleep(0.1)
            for bundle_name, bundle_id in bundle_list:
                if not magic_loop_running: break
                try:
                    bundle_pkt = await bundle_packet_async(bundle_id, key, iv, region)
                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', bundle_pkt)
                    await asyncio.sleep(0.2)
                except: continue
            for i in range(5):
                if not magic_loop_running: break
                await asyncio.sleep(1)
            if magic_loop_running:
                leave_packet = await ExiT(None, key, iv)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)
                await asyncio.sleep(0.5)
        except Exception as e: print(f"❌ Magic error: {e}"); await asyncio.sleep(1)

async def handle_magic_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    global magic_loop_running, magic_loop_task, magic_team_code
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        await safe_send_message(chat_type, "[B][C][FF0000]❌ Usage: /magic (team_code)", uid, chat_id, key, iv)
        return
    team_code = parts[1]
    magic_team_code = team_code
    if magic_loop_task and not magic_loop_task.done():
        magic_loop_running = False
        magic_loop_task.cancel()
        await asyncio.sleep(0.5)
    start_msg = f"[B][C][FFFF00]🎩 MAGIC STARTED!\n🏷️ Team: {team_code}\n📦 Bundles: {len(BUNDLE)}\n💡 /offmagic to stop"
    await safe_send_message(chat_type, start_msg, uid, chat_id, key, iv)
    magic_loop_running = True
    magic_loop_task = asyncio.create_task(magic_loop_function(team_code, key, iv, region, chat_type, uid, chat_id))

async def handle_offmagic_command(uid, chat_id, key, iv, chat_type):
    global magic_loop_running, magic_loop_task
    if magic_loop_task and not magic_loop_task.done():
        magic_loop_running = False
        magic_loop_task.cancel()
        await safe_send_message(chat_type, "[B][C][FFFF00]🎩 MAGIC STOPPED!", uid, chat_id, key, iv)
    else:
        await safe_send_message(chat_type, "[B][C][FF0000]❌ No active magic!", uid, chat_id, key, iv)

# =================== LAGC FUNCTIONS ===================
async def lagc_loop_function(team_code, key, iv, region, chat_type, sender_uid, chat_id):
    """Ultra fast join-exit loop - runs for 2 minutes max"""
    global lagc_running
    start_time = time.time()
    while lagc_running:
        try:
            # Check if 2 minutes elapsed
            if time.time() - start_time >= LAGC_DURATION:
                lagc_running = False
                await safe_send_message(chat_type, "[B][C][FFFF00]⏱️ LAGC auto-stopped (2 min)", sender_uid, chat_id, key, iv)
                break

            # Join team
            join_packet = await GenJoinSquadsPacket(team_code, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)

            # Small delay
            await asyncio.sleep(0.05)

            # Exit team
            leave_packet = await ExiT(None, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)

            # Wait 0.1 seconds before next cycle
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"❌ LAGC error: {e}")
            await asyncio.sleep(0.5)

async def handle_lagc_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /lagc teamcode command"""
    global lagc_running, lagc_task, lagc_team_code
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        await safe_send_message(chat_type, "[B][C][FF0000]❌ Usage: /lagc (team_code)", uid, chat_id, key, iv)
        return

    team_code = parts[1]
    lagc_team_code = team_code

    # Stop any existing lagc
    if lagc_task and not lagc_task.done():
        lagc_running = False
        lagc_task.cancel()
        await asyncio.sleep(0.3)

    start_msg = f"[B][C][FF0000]⚡ LAGC STARTED!\n🏷️ Team: {team_code}\n⏱️ Auto-stop: 2 min\n💡 /stop_lagc to stop"
    await safe_send_message(chat_type, start_msg, uid, chat_id, key, iv)

    lagc_running = True
    lagc_task = asyncio.create_task(lagc_loop_function(team_code, key, iv, region, chat_type, uid, chat_id))

async def handle_stop_lagc_command(uid, chat_id, key, iv, chat_type):
    """Handle /stop_lagc command"""
    global lagc_running, lagc_task
    if lagc_task and not lagc_task.done():
        lagc_running = False
        lagc_task.cancel()
        await safe_send_message(chat_type, "[B][C][FF0000]⚡ LAGC STOPPED!", uid, chat_id, key, iv)
    else:
        await safe_send_message(chat_type, "[B][C][FF0000]❌ No active lagc!", uid, chat_id, key, iv)

START_SPAM_DURATION = 18     
WAIT_AFTER_MATCH_SECONDS = 20 
START_SPAM_DELAY = 0.2       
region = 'IN'
WHITELISTED_UIDS = {
    "2579372995"  
}
WHITELIST_ONLY = False  # Changed to False to remove restriction
BOT_OWNER_UID = 2579372095  
PLAYER_NAME_CACHE = {}  
freeze_running = False
freeze_task = None
FREEZE_EMOTES = [909052010, 909052010, 909052010]
FREEZE_DURATION = 60  # seconds

# manager and status_response_cache initialization moved under if __name__ == '__main__': to avoid RuntimeError

evo_emotes = {
    "1": "909000063",   # AK
    "2": "909000068",   # SCAR
    "3": "909000075",   # 1st MP40
    "4": "909040010",   # 2nd MP40
    "5": "909000081",   # 1st M1014
    "6": "909039011",   # 2nd M1014
    "7": "909000085",   # XM8
    "8": "909000090",   # Famas
    "9": "909000098",   # UMP
    "10": "909035007",  # M1887
    "11": "909042008",  # Woodpecker
    "12": "909041005",  # Groza
    "13": "909033001",  # M4A1
    "14": "909038010",  # Thompson
    "15": "909038012",  # G18
    "16": "909045001",  # Parafal
    "17": "909049010",  # P90
    "18": "909051003"   # m60
}
#------------------------------------------#

# Emote mapping for evo commands
EMOTE_MAP = {
    1: 909000063,
    2: 909000081,
    3: 909000075,
    4: 909000085,
    5: 909000134,
    6: 909000098,
    7: 909035007,
    8: 909051012,
    9: 909000141,
    10: 909034008,
    11: 909051015,
    12: 909041002,
    13: 909039004,
    14: 909042008,
    15: 909051014,
    16: 909039012,
    17: 909040010,
    18: 909035010,
    19: 909041005,
    20: 909051003,
    21: 909034001
}
# RARE LOOK CHANGER BUNDLE ID
# RARE LOOK CHANGER BUNDLE ID
BUNDLE = {
    # Name based
    "rampage": 914000002,
    "cannibal": 914000003,
    "devil": 914038001,
    "scorpio": 914039001,
    "frostfire": 914042001,
    "paradox": 914044001,
    "naruto": 914047001,
    "aurora": 914047002,
    "midnight": 914048001,
    "itachi": 914050001,
    "dreamspace": 914051001,
    "OB54ABHI": 914053001,

    # Number based (same order)
    "1": 914000002,
    "2": 914000003,
    "3": 914038001,
    "4": 914039001,
    "5": 914042001,
    "6": 914044001,
    "7": 914047001,
    "8": 914047002,
    "9": 914048001,
    "10": 914050001,
    "11": 914051001,
    "12": 914053001
}
delay_map = {
                            '1': 5.1,       # rampage
                            '2': 3.0,       # cannibal
                            '3': 3.0,       # devil
                            '4': 5.0,       # scorpio
                            '5': 3.3,       # frostfire
                            '6': 3.5,       # paradox
                            '7': 2.6,       # naruto
                            '8': 3.7,       # aurora
                            '9': 4.4,       # midnight
                            '10': 3.0,      # itachi
                            '11': 4.2,      # dreamspace
                            '12': 4.8,       # OB54ABHI
                            'rampage': 5.1,
                            'cannibal': 3.0,
                            'devil': 3.0,
                            'scorpio': 5.0,
                            'frostfire': 3.3,
                            'paradox': 3.5,
                            'naruto': 2.6,
                            'aurora': 3.7,
                            'midnight': 4.4,
                            'itachi': 3.0,
                            'dreamspace': 4.2, 
                            'OB54ABHI': 4.8
                        }
# Badge values for s1 to s8 commands - using your exact values
BADGE_VALUES = {
    "s1": 1048576,    # Your first badge
    "s2": 32768,      # Your second badge  
    "s3": 2048,       # Your third badge
    "s4": 64,         # Your fourth badge
    "s5": 262144     # Your seventh badge
}

def titles():
    """Return all titles instead of just one random"""
    titles_list = [
        905090075, 904990072, 904990069, 905190079
    ]
    return titles_list  # Return the full list instead of random.choice            
    
def create_credentials_template():
    """Create a template credentials file"""
    template = """# APPLE GAMING FF Free Fire Bot Credentials
# Fill in your Free Fire account credentials below

# Format 1: Comma-separated (RECOMMENDED)
uid=4263143059,password=2336099414_W0363_BY_SPIDEERIO_GAMING_WBYMF

# OR Format 2: Line-separated
# uid: 4263143059
# password: 2336099414_W0363_BY_SPIDEERIO_GAMING_WBYMF

# Save this file and restart the bot
"""
    
    filename = "bot.txt"
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"📝 Created {filename} template file")
        print("✏️ Please edit it with your actual credentials")
        return False
    return True
    
da = 'f2212101'
dec = ['80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '8a', '8b', '8c', '8d', '8e', '8f', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99', '9a', '9b', '9c', '9d', '9e', '9f', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'aa', 'ab', 'ac', 'ad', 'ae', 'af', 'b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9', 'ba', 'bb', 'bc', 'bd', 'be', 'bf', 'c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9', 'ca', 'cb', 'cc', 'cd', 'ce', 'cf', 'd0', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9', 'da', 'db', 'dc', 'dd', 'de', 'df', 'e0', 'e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8', 'e9', 'ea', 'eb', 'ec', 'ed', 'ee', 'ef', 'f0', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'fa', 'fb', 'fc', 'fd', 'fe', 'ff']
x_list = ['1','01', '02', '03', '04', '05', '06', '07', '08', '09', '0a', '0b', '0c', '0d', '0e', '0f', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '1a', '1b', '1c', '1d', '1e', '1f', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '2a', '2b', '2c', '2d', '2e', '2f', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '3a', '3b', '3c', '3d', '3e', '3f', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '4a', '4b', '4c', '4d', '4e', '4f', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '5a', '5b', '5c', '5d', '5e', '5f', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '6a', '6b', '6c', '6d', '6e', '6f', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '7a', '7b', '7c', '7d', '7e', '7f']

def Decrypt_ID(da):
    """EXACT SAME as your code"""
    if da != None and len(da) == 10:
        w = 128
        xxx = len(da)/2 - 1
        xxx = str(xxx)[:1]
        for i in range(int(xxx)-1):
            w = w * 128
        x1 = da[:2]
        x2 = da[2:4]
        x3 = da[4:6]
        x4 = da[6:8]
        x5 = da[8:10]
        return str(w * x_list.index(x5) + (dec.index(x2) * 128) + dec.index(x1) + (dec.index(x3) * 128 * 128) + (dec.index(x4) * 128 * 128 * 128))

    if da != None and len(da) == 8:
        w = 128
        xxx = len(da)/2 - 1
        xxx = str(xxx)[:1]
        for i in range(int(xxx)-1):
            w = w * 128
        x1 = da[:2]
        x2 = da[2:4]
        x3 = da[4:6]
        x4 = da[6:8]
        return str(w * x_list.index(x4) + (dec.index(x2) * 128) + dec.index(x1) + (dec.index(x3) * 128 * 128))
    
    return None

def Encrypt_ID(x):
    """EXACT SAME as your code"""
    x = int(x)
    x = x / 128 
    if x > 128:
        x = x / 128
        if x > 128:
            x = x / 128
            if x > 128:
                x = x / 128
                strx = int(x)
                y = (x - int(strx)) * 128
                stry = str(int(y))
                z = (y - int(stry)) * 128
                strz = str(int(z))
                n = (z - int(strz)) * 128
                strn = str(int(n))
                m = (n - int(strn)) * 128
                return dec[int(m)] + dec[int(n)] + dec[int(z)] + dec[int(y)] + x_list[int(x)]
            else:
                strx = int(x)
                y = (x - int(strx)) * 128
                stry = str(int(y))
                z = (y - int(stry)) * 128
                strz = str(int(z))
                n = (z - int(strz)) * 128
                strn = str(int(n))
                return dec[int(n)] + dec[int(z)] + dec[int(y)] + x_list[int(x)]

def decrypt_api(cipher_text):
    """EXACT SAME as your code"""
    key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plain_text = unpad(cipher.decrypt(bytes.fromhex(cipher_text)), AES.block_size)
    return plain_text.hex()

def encrypt_api(plain_text):
    """EXACT SAME as your code"""
    plain_text = bytes.fromhex(plain_text)
    key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
    return cipher_text.hex()

def encrypt_message(plaintext_bytes):
    """EXACT SAME as your Flask API"""
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(plaintext_bytes, AES.block_size)
    encrypted = cipher.encrypt(padded)
    return binascii.hexlify(encrypted).decode('utf-8')    

def create_uid_protobuf(uid):
    """EXACT SAME as your Flask API"""
    msg = dev_generator_pb2.dev_generator()
    msg.saturn_ = int(uid)
    msg.garena = 1
    return msg.SerializeToString()

def enc(uid):
    """EXACT SAME as your Flask API"""
    pb = create_uid_protobuf(uid)
    return encrypt_message(pb)

def decode_player_info(binary):
    """EXACT SAME as your Flask API"""
    info = devxt_count_pb2.xt()
    info.ParseFromString(binary)
    return info    
    
import requests
import json

def load_jwt_token():
    """Load token from token.json"""
    try:
        with open("token.json", "r") as f:
            data = json.load(f)
        token = data.get("token")
        if token:
            print(f"✅ Loaded token: {token[:20]}...")
            return token
        else:
            print("❌ No token found in token.json")
            return None
    except Exception as e:
        print(f"❌ Error loading token: {e}")
        return None

def load_tokens_ind():
    """Load bulk tokens from token_ind.json"""
    try:
        with open("token_ind.json", "r") as f:
            tokens = json.load(f)
        print(f"📦 Loaded {len(tokens)} tokens from token_ind.json")
        return tokens
    except:
        print("❌ No tokens found in token_ind.json")
        return None

def get_player_info(uid):
    try:
        url = f"http://localhost:5003/get?uid={uid}"
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            return None, f"API Error: {res.status_code}"

        data = res.json()

        # basic validation
        if "AccountInfo" not in data:
            return None, "Invalid API response"

        return data

    except requests.exceptions.Timeout:
        return None, "Request timeout"

    except Exception as e:
        return None, str(e)

async def send_full_player_info(data, chat_type, uid, chat_id, key, iv):
    """Send full player info in formatted messages"""
    
    if isinstance(data, tuple) and len(data) == 2:
        data = data[0]  # If tuple, take first element
    
    acc = data.get("AccountInfo", {})
    guild = data.get("GuildInfo", {})
    social = data.get("socialinfo", {})  # ← এই variable টি use করুন
    captain = data.get("captainBasicInfo", {})

    # ────────── MESSAGE 1 : COMMON ACCOUNT INFO ──────────
    msg1 = f"""
[C][B][FF1493]═════════════
[C][B][00FFFF]  COMMON ACCOUNT INFO
[C][FF1493]═════════════

[C][FFD700]Name        : [00FF00]{acc.get('AccountName', 'N/A')}
[C][FFD700]UID         : [00FFAA]{xMsGFixinG(social.get('accountId', uid))} 
[C][FFD700]Level       : [FF00FF]{acc.get('AccountLevel', 'N/A')}
[C][FFD700]EXP         : [00FFFF]{xMsGFixinG(acc.get('AccountEXP', '0'))}
[C][FFD700]Likes       : [FF4444]{xMsGFixinG(acc.get('AccountLikes', '0'))}
[C][FFD700]Region      : [FFFFFF]{acc.get('AccountRegion', 'N/A')}
[C][FFD700]BP Badge    : [FFA500]{xMsGFixinG(acc.get('AccountBPBadges', '0'))}
[C][FFD700]Version     : [AAAAFF]{acc.get('ReleaseVersion', 'N/A')}

[C][FF1493]═════════════
"""
    await safe_send_message(chat_type, msg1, uid, chat_id, key, iv)
    await asyncio.sleep(0.5)

    # ────────── MESSAGE 2 : DATE + RANK INFO ──────────
    lang = social.get("language", "N/A")
    if "_" in lang:
        lang = lang.split("_")[-1]

    msg2 = f"""
[C][B][00AAFF]═════════════
[C][B][FFFFFF]  ACCOUNT DETAILS
[C][00AAFF]═════════════

[C][FFAA00]Create Date   : [00FF00]{xMsGFixinG(human_time(acc.get('AccountCreateTime', '0'))[:16])}
[C][FFAA00]Last Login    : [00FF00]{xMsGFixinG(human_time(acc.get('AccountLastLogin', '0'))[:16])}
[C][FF00FF]BR Max Rank   : [FFD700]{xMsGFixinG(acc.get('BrMaxRank', 'N/A'))}
[C][FF00FF]BR Points     : [FFD700]{xMsGFixinG(acc.get('BrRankPoint', 'N/A'))}
[C][00FFFF]CS Max Rank   : [AA00FF]{xMsGFixinG(acc.get('CsMaxRank', 'N/A'))}
[C][00FFFF]CS Points     : [AA00FF]{xMsGFixinG(acc.get('CsRankPoint', 'N/A'))}
[C][FFFFFF]Language      : [66FF00]{lang}

[C][00AAFF]═════════════
"""
    await safe_send_message(chat_type, msg2, uid, chat_id, key, iv)
    await asyncio.sleep(0.5)

    # ────────── MESSAGE 3 : FULL GUILD INFO ──────────
    msg3 = f"""
[C][B][FF8800]═════════════
[C][B][FFFFFF]  GUILD INFORMATION
[C][FF8800]═════════════

[C][00FFFF]Guild Name    : [00FF00]{guild.get('GuildName', 'No Guild')}
[C][00FFFF]Guild ID      : [FF00FF]{xMsGFixinG(guild.get('GuildID', '0'))}
[C][00FFFF]Owner UID     : [FFD700]{xMsGFixinG(guild.get('GuildOwner', '0'))}
[C][00FFFF]Guild Level   : [FF4444]{guild.get('GuildLevel', 'N/A')}
[C][00FFFF]Members       : [66FFAA]{guild.get('GuildMember', '0')}/{guild.get('GuildCapacity', '0')}

[C][FF8800]═════════════
"""
    await safe_send_message(chat_type, msg3, uid, chat_id, key, iv)


def get_detailed_player_info(uid, token):
    """Get detailed player info as formatted string"""
    try:
        url = "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"
        encrypted_uid = enc(uid)
        edata = bytes.fromhex(encrypted_uid)
        headers = {
            'User-Agent': "Dalvik/2.1.0",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Authorization': f"Bearer {token}",
            'Content-Type': "application/x-www-form-urlencoded",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': "OB54"
        }
        response = requests.post(url, data=edata, headers=headers, verify=False, timeout=10)
        if response.status_code != 200:
            return f"❌ Failed to get info for UID {uid} (HTTP {response.status_code})"
        info = decode_player_info(response.content)
        data = json.loads(json_format.MessageToJson(info))
        account = data.get("AccountInfo", {})
        # Extract fields
        name = account.get("PlayerNickname", "Unknown")
        level = account.get("Level", "N/A")
        exp = account.get("Exp", "N/A")
        rank = account.get("Rank", "N/A")
        avatar = account.get("Avatar", "N/A")
        title = account.get("Title", "N/A")
        clan = account.get("ClanName", "None")
        # Format nicely
        result = f"""
[B][C][FFFF00]📊 PLAYER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[FFFFFF]👤 Name     : [FFFF00]{name}
[FFFFFF]🆔 UID      : [FFFF00]{uid}
[FFFFFF]📈 Level    : [FFFF00]{level}
[FFFFFF]⭐ Rank     : [FFFF00]{rank}
[FFFFFF]🎭 Avatar   : [FFFF00]{avatar}
[FFFFFF]🏷️ Title    : [FFFF00]{title}
[FFFFFF]🏰 Clan     : [FFFF00]{clan}
[FFFFFF]✨ Exp      : [FFFF00]{exp}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return result
    except Exception as e:
        return f"❌ Error getting player info: {str(e)}"

def send_friend_request_single(uid, token, region="IND"):
    """EXACT SAME as your Flask function but single"""
    try:
        encrypted_id = Encrypt_ID(uid)
        payload = f"08a7c4839f1e10{encrypted_id}1801"
        encrypted_payload = encrypt_api(payload)
        
        # Determine URL based on region
        if region.lower() == "ind":
            url = "https://client.ind.freefiremobile.com/RequestAddingFriend"
        elif region.lower() == "bd":
            url = "https://clientbp.ggpolarbear.com/RequestAddingFriend"
        else:
            url = "https://client.ind.freefiremobile.com/RequestAddingFriend"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB54",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0"
        }
        
        print(f"📤 Sending friend request to {uid}...")
        response = requests.post(url, data=bytes.fromhex(encrypted_payload), headers=headers, timeout=10, verify=False)
        
        if response.status_code == 200:
            print(f"✅ Success: Friend request sent to {uid}")
            return True
        else:
            print(f"❌ Failed: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False    
    
def start_autooo(self):    
    try:
        fields = {
            1: 9,
            2: {
                1: 12480598706,
            },
        }
        packet = create_protobuf_packet(fields).hex()
        header_length = len(encrypt_packet(packet, self.key, self.iv)) // 2
        header_length_final = dec_to_hex(header_length)
        if len(header_length_final) == 2:
            final_packet = "0515000000" + header_length_final + self.nmnmmmmn(packet)
        elif len(header_length_final) == 3:
            final_packet = "051500000" + header_length_final + self.nmnmmmmn(packet)
        elif len(header_length_final) == 4:
            final_packet = "05150000" + header_length_final + self.nmnmmmmn(packet)
        elif len(header_length_final) == 5:
            final_packet = "0515000" + header_length_final + self.nmnmmmmn(packet)
        return bytes.fromhex(final_packet)
    except exception as e:
        print(e)

def load_credentials_from_file(filename="bot.txt"):
    """
    Load UID and password from bot.txt file
    """
    try:
        if not os.path.exists(filename):
            print(f"❌ {filename} not found!")
            create_credentials_template()
            return None, None
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        uid = None
        password = None
        
        # Try to find uid and password using regex
        import re
        
        # Look for uid=value or uid: value
        uid_match = re.search(r'(?:uid\s*[=:]\s*)(\d+)', content, re.IGNORECASE)
        if uid_match:
            uid = uid_match.group(1)
        
        # Look for password=value or password: value
        pass_match = re.search(r'(?:password\s*[=:]\s*)([^\s\n\r]+)', content, re.IGNORECASE)
        if pass_match:
            password = pass_match.group(1)
        
        if not uid or not password:
            print(f"❌ Could not find UID/password in {filename}")
            print("📝 Please make sure the file contains:")
            print("   uid=YOUR_UID,password=YOUR_PASSWORD")
            print("   OR")
            print("   uid: YOUR_UID")
            print("   password: YOUR_PASSWORD")
            return None, None
        
        print(f"✅ Loaded credentials from {filename}")
        print(f"👤 UID: {uid}")
        print(f"🔑 Password: {'*' * len(password)}")
        
        return uid, password
        
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return None, None

# Load emotes from JSON file (your format)
def load_emotes_from_json():
    """Load emote IDs from emotes.json file with your exact format"""
    emotes_file = "emotes.json"
    
    try:
        with open(emotes_file, 'r') as f:
            emotes_data = json.load(f)
        
        # Access using your structure: data["EMOTES"]["numbers"] and data["EMOTES"]["names"]
        number_emotes = emotes_data.get("EMOTES", {}).get("numbers", {})
        name_emotes = emotes_data.get("EMOTES", {}).get("names", {})
        
        print(f"✅ Loaded {len(number_emotes)} number emotes and {len(name_emotes)} named emotes")
        return {
            "numbers": number_emotes,
            "names": name_emotes
        }
        
    except Exception as e:
        print(f"❌ Error loading {emotes_file}: {e}")
        # Return empty dictionaries as fallback
        return {"numbers": {}, "names": {}}

# Load emotes globally
EMOTES_DATA = load_emotes_from_json()
NUMBER_EMOTES = EMOTES_DATA["numbers"]
NAME_EMOTES = EMOTES_DATA["names"]

# Helper functions for ghost join
def dec_to_hex(decimal):
    """Convert decimal to hex string"""
    hex_str = hex(decimal)[2:]
    return hex_str.upper() if len(hex_str) % 2 == 0 else '0' + hex_str.upper()




# =================== BOT RESTART FUNCTION ===================
def restart_bot():
    """Restart the bot - sends success message and restarts"""
    print("🔄 Bot restart initiated...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

async def handle_restart_command(uid, chat_id, key, iv, chat_type):
    """Handle * command"""
    success_msg = "[FFDAB9][b][c]- Ｇᴏᴏᴅ Ｂʏᴇᴇ !!"
    await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
    await asyncio.sleep(1)
    restart_bot()

# =================== AI API CALL FUNCTION ===================
# =================== RIZAK PACKET FUNCTION ===================
async def rizak(uid, secret_code, key, iv):
    """Rizak packet function - creates special packet for team leave/kick events"""
    fields = {
        1: 61,
        2: {
            1: int(uid),  
            2: {
                1: int(uid), 
                2: int(datetime.now().timestamp()),
                3: RIZER,
                5: 12,
                6: random.randint(11, 16),
                7: 1,
                8: {
                    2: 1,
                    3: 1
                },
                9: 1,   
            },
            3: str(secret_code),  
        }
    }
    packet = await CrEaTe_ProTo(fields)
    packet_hex = packet.hex()
    header_lenth = len(await encrypt_packet(packet_hex, key, iv)) // 2
    header_lenth_final = dec_to_hex(header_lenth)
    prefix = "0515" + "0" * (6 - len(header_lenth_final))

    encrypted = await encrypt_packet(packet_hex, key, iv)
    final_packet = prefix + header_lenth_final + encrypted
    return bytes.fromhex(final_packet)

async def handle_rizak_on_leave(uid, chat_id, key, iv, chat_type):
    """Handle rizak packet when bot leaves or gets kicked from team"""
    try:
        # Generate a secret code based on timestamp
        secret_code = f"RIZER_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
        rizak_packet = await rizak(uid, secret_code, key, iv)

        if rizak_packet and online_writer:
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', rizak_packet)
            print(f"✅ ABHI packet sent on team leave/kick for UID: {uid}")

            # Send notification message
            notify_msg = "[B][C][00FF00]🔄 ABHI packet activated!\n[FFFFFF]Bot left team or was kicked."
            await safe_send_message(chat_type, notify_msg, uid, chat_id, key, iv)
    except Exception as e:
        print(f"❌ Rizak packet error: {e}")

async def handle_ghost_man_command(uid, chat_id, key, iv, chat_type):
    """Handle /_man command - calls rizak function manually"""
    try:
        secret_code = f"GHOST_MAN_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
        rizak_packet = await rizak(uid, secret_code, key, iv)

        if rizak_packet and online_writer:
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', rizak_packet)
            success_msg = "[B][C][00FF00]✅ Ghost Man activated! 👻\n[FFFFFF]Rizak packet sent successfully!"
        else:
            success_msg = "[B][C][FF0000]❌ Failed to send rizak packet!"

        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Ghost Man error: {str(e)[:50]}"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)

# =================== GHOST JOIN PACKET FUNCTION ===================
async def ghost_join_packet(bot_uid, team_code, key, iv):
    """Create ghost join packet for joining team without showing in member list"""
    try:
        # Create the join packet structure
        fields = {
            1: 55,  # Packet type for team join
            2: {
                1: int(bot_uid),
                2: str(team_code),
                3: 1,  # Ghost mode flag
                4: {
                    1: 1,  # Hidden join
                    2: 0   # Don't show in list
                }
            }
        }

        proto_bytes = await CrEaTe_ProTo(fields)
        packet_hex = proto_bytes.hex()

        # Encrypt the packet
        encrypted = await encrypt_packet(packet_hex, key, iv)
        header_length = len(encrypted) // 2
        header_length_hex = dec_to_hex(header_length)

        # Build final packet with header
        prefix = "051500" + "0" * (6 - len(header_length_hex))
        final_packet = prefix + header_length_hex + encrypted

        return bytes.fromhex(final_packet)
    except Exception as e:
        print(f"❌ Ghost join packet error: {e}")
        return None

# =================== TEAM PUBLIC/PRIVATE FUNCTIONS ===================
async def Team_Public(bot_uid, key, iv):
    """Team public packet - for /private command"""
    fields = {1: 36, 2: {1: int(bot_uid)}}
    proto_bytes = await CrEaTe_ProTo(fields)
    packet_hex = proto_bytes.hex()

    encrypted = await encrypt_packet(packet_hex, key, iv)
    header_length = len(encrypted) // 2
    header_length_hex = dec_to_hex(header_length)

    prefix = "051500" + "0" * (6 - len(header_length_hex))
    final_packet = prefix + header_length_hex + encrypted
    return bytes.fromhex(final_packet)

async def Team_Private(bot_uid, key, iv):
    """Team private packet - for /private command"""
    fields = {1: 37, 5: {1: int(bot_uid)}}
    proto_bytes = await CrEaTe_ProTo(fields)
    packet_hex = proto_bytes.hex()

    encrypted = await encrypt_packet(packet_hex, key, iv)
    header_length = len(encrypted) // 2
    header_length_hex = dec_to_hex(header_length)

    prefix = "051500" + "0" * (6 - len(header_length_hex))
    final_packet = prefix + header_length_hex + encrypted
    return bytes.fromhex(final_packet)

async def handle_private_command(uid, chat_id, key, iv, chat_type):
    """Handle /private command - sends team private packet"""
    try:
        private_packet = await Team_Private(int(uid), key, iv)
        if private_packet and online_writer:
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', private_packet)
            success_msg = "[B][C][00FF00]✅ Team private packet sent! 🔒"
        else:
            success_msg = "[B][C][FF0000]❌ Failed to send team private packet!"
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Error in /private: {str(e)[:50]}"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)

async def encrypt_packet(packet_hex, key, iv):
    """Encrypt packet using AES CBC"""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    packet_bytes = bytes.fromhex(packet_hex)
    padded_packet = pad(packet_bytes, AES.block_size)
    encrypted = cipher.encrypt(padded_packet)
    return encrypted.hex()

async def nmnmmmmn(packet_hex, key, iv):
    """Wrapper for encrypt_packet"""
    return await encrypt_packet(packet_hex, key, iv)
    

def generate_random_hex_color():
    """Generate random hex color for messages"""
    return ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])

def bunner_():
    """Generate random avatar ID"""
    return random.randint(100000000, 999999999)

# Add this function to your code
def Encrypt(number):
    """Encrypt function from your first TCP bot"""
    number = int(number)
    encoded_bytes = []
    
    while True:
        byte = number & 0x7F
        number >>= 7
        if number:
            byte |= 0x80
        encoded_bytes.append(byte)
        if not number:
            break
    
    return bytes(encoded_bytes).hex()


async def send_working_join_request(target_uid, key, iv, region, LoGinDaTaUncRypTinG):
    """Send join request that actually works"""
    
    try:
        # Step 1: Reset bot to solo mode
        print("🔄 Resetting bot to solo mode...")
        await reset_bot_state(key, iv, region)
        await asyncio.sleep(1)
        
        # Step 2: Create bot's own squad (so it has context)
        print("🏠 Creating bot squad...")
        squad_packet = await OpEnSq(key, iv, region)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', squad_packet)
        await asyncio.sleep(1)
        
        # Step 3: Send join request
        print(f"📨 Sending join request to {target_uid}...")
        join_packet = await create_working_join_request(target_uid, key, iv, region, LoGinDaTaUncRypTinG)
        
        if join_packet:
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
            print(f"✅ Bot join request sent! Player can now accept.")
            return True
        else:
            print(f"❌ Failed to create join packet")
            return False
            
    except Exception as e:
        print(f"❌ Error in working join request: {e}")
        return False
        
async def handle_join_req_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type, LoGinDaTaUncRypTinG):
    """Handle /join_req command - bot sends join request to player"""
    
    parts = inPuTMsG.strip().split()
    
    if len(parts) < 2:
        error_msg = f"""[B][C][FF0000]❌ Usage: /join_req (player_uid)
Example: /join_req 123456789

What happens:
1. Bot goes solo mode
2. Bot creates its own squad  
3. Bot sends join request to player
4. Player sees: "BotName wants to join your team"
5. Player clicks Accept → Bot joins player's team
"""
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    target_uid = parts[1]
    
    if not target_uid.isdigit():
        error_msg = f"[B][C][FF0000]❌ Invalid UID! Must be numbers only.\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    # Send initial message
    initial_msg = f"""[B][C][FFFF00]🤖 BOT JOIN REQUEST INITIATED

👤 Target Player: {target_uid}
⚙️ Steps:
1. Bot resetting to solo mode...
2. Bot creating squad...
3. Sending join request...

⏳ Please wait...
"""
    await safe_send_message(chat_type, initial_msg, uid, chat_id, key, iv)
    
    try:
        success = await send_working_join_request(target_uid, key, iv, region, LoGinDaTaUncRypTinG)
        
        if success:
            success_msg = f"""[B][C][FFFF00]✅ BOT JOIN REQUEST SENT!

🎯 Target: {target_uid}
🤖 Bot Name: NARUTO-CODEX
✅ Status: Ready to join

📱 Player will see:
"ꫝʙʜɪㅤ  wants to join your team"

✅ When player clicks ACCEPT:
Bot will automatically join player's team!
"""
        else:
            success_msg = f"""[B][C][FF0000]❌ FAILED!

Possible reasons:
1. বো👽কাচু👽দা ম👽নে হয় offl👽ine গেছে
2. নাহলে ও👽য় চ👽দা👽চু👽দী👽তে BU👽SY আছে 

Try again in 10 seconds.
"""
        
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
        
        # Cleanup: Leave squad after sending request
        await asyncio.sleep(3)
        leave_packet = await ExiT(None, key, iv)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)
        print("🧹 Bot cleaned up (left squad)")
        
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Error: {str(e)[:50]}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)        
        
async def create_simple_start_packet(key, iv):
    """Create simple start match packet (00 00 00 d6)"""
    
    # This appears to be a minimal start packet
    # 00 00 00 d6 in hex = 214 in decimal (packet type?)
    
    fields = {
        1: 214,  # Packet type for start match (d6 hex = 214 decimal)
        2: {
            1: 1,  # Start match command
        }
    }
    
    packet = await CrEaTe_ProTo(fields)
    packet_hex = packet.hex()
    
    # Generate final packet
    final_packet = await GeneRaTePk(packet_hex, '0514', key, iv)  # Use appropriate packet type
    
    print(f"✅ Simple start match packet created")
    return final_packet
    
async def create_detailed_start_packet(key, iv, region="IND"):
    """Create detailed start match packet with device info"""
    
    # Decoded from your hex: contains device info (vivo, arm64, etc.)
    
    fields = {
        1: 269,  # 0x10D = 269 decimal (detailed start packet)
        2: {
            1: 8,           # Unknown
            2: 8,           # Unknown
            3: 11,          # Unknown
            4: 1,           # Unknown
            5: "vivo",      # Device brand
            6: "130",       # Device model
            7: "arm64-v8a", # CPU architecture
            8: "f538dc9b-cec9-43cd-8125-95f7f4f1f7e3",  # Device ID
            9: "FFD58FB4F76F648C2A5E21EBCFA3AAE81B4C9B7D97",  # Unknown
            10: "voice",    # Audio type
            11: "V2059",    # Version
            12: "mt6785",   # Processor
            13: "AFFD58FB4F76F648C2A5E21EBCFA3AAE81B4C9B7D97",  # Unknown
            14: "IND_1999120752610979840",  # Region + timestamp
            15: 269         # Packet length?
        }
    }
    
    packet = await CrEaTe_ProTo(fields)
    packet_hex = packet.hex()
    
    # Determine packet type based on region
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"
        
    final_packet = await GeneRaTePk(packet_hex, packet_type, key, iv)
    
    print(f"✅ Detailed start match packet created")
    return final_packet
        
async def generate_guest_accounts(count=1, name="BlackApis", password_prefix="FF"):
    """Generate guest accounts using the API"""
    api_url = f""
    
    accounts = []
    failed_attempts = 0
    max_retries = 10
    
    print(f"📡 Generating {count} guest accounts...")
    
    for i in range(count):
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                print(f"🔄 Attempt {retry_count + 1}/{max_retries} for account {i + 1}/{count}...")
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                    async with session.get(api_url) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get("success"):
                                account = {
                                    'uid': data.get('uid'),
                                    'password': data.get('password'),
                                    'name': data.get('name'),
                                    'timestamp': time.time()
                                }
                                accounts.append(account)
                                print(f"✅ Account {i + 1}: {account['uid']}")
                                success = True
                                failed_attempts = 0  # Reset failed attempts counter
                                
                            else:
                                print(f"❌ API error: {data.get('message', 'Unknown error')}")
                                retry_count += 1
                                await asyncio.sleep(2)
                                
                        elif response.status == 503:
                            print(f"⚠️ Server busy (503), retrying in 3 seconds...")
                            retry_count += 1
                            await asyncio.sleep(3)
                            
                        else:
                            print(f"❌ HTTP {response.status}, retrying...")
                            retry_count += 1
                            await asyncio.sleep(2)
                            
            except asyncio.TimeoutError:
                print(f"⏰ Timeout, retrying...")
                retry_count += 1
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}...")
                retry_count += 1
                await asyncio.sleep(2)
        
        if not success:
            print(f"❌ Failed to generate account {i + 1} after {max_retries} attempts")
            failed_attempts += 1
            
            # If too many failures in a row, stop
            if failed_attempts >= 3:
                print("🛑 Too many failures, stopping...")
                break
        
        # Small delay between accounts to avoid rate limiting
        if i < count - 1:
            await asyncio.sleep(1)
    
    return accounts

def save_guest_accounts(accounts, filename="guest_accounts.json"):
    """Save guest accounts to JSON file"""
    try:
        # Load existing accounts if file exists
        existing = []
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                existing = json.load(f)
        
        # Combine with new accounts
        all_accounts = existing + accounts
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(all_accounts, f, indent=2)
        
        print(f"💾 Saved {len(accounts)} accounts to {filename}")
        print(f"📊 Total accounts: {len(all_accounts)}")
        
        return True
    except Exception as e:
        print(f"❌ Error saving accounts: {e}")
        return False

async def generate_and_save_accounts(count, name="BlackApis", password_prefix="FF"):
    """Generate and save accounts with progress updates"""
    start_time = time.time()
    
    print(f"\n🎯 GENERATING {count} GUEST ACCOUNTS")
    print("="*50)
    
    accounts = await generate_guest_accounts(count, name, password_prefix)
    
    if accounts:
        # Save to file
        save_guest_accounts(accounts)
        
        # Display results
        elapsed = time.time() - start_time
        print("\n" + "="*50)
        print("📊 GENERATION COMPLETE")
        print("="*50)
        print(f"✅ Success: {len(accounts)}/{count} accounts")
        print(f"⏱️ Time: {elapsed:.1f} seconds")
        print(f"📁 Saved to: guest_accounts.json")
        
        # Show first 3 accounts as preview
        print("\n📋 FIRST 3 ACCOUNTS:")
        for i, acc in enumerate(accounts[:3]):
            print(f"  {i+1}. UID: {acc['uid']} | Pass: {acc['password']}")
        
        if len(accounts) > 3:
            print(f"  ... and {len(accounts) - 3} more")
    
    return accounts        
        
async def start_match(key, iv, region, detailed=False):
    """Start Free Fire match - bot must be in a squad/team"""
    
    try:
        if detailed:
            start_packet = await create_detailed_start_packet(key, iv, region)
        else:
            start_packet = await create_simple_start_packet(key, iv)
        
        if start_packet:
            # Send via Online connection
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', start_packet)
            print("🎮 Start match packet sent!")
            return True
        else:
            print("❌ Failed to create start packet")
            return False
            
    except Exception as e:
        print(f"❌ Error starting match: {e}")
        return False       
        
async def handle_start_match_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /ss command to start match"""
    
    parts = inPuTMsG.strip().split()
    
    # Check if user wants detailed start
    detailed = False
    if len(parts) > 1 and parts[1].lower() == "detailed":
        detailed = True
    
    # Send initial message
    initial_msg = f"""[B][C][FFFF00]🎮 STARTING MATCH...

⚙️ Mode: {'Detailed' if detailed else 'Simple'}
🤖 Bot must be in a squad!
⏳ Please wait...
"""
    await safe_send_message(chat_type, initial_msg, uid, chat_id, key, iv)
    
    try:
        success = await start_match(key, iv, region, detailed)
        
        if success:
            success_msg = f"""[B][C][FFFF00]✅ MATCH START COMMAND SENT!

📋 Details:
• Type: {'Detailed device info' if detailed else 'Simple start'}
• Status: Match starting...
• Requirement: Bot must be squad leader

🎯 If bot is squad leader, match will begin!
"""
        else:
            success_msg = f"""[B][C][FF0000]❌ FAILED TO START MATCH!

Possible reasons:
1. Bot not in a squad
2. Bot not squad leader
3. Invalid packet structure
4. Server connection issue

💡 Make sure bot is in a squad as leader!
"""
        
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
        
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Error: {str(e)[:50]}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        
async def debug_start_match():
    """Debug function to test start packets"""
    
    print("🔍 Analyzing start packets...")
    print(f"Simple packet hex: 00 00 00 d6")
    print(f"Decimal value: {int('d6', 16)} = 214")
    
    # Try to decode the detailed packet
    detailed_hex = "0a8d010808100b180122047669766f2a02313330f6a8858c023a0961726d36342d76386142004a2466353338643963622d636563392d343363642d383132352d393566376634663166376533522a4646443538464234463736463634384332413545323145424346413341414538314234433942374439375a05766f69636562055632303539680172066d74363738351241464644353846423446373646363438433241354532314542434641334141453831423443394237443937494e445f31393939313230373532363130393739383430188d01"
    
    print(f"\n📊 Detailed packet length: {len(detailed_hex)//2} bytes")
    print(f"First bytes: {detailed_hex[:20]}...")
    
    # Try to parse as protobuf
    try:
        from protobuf_decoder.protobuf_decoder import Parser
        parsed = Parser().parse(bytes.fromhex(detailed_hex))
        print(f"\n✅ Parsed detailed packet:")
        print(parsed)
    except Exception as e:
        print(f"❌ Could not parse: {e}")
        


async def check_player_status(target_uid, key, iv, max_wait=3):
    """Direct function to check player status with proper waiting"""
    try:
        # Clear old cache
        if target_uid in status_response_cache:
            del status_response_cache[target_uid]
        
        # Send request
        status_packet = await createpacketinfo(target_uid, key, iv)
        if not status_packet:
            return None, "Failed to create packet"
        
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', status_packet)
        print(f"📤 Sent status request for {target_uid}")
        
        # Wait for response with polling
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if target_uid in status_response_cache:
                cache_data = status_response_cache[target_uid]
                return cache_data, "Success"
            
            await asyncio.sleep(0.1)  # Short sleep
        
        return None, f"No response after {max_wait} seconds"
        
    except Exception as e:
        return None, f"Error: {str(e)}"

async def createpacketinfo(idddd, key, iv):
    """Create player status request packet - SAME as first TCP bot"""
    try:
        ida = Encrypt(idddd)
        packet = f"080112090A05{ida}1005"
        header_lenth = len(await encrypt_packet(packet, key, iv)) // 2
        header_lenth_final = dec_to_hex(header_lenth)
        
        if len(header_lenth_final) == 2:
            final_packet = "0F15000000" + header_lenth_final + await nmnmmmmn(packet, key, iv)
        elif len(header_lenth_final) == 3:
            final_packet = "0F1500000" + header_lenth_final + await nmnmmmmn(packet, key, iv)
        elif len(header_lenth_final) == 4:
            final_packet = "0F150000" + header_lenth_final + await nmnmmmmn(packet, key, iv)
        elif len(header_lenth_final) == 5:
            final_packet = "0F15000" + header_lenth_final + await nmnmmmmn(packet, key, iv)
        else:
            final_packet = "0F1500000" + header_lenth_final + await nmnmmmmn(packet, key, iv)
            
        return bytes.fromhex(final_packet)
        
    except Exception as e:
        print(f"Error creating packet info: {e}")
        return None

def fix_num(number):
    """Format numbers with breaks - from first TCP"""
    fixed = ""
    count = 0
    num_str = str(number)
    
    for char in num_str:
        if char.isdigit():
            count += 1
        fixed += char
        if count == 3:
            fixed += "[c]"
            count = 0
    return fixed

def get_available_room(input_text):
    """Parse protobuf to JSON - from first TCP"""
    try:
        from protobuf_decoder.protobuf_decoder import Parser
        parsed_results = Parser().parse(input_text)
        parsed_results_objects = parsed_results
        parsed_results_dict = parse_results(parsed_results_objects)
        json_data = json.dumps(parsed_results_dict)
        return json_data
    except Exception as e:
        print(f"error {e}")
        return None

def parse_results(parsed_results):
    """Helper for get_available_room"""
    result_dict = {}
    for result in parsed_results:
        field_data = {}
        field_data["wire_type"] = result.wire_type
        if result.wire_type == "varint":
            field_data["data"] = result.data
        if result.wire_type == "string":
            field_data["data"] = result.data
        if result.wire_type == "bytes":
            field_data["data"] = result.data
        elif result.wire_type == "length_delimited":
            field_data["data"] = parse_results(result.data.results)
        result_dict[result.field] = field_data
    return result_dict  # ← ADD THIS LINE

def get_player_status(packet):
    """Get player status from packet"""
    json_result = get_available_room(packet)
    if not json_result:
        return "OFFLINE"
    
    parsed_data = json.loads(json_result)
    
    if "5" not in parsed_data or "data" not in parsed_data["5"]:
        return "OFFLINE"
    
    json_data = parsed_data["5"]["data"]
    
    if "1" not in json_data or "data" not in json_data["1"]:
        return "OFFLINE"
    
    data = json_data["1"]["data"]
    
    if "3" not in data:
        return "OFFLINE"
    
    status_data = data["3"]
    
    if "data" not in status_data:
        return "OFFLINE"
    
    status = status_data["data"]
    
    if status == 1:
        return "SOLO"
    if status == 2:
        if "9" in data and "data" in data["9"]:
            group_count = data["9"]["data"]
            countmax1 = data["10"]["data"]
            countmax = countmax1 + 1
            return f"INSQUAD ({group_count}/{countmax})"
        return "INSQUAD"
    if status in [3, 5]:
        return "INGAME"
    if status == 4:
        return "IN ROOM"
    if status in [6, 7]:
        return "IN SOCIAL ISLAND MODE"
    
    return "NOTFOUND"

def get_idroom_by_idplayer(packet):
    """Extract room ID from player info packet"""
    try:
        json_result = get_available_room(packet)
        parsed_data = json.loads(json_result)
        json_data = parsed_data["5"]["data"]
        data = json_data["1"]["data"]
        idroom = data['15']["data"]
        return idroom
    except Exception as e:
        print(f"Error extracting room ID: {e}")
        return None



def get_leader(packet):
    """Extract leader ID from squad packet"""
    try:
        json_result = get_available_room(packet)
        parsed_data = json.loads(json_result)
        json_data = parsed_data["5"]["data"]
        data = json_data["1"]["data"]
        leader = data['8']["data"]
        return leader
    except Exception as e:
        print(f"Error extracting leader: {e}")
        return None

# Add to your global variables

# Add near top with other globals
status_queue = asyncio.Queue()
cache_dict = {}

# In TcPOnLine, instead of caching directly:
async def handle_status_response(hex_data):
    """Process and queue status responses"""
    try:
        # ... parsing code ...
        
        # Put in queue instead of direct cache
        await status_queue.put({
            'player_id': player_id,
            'data': cache_entry
        })
        
        print(f"📤 Queued status for {player_id}")
        
    except Exception as e:
        print(f"❌ Queue error: {e}")

# In TcPChaT, add a queue consumer
async def cache_consumer():
    """Consume status responses from queue"""
    while True:
        try:
            item = await status_queue.get()
            player_id = item['player_id']
            cache_dict[player_id] = item['data']
            print(f"📥 Cache updated for {player_id}")
            status_queue.task_done()
        except Exception as e:
            print(f"❌ Consumer error: {e}")
        await asyncio.sleep(0.1)



# Start consumer in your main function
async def StarTinG():
    # Start consumer
    consumer_task = asyncio.create_task(cache_consumer())
    
    while True:
        try:
            await asyncio.wait_for(MaiiiinE(), timeout = 7 * 60 * 60)
        except KeyboardInterrupt:
            consumer_task.cancel()
            break
        except asyncio.TimeoutError: 
            print("Token ExpiRed ! , ResTartinG")
        except Exception as e: 
            print(f"ErroR TcP - {e} => ResTarTinG ...")

import pickle
import os
import time

CACHE_FILE = 'status_cache.pkl'
CACHE_TIMEOUT = 30  # Cache entries expire after 30 seconds

def save_to_cache(player_id, data):
    """Save status to file cache with timestamp"""
    try:
        # Load existing cache
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'rb') as f:
                    cache = pickle.load(f)
            except:
                cache = {}
        else:
            cache = {}
        
        # Add timestamp
        data['saved_at'] = time.time()
        
        # Update cache
        cache[str(player_id)] = data
        
        # Save back
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(cache, f)
        
        print(f"💾 Saved to file cache: {player_id}")
        return True
    except Exception as e:
        print(f"❌ Cache save error: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_from_cache(player_id):
    """Load status from file cache, check expiration"""
    try:
        if not os.path.exists(CACHE_FILE):
            return None
        
        with open(CACHE_FILE, 'rb') as f:
            cache = pickle.load(f)
        
        player_key = str(player_id)
        if player_key in cache:
            data = cache[player_key]
            
            # Check if cache is expired
            if 'saved_at' in data:
                if time.time() - data['saved_at'] > CACHE_TIMEOUT:
                    print(f"⏰ Cache expired for {player_id}")
                    del cache[player_key]
                    with open(CACHE_FILE, 'wb') as f:
                        pickle.dump(cache, f)
                    return None
            
            print(f"📥 Loaded from cache: {player_id}")
            return data
        
        return None
    except Exception as e:
        print(f"❌ Cache load error: {e}")
        return None

def clear_cache_entry(player_id):
    """Clear specific cache entry"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'rb') as f:
                cache = pickle.load(f)
            
            player_key = str(player_id)
            if player_key in cache:
                del cache[player_key]
                
            with open(CACHE_FILE, 'wb') as f:
                pickle.dump(cache, f)
            print(f"🗑️ Cleared cache for {player_id}")
    except Exception as e:
        print(f"❌ Clear cache error: {e}")

def debug_file_cache():
    """Debug the file cache"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'rb') as f:
                cache = pickle.load(f)
            print(f"\n📁 FILE CACHE DEBUG:")
            print(f"Size: {len(cache)} entries")
            for uid, data in cache.items():
                age = time.time() - data.get('saved_at', 0)
                status = data.get('status', 'NO STATUS')
                print(f"  {uid}: {status} (age: {age:.1f}s)")
            print("---\n")
            return cache
        else:
            print("📁 No cache file exists")
            return {}
    except Exception as e:
        print(f"❌ Cache debug error: {e}")
        return {}

def load_from_cache(player_id):
    """Load status from file cache"""
    try:
        if not os.path.exists(CACHE_FILE):
            return None
        
        with open(CACHE_FILE, 'rb') as f:
            cache = pickle.load(f)
        
        if player_id in cache:
            return cache[player_id]
        return None
    except Exception as e:
        print(f"❌ Cache load error: {e}")
        return None

def clear_cache_entry(player_id):
    """Clear specific cache entry"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'rb') as f:
                cache = pickle.load(f)
            
            if player_id in cache:
                del cache[player_id]
                
            with open(CACHE_FILE, 'wb') as f:
                pickle.dump(cache, f)
    except:
        pass


    
    
    async def get_account_token(self, uid, password):
        """Get access token for a specific account"""
        try:
            url = "https://100067.connect.garena.com/oauth/guest/token/grant"
            headers = {
                "Host": "100067.connect.garena.com",
                "User-Agent": await Ua(),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "close"
            }
            data = {
                "uid": uid,
                "password": password,
                "response_type": "token",
                "client_type": "2",
                "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
                "client_id": "100067"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        data = await response.json()
                        open_id = data.get("open_id")
                        access_token = data.get("access_token")
                        return open_id, access_token
            return None, None
        except Exception as e:
            print(f"❌ Error getting token for {uid}: {e}")
            return None, None
    
    async def send_join_from_account(self, target_uid, account_uid, password, key, iv, region):
        """Send join request from a specific account"""
        try:
            # Get token for this account
            open_id, access_token = await self.get_account_token(account_uid, password)
            if not open_id or not access_token:
                return False
            
            # Create join packet using the account's credentials
            join_packet = await self.create_account_join_packet(target_uid, account_uid, open_id, access_token, key, iv, region)
            if join_packet:
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error sending join from {account_uid}: {e}")
            return False

async def join_custom_room(room_id, room_password, key, iv, region):
    """Join custom room with proper Free Fire packet structure"""
    fields = {
        1: 61,  # Room join packet type (verified for Free Fire)
        2: {
            1: int(room_id),
            2: {
                1: int(room_id),  # Room ID
                2: int(time.time()),  # Timestamp
                3: "BOT",  # Player name
                5: 12,  # Unknown
                6: 9999999,  # Unknown
                7: 1,  # Unknown
                8: {
                    2: 1,
                    3: 1,
                },
                9: 3,  # Room type
            },
            3: str(room_password),  # Room password
        }
    }
    
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"
        
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet_type, key, iv)
    
async def leave_squad(key, iv, region):
    """Leave squad - converted from your old TCP leave_s()"""
    fields = {
        1: 7,
        2: {
            1: 12480598706  # Your exact value from old TCP
        }
    }
    
    packet = (await CrEaTe_ProTo(fields)).hex()
    
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"
        
    return await GeneRaTePk(packet, packet_type, key, iv)    
    
async def request_join_with_badge(target_uid, badge_value, key, iv, region="IND"):
    """Fixed badge spam function matching craftland_badge structure"""
    try:
        # Get random avatar
        avatar_id = int(await xBunnEr())
        
        fields = {
            1: 33,  # Packet type
            2: {
                1: int(target_uid),        # Target UID
                2: region.upper(),        # Country code
                3: 1,                     # Status 1
                4: 1,                     # Status 2
                5: bytes([1, 7, 9, 10, 11, 18, 25, 26, 32]),  # Numbers field
                6: "TG:[C][B][FF0000] @Beotherjk",  # Nickname
                7: 330,                   # Rank
                8: 1000,                  # Field 8
                10: region.upper(),       # Region code
                11: bytes([              # UUID
                    49, 97, 99, 52, 98, 56, 48, 101, 99, 102, 48, 52, 55, 56,
                    97, 52, 52, 50, 48, 51, 98, 102, 56, 102, 97, 99, 54, 49,
                    50, 48, 102, 53
                ]),
                12: 1,                    # Field 12
                13: int(target_uid),      # Repeated UID
                14: {                    # Field 14 (nested)
                    1: 2203434355,
                    2: 8,
                    3: b"\x10\x15\x08\x0A\x0B\x13\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
                },
                16: 1,                    # Field 16
                17: 1,                    # Field 17
                18: 312,                  # Field 18
                19: 46,                   # Field 19
                23: bytes([16, 1, 24, 1]), # Field 23
                24: avatar_id,            # Avatar ID
                26: {},                   # Empty field 26
                27: {                    # Field 27 (critical for badge!)
                    1: 11,               # Field 27.1
                    2: 12999994075,      # Field 27.2 (your bot UID)
                    3: 9999              # Field 27.3
                },
                28: {},                   # Empty field 28
                31: {                    # Field 31 (badge value here too)
                    1: 1,
                    2: int(badge_value)  # BADGE VALUE
                },
                32: int(badge_value),     # Field 32 (badge value again)
                34: {                    # Field 34
                    1: int(target_uid),  # Target UID again
                    2: 8,
                    3: b"\x0F\x06\x15\x08\x0A\x0B\x13\x0C\x11\x04\x0E\x14\x07\x02\x01\x05\x10\x03\x0D\x12"
                }
            },
            10: "en",                     # Language
            13: {                        # Field 13
                2: 1,
                3: 1
            }
        }
        
        # Convert to protobuf
        proto_bytes = await CrEaTe_ProTo(fields)
        packet_hex = proto_bytes.hex()
        
        # Determine packet type based on region
        if region.lower() == "ind":
            packet_type = '0514'
        elif region.lower() == "bd":
            packet_type = "0519"
        else:
            packet_type = "0515"
            
        # Generate final encrypted packet
        final_packet = await GeneRaTePk(packet_hex, packet_type, key, iv)
        
        print(f"✅ Created badge packet with value {badge_value} for UID {target_uid}")
        return final_packet
        
    except Exception as e:
        print(f"❌ Error creating badge packet: {e}")
        import traceback
        traceback.print_exc()
        return None
    
async def reset_bot_state(key, iv, region):
    """Reset bot to solo mode before spam - Critical step from your old TCP"""
    try:
        # Leave any current squad (using your exact leave_s function)
        leave_packet = await leave_squad(key, iv, region)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)
        await asyncio.sleep(0.5)
        
        print("✅ Bot state reset - left squad")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting bot: {e}")
        return False    
    
async def create_custom_room(room_name, room_password, max_players, key, iv, region):
    """Create a custom room"""
    fields = {
        1: 3,  # Create room packet type
        2: {
            1: room_name,
            2: room_password,
            3: max_players,  # 2, 4, 8, 16, etc.
            4: 1,  # Room mode
            5: 1,  # Map
            6: "en",  # Language
            7: {   # Player info
                1: "BotHost",
                2: int(await xBunnEr()),
                3: 330,
                4: 1048576,
                5: "BOTCLAN"
            }
        }
    }
    
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"
        
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet_type, key, iv)              




async def handle_badge_command(cmd, inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle individual badge commands"""
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        error_msg = f"[B][C][FF0000]❌ Usage: /{cmd} (uid)\nExample: /{cmd} 123456789\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    target_uid = parts[1]
    badge_value = BADGE_VALUES.get(cmd, 1048576)
    
    if not target_uid.isdigit():
        error_msg = f"[B][C][FF0000]❌ Please write a valid player ID!\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    # Send initial message
    initial_msg = f"[B][C][1E90FF]🌀 Request received! Preparing to send {cmd} ({badge_value}) to {target_uid}...\n"
    await safe_send_message(chat_type, initial_msg, uid, chat_id, key, iv)
    
    try:
        # Create badge packet
        badge_packet = await request_join_with_badge(target_uid, badge_value, key, iv, region)
        
        if badge_packet:
            # Send packet 5 times for spam effect
            for i in range(5):
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', badge_packet)
                print(f"✅ Sent /{cmd} badge #{i+1} with value {badge_value}")
                await asyncio.sleep(0.2)  # Slight delay
            
            success_msg = f"[B][C][FFFF00]✅ Successfully Sent {cmd} Badge!\n🎯 Target: {target_uid}\n🏷️ Badge Value: {badge_value}\n📤 Packets Sent: 5\n"
        else:
            success_msg = f"[B][C][FF0000]❌ Failed to create badge packet!\n"
        
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
        
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Error in /{cmd}: {str(e)}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)



async def badge_spam(cmd, inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle individual badge commands"""
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        error_msg = f"[B][C][FF0000]❌ Usage: /{cmd} (uid)\nExample: /{cmd} 123456789\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    target_uid = parts[1]
    badge_value = BADGE_VALUES.get("s2", 32768)
    
    if not target_uid.isdigit():
        error_msg = f"[B][C][FF0000]❌ Please write a valid player ID!\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    # Send initial message
    initial_msg = f"[B][C][1E90FF]🌀 Request received! Preparing to send spam ({badge_value}) to {xMsGFixinG(target_uid)}...\n"
    await safe_send_message(chat_type, initial_msg, uid, chat_id, key, iv)
    
    try:
        # Create badge packet
        badge_packet = await request_join_with_badge(target_uid, badge_value, key, iv, region)
        
        if badge_packet:
            # Send packet 5 times for spam effect
            for i in range(50):
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', badge_packet)
                print(f"✅ Sent /{cmd} badge #{i+1} with value {badge_value}")
                await asyncio.sleep(0.2)  # Slight delay
            
            success_msg = f"[B][C][FFFF00]✅ Successfully Sent {cmd} Badge!\n🎯 Target: {target_uid}\n🏷️ Badge Value: {badge_value}\n📤 Packets Sent: 5\n"
        else:
            success_msg = f"[B][C][FF0000]❌ Failed to create badge packet!\n"
        
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
        
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Error in /{cmd}: {str(e)}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)


    
    
async def auto_rings_emote_dual(uid, key, iv, region):
    """Send The Rings emote to both sender and bot for dual emote effect"""
    try:
        # The Rings emote ID
        rings_emote_id = 909052002
        
        # Get bot's UID
        bot_uid = 13601801571
        
        # Send emote to SENDER (person who invited)
        emote_to_sender = await Emote_k(int(uid), rings_emote_id, key, iv, region)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_to_sender)
        
        # Small delay between emotes
        await asyncio.sleep(0.5)
        
        # Send emote to BOT (bot performs emote on itself)
        emote_to_bot = await Emote_k(int(bot_uid), rings_emote_id, key, iv, region)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_to_bot)
        
        print(f"🤖 Bot performed dual Rings emote with sender {uid} and bot {bot_uid}!")
        
    except Exception as e:
        print(f"Error sending dual rings emote: {e}")    
    
    
async def Room_Spam(Uid, Rm, Nm, K, V):
    fields = {
        1: 78,
        2: {
            1: int(Rm),  
            2: "iG:[C][B][FF0000]ABHI ",  
            3: {
                2: 1,
                3: 1
            },
            4: 330,      
            5: 6000,     
            6: 201,      
            10: int(await xBunnEr()),  
            11: int(Uid), # Target UID
            12: 1,       
            15: {
                1: 1,
                2: 32768
            },
            16: 32768,    
            18: {
                1: 11481904755,  
                2: 8,
                3: "\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
            },
            
            31: {
                1: 1,
                2: 32768
            },
            32: 32768,    
            34: {
                1: int(Uid),   
                2: 8,
                3: bytes([15,6,21,8,10,11,19,12,17,4,14,20,7,2,1,5,16,3,13,18])
            }
        }
    }
    
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0e15', K, V)

#ADDING-100-LIKES-IN-24H
def send_likes(uid):
    try:
        likes_api_response = requests.get(
             f"http://217.154.114.227:10468/like?uid={uid}&server_name=BD&password=MAHIR@123",
             timeout=10
             )
      
      
        if likes_api_response.status_code != 200:
            return f"""
[C][B][FF0000]━━━━━
[FFFFFF]Like API Error!
━━━━━
"""

        api_json_response = likes_api_response.json()

        player_name = api_json_response.get('PlayerNickname', 'Unknown')
        likes_before = api_json_response.get('LikesbeforeCommand', 0)
        likes_after = api_json_response.get('LikesafterCommand', 0)
        likes_added = api_json_response.get('LikesGivenByAPI', 0)
        status = api_json_response.get('status', 0)

        if status == 1 and likes_added > 0:
            # ✅ Success
            return f"""
[C][B][11EAFD]‎━━━━━━━━━━━━
[FFFFFF]Likes Status:

[00FF00]Likes Sent Successfully!

[FFFFFF]Player Name : [00FF00]{xMsGFixinG(player_name)}  
[FFFFFF]Likes Added : [00FF00]{xMsGFixinG(likes_added)}  
[FFFFFF]Likes Before : [00FF00]{xMsGFixinG(likes_before)}  
[FFFFFF]Likes After : [00FF00]{xMsGFixinG(likes_after)}  
[C][B][11EAFD]‎━━━━━━━━━━━━
[C][B][FFB300]Subscribe: [FFFFFF]NARUTO CODEX [00FF00]!!
"""
        elif status == 2 or likes_before == likes_after:
            # 🚫 Already claimed / Maxed
            return f"""
[C][B][FF0000]━━━━━━━━━━━━

[FFFFFF]No Likes Sent!

[FF0000]You have already taken likes with this UID.
Try again after 24 hours.

[FFFFFF]Player Name : [FF0000]{xMsGFixinG(player_name)}  
[FFFFFF]Likes Before : [FF0000]{xMsGFixinG(likes_before)}  
[FFFFFF]Likes After : [FF0000]{xMsGFixinG(likes_after)}  
[C][B][FF0000]━━━━━━━━━━━━
"""
        else:
            # ❓ Unexpected case
            return f"""
[C][B][FF0000]━━━━━━━━━━━━
[FFFFFF]Unexpected Response!
Something went wrong.

Please try again or contact support.
━━━━━━━━━━━━
"""

    except requests.exceptions.RequestException:
        return """
[C][B][FF0000]━━━━━
[FFFFFF]Like API Connection Failed!
Is the API server (app.py) running?
━━━━━
"""
    except Exception as e:
        return f"""
[C][B][FF0000]━━━━━
[FFFFFF]An unexpected error occurred:
[FF0000]{str(e)}
━━━━━
"""

async def accept_join(target_uid, badge_value, key, iv):
    """Send badge join request silently"""

    print('send')

    if not str(target_uid).isdigit():
        return
    
    try:
        # region default bd
        badge_packet = await request_join_with_badge(target_uid, badge_value, key, iv, "bd")
        
        if badge_packet:
            for i in range(1):
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', badge_packet)
                print(f"✅ Sent badge #{i+1} with value {badge_value}")
                await asyncio.sleep(0.2)
        else:
            print("❌ Failed to create badge packet!")
        
    except Exception as e:
        print(f"❌ Error in accept_join: {str(e)}")


async def evo_cycle_spam(uids, key, iv, region, LoGinDaTaUncRypTinG):
    """Cycle through all evolution emotes - BOT DOES OPPOSITE"""
    global evo_cycle_running
    
    # GET BOT UID FROM LOGIN DATA
    try:
        # Try to get from login data (passed as parameter)
        bot_uid = LoGinDaTaUncRypTinG.AccountUID
        print(f"🤖 Using bot UID from login: {bot_uid}")
    except:
        # Fallback to your hardcoded UID
        bot_uid = 2579372095
        print(f"🤖 Using hardcoded bot UID: {bot_uid}")
    
    cycle_count = 0
    while evo_cycle_running:
        cycle_count += 1
        print(f"Starting evolution emote cycle #{cycle_count}")
        
        emote_list = list(evo_emotes.items())
        total_emotes = len(emote_list)
        
        for index, (emote_number, emote_id) in enumerate(emote_list):
            if not evo_cycle_running:
                break
                
            # USER does emote #X
            for uid in uids:
                try:
                    uid_int = int(uid)
                    user_emote = await Emote_k(uid_int, int(emote_id), key, iv, region)
                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', user_emote)
                    print(f"👤 User emote #{emote_number}")
                except Exception as e:
                    print(f"Error: {e}")
            
            # ADD SMALL DELAY
            await asyncio.sleep(0.5)
            
            # BOT does opposite emote (last emote when user does first, etc.)
            opposite_index = total_emotes - 1 - index
            opposite_number, opposite_id = emote_list[opposite_index]
            
            try:
                # BOT sends emote to ITSELF
                bot_self_emote = await Emote_k(int(bot_uid), int(opposite_id), key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', bot_self_emote)
                
                # ALSO send to first user for visibility
                await asyncio.sleep(0.3)
                if uids:
                    first_uid = int(uids[0])
                    bot_to_user = await Emote_k(first_uid, int(opposite_id), key, iv, region)
                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', bot_to_user)
                
                print(f"🤖 Bot OPPOSITE emote #{opposite_number} (sent to self + user)")
            except Exception as e:
                print(f"Bot error: {e}")
            
            # Wait 5 seconds before next emote
            if evo_cycle_running:
                print(f"Waiting 5 seconds before next emote...")
                wait_time = 5
                for i in range(wait_time):
                    if not evo_cycle_running:
                        break
                    await asyncio.sleep(1)
    
    print("Cycle stopped")
    
async def reject_spam_loop(target_uid, key, iv):
    """Send reject spam packets to target in background"""
    global reject_spam_running
    
    count = 0
    max_spam = 150
    
    while reject_spam_running and count < max_spam:
        try:
            # Send both packets
            packet1 = await banecipher1(target_uid, key, iv)
            packet2 = await banecipher(target_uid, key, iv)
            
            # Send to Online connection
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', packet1)
            await asyncio.sleep(0.1)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', packet2)
            
            count += 1
            print(f"Sent reject spam #{count} to {target_uid}")
            
            # 0.2 second delay between spam cycles
            await asyncio.sleep(0.2)
            
        except Exception as e:
            print(f"Error in reject spam: {e}")
            break
    
    return count    
    
async def handle_reject_completion(spam_task, target_uid, sender_uid, chat_id, chat_type, key, iv):
    """Handle completion of reject spam and send final message"""
    try:
        spam_count = await spam_task
        
        # Send completion message
        if spam_count >= 150:
            completion_msg = f"[B][C][FFFF00]✅ Reject Spam Completed Successfully for ID {target_uid}\n✅ Total packets sent: {spam_count * 2}\n"
        else:
            completion_msg = f"[B][C][FFFF00]⚠️ Reject Spam Partially Completed for ID {target_uid}\n⚠️ Total packets sent: {spam_count * 2}\n"
        
        await safe_send_message(chat_type, completion_msg, sender_uid, chat_id, key, iv)
        
    except asyncio.CancelledError:
        print("Reject spam was cancelled")
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ ERROR in reject spam: {str(e)}\n"
        await safe_send_message(chat_type, error_msg, sender_uid, chat_id, key, iv)    
    
    
    
async def banecipher(target_uid, key, iv):
    """Create reject spam packet 1 - Converted to new async format"""
    banner_text = f"""
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][0000FF]======================================================================================================================================================================================================================================================
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███




"""        
    fields = {
        1: 5,
        2: {
            1: int(client_id),
            2: 1,
            3: int(client_id),
            4: banner_text
        }
    }
    
    # Use CrEaTe_ProTo from xC4.py (async)
    packet = await CrEaTe_ProTo(fields)
    packet_hex = packet.hex()
    
    # Use EnC_PacKeT from xC4.py (async)
    encrypted_packet = await EnC_PacKeT(packet_hex, key, iv)
    
    # Calculate header length
    header_length = len(encrypted_packet) // 2
    header_length_final = await DecodE_HeX(header_length)
    
    # Build final packet based on header length
    if len(header_length_final) == 2:
        final_packet = "0515000000" + header_length_final + encrypted_packet
    elif len(header_length_final) == 3:
        final_packet = "051500000" + header_length_final + encrypted_packet
    elif len(header_length_final) == 4:
        final_packet = "05150000" + header_length_final + encrypted_packet
    elif len(header_length_final) == 5:
        final_packet = "0515000" + header_length_final + encrypted_packet
    else:
        final_packet = "0515000000" + header_length_final + encrypted_packet

    return bytes.fromhex(final_packet)

async def black666(client_id, key, iv):
    banner_text = "[FF0000][B][C] ERROR , WELCOME TO [FFFFFF]AROHI [FFFF00]___X³____ BOT ! \n[FFFF00]NEW VERSION NEW FUNCTION !\n[FF0000]TELEGRAM : @classic_aruhi\n\n"     
    fields = {
        1: 5,
        2: {
            1: int(client_id),
            2: 1,
            3: int(client_id),
            4: banner_text
        }
    }
    
    # Use CrEaTe_ProTo from xC4.py (async)
    packet = await CrEaTe_ProTo(fields)
    packet_hex = packet.hex()
    
    # Use EnC_PacKeT from xC4.py (async)
    encrypted_packet = await EnC_PacKeT(packet_hex, key, iv)
    
    # Calculate header length
    header_length = len(encrypted_packet) // 2
    header_length_final = await DecodE_HeX(header_length)
    
    # Build final packet based on header length
    if len(header_length_final) == 2:
        final_packet = "0515000000" + header_length_final + encrypted_packet
    elif len(header_length_final) == 3:
        final_packet = "051500000" + header_length_final + encrypted_packet
    elif len(header_length_final) == 4:
        final_packet = "05150000" + header_length_final + encrypted_packet
    elif len(header_length_final) == 5:
        final_packet = "0515000" + header_length_final + encrypted_packet
    else:
        final_packet = "0515000000" + header_length_final + encrypted_packet

    return bytes.fromhex(final_packet)

async def banecipher1(client_id, key, iv):
    """Create reject spam packet 2 - Converted to new async format"""
    gay_text = f"""
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
.
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][0000FF]======================================================================================================================================================================================================================================================
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███
[b][000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███[000000]███




"""        
    fields = {
        1: int(client_id),
        2: 5,
        4: 50,
        5: {
            1: int(client_id),
            2: gay_text,
        }
    }
    
    # Use CrEaTe_ProTo from xC4.py (async)
    packet = await CrEaTe_ProTo(fields)
    packet_hex = packet.hex()
    
    # Use EnC_PacKeT from xC4.py (async)
    encrypted_packet = await EnC_PacKeT(packet_hex, key, iv)
    
    # Calculate header length
    header_length = len(encrypted_packet) // 2
    header_length_final = await DecodE_HeX(header_length)
    
    # Build final packet based on header length
    if len(header_length_final) == 2:
        final_packet = "0515000000" + header_length_final + encrypted_packet
    elif len(header_length_final) == 3:
        final_packet = "051500000" + header_length_final + encrypted_packet
    elif len(header_length_final) == 4:
        final_packet = "05150000" + header_length_final + encrypted_packet
    elif len(header_length_final) == 5:
        final_packet = "0515000" + header_length_final + encrypted_packet
    else:
        final_packet = "0515000000" + header_length_final + encrypted_packet

    return bytes.fromhex(final_packet)
    
async def get_colorful_message(message_text, message_number):
    """Generate message with different colors"""
    color_palette = ["FF0000", "FFFF00", "0000FF", "FFFF00", "FF00FF", 
                     "00FFFF", "FFA500", "FF1493", "00FF7F", "7B68EE",
                     "FFD700", "00CED1", "FF69B4", "32CD32", "9370DB",
                     "FF4500", "1E90FF", "ADFF2F", "FF6347", "8A2BE2"]
    
    color_index = (message_number - 1) % len(color_palette)
    return f"[C][B][{color_palette[color_index]}]{message_text}"    

def get_random_avatar():
	avatar_list = [
         '902050001', '902050002', '902050003', '902039016', '902050004', 
        '902047011', '902047010', '902049015', '902050006', '902049020'
    ]
	random_avatar = random.choice(avatar_list)
	return  random_avatar

async def xSEndMsgsQQ(Msg , id , K , V):
    fields = {1: id , 2: id , 4: Msg , 5: 1756580149, 7: 2, 8: 904990072, 9: {1: "xBe4!sTo - C4", 2: int(get_random_avatar()), 4: 330, 5: 1001000001, 8: "xBe4!sTo - C4", 10: 1, 11: 1, 13: {1: 2}, 14: {1: 1158053040, 2: 8, 3: "\u0010\u0015\b\n\u000b\u0015\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"}}, 10: "en", 13: {2: 2, 3: 1}}
    Pk = (await CrEaTe_ProTo(fields)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return await GeneRaTePk(Pk, '1201', K, V)     

async def Create_xr_room_packet_fixed__(room_id, key, iv):
    """FIXED: Room chat packets must use Whisper connection"""
    random_color = generate_random_hex_color()

    fields = {
        1: 1,
        2: {
            1: 2579372095,  # Bot UID
            2: int(room_id),
            3: 3,  # Chat type 3 = room chat
            4: f"[FFFFFF]Hello",
            5: int(time.time()),  # Current timestamp, not hardcoded
            7: 2,
            9: {
                1: "XR SUPER ",
                2: bunner_(),   
                4: 228,
                7: 1,
            },
            10: "ar",  # Language (arabic? change to "en" if needed)
            13: {
                2: 1,
                3: 1
            }
        }
    }

    # Convert to protobuf hex
    proto_hex = (await CrEaTe_ProTo(fields)).hex()
    
    print(f"📦 Room chat proto: {len(proto_hex)//2} bytes")
    print(f"Hex start: {proto_hex[:50]}...")
    
    # CRITICAL FIX: Room chat uses Whisper connection (12xx headers)
    # Try different packet types for Whisper
    packet_type = "1215"  # Whisper connection for chat
    
    # Generate final encrypted packet
    final_packet = await GeneRaTePk(proto_hex, packet_type, key, iv)
    
    return final_packet

async def send_wave_messages(message_text, repeats, chat_id, key, iv, region):
    """Send message in wave pattern: expanding then shrinking"""
    global msg_spam_running
    
    count = 0
    total_cycles = 0
    
    while msg_spam_running and total_cycles < repeats:
        try:
            # EXPANDING phase (h, he, hel, hell, hello)
            for i in range(1, len(message_text) + 1):
                if not msg_spam_running:
                    break
                    
                partial_msg = message_text[:i]
                colorful_msg = await get_colorful_message(partial_msg, i)
                
                msg_packet = await xSEndMsgsQ(colorful_msg, int(chat_id), key, iv)
                if msg_packet and whisper_writer:
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', msg_packet)
                    count += 1
                    print(f"✅ Wave #{total_cycles+1} - Expanding: '{partial_msg}'")
                    await asyncio.sleep(0.1)
            
            # SHRINKING phase (hell, hel, he, h)
            for i in range(len(message_text) - 1, 0, -1):
                if not msg_spam_running:
                    break
                    
                partial_msg = message_text[:i]
                colorful_msg = await get_colorful_message(partial_msg, i)
                
                msg_packet = await xSEndMsgsQQ(colorful_msg, int(chat_id), key, iv)
                if msg_packet and whisper_writer:
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', msg_packet)
                    count += 1
                    print(f"✅ Wave #{total_cycles+1} - Shrinking: '{partial_msg}'")
                    await asyncio.sleep(0.1)
            
            total_cycles += 1
            print(f"🌀 Completed wave cycle {total_cycles}/{repeats}")
            
        except Exception as e:
            print(f"❌ Error in wave messages: {e}")
            break
    
    return count, total_cycles

async def handle_wave_completion(spam_task, message_text, repeats, sender_uid, chat_id, chat_type, key, iv):
    """Handle completion of wave messages"""
    try:
        message_count, cycles_completed = await spam_task
        
        total_per_cycle = (len(message_text) * 2) - 2
        expected_total = total_per_cycle * repeats
        

        
    except asyncio.CancelledError:
        cancel_msg = f"[B][C][FFFF00]🛑 WAVE CANCELLED!\n"
        await safe_send_message(chat_type, cancel_msg, sender_uid, chat_id, key, iv)

# Replace the msg_spam_loop function with this simpler version:
async def msg_spam_loop(message_text, times, chat_id, key, iv, region):
    """Send message multiple times in team chat using existing functions"""
    global msg_spam_running
    
    count = 0
    
    while msg_spam_running and count < times:
        try:
            # Use the existing xSEndMsgsQ function from xC4.py
            # This is for squad chat (chat_type 0)
            # Replace: msg_packet = await xSEndMsgsQ(message_text, int(chat_id), key, iv)
            # With:
            colorful_message = await get_colorful_message(message_text, count + 1)
            msg_packet = await xSEndMsgsQQ(colorful_message, int(chat_id), key, iv)
            
            if not msg_packet:
                print("❌ Failed to create message packet")
                break
                
            # Send the packet - use ChaT connection type for squad messages
            if whisper_writer:
                await SEndPacKeT(whisper_writer, online_writer, 'ChaT', msg_packet)
                count += 1
                print(f"✅ Sent message #{count}/{times} to squad chat: '{message_text}'")
                
                # Adjust delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Error in msg spam loop: {e}")
            import traceback
            traceback.print_exc()
            break
    
    return count

# Update the command handler to use the correct chat_id
# In the TcPChaT function, update the /massage command:



# Also, let's improve the handle_msg_spam_completion function:
async def handle_msg_spam_completion(spam_task, message_text, times, sender_uid, chat_id, chat_type, key, iv):
    """Handle completion of message spam and send final message"""
    try:
        actual_times = await spam_task
        
        # Send completion message
        if actual_times >= times:
            completion_msg = f"[B][C][FFFF00]✅ MESSAGE SPAM COMPLETED!\n"
            completion_msg += f"[FFFFFF]📝 Message: {message_text}\n"
            completion_msg += f"[FFFFFF]📊 Requested: {times} times\n"
            completion_msg += f"[FFFFFF]✅ Sent: {actual_times} times\n"
            completion_msg += f"[FFFF00]✓ Success rate: 100%\n"
            completion_msg += f"[FFFFFF]💬 Check squad chat to see messages!\n"
        elif actual_times > 0:
            completion_msg = f"[B][C][FFFF00]⚠️ MESSAGE SPAM PARTIALLY COMPLETED!\n"
            completion_msg += f"[FFFFFF]📝 Message: {message_text}\n"
            completion_msg += f"[FFFFFF]📊 Requested: {times} times\n"
            completion_msg += f"[FFFFFF]⚠️ Sent: {actual_times} times\n"
            completion_msg += f"[FFFF00]↯ Success rate: {(actual_times/times)*100:.1f}%\n"
            completion_msg += f"[FFFFFF]💬 Check squad chat to see messages!\n"
        else:
            completion_msg = f"[B][C][FF0000]❌ MESSAGE SPAM FAILED!\n"
            completion_msg += f"[FFFFFF]📝 Message: {message_text}\n"
            completion_msg += f"[FFFFFF]📊 Requested: {times} times\n"
            completion_msg += f"[FFFFFF]❌ Sent: 0 times\n"
            completion_msg += f"[FF0000]✗ Failed to send any messages\n"
            completion_msg += f"[FFFFFF]🔧 Possible issues:\n"
            completion_msg += f"[FFFFFF]1. Bot not in a squad\n"
            completion_msg += f"[FFFFFF]2. Invalid chat_id\n"
            completion_msg += f"[FFFFFF]3. Connection error\n"
        
        await safe_send_message(chat_type, completion_msg, sender_uid, chat_id, key, iv)
        
    except asyncio.CancelledError:
        print("Message spam was cancelled by user")
        cancel_msg = f"[B][C][FFFF00]🛑 MESSAGE SPAM CANCELLED!\n[FFFFFF]Message spam was stopped by user command.\n"
        await safe_send_message(chat_type, cancel_msg, sender_uid, chat_id, key, iv)
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ ERROR in message spam completion: {str(e)}\n"
        await safe_send_message(chat_type, error_msg, sender_uid, chat_id, key, iv)
        
async def send_msg_in_room_async(Msg, room_id, key, iv):
    """Converted to your async TCP format"""
    from datetime import datetime
    sticker_value = get_random_sticker()
    
    fields = {
        1: 1,
        2: {
            1: int(room_id),
            2: int(room_id),
            3: 3,
            4: f"{Msg}",
            5: int(datetime.now().timestamp()),
            7: 2,
            8: f'{{"StickerStr" : "{sticker_value}", "type":"Sticker"}}',
            9: {
                1: "byte bot",
                2: int(await xBunnEr()),  # Changed to your function
                4: 329,
                7: 1,
            },
            10: "en",
            13: {2: 1, 3: 1},
        },
    }

    # Create protobuf packet using your function
    packet = await CrEaTe_ProTo(fields)
    
    # Convert to hex and add "7200"
    packet_hex = packet.hex() + "7200"

    # Encrypt using your function
    encrypted_packet = await encrypt_packet(packet_hex, key, iv)
    
    # Calculate header length
    header_length = len(encrypted_packet) // 2
    header_length_final = await DecodE_HeX(header_length)

    # Determine format based on header length
    if len(header_length_final) == 2:
        final_packet = "1215000000" + header_length_final + encrypted_packet
        return bytes.fromhex(final_packet)

    elif len(header_length_final) == 3:
        final_packet = "121500000" + header_length_final + encrypted_packet
        return bytes.fromhex(final_packet)

    elif len(header_length_final) == 4:
        final_packet = "12150000" + header_length_final + encrypted_packet
        return bytes.fromhex(final_packet)

    elif len(header_length_final) == 5:
        final_packet = "12150000" + header_length_final + encrypted_packet
        return bytes.fromhex(final_packet)

# Command handler for room messages:
async def create_training_start_packet(key, iv, region):
    """Create packet to start training mode in Free Fire"""
    
    try:

        
        fields = {
            1: 39,  # Packet type for training (0x27 = 39)
            2: {
                1: 1,  # Action type (1 = start/enter)
                2: 1,  # Training mode type (1 = normal training)
                3: 0,  # Unknown flag
                4: 0,  # Unknown flag
                # The rest appears to be encrypted training data
                5: {
                    1: bytes.fromhex("79 2c 59 bf e0 5b be a6 00 ae 89 a5 26 4f 55 6f"),
                    2: bytes.fromhex("40 e5 e3 52 aa e2 46 26 ef e8 ac 5c 6c b1 db 9e"),
                    3: bytes.fromhex("87 09 4d aa ed c2 eb da")
                }
            }
        }
        
        # Alternative simpler structure (more likely):
        fields_simple = {
            1: 39,  # Training packet type
            2: {
                1: 1,   # Start training command
                2: 0,   # Training ground ID (0 = default)
                3: 1,   # Mode (1 = training)
                4: {    # Training settings
                    1: 1,  # Weapons enabled
                    2: 1,  # Bots enabled
                    3: 0,  # Unlimited ammo
                    4: 1,  # Health regen
                    5: 0   # God mode
                }
            }
        }
        
        # Let's try the simple structure first
        packet = await CrEaTe_ProTo(fields_simple)
        packet_hex = packet.hex()
        
        print(f"📦 Created training packet: {packet_hex[:50]}...")
        
        # Determine packet header based on region
        if region.lower() == "ind":
            packet_type = '0514'
        elif region.lower() == "bd":
            packet_type = "0519"
        else:
            packet_type = "0515"
            
        # Generate final encrypted packet
        final_packet = await GeneRaTePk(packet_hex, packet_type, key, iv)
        
        print(f"✅ Training start packet created")
        return final_packet
        
    except Exception as e:
        print(f"❌ Error creating training packet: {e}")
        import traceback
        traceback.print_exc()
        return None


async def start_training_mode(key, iv, region):
    """Start training mode - sends the training start packet"""
    
    try:
        training_packet = await create_training_start_packet(key, iv, region)
        
        if training_packet:
            # Send to Online connection
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', training_packet)
            print("🎮 Training mode start packet sent!")
            return True
        else:
            print("❌ Failed to create training packet")
            return False
            
    except Exception as e:
        print(f"❌ Error starting training: {e}")
        return False


# Add this command handler to your TcPChaT function:
async def handle_training_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /train command to start training mode"""
    
    parts = inPuTMsG.strip().split()
    
    if len(parts) == 1:
        # Just /train - start default training
        initial_msg = f"[B][C][FFFF00]🎮 Starting training mode...\n"
        await safe_send_message(chat_type, initial_msg, uid, chat_id, key, iv)
        
        success = await start_training_mode(key, iv, region)
        
        if success:
            success_msg = f"[B][C][FFFF00]✅ Training mode started!\n🏋️ Enter training ground to practice!\n"
        else:
            success_msg = f"[B][C][FF0000]❌ Failed to start training!\n"
            
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
        
    elif len(parts) == 2 and parts[1] == "custom":
        # /train custom - custom training settings
        initial_msg = f"[B][C][FFFF00]🎮 Starting custom training...\n"
        await safe_send_message(chat_type, initial_msg, uid, chat_id, key, iv)
        
        # You can add custom training settings here
        success = await start_training_mode(key, iv, region)
        
        if success:
            success_msg = f"[B][C][FFFF00]✅ Custom training started!\n⚙️ Custom settings applied!\n"
        else:
            success_msg = f"[B][C][FF0000]❌ Failed to start custom training!\n"
            
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
        
    else:
        error_msg = f"[B][C][FF0000]❌ Usage: /train [custom]\nExamples:\n/train - Start default training\n/train custom - Custom training\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)

async def lag_team_loop(team_code, key, iv, region):
    """Rapid join/leave loop to create lag"""
    global lag_running
    count = 0
    
    while lag_running:
        try:
            # Join the team
            join_packet = await GenJoinSquadsPacket(team_code, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
            
            # Very short delay before leaving
            await asyncio.sleep(0.01)  # 10 milliseconds
            
            # Leave the team
            leave_packet = await ExiT(None, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)
            
            count += 1
            print(f"Lag cycle #{count} completed for team: {team_code}")
            
            # Short delay before next cycle
            await asyncio.sleep(0.01)  # 10 milliseconds between cycles
            
        except Exception as e:
            print(f"Error in lag loop: {e}")
            # Continue the loop even if there's an error
            await asyncio.sleep(0.1)
 
####################################

#Clan-info-by-clan-id
def Get_clan_info(clan_id):
    try:
        url = f"https://get-clan-info.vercel.app/get_clan_info?clan_id={clan_id}"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            msg = f""" 
[11EAFD][b][c]
°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°
▶▶▶▶GUILD DETAILS◀◀◀◀
Achievements: {data['achievements']}\n\n
Balance : {fix_num(data['balance'])}\n\n
Clan Name : {data['clan_name']}\n\n
Expire Time : {fix_num(data['guild_details']['expire_time'])}\n\n
Members Online : {fix_num(data['guild_details']['members_online'])}\n\n
Regional : {data['guild_details']['regional']}\n\n
Reward Time : {fix_num(data['guild_details']['reward_time'])}\n\n
Total Members : {fix_num(data['guild_details']['total_members'])}\n\n
ID : {fix_num(data['id'])}\n\n
Last Active : {fix_num(data['last_active'])}\n\n
Level : {fix_num(data['level'])}\n\n
Rank : {fix_num(data['rank'])}\n\n
Region : {data['region']}\n\n
Score : {fix_num(data['score'])}\n\n
Timestamp1 : {fix_num(data['timestamp1'])}\n\n
Timestamp2 : {fix_num(data['timestamp2'])}\n\n
Welcome Message: {data['welcome_message']}\n\n
XP: {fix_num(data['xp'])}\n\n
°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°
            """
            return msg
        else:
            msg = """
[11EAFD][b][c]
°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°
Failed to get info, please try again later!!

°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°
            """
            return msg
    except:
        pass

#CHAT WITH AI
def talk_with_ai(question):
    url = f""
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        msg = data["message"]["responce"]
        return msg
    else:
        return "An error occurred while connecting to the server."
#SPAM REQUESTS
def spam_requests(player_id):
    # This URL now correctly points to the Flask app you provided
    url = f"http://217.154.114.227:10468/like?uid={uid}&server_name=BD&password=MAHIR@123"
    try:
        res = requests.get(url, timeout=20) # Added a timeout
        if res.status_code == 200:
            data = res.json()
            # Return a more descriptive message based on the API's JSON response
            return f"API Status: Success [{data.get('success_count', 0)}] Failed [{data.get('failed_count', 0)}]"
        else:
            # Return the error status from the API
            return f"API Error: Status {res.status_code}"
    except requests.exceptions.RequestException as e:
        # Handle cases where the API isn't running or is unreachable
        print(f"Could not connect to spam API: {e}")
        return "Failed to connect to spam API."
####################################

# ** NEW INFO FUNCTION using the new API **
def newinfo(uid):
    # Base URL without parameters
    url = "https://mafuuuu-info-api.vercel.app/mafu-info?uid="
    # Parameters dictionary - this is the robust way to do it
    params = {
        'uid': uid,
        'server': server2,  # Hardcoded to bd as requested
        'key': key2
    }
    try:
        # Pass the parameters to requests.get()
        response = requests.get(url, params=params, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            # Check if the expected data structure is in the response
            if "basicInfo" in data:
                return {"status": "ok", "data": data}
            else:
                # The API returned 200, but the data is not what we expect (e.g., error message in JSON)
                return {"status": "error", "message": data.get("error", "Invalid ID or data not found.")}
        else:
            # The API returned an error status code (e.g., 404, 500)
            try:
                # Try to get a specific error message from the API's response
                error_msg = response.json().get('error', f"API returned status {response.status}")
                return {"status": "error", "message": error_msg}
            except ValueError:
                # If the error response is not JSON
                return {"status": "error", "message": f"API returned status {response.status}"}

    except requests.exceptions.RequestException as e:
        # Handle network errors (e.g., timeout, no connection)
        return {"status": "error", "message": f"Network error: {str(e)}"}
    except ValueError: 
        # Handle cases where the response is not valid JSON
        return {"status": "error", "message": "Invalid JSON response from API."}
        

####################################
async def bundle_packet_async(bundle_id, key, iv, region="ind"):
    """Create bundle packet"""
    fields = {
        1: 88,
        2: {
            1: {
                1: bundle_id,
                2: 1
            },
            2: 2
        }
    }
    
    # Use your CrEaTe_ProTo function
    packet = await CrEaTe_ProTo(fields)
    packet_hex = packet.hex()
    
    # Use your encrypt_packet function
    encrypted = await encrypt_packet(packet_hex, key, iv)
    
    # Use your DecodE_HeX function
    header_length = len(encrypted) // 2
    header_length_hex = await DecodE_HeX(header_length)
    
    # Build final packet based on region
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"
    
    # Determine header based on length
    if len(header_length_hex) == 2:
        final_header = f"{packet_type}000000"
    elif len(header_length_hex) == 3:
        final_header = f"{packet_type}00000"
    elif len(header_length_hex) == 4:
        final_header = f"{packet_type}0000"
    elif len(header_length_hex) == 5:
        final_header = f"{packet_type}000"
    else:
        final_header = f"{packet_type}000000"
    
    final_packet_hex = final_header + header_length_hex + encrypted
    return bytes.fromhex(final_packet_hex)

async def base_to_hex(value):
    hex_val = format(value, 'x')
    
    # যদি odd length হয় → সামনে 0 add
    if len(hex_val) % 2 != 0:
        hex_val = '0' + hex_val
        
    return hex_val

async def animation_packet(bundle_id, key, iv):
    fields = {
        1: 88,
        2: {
            1: {
                1: int(bundle_id),
            }
        }
    }

    proto_bytes = await CrEaTe_ProTo(fields)
    packet_hex = proto_bytes.hex()

    encrypted_packet = await encrypt_packet(packet_hex, key, iv)

    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)

    if len(packet_length_hex) == 2:
        header = "0519000000"
    elif len(packet_length_hex) == 3:
        header = "051900000"
    elif len(packet_length_hex) == 4:
        header = "05190000"
    elif len(packet_length_hex) == 5:
        header = "0519000"
    else:
        header = "0519000000"

    final_packet = header + packet_length_hex + encrypted_packet

    return bytes.fromhex(final_packet)

	
#ADDING-100-LIKES-IN-24H
def send_likes(uid):
    try:
        likes_api_response = requests.get(
             f"http://217.154.114.227:10468/like?uid={uid}&server_name=BD&password=MAHIR@123",
             timeout=10
             )
      
      
        if likes_api_response.status_code != 200:
            return f"""
[C][B][FF0000]━━━━━
[FFFFFF]Like API Error!
Status Code: {likes_api_response.status_code}
Please check if the uid is correct.
━━━━━
"""

        api_json_response = likes_api_response.json()

        player_name = api_json_response.get('PlayerNickname', 'Unknown')
        likes_before = api_json_response.get('LikesbeforeCommand', 0)
        likes_after = api_json_response.get('LikesafterCommand', 0)
        likes_added = api_json_response.get('LikesGivenByAPI', 0)
        status = api_json_response.get('status', 0)

        if status == 1 and likes_added > 0:
            # ✅ Success
            return f"""
[C][B][11EAFD]‎━━━━━━━━━━━━
[FFFFFF]Likes Status:

[FFFF00]Likes Sent Successfully!

[FFFFFF]Player Name : [FFFF00]{player_name}  
[FFFFFF]Likes Added : [FFFF00]{likes_added}  
[FFFFFF]Likes Before : [FFFF00]{likes_before}  
[FFFFFF]Likes After : [FFFF00]{likes_after}  
[C][B][11EAFD]‎━━━━━━━━━━━━
[C][B][FFB300]Subscribe: [FFFFFF]SPIDEERIO YT [FFFF00]!!
"""
        elif status == 2 or likes_before == likes_after:
            # 🚫 Already claimed / Maxed
            return f"""
[C][B][FF0000]━━━━━━━━━━━━

[FFFFFF]No Likes Sent!

[FF0000]You have already taken likes with this UID.
Try again after 24 hours.

[FFFFFF]Player Name : [FF0000]{player_name}  
[FFFFFF]Likes Before : [FF0000]{likes_before}  
[FFFFFF]Likes After : [FF0000]{likes_after}  
[C][B][FF0000]━━━━━━━━━━━━
"""
        else:
            # ❓ Unexpected case
            return f"""
[C][B][FF0000]━━━━━━━━━━━━
[FFFFFF]Unexpected Response!
Something went wrong.

Please try again or contact support.
━━━━━━━━━━━━
"""

    except requests.exceptions.RequestException:
        return """
[C][B][FF0000]━━━━━
[FFFFFF]Like API Connection Failed!
Is the API server (app.py) running?
━━━━━
"""
    except Exception as e:
        return f"""
[C][B][FF0000]━━━━━
[FFFFFF]An unexpected error occurred:
[FF0000]{str(e)}
━━━━━
"""
####################################
#CHECK ACCOUNT IS BANNED

Hr = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB54"}

# ---- Random Colores ----
def get_random_color():
    colors = [
        "[FF0000]", "[FFFF00]", "[0000FF]", "[FFFF00]", "[FF00FF]", "[00FFFF]", "[FFFFFF]", "[FFA500]",
        "[A52A2A]", "[800080]", "[000000]", "[808080]", "[C0C0C0]", "[FFC0CB]", "[FFD700]", "[ADD8E6]",
        "[90EE90]", "[D2691E]", "[DC143C]", "[00CED1]", "[9400D3]", "[F08080]", "[20B2AA]", "[FF1493]",
        "[7CFC00]", "[B22222]", "[FF4500]", "[DAA520]", "[00BFFF]", "[00FF7F]", "[4682B4]", "[6495ED]",
        "[5F9EA0]", "[DDA0DD]", "[E6E6FA]", "[B0C4DE]", "[556B2F]", "[8FBC8F]", "[2E8B57]", "[3CB371]",
        "[6B8E23]", "[808000]", "[B8860B]", "[CD5C5C]", "[8B0000]", "[FF6347]", "[FF8C00]", "[BDB76B]",
        "[9932CC]", "[8A2BE2]", "[4B0082]", "[6A5ACD]", "[7B68EE]", "[4169E1]", "[1E90FF]", "[191970]",
        "[00008B]", "[000080]", "[008080]", "[008B8B]", "[B0E0E6]", "[AFEEEE]", "[E0FFFF]", "[F5F5DC]",
        "[FAEBD7]"
    ]
    return random.choice(colors)
    
def get_random_evo_emote():
    """Return random evo emote ID"""
    evo_emotes = [
        909000063,  # AK
        909000068,  # SCAR  
        909000075,  # 1st MP40
        909040010,  # 2nd MP40
        909000081,  # 1st M1014
        909039011,  # 2nd M1014
        909000085,  # XM8
        909000090,  # Famas
        909000098,  # UMP
        909035007,  # M1887
        909042008,  # Woodpecker
        909041005,  # Groza
        909033001,  # M4A1
        909038010,  # Thompson
        909038012,  # G18
        909045001,  # Parafal
        909049010,  # P90
        909051003   # M60
    ]
    return random.choice(evo_emotes)
    
async def extract_uid_from_emote_packet(data_hex, key, iv):
    """Extract UID from emote packet (the sender)"""
    try:
        # Decrypt the packet
        packet = await DeCode_PackEt(data_hex[10:])
        packet_json = json.loads(packet)
        
        print(f"📦 Analyzing packet structure: {json.dumps(packet_json, indent=2)[:200]}...")
        
        # PATTERN 1: Your Emote_k() structure (Type 21)
        if packet_json.get('1') == 21:
            if ('2' in packet_json and 'data' in packet_json['2'] and
                '5' in packet_json['2']['data'] and 'data' in packet_json['2']['data']['5']):
                
                nested = packet_json['2']['data']['5']['data']
                if '1' in nested:
                    uid = nested['1']['data']
                    print(f"✅ Extracted UID from pattern 21: {uid}")
                    return uid
        
        # PATTERN 2: Direct emote structure
        elif packet_json.get('1') == 26:
            if ('2' in packet_json and 'data' in packet_json['2'] and
                '1' in packet_json['2']['data']):
                
                uid = packet_json['2']['data']['1']['data']
                print(f"✅ Extracted UID from pattern 26: {uid}")
                return uid
        
        # PATTERN 3: Try common paths
        for path in ['2/1', '5/1', '2/data/1', '5/data/1']:
            try:
                uid = get_nested_value(packet_json, path)
                if uid and str(uid).isdigit() and len(str(uid)) > 6:
                    print(f"✅ Extracted UID from path {path}: {uid}")
                    return uid
            except:
                pass
        
        print(f"❌ Could not extract UID from packet")
        return None
        
    except Exception as e:
        print(f"❌ UID extraction error: {e}")
        return None

def get_nested_value(data, path):
    """Get value from nested JSON path like '2/5/1'"""
    keys = path.split('/')
    current = data
    
    for key in keys:
        if key.isdigit():
            key = str(key)  # JSON keys are strings
        
        if key in current and 'data' in current[key]:
            current = current[key]['data']
        else:
            return None
    
    return current

async def ultra_quick_emote_attack(team_code, emote_id, target_uid, key, iv, region):
    """Join team, authenticate chat, perform emote, and leave automatically"""
    try:
        # Step 1: Join the team
        join_packet = await GenJoinSquadsPacket(team_code, key, iv)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
        print(f"🤖 Joined team: {team_code}")
        
        # Wait for team data and chat authentication
        #await asyncio.sleep(0.01)  # Increased to ensure proper connection
        
        # Step 2: The bot needs to be detected in the team and authenticate chat
        # This happens automatically in TcPOnLine, but we need to wait for it
        
        # Step 3: Perform emote to target UID
        emote_packet = await Emote_k(int(target_uid), int(emote_id), key, iv, region)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_packet)
        print(f"🎭 Performed emote {emote_id} to UID {target_uid}")
        
        # Wait for emote to register
        #await asyncio.sleep(0.01)
        
        # Step 4: Leave the team
        leave_packet = await ExiT(None, key, iv)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)
        print(f"🚪 Left team: {team_code}")
        
        return True, f"Quick emote attack completed! Sent emote to UID {target_uid}"
        
    except Exception as e:
        return False, f"Quick emote attack failed: {str(e)}"
        
        
async def encrypted_proto(encoded_hex):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(encoded_hex, AES.block_size)
    encrypted_payload = cipher.encrypt(padded_message)
    return encrypted_payload
    
async def GeNeRaTeAccEss(uid , password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": (await Ua()),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close"}
    data = {
        "uid": uid,
        "password": password,
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=Hr, data=data) as response:
            if response.status != 200: return "Failed to get access token"
            data = await response.json()
            open_id = data.get("open_id")
            access_token = data.get("access_token")
            return (open_id, access_token) if open_id and access_token else (None, None)

async def EncRypTMajoRLoGin(open_id, access_token):
    major_login = MajoRLoGinrEq_pb2.MajorLogin()
    major_login.event_time = str(datetime.now())[:-7]
    major_login.game_name = "free fire"
    major_login.platform_id = 2
    major_login.client_version = "1.126.2"
    major_login.client_version_code = "2024010012"
    major_login.system_software = "Android OS 11 / API-30 (RQ3A.210805.001)"
    major_login.system_hardware = "Handheld"
    major_login.device_type = "Handheld"
    major_login.telecom_operator = "Verizon"
    major_login.network_operator_a = "Verizon"
    major_login.network_type = "WIFI"
    major_login.network_type_a = "WIFI"
    major_login.screen_width = 1080
    major_login.screen_height = 2400
    major_login.screen_dpi = "440"
    major_login.processor_details = "ARMv8"
    major_login.cpu_type = 2
    major_login.cpu_architecture = "64"
    major_login.memory = 6144
    major_login.gpu_renderer = "Adreno (TM) 650"
    major_login.gpu_version = "OpenGL ES 3.2 V@1.50"
    major_login.graphics_api = "OpenGLES3"
    major_login.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    major_login.client_ip = ""
    major_login.language = "en"
    major_login.open_id = open_id
    major_login.open_id_type = "4"
    major_login.login_open_id_type = 4
    major_login.access_token = access_token
    major_login.login_by = 3
    major_login.platform_sdk_id = 2
    major_login.origin_platform_type = "4"
    major_login.primary_platform_type = "4"
    memory_available = major_login.memory_available
    memory_available.version = 55
    memory_available.hidden_value = 81
    major_login.external_storage_total = 128512
    major_login.external_storage_available = random.randint(38000, 52000)
    major_login.internal_storage_total = 110731
    major_login.internal_storage_available = random.randint(18000, 32000)
    major_login.game_disk_storage_total = 26628
    major_login.game_disk_storage_available = random.randint(18000, 25000)
    major_login.external_sdcard_total_storage = 119234
    major_login.external_sdcard_avail_storage = random.randint(25000, 60000)
    major_login.library_path = "/data/app/~~random/base.apk"
    major_login.library_token = "hash|base.apk"
    major_login.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    major_login.supported_astc_bitset = 16383
    major_login.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    major_login.loading_time = random.randint(9000, 18000)
    major_login.release_channel = "android"
    major_login.channel_type = 3
    major_login.reg_avatar = 1
    major_login.if_push = 1
    major_login.is_vpn = 0
    major_login.android_engine_init_flag = 110009
    string = major_login.SerializeToString()
    return  await encrypted_proto(string)

async def MajorLogin(payload):
    url = "https://loginbp.ggwhitehawk.com/MajorLogin",
                "https://loginbp.ggpolarbear.com/MajorLogin",
                "https://loginbp.ggblueshark.com/MajorLogin"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as response:
            if response.status == 200: return await response.read()
            return None

async def GetLoginData(base_url, payload, token):
    url = f"{base_url}/GetLoginData"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    Hr['Authorization']= f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=Hr, ssl=ssl_context) as response:
            if response.status == 200: return await response.read()
            return None

async def DecRypTMajoRLoGin(MajoRLoGinResPonsE):
    proto = MajoRLoGinrEs_pb2.MajorLoginRes()
    proto.ParseFromString(MajoRLoGinResPonsE)
    return proto

async def DecRypTLoGinDaTa(LoGinDaTa):
    proto = PorTs_pb2.GetLoginData()
    proto.ParseFromString(LoGinDaTa)
    return proto

async def DecodeWhisperMessage(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = DEcwHisPErMsG_pb2.DecodeWhisper()
    proto.ParseFromString(packet)
    return proto
    
async def decode_team_packet(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = sQ_pb2.recieved_chat()
    proto.ParseFromString(packet)
    return proto
    
async def xAuThSTarTuP(TarGeT, token, timestamp, key, iv):
    uid_hex = hex(TarGeT)[2:]
    uid_length = len(uid_hex)
    encrypted_timestamp = await DecodE_HeX(timestamp)
    encrypted_account_token = token.encode().hex()
    encrypted_packet = await EnC_PacKeT(encrypted_account_token, key, iv)
    encrypted_packet_length = hex(len(encrypted_packet) // 2)[2:]
    if uid_length == 9: headers = '0000000'
    elif uid_length == 8: headers = '00000000'
    elif uid_length == 10: headers = '000000'
    elif uid_length == 7: headers = '000000000'
    else: print('Unexpected length') ; headers = '0000000'
    return f"0115{headers}{uid_hex}{encrypted_timestamp}00000{encrypted_packet_length}{encrypted_packet}"
    

async def cHTypE(H):
    """Detect chat type including custom rooms"""
    if not H: 
        return 'Squid'
    elif H == 1: 
        return 'CLan'
    elif H == 2: 
        return 'PrivaTe'
    elif H == 3: 
        return 'CustomRoom'  # Custom room chat type
    else:
        return 'Squid'  # Default fallback
    
async def SEndMsG(H, message, Uid, chat_id, key, iv, region):
    """Send message to any chat type including custom rooms"""
    TypE = await cHTypE(H)
    
    if TypE == 'Squid': 
        msg_packet = await xSEndMsgsQ(message, chat_id, key, iv)
    elif TypE == 'CLan': 
        msg_packet = await xSEndMsg(message, 1, chat_id, chat_id, key, iv)
    elif TypE == 'PrivaTe': 
        msg_packet = await xSEndMsg(message, 2, Uid, Uid, key, iv)
    else:
        # Fallback to squad chat
        msg_packet = await xSEndMsgsQ(message, chat_id, key, iv)
        
    return msg_packet
    
    
async def SEndPacKeT(OnLinE , ChaT , TypE , PacKeT):
    if TypE == 'ChaT' and ChaT: whisper_writer.write(PacKeT) ; await whisper_writer.drain()
    elif TypE == 'OnLine': online_writer.write(PacKeT) ; await online_writer.drain()
    else: return 'UnsoPorTed TypE ! >> ErrrroR (:():)' 

async def safe_send_message(chat_type, message, target_uid, chat_id, key, iv, max_retries=3, region="ind"):
    """Enhanced safe send message that works with custom rooms"""
    for attempt in range(max_retries):
        try:
            P = await SEndMsG(chat_type, message, target_uid, chat_id, key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                
            print(f"✅ Message sent successfully to chat type {chat_type} (attempt {attempt + 1})")
            return True
        except Exception as e:
            print(f"❌ Failed to send message (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
    return False

async def fast_emote_spam(uids, emote_id, key, iv, region):
    """Fast emote spam function that sends emotes rapidly"""
    global fast_spam_running
    count = 0
    max_count = 25  # Spam 25 times
    
    while fast_spam_running and count < max_count:
        for uid in uids:
            try:
                uid_int = int(uid)
                H = await Emote_k(uid_int, int(emote_id), key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
            except Exception as e:
                print(f"Error in fast_emote_spam for uid {uid}: {e}")
        
        count += 1
        await asyncio.sleep(0.1)  # 0.1 seconds interval between spam cycles

# NEW FUNCTION: Custom emote spam with specified times
async def custom_emote_spam(uid, emote_id, times, key, iv, region):
    """Custom emote spam function that sends emotes specified number of times"""
    global custom_spam_running
    count = 0
    
    while custom_spam_running and count < times:
        try:
            uid_int = int(uid)
            H = await Emote_k(uid_int, int(emote_id), key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
            count += 1
            await asyncio.sleep(0.0000001)  # 0.1 seconds interval between emotes
        except Exception as e:
            print(f"Error in custom_emote_spam for uid {uid}: {e}")
            break

async def create_level_up_bot_connection(key, iv, region):
    """Create a separate connection for level-up bot"""
    try:
        # This would use a different bot account
        # For now, we'll use the main bot
        print("🤖 Level-up bot connection initialized")
        return True
    except Exception as e:
        print(f"❌ Level-up bot connection error: {e}")
        return False

async def level_up_join_team(team_code, key, iv, region):
    """Level-up bot joins the team"""
    try:
        join_packet = await GenJoinSquadsPacket(team_code, key, iv)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
        print(f"🤖 Level-up bot joining team: {team_code}")
        await asyncio.sleep(2)
        return True
    except Exception as e:
        print(f"❌ Level-up bot join error: {e}")
        return False

async def level_up_leave_team(key, iv):
    """Level-up bot leaves the team"""
    try:
        leave_packet = await ExiT(None, key, iv)
        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)
        print("🤖 Level-up bot leaving team")
        await asyncio.sleep(1)
        return True
    except Exception as e:
        print(f"❌ Level-up bot leave error: {e}")
        return False
        
async def level_up_loop(team_code, target_uid, key, iv, region, chat_type, chat_id):
    """Main level-up automation loop"""
    global level_up_running
    
    cycle_count = 0
    max_cycles = 1000  # Safety limit
    
    print(f"🚀 Starting level-up automation for team {team_code}")
    
    while level_up_running and cycle_count < max_cycles:
        try:
            cycle_count += 1
            print(f"🔄 Level-up cycle #{cycle_count}")
            
            # Step 1: Send instruction message
            instruction_msg = f"""[B][C][FFFF00]🔄 LEVEL-UP CYCLE #{cycle_count}

🤖 Bot: Joining your team...
🎮 Action: Will start match
⏱️ After match: Wait {level_up_wait_time} seconds
🔄 Then: Repeat process

📊 Status: Bot is working...
"""
            await safe_send_message(chat_type, instruction_msg, target_uid, chat_id, key, iv)
            
            # Step 2: Join the team
            join_success = await level_up_join_team(team_code, key, iv, region)
            if not join_success:
                print("❌ Failed to join team, retrying...")
                await asyncio.sleep(2)
                continue
            
            # Step 3: Send "ready" message
            ready_msg = f"[B][C][FFFF00]✅ Bot joined! Starting match...\n"
            await safe_send_message(chat_type, ready_msg, target_uid, chat_id, key, iv)
            
            # Step 4: Start the match (spam start packet)
            start_packet = await FS(key, iv)
            spam_duration = 10  # Spam for 10 seconds
            start_time = time.time()
            
            while time.time() - start_time < spam_duration and level_up_running:
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', start_packet)
                await asyncio.sleep(0.2)  # 200ms delay between packets
            
            # Step 5: Wait for match to complete (simulate)
            waiting_msg = f"""[B][C][FFFF00]⏱️ MATCH IN PROGRESS...

⏳ Waiting for match to complete...
🔄 Next cycle starts in {level_up_wait_time} seconds
🤖 Bot remains in team

💡 Let the match complete normally!
"""
            await safe_send_message(chat_type, waiting_msg, target_uid, chat_id, key, iv)
            
            # Step 6: Wait the specified time
            wait_count = 0
            while wait_count < level_up_wait_time and level_up_running:
                await asyncio.sleep(1)
                wait_count += 1
                
                # Progress update every 5 seconds
                if wait_count % 5 == 0:
                    progress_msg = f"[B][C][FFFF00]⏱️ {wait_count}/{level_up_wait_time} seconds waited...\n"
                    await safe_send_message(chat_type, progress_msg, target_uid, chat_id, key, iv)
            
            if not level_up_running:
                break
            
            # Step 7: Leave team
            leave_success = await level_up_leave_team(key, iv)
            
            if leave_success:
                leave_msg = f"[B][C][FF0000]🚪 Bot left team to restart cycle...\n"
                await safe_send_message(chat_type, leave_msg, target_uid, chat_id, key, iv)
            
            # Step 8: Small delay before next cycle
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Error in level-up cycle: {e}")
            # Try to recover
            await level_up_leave_team(key, iv)
            await asyncio.sleep(3)
    
    print("🛑 Level-up automation stopped")

async def Send_Entry_Emote(uid, K, V, emote_id=912038002, session_id=5, trigger_type=1):
    """Send arrival/entry animation emote
    
    Args:
        uid: Target player UID
        K: Encryption key
        V: Initialization vector
        emote_id: Emote ID (default: 912038002 - arrival animation)
        session_id: Session ID (default: 5)
        trigger_type: Trigger type (default: 1 - entry)
    """
    try:
        fields = {
            1: 4,           # Packet ID for entry emotes
            2: int(uid),    # Player UID
            3: int(session_id),     # Session ID
            4: int(emote_id),       # Emote ID
            5: int(trigger_type),   # Trigger Type (1=entry, 2=exit, etc.)
            6: int(uid),    # Repeated UID
            7: 1,           # Static Value
            8: int(uid),    # Repeated UID
            9: int(uid),    # Repeated UID
            10: int(uid),   # Repeated UID
            11: int(uid),   # Repeated UID
        }
        
        # Different arrival animations
        arrival_emotes = {
            "default": 912038002,
        }
        
        # Use provided emote_id or default
        if isinstance(emote_id, str) and emote_id in arrival_emotes:
            fields[4] = arrival_emotes[emote_id]
        
        proto_hex = (await CrEaTe_ProTo(fields)).hex()
        
        # Determine packet type based on region (you might need to pass region)
        # For now using '0515' as in your example
        return await GeneRaTePk(proto_hex, '0515', K, V)
        
    except Exception as e:
        print(f"❌ Error creating entry emote packet: {e}")
        return None



# NEW FUNCTION: Evolution emote spam with mapping
async def evo_emote_spam(uids, number, key, iv, region):
    """Send evolution emotes based on number mapping"""
    try:
        emote_id = EMOTE_MAP.get(int(number))
        if not emote_id:
            return False, f"Invalid number! Use 1-21 only."
        
        success_count = 0
        for uid in uids:
            try:
                uid_int = int(uid)
                H = await Emote_k(uid_int, emote_id, key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                success_count += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error sending evo emote to {uid}: {e}")
        
        return True, f"Sent evolution emote {number} (ID: {emote_id}) to {success_count} player(s)"
    
    except Exception as e:
        return False, f"Error in evo_emote_spam: {str(e)}"



# NEW FUNCTION: Fast evolution emote spam
async def evo_fast_emote_spam(uids, number, key, iv, region):
    """Fast evolution emote spam function"""
    global evo_fast_spam_running
    count = 0
    max_count = 25  # Spam 25 times
    
    emote_id = EMOTE_MAP.get(int(number))
    if not emote_id:
        return False, f"Invalid number! Use 1-21 only."
    
    while evo_fast_spam_running and count < max_count:
        for uid in uids:
            try:
                uid_int = int(uid)
                H = await Emote_k(uid_int, emote_id, key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
            except Exception as e:
                print(f"Error in evo_fast_emote_spam for uid {uid}: {e}")
        
        count += 1
        await asyncio.sleep(0.1)  # CHANGED: 0.5 seconds to 0.1 seconds
    
    return True, f"Completed fast evolution emote spam {count} times"
    
async def send_required_packets(key, iv, region, bot_uid):
    """Send packets required after connection"""
    try:
        # Packet 1: Client info
        fields1 = {
            1: 100,
            2: {
                1: bot_uid,
                2: "2.123.7",  # Game version
                3: "Android",
                4: "en",
            }
        }
        
        # Packet 2: Device info
        fields2 = {
            1: 101,
            2: {
                1: "[FF9000]ABHI",
                2: "1901",
                3: "arm64-v8a",
                4: str(time.time()),
            }
        }
        
        packets = []
        for fields in [fields1, fields2]:
            if region.lower() == "ind":
                packet_type = '0514'
            elif region.lower() == "bd":
                packet_type = "0519"
            else:
                packet_type = "0515"
                
            packet = await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet_type, key, iv)
            packets.append(packet)
        
        return packets
        
    except Exception as e:
        print(f"❌ Required packets error: {e}")
        return []

# NEW FUNCTION: Custom evolution emote spam with specified times
async def evo_custom_emote_spam(uids, number, times, key, iv, region):
    """Custom evolution emote spam with specified repeat times"""
    global evo_custom_spam_running
    count = 0
    
    emote_id = EMOTE_MAP.get(int(number))
    if not emote_id:
        return False, f"Invalid number! Use 1-21 only."
    
    while evo_custom_spam_running and count < times:
        for uid in uids:
            try:
                uid_int = int(uid)
                H = await Emote_k(uid_int, emote_id, key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
            except Exception as e:
                print(f"Error in evo_custom_emote_spam for uid {uid}: {e}")
        
        count += 1
        await asyncio.sleep(0.1)  # CHANGED: 0.5 seconds to 0.1 seconds
    
    return True, f"Completed custom evolution emote spam {count} times"

async def RejectMSGtaxt(squad_owner,uid, key, iv, region="IND"):
    random_banner = f"""
.
.
.










[00FF00]TCP BOT
[FFFF00]WLC TO ꫝʙʜɪㅤGᴍʀ BOT




 """
    fields = {
    1: 5,
    2: {
        1: int(squad_owner),
        2: 1,
        3: int(uid),
        4: random_banner
    }
    }
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"

    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , packet_type , key, iv)

async def send_keep_alive(key, iv, region):
    """Send keep-alive packet to maintain connection"""
    try:
        fields = {
            1: 99,  # Keep-alive packet type
            2: {
                1: int(time.time()),
                2: 1,  # Keep-alive flag
            }
        }
        
        if region.lower() == "ind":
            packet_type = '0514'
        elif region.lower() == "bd":
            packet_type = "0519"
        else:
            packet_type = "0515"
            
        packet = await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet_type, key, iv)
        return packet
    except Exception as e:
        print(f"❌ Keep-alive error: {e}")
        return None

async def ArohiAccepted(uid,code,K,V):
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
            8: "1.126.2",
            9: 3,
            10: 1
            },
            10: str(code),
        }
        }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0515' , K , V)


async def new_lag(key , iv):
    fields = {
        1: 15,
        2: {
            1: 804266360,
            2: 1
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0515' , key , iv)




async def convert_kyro_to_your_system(target_uid, chat_id, key, iv, nickname="rizer", title_id=None):
    """EXACT conversion with customizable title ID"""
    try:
        # Use provided title_id or get random one
        if title_id is None:
            # Get a random title from the list
            available_titles = [905090075, 904990072, 904990069, 905190079]
            title_id = random.choice(available_titles)
        
        # Create fields dictionary with specific title_id
        fields = {
            1: 1,
            2: {
                1: int(target_uid),
                2: int(chat_id),
                5: int(datetime.now().timestamp()),
                8: f'{{"TitleID":{title_id},"type":"Title"}}',  # Use specific title ID
                # ... rest of your fields
                9: {
                    1: f"[C][B][FF0000]{nickname}",
                    2: int(await xBunnEr()),
                    4: 330,
                    5: 102000015,
                    8: "BOT TEAM",
                    10: 1,
                    11: 1,
                    13: {
                        1: 2
                    },
                    14: {
                        1: 1158053040,
                        2: 8,
                        3: b"\x10\x15\x08\x0a\x0b\x15\x0c\x0f\x11\x04\x07\x02\x03\x0d\x0e\x12\x01\x05\x06"
                    }
                },
                10: "en",
                13: {
                    2: 2,
                    3: 1
                },
                14: {}
            }
        }
        
        # ... rest of your existing function
        proto_bytes = await CrEaTe_ProTo(fields)
        packet_hex = proto_bytes.hex()
        
        encrypted_packet = await encrypt_packet(packet_hex, key, iv)
        packet_length = len(encrypted_packet) // 2
        hex_length = f"{packet_length:04x}"
        
        zeros_needed = 6 - len(hex_length)
        packet_prefix = "121500" + ("0" * zeros_needed)
        
        final_packet_hex = packet_prefix + hex_length + encrypted_packet
        final_packet = bytes.fromhex(final_packet_hex)
        
        print(f"✅ Created packet with Title ID: {title_id}")
        return final_packet
        
    except Exception as e:
        print(f"❌ Conversion error: {e}")
        return None
        
def get_random_sticker():
    """
    Randomly select one sticker from available packs
    """

    sticker_packs = [
        # NORMAL STICKERS (1200000001-1 to 24)
        ("1200000001", 1, 24),

        # KELLY EMOJIS (1200000002-1 to 15)
        ("1200000002", 1, 15),

        # MAD CHICKEN (1200000004-1 to 13)
        ("1200000004", 1, 13),
    ]

    pack_id, start, end = random.choice(sticker_packs)
    sticker_no = random.randint(start, end)

    return f"[1={pack_id}-{sticker_no}]"
        
async def send_sticker(target_uid, chat_id, key, iv, nickname="BLACK"):
    """Send Random Sticker using /sticker command"""
    try:
        sticker_value = get_random_sticker()

        fields = {
            1: 1,
            2: {
                1: int(target_uid),
                2: int(chat_id),
                5: int(datetime.now().timestamp()),
                8: f'{{"StickerStr" : "{sticker_value}", "type":"Sticker"}}',
                9: {
                    1: f"[C][B][FF0000]{nickname}",
                    2: int(get_random_avatar()),
                    4: 330,
                    5: 102000015,
                    8: "RIZERR",
                    10: 1,
                    11: 66,
                    12: 66,
                    13: {1: 2},
                    14: {
                        1: 1158053040,
                        2: 8,
                        3: b"\x10\x15\x08\x0a\x0b\x15\x0c\x0f\x11\x04\x07\x02\x03\x0d\x0e\x12\x01\x05\x06"
                    }
                },
                10: "en",
                13: {
                    2: 2,
                    3: 1
                },
                14: {}
            }
        }

        proto_bytes = await CrEaTe_ProTo(fields)
        packet_hex = proto_bytes.hex()

        encrypted_packet = await encrypt_packet(packet_hex, key, iv)
        packet_length = len(encrypted_packet) // 2
        hex_length = f"{packet_length:04x}"

        zeros_needed = 6 - len(hex_length)
        packet_prefix = "121500" + ("0" * zeros_needed)

        final_packet_hex = packet_prefix + hex_length + encrypted_packet
        final_packet = bytes.fromhex(final_packet_hex)

        print(f"✅ Sticker Sent: {sticker_value}")
        return final_packet

    except Exception as e:
        print(f"❌ Sticker error: {e}")
        return None

# Alternative: DIRECT port of your friend's function but with your UID
async def send_kyro_title_adapted(chat_id, key, iv, target_uid, nickname="rizer"):
    """Direct adaptation of your friend's working function"""
    try:
        # Import your proto file (make sure it's in the same directory)
        from kyro_title_pb2 import GenTeamTitle
        
        root = GenTeamTitle()
        root.type = 1
        
        nested_object = root.data
        nested_object.uid = int(target_uid)  # CHANGE: Use target UID
        nested_object.chat_id = int(chat_id)
        nested_object.title = f"{{\"TitleID\":{titles()},\"type\":\"Title\"}}"
        nested_object.timestamp = int(datetime.now().timestamp())
        nested_object.language = "en"
        
        nested_details = nested_object.field9
        nested_details.Nickname = f"[C][B][FF0000]{nickname}"  # CHANGE: Your nickname
        nested_details.avatar_id = int(await xBunnEr())  # Use your function
        nested_details.rank = 330
        nested_details.badge = 102000015
        nested_details.Clan_Name = "ABHI EMPIRE"  # CHANGE: Your clan
        nested_details.field10 = 1
        nested_details.global_rank_pos = 1
        nested_details.badge_info.value = 2
        
        nested_details.prime_info.prime_uid = 1158053040
        nested_details.prime_info.prime_level = 8
        # IMPORTANT: This must be bytes, not string!
        nested_details.prime_info.prime_hex = b"\x10\x15\x08\x0a\x0b\x15\x0c\x0f\x11\x04\x07\x02\x03\x0d\x0e\x12\x01\x05\x06"
        
        nested_options = nested_object.field13
        nested_options.url_type = 2
        nested_options.curl_platform = 1
        
        nested_object.empty_field.SetInParent()
        
        # Serialize
        packet = root.SerializeToString().hex()
        
        # Use YOUR encryption function
        encrypted_packet = await encrypt_packet(packet, key, iv)
        
        # Calculate length
        packet_length = len(encrypted_packet) // 2
        
        # Convert to hex (4 characters with leading zeros)
        hex_length = f"{packet_length:04x}"
        
        # Build packet EXACTLY like your friend
        zeros_needed = 6 - len(hex_length)
        packet_prefix = "121500" + ("0" * zeros_needed)
        
        final_packet_hex = packet_prefix + hex_length + encrypted_packet
        return bytes.fromhex(final_packet_hex)
        
    except Exception as e:
        print(f"❌ Direct adaptation error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def send_all_titles_sequentially(uid, chat_id, key, iv, region, chat_type):
    """Send all titles one by one with 2-second delay"""
    
    # Get all titles
    all_titles = [
        905090075, 904990072, 904990069, 905190079
    ]
    
    total_titles = len(all_titles)
    
    # Send initial message
    start_msg = f"""[B][C][FFFF00]⏳ Sending titles now...
"""
    await safe_send_message(chat_type, start_msg, uid, chat_id, key, iv)
    
    try:
        for index, title_id in enumerate(all_titles):
            title_number = index + 1
            
            # Create progress message
            progress_msg = f"""[B][C][FFFF00]📤 SENDING TITLE {title_number}/{total_titles}


"""
            await safe_send_message(chat_type, progress_msg, uid, chat_id, key, iv)
            
            # Send the actual title using your existing method
            # You'll need to use your existing title sending logic here
            # For example:
            title_packet = await convert_kyro_to_your_system(uid, chat_id, key, iv, nickname="NARUTO-CODEX", title_id=title_id)
            
            if title_packet and whisper_writer:
                whisper_writer.write(title_packet)
                await whisper_writer.drain()
                print(f"✅ Sent title {title_number}/{total_titles}: {title_id}")
            
            # Wait 2 seconds before next title (unless it's the last one)
            if title_number < total_titles:
                await asyncio.sleep(2)
        
        # Completion message
        completion_msg = f"""[B][C][FFFF00]✅ ALL TITLES SENT SUCCESSFULLY!

"""
        await safe_send_message(chat_type, completion_msg, uid, chat_id, key, iv)
        
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Error sending titles: {str(e)}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)

async def handle_all_titles_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type=0):
    """Handle /alltitles command to send all titles sequentially"""
    
    parts = inPuTMsG.strip().split()
    
    if len(parts) == 1:
        target_uid = uid
        target_name = "Yourself"
    elif len(parts) == 2 and parts[1].isdigit():
        target_uid = parts[1]
        target_name = f"UID {target_uid}"
    else:
        error_msg = f"""[B][C][FF0000]❌ Usage: /alltitles [uid]
        
📝 Examples:
/alltitles - Send all titles to yourself
/alltitles 123456789 - Send all titles to specific UID

🎯 What it does:
1. Sends all 4 titles one by one
2. 2-second delay between each title
3. Sends in background (non-blocking)
4. Shows progress updates
"""
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    # Start the title sequence in the background
    asyncio.create_task(
        send_all_titles_sequentially(target_uid, chat_id, key, iv, region, chat_type)
    )
    
    # Immediate response
    response_msg = f"""[B][C][FFFF00]🚀 STARTING TITLE SEQUENCE IN BACKGROUND!

👤 Target: {target_name}
🎖️ Total Titles: 4
⏱️ Delay: 2 seconds each
📱 Status: Running in background...

💡 You'll receive progress updates as titles are sent!
"""
    await safe_send_message(chat_type, response_msg, uid, chat_id, key, iv)


async def noob(target_uid, chat_id, key, iv, nickname="rizer", title_id=None):
    """EXACT conversion with customizable title ID"""
    try:
        # Use provided title_id or get random one
        if title_id is None:
            # Get a random title from the list
            available_titles = [904090014, 904090015, 904090024, 904090025, 904090026, 904090027, 904990070, 904990071, 904990072]
            title_id = random.choice(available_titles)
        
        # Create fields dictionary with specific title_id
        fields = {
            1: 1,
            2: {
                1: int(target_uid),
                2: int(chat_id),
                5: int(datetime.now().timestamp()),
                8: f'{{"TitleID":{title_id},"type":"Title"}}',
                9: {
                    1: f"[C][B][FF0000]{nickname}",
                    2: int(await xBunnEr()),
                    4: 330,
                    5: 102000015,
                    8: "ABHI EMPIRE",
                    10: 1,
                    11: 1,
                    13: {
                        1: 2
                    },
                    14: {
                        1: 1158053040,
                        2: 8,
                        3: b"\x10\x15\x08\x0a\x0b\x15\x0c\x0f\x11\x04\x07\x02\x03\x0d\x0e\x12\x01\x05\x06"
                    }
                },
                10: "en",
                13: {
                    2: 2,
                    3: 1
                },
                14: {}
            }
        }
        
        # ... rest of your existing function
        proto_bytes = await CrEaTe_ProTo(fields)
        packet_hex = proto_bytes.hex()
        
        encrypted_packet = await encrypt_packet(packet_hex, key, iv)
        packet_length = len(encrypted_packet) // 2
        hex_length = f"{packet_length:04x}"
        
        zeros_needed = 6 - len(hex_length)
        packet_prefix = "121500" + ("0" * zeros_needed)
        
        final_packet_hex = packet_prefix + hex_length + encrypted_packet
        final_packet = bytes.fromhex(final_packet_hex)
        
        print(f"✅ Created packet with Title ID: {title_id}")
        return final_packet
        
    except Exception as e:
        print(f"❌ Conversion error: {e}")
        return None
        


async def get_player_name_from_uid(uid, region="IND"):
    """Get player name from UID - uses same method as /friend command"""
    try:
        # Load token from token.json (same as /friend command)
        token = load_jwt_token()
        if not token:
            return f"Player_{uid[:4]}"  # Fallback if no token
        
        # Use your existing get_player_info function
        player_name, player_uid = get_player_info(str(uid), token)
        
        if player_name and player_name != "Unknown":
            return player_name
        else:
            return f"Player_{uid[:4]}"
            
    except Exception as e:
        print(f"❌ Error getting name for {uid}: {e}")
        return f"Player_{uid[:4]}"  # Fallback

async def send_all_titles_sequentiallly(uid, chat_id, key, iv, region, chat_type):
    """Send all titles one by one with 2-second delay"""
    
    # Get all titles
    all_titles = [
        904090014, 904090015, 904090024, 904090025, 904090026, 904090027, 904990070, 904990071, 904990072
    ]
    
    total_titles = len(all_titles)
    
    # Send initial message
    start_msg =  f"""[B][C][FFFF00] এই শা🤫লা বো👽কা👽চু👽দা তুই NARUTO-CODEX কে নুব বলছিস তোর মাকে কন👽ডম চু👽দি 


"""
    await safe_send_message(chat_type, start_msg, uid, chat_id, key, iv)
    
    try:
        for index, title_id in enumerate(all_titles):
            title_number = index + 1
            

            
            # Send the actual title using your existing method
            # You'll need to use your existing title sending logic here
            # For example:
            title_packet = await noob(uid, chat_id, key, iv, nickname="rizer", title_id=title_id)
            
            if title_packet and whisper_writer:
                whisper_writer.write(title_packet)
                await whisper_writer.drain()
                print(f"✅ Sent title {title_number}/{total_titles}: {title_id}")
            
            # Wait 2 seconds before next title (unless it's the last one)
            if title_number < total_titles:
                await asyncio.sleep(2)
        
        # Completion message
        completion_msg =  f"""[B][C][FFFF00] মা💀দা💀রচো💀দ এ💀ইসব টাই💀টেল দিয়ে দেখা রে💀ন্ডি মা🤫গির পো🤫লা
"""
        await safe_send_message(chat_type, completion_msg, uid, chat_id, key, iv)
        
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Error sending titles: {str(e)}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)

async def handle_alll_titles_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type=0):
    """Handle /alltitles command to send all titles sequentially"""
    
    parts = inPuTMsG.strip().split()
    
    if len(parts) == 1:
        target_uid = uid
        target_name = "Yourself"
    elif len(parts) == 2 and parts[1].isdigit():
        target_uid = parts[1]
        target_name = f"UID {target_uid}"
    else:
        error_msg = f"""[B][C][FF0000]❌ Usage: /alltitles [uid]
        
📝 Examples:
/alltitles - Send all titles to yourself
/alltitles 123456789 - Send all titles to specific UID

🎯 What it does:
1. Sends all 4 titles one by one
2. 2-second delay between each title
3. Sends in background (non-blocking)
4. Shows progress updates
"""
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    # Start the title sequence in the background
    asyncio.create_task(
        send_all_titles_sequentiallly(target_uid, chat_id, key, iv, region, chat_type)
    )
    


async def RoomJoin(room_id, password, key, iv):
    """Join Free Fire custom room"""
    try:
        # Import your proto file
        from room_join_pb2 import join_room
        
        root = join_room()
        root.field_1 = 3  # Room join command
        
        # Nested object
        nested_object = root.field_2
        nested_object.field_1 = int(room_id)
        nested_object.field_2 = str(password)
        
        # Field 8
        nested_8 = nested_object.field_8
        nested_8.field_1 = "IDC3"
        nested_8.field_2 = 149
        nested_8.field_3 = "IND"
        
        # Other fields
        nested_object.field_9 = "\x01\x03\x04\x07\x09\x0a\x0b\x12\x0e\x16\x19\x20\x1d"  # Bytes, not string
        nested_object.field_10 = 1
        nested_object.field_12.SetInParent()  # Empty field
        nested_object.field_13 = 1
        nested_object.field_14 = 1
        nested_object.field_16 = "en"
        
        # Field 22
        nested_22 = nested_object.field_22
        nested_22.field_1 = 21
        
        # Serialize
        packet_hex = root.SerializeToString().hex()
        
        # Encrypt using your function
        encrypted_packet = await encrypt_packet(packet_hex, key, iv)
        packet_length = len(encrypted_packet) // 2
        
        # Convert length to hex
        hex_length = dec_to_hex(packet_length)  # Use your existing function
        
        # Build packet header (type 0e15 for room join)
        if len(hex_length) == 2:
            header = "0e15000000"
        elif len(hex_length) == 3:
            header = "0e1500000"
        elif len(hex_length) == 4:
            header = "0e150000"
        elif len(hex_length) == 5:
            header = "0e15000"
        else:
            header = "0e150000"
        
        final_packet_hex = header + hex_length + encrypted_packet
        
        return bytes.fromhex(final_packet_hex)
        
    except Exception as e:
        print(f"❌ Room join error: {e}")
        import traceback
        traceback.print_exc()
        return None
        

# Alternative: Using your fields dictionary format
async def RoomJoin_fields(room_id, password, key, iv):
    """Room join using your CrEaTe_ProTo format"""
    try:
        fields = {
            1: 3,  # Room join command
            2: {   # Nested object
                1: int(room_id),   # room_id
                2: str(password),  # password
                8: {  # field_8
                    1: "IDC3",
                    2: 149,
                    3: "IND"
                },
                9: b"\x01\x03\x04\x07\x09\x0a\x0b\x12\x0e\x16\x19\x20\x1d",  # Bytes!
                10: 1,
                12: {},  # Empty field
                13: 1,
                14: 1,
                16: "en",
                22: {  # field_22
                    1: 21
                }
            }
        }
        
        # Convert to protobuf
        proto_bytes = await CrEaTe_ProTo(fields)
        packet_hex = proto_bytes.hex()
        
        # Encrypt and build packet
        encrypted_packet = await encrypt_packet(packet_hex, key, iv)
        packet_length = len(encrypted_packet) // 2
        hex_length = dec_to_hex(packet_length)
        
        # Build header
        if len(hex_length) == 2:
            header = "0e15000000"
        elif len(hex_length) == 3:
            header = "0e1500000"
        elif len(hex_length) == 4:
            header = "0e150000"
        elif len(hex_length) == 5:
            header = "0e15000"
        else:
            header = "0e150000"
        
        final_packet_hex = header + hex_length + encrypted_packet
        return bytes.fromhex(final_packet_hex)
        
    except Exception as e:
        print(f"❌ Room join fields error: {e}")
        return None

def remove_from_whitelist(uid_to_remove):
    """Remove UID from whitelist"""
    global WHITELISTED_UIDS
    
    uid_str = str(uid_to_remove)
    
    # Don't allow removing owner
    if uid_str == "2270928791":  # Your UID
        return False, "Cannot remove bot owner from whitelist!"
    
    if uid_str not in WHITELISTED_UIDS:
        return False, f"UID {uid_str} not in whitelist"
    
    WHITELISTED_UIDS.remove(uid_str)
    return True, f"✅ Removed {uid_str} from whitelist"



async def handle_xjoin_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /xjoin command to join custom rooms"""
    
    parts = inPuTMsG.strip().split()
    
    if len(parts) < 3:
        error_msg = f"""[B][C][FF0000]🎮 ROOM JOIN COMMAND

❌ Usage: /xjoin (room_id) (password)

📝 Examples:
/xjoin 123456 0000
/xjoin 987654 1111

🔑 Room Info:
• Room ID: 6-digit number
• Password: Usually 4 digits (0000-9999)

💡 Bot will join the custom room!
"""
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    room_id = parts[1]
    password = parts[2]
    
    if not room_id.isdigit():
        error_msg = f"[B][C][FF0000]❌ Room ID must be numbers only!\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    # Send initial message
    initial_msg = f"[B][C][FFFF00]🚀 JOINING CUSTOM ROOM...\n🏠 Room: {room_id}\n🔑 Password: {password}\n"
    await safe_send_message(chat_type, initial_msg, uid, chat_id, key, iv)
    
    try:
        # Try method 1: Direct proto method
        room_packet = await RoomJoin(room_id, password, key, iv)
        
        if not room_packet:
            # Try method 2: Fields method
            room_packet = await RoomJoin_fields(room_id, password, key, iv)
        
        if room_packet and online_writer:
            # Send via Online connection
            online_writer.write(room_packet)
            await online_writer.drain()
            
            print(f"✅ Room join packet sent! Room: {room_id}")
            # REMOVED the undefined join_room_chanel call
            success_msg = f"""[B][C][FFFF00]✅ ROOM JOIN COMMAND SENT!

🏠 Room ID: {room_id}
🔑 Password: {password}
"""
        else:
            success_msg = f"[B][C][FF0000]❌ Failed to create room join packet!\n"
        
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
        
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Error joining room: {str(e)}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)

async def handle_room_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /room command with proper error handling"""
    
    parts = inPuTMsG.strip().split()
    
    if len(parts) < 2:
        error_msg = f"[B][C][FF0000]❌ Usage: /room (uid)\nExample: /room 11686472351\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    target_uid = parts[1]
    
    try:
        # Step 1: Check player status
        status_result, status_message = await check_player_status(target_uid, key, iv)
        
        packet = None
        player_status = None
        
        # If live check failed, try cache
        if not status_result:
            # Check cache
            cached_data = load_from_cache(target_uid)
            if cached_data and 'packet' in cached_data:
                packet = cached_data['packet']
                player_status = cached_data.get('status', 'UNKNOWN')
                print(f"⚠️ Using cached data for {target_uid}")
            else:
                error_msg = f"[B][C][FF0000]❌ Player {target_uid} not found\n"
                await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
                return
        else:
            # Use live data
            packet = status_result.get('packet', b'')
            player_status = get_player_status(packet)
        
        # Step 2: Check if player is in room
        if not player_status or "IN ROOM" not in player_status:
            info_msg = f"""[B][C][FFFF00]📊 STATUS: {player_status or 'UNKNOWN'}

👤 Player: {target_uid}
❌ Not in custom room

💡 Player must join custom room first!"""
            await safe_send_message(chat_type, info_msg, uid, chat_id, key, iv)
            return
        
        # Step 3: Extract room ID
        room_id = get_idroom_by_idplayer(packet) if packet else None
        
        if not room_id:
            error_msg = f"[B][C][FF0000]❌ Failed to extract room ID\n"
            await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
            return
        
        # Step 4: SUCCESS - Send room info
        success_msg = f"""[B][C][FFFF00]✅ ROOM FOUND!

👤 Player: {target_uid}
🏠 Room ID: {room_id}
📊 Status: {player_status}
⚡ Data: {'CACHED' if not status_result else 'LIVE'}

💡 Quick join: /xjoin {room_id} 0000
"""
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
        
        # Step 5: AUTO-SPAM (add this if you want spam)
        # Uncomment this section if you want auto-spam:
        
        spam_count = 5
        for i in range(spam_count):
            try:
                spam_packet = await Room_Spam(target_uid, room_id, f"Spam_{i+1}", key, iv)
                if spam_packet and online_writer:
                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', spam_packet)
                    await asyncio.sleep(0.2)
            except Exception as e:
                print(f"Spam error: {e}")
        
        spam_msg = f"[B][C][FFFF00]✅ Spammed {spam_count} invites!\n"
        await safe_send_message(chat_type, spam_msg, uid, chat_id, key, iv)
        
        
    except Exception as e:
        print(f"❌ Room command error: {e}")
        error_msg = f"[B][C][FF0000]❌ Error: {str(e)[:80]}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)

# Room spam command (send multiple messages)
async def handle_room_spam_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /spamroom command to send room spam messages"""
    
    parts = inPuTMsG.strip().split()
    
    if len(parts) < 4:
        error_msg = f"""[B][C][FF0000]❌ Usage: /spamroom (room_id) (uid) (message)
        
📝 Example: /spamroom 123456 14010319252 Hello World!

⚙️ Parameters:
• room_id = Custom room ID (numbers)
• uid = Player UID to spam
• message = Text message to send

🎯 What it does:
1. Creates room spam packet
2. Sends message to specified room
3. Uses colorful formatting
4. Packet type: 0e15 (room spam)
"""
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    try:
        room_id = parts[1]
        target_uid = parts[2]
        message = ' '.join(parts[3:])
        
        # Validate inputs
        if not room_id.isdigit():
            error_msg = f"[B][C][FF0000]❌ Room ID must be numbers only!\n"
            await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
            return
            
        if not target_uid.isdigit():
            error_msg = f"[B][C][FF0000]❌ UID must be numbers only!\n"
            await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
            return
        
        # Send initial message
        initial_msg = f"[B][C][FFFF00]🚀 PREPARING ROOM SPAM...\n"
        initial_msg += f"🏠 Room ID: {room_id}\n"
        initial_msg += f"👤 Target UID: {target_uid}\n"
        initial_msg += f"📝 Message: {message[:30]}...\n"
        initial_msg += f"📦 Packet type: 0e15\n"
        initial_msg += f"⏳ Creating packet...\n"
        
        await safe_send_message(chat_type, initial_msg, uid, chat_id, key, iv)
        
        # Create and send the spam packet
        spam_packet = await SPam_Room(target_uid, room_id, message, key, iv)
        
        if spam_packet:
            # Send via Online connection (since it's room-related)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', spam_packet)
            
            success_msg = f"""[B][C][FFFF00]✅ ROOM SPAM PACKET SENT!

🏠 Room: {room_id}
👤 Target: {target_uid}
📝 Message: {message[:40]}...
📦 Packet: Type 0e15 (Room Spam)
✅ Status: Delivered successfully

💡 Packet includes:
• Colorful message formatting
• Avatar: {await xBunnEr()}
• Rank: 330
• Badge: 201
"""
        else:
            success_msg = f"[B][C][FF0000]❌ Failed to create spam packet!\n"
        
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
        
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Error: {str(e)}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)

# Also create a shorter alias command handler
async def handle_sr_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /sr command (short version of /spamroom)"""
    await handle_room_spam_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type)
        
async def detect_emote_perfect(data_hex, key, iv):
    """100% ACCURATE emote detection using YOUR exact packet structure"""
    
    try:
        # Step 1: Decrypt using your EXACT method
        decrypted = await DeCode_PackEt(data_hex[10:])  # Use YOUR existing function
        packet_json = json.loads(decrypted)
        
        # Step 2: EXACT STRUCTURE MATCHING
        # Check for Type 21 (from your Emote_k function)
        if packet_json.get('1') == 21:
            # Check for the EXACT structure you use
            if '2' in packet_json and 'data' in packet_json['2']:
                emote_data = packet_json['2']['data']
                
                # Verify EXACT field structure matches Emote_k()
                if ('1' in emote_data and '2' in emote_data and 
                    '5' in emote_data and 'data' in emote_data['5']):
                    
                    nested = emote_data['5']['data']
                    
                    # THIS IS THE 100% ACCURATE DETECTION
                    # Matches EXACTLY what you send in Emote_k()
                    if '1' in nested and '3' in nested:
                        return {
                            'type': 'emote',
                            'packet_type': 21,  # ← EXACT MATCH
                            'identifier': emote_data.get('1', {}).get('data'),
                            'base_emote': emote_data.get('2', {}).get('data'),
                            'target_uid': nested.get('1', {}).get('data'),  # WHO received it
                            'emote_id': nested.get('3', {}).get('data'),
                            'confidence': 100.0,
                            'raw_packet': packet_json
                        }
        
        # ALTERNATIVE FORMAT: Direct to player
        elif packet_json.get('1') == 26:  # Another emote type
            # Add similar exact matching here
            pass
        
        return None
        
    except Exception as e:
        print(f"❌ Perfect detection error: {e}")
        return None
        
async def detect_emote_with_sender(data_hex, key, iv):
    """Detect emote AND find who sent it"""
    
    try:
        # First, detect if it's an emote packet
        emote_info = await detect_emote_perfect(data_hex, key, iv)
        
        if not emote_info:
            return None
        
        # Now we need to find the SENDER's UID
        # Look for sender in different packet parts
        
        # METHOD 1: Check packet header for UID
        packet_header = data_hex[:20]
        
        # Look for UID patterns in hex (9-11 digits)
        import re
        uid_pattern = r'(\d{9,11})'
        
        # Search in entire packet
        all_uids = re.findall(uid_pattern, data_hex)
        
        if len(all_uids) >= 2:
            # We have at least 2 UIDs: sender and target
            # The target is already in emote_info['target_uid']
            target_uid = str(emote_info['target_uid'])
            
            # Find which UID is NOT the target
            for uid in all_uids:
                if uid != target_uid:
                    # This is likely the SENDER
                    emote_info['sender_uid'] = int(uid)
                    emote_info['detection_method'] = 'uid_pattern'
                    
                    print(f"✅ SENDER FOUND: {uid} sent emote to {target_uid}")
                    return emote_info
        
        # METHOD 2: Look in packet structure
        packet_json = emote_info['raw_packet']
        
        # Search recursively for UID that's NOT the target
        def find_sender_in_json(obj, target_uid):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == 'data' and isinstance(v, (int, str)):
                        v_str = str(v)
                        if v_str.isdigit() and len(v_str) > 8:
                            if v_str != str(target_uid):
                                return int(v)
                    elif isinstance(v, dict):
                        result = find_sender_in_json(v, target_uid)
                        if result:
                            return result
            return None
        
        sender_uid = find_sender_in_json(packet_json, emote_info['target_uid'])
        if sender_uid:
            emote_info['sender_uid'] = sender_uid
            emote_info['detection_method'] = 'json_search'
            return emote_info
        
        # If we can't find sender, at least we detected the emote
        emote_info['sender_uid'] = None
        return emote_info
        
    except Exception as e:
        print(f"❌ Sender detection error: {e}")
        return None


async def send_title_packet_direct(target_uid, chat_id, key, iv, region="ind"):
    """Send title packet directly without chat context - for auto-join"""
    try:
        print(f"🎖️ Sending title to {target_uid} in chat {chat_id}")
        
        # Method 1: Using your existing function
        title_packet = await convert_kyro_to_your_system(target_uid, chat_id, key, iv)
        
        if title_packet and whisper_writer:
            # Send via Whisper connection
            whisper_writer.write(title_packet)
            await whisper_writer.drain()
            print(f"✅ Title sent via Whisper to {target_uid}")
            return True
            
    except Exception as e:
        print(f"❌ Error sending title directly: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def extract_type_5(packet_json):
    """Extract from Type 5 packets"""
    if packet_json.get('1') == 5:
        try:
            if '2' in packet_json and 'data' in packet_json['2']:
                data = packet_json['2']['data']
                sender = data.get('1', {}).get('data')
                emote_id = data.get('4', {}).get('data')
                
                if sender:
                    return {
                        'sender_uid': sender,
                        'emote_id': emote_id or 909051015,  # Default if not found
                        'packet_type': 5,
                        'confidence': 'medium'
                    }
        except:
            pass
    return None

async def extract_emote_info(data_hex, key, iv):
    """Extract full emote info from packet"""
    try:
        packet = await DeCode_PackEt(data_hex[10:])
        packet_json = json.loads(packet)
        
        # DEBUG: Print packet structure
        # print("📦 Packet JSON:", json.dumps(packet_json, indent=2)[:300])
        
        # Check all possible structures
        structures = [
            # Type 21 (from your Emote_k)
            lambda: extract_type_21(packet_json),
            # Type 26
            lambda: extract_type_26(packet_json),
            # Type 5
            lambda: extract_type_5(packet_json),
            # Generic search
            lambda: generic_extract(packet_json)
        ]
        
        for extractor in structures:
            info = extractor()
            if info and info.get('sender_uid'):
                return info
        
        return None
        
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return None

def extract_type_21(packet_json):
    """Extract from Type 21 (your Emote_k structure)"""
    if packet_json.get('1') == 21:
        try:
            if ('2' in packet_json and 'data' in packet_json['2'] and
                '5' in packet_json['2']['data'] and 'data' in packet_json['2']['data']['5']):
                
                data = packet_json['2']['data']
                nested = data['5']['data']
                
                sender = nested.get('1', {}).get('data')
                emote_id = nested.get('3', {}).get('data')
                
                if sender and emote_id:
                    return {
                        'sender_uid': sender,
                        'emote_id': emote_id,
                        'packet_type': 21,
                        'confidence': 'high'
                    }
        except:
            pass
    return None

def extract_type_26(packet_json):
    """Extract from Type 26 (common emote)"""
    if packet_json.get('1') == 26:
        try:
            if '2' in packet_json and 'data' in packet_json['2']:
                data = packet_json['2']['data']
                sender = data.get('1', {}).get('data')
                emote_id = data.get('2', {}).get('data')
                
                if sender and emote_id:
                    return {
                        'sender_uid': sender,
                        'emote_id': emote_id,
                        'packet_type': 26,
                        'confidence': 'high'
                    }
        except:
            pass
    return None

# Add these imports at the top with your other imports
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import json
import requests
import asyncio

# Add these constants with your other global variables
BIO_ENCRYPTION_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
BIO_ENCRYPTION_IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
FREEFIRE_VERSION = "OB54"

def decode_jwt_noverify(token: str):
    """Decode JWT without verification"""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
        return payload
    except Exception:
        return None

# Add these global variables

async def is_bot_in_squad(bot_uid, key, iv):
    """Quick check if bot is in squad (with caching)"""
    global last_bot_status_check, cached_bot_status
    
    # Use cache if recent
    current_time = time.time()
    if (current_time - last_bot_status_check < bot_status_cache_time and 
        cached_bot_status is not None):
        return cached_bot_status
    
    try:
        # Send status request
        status_packet = await createpacketinfo(bot_uid, key, iv)
        if status_packet and online_writer:
            online_writer.write(status_packet)
            await online_writer.drain()
            
            # Wait for response
            await asyncio.sleep(2)
            
            # Check cache
            if bot_uid in status_response_cache:
                packet = status_response_cache[bot_uid].get('packet', b'')
                status = get_player_status(packet)
                
                in_squad = "INSQUAD" in status
                cached_bot_status = in_squad
                last_bot_status_check = current_time
                
                return in_squad
        
        return False
        
    except Exception as e:
        print(f"❌ Squad check error: {e}")
        return False

def get_bio_server_url(lock_region: str):
    """Get bio endpoint based on region"""
    region = lock_region.upper()
    if region == "IND":
        return "https://client.ind.freefiremobile.com/UpdateSocialBasicInfo"
    elif region in {"BR", "US", "SAC", "NA"}:
        return "https://client.us.freefiremobile.com/UpdateSocialBasicInfo"
    elif region == "BD":
        return "https://clientbp.ggpolarbear.com/UpdateSocialBasicInfo"
    elif region == "SG":
        return "https://client.sg.freefiremobile.com/UpdateSocialBasicInfo"
    else:
        return "https://clientbp.ggpolarbear.com/UpdateSocialBasicInfo"

def create_bio_protobuf(bio_text):
    """Create protobuf message for bio update - EXACT SAME AS YOUR FLASK API"""
    # This creates the EXACT same protobuf structure as your Flask API
    
    # Protobuf structure from your API:
    # field_2: 17 (0x11)
    # field_5: EmptyMessage
    # field_6: EmptyMessage  
    # field_8: bio_text (string)
    # field_9: 1 (0x01)
    # field_11: EmptyMessage
    # field_12: EmptyMessage
    
    # Build protobuf manually (matching your exact structure)
    # Field 2: varint 17
    field_2 = b'\x08\x11'  # tag:1 type:varint value:17
    
    # Field 5: EmptyMessage (empty bytes)
    field_5 = b'\x2A\x00'  # tag:5 type:length-delimited length:0
    
    # Field 6: EmptyMessage (empty bytes)
    field_6 = b'\x32\x00'  # tag:6 type:length-delimited length:0
    
    # Field 8: bio text (string)
    bio_bytes = bio_text.encode('utf-8')
    bio_length = len(bio_bytes)
    field_8 = b'\x42' + bytes([bio_length]) + bio_bytes  # tag:8 type:string
    
    # Field 9: varint 1
    field_9 = b'\x48\x01'  # tag:9 type:varint value:1
    
    # Field 11: EmptyMessage
    field_11 = b'\x5A\x00'  # tag:11 type:length-delimited length:0
    
    # Field 12: EmptyMessage
    field_12 = b'\x62\x00'  # tag:12 type:length-delimited length:0
    
    # Combine all fields
    protobuf_data = field_2 + field_5 + field_6 + field_8 + field_9 + field_11 + field_12
    return protobuf_data

async def set_bio_directly_async_with_retry(jwt_token, bio_text, region="IND", max_retries=3, retry_delay=2):
    """Set bio with automatic retry logic"""
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Bio API attempt {attempt + 1}/{max_retries}")
            
            result = await set_bio_directly_async(jwt_token, bio_text, region)
            
            if result.get("success"):
                return result
            else:
                print(f"❌ Bio update failed: {result.get('message')}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    
        except Exception as e:
            print(f"❌ Bio attempt {attempt + 1} error: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            continue
    
    # If all retries failed
    return {
        "success": False,
        "message": f"All {max_retries} attempts failed"
    }

async def set_bio_directly_async(jwt_token, bio_text, region="IND"):
    """Set bio directly - ASYNC version with better error handling"""
    try:
        # Decode JWT to get region
        payload = decode_jwt_noverify(jwt_token)
        if not payload:
            return {
                "success": False,
                "message": "Invalid JWT token"
            }
        
        lock_region = payload.get("lock_region", region).upper()
        url_bio = get_bio_server_url(lock_region)
        
        print(f"🔧 Setting bio for region: {lock_region}")
        print(f"📝 Bio text: {bio_text}")
        
        # Create protobuf message
        data_bytes = create_bio_protobuf(bio_text)
        print(f"📦 Protobuf created: {len(data_bytes)} bytes")
        
        # Encrypt using AES CBC
        cipher = AES.new(BIO_ENCRYPTION_KEY, AES.MODE_CBC, BIO_ENCRYPTION_IV)
        
        # Pad data to AES block size (16 bytes)
        padding_length = 16 - (len(data_bytes) % 16)
        if padding_length:
            data_bytes += bytes([padding_length] * padding_length)
        
        encrypted_data = cipher.encrypt(data_bytes)
        print(f"🔐 Encrypted: {len(encrypted_data)} bytes")
        
        # Headers
        headers = {
            "Expect": "100-continue",
            "Authorization": f"Bearer {jwt_token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": FREEFIRE_VERSION,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F Build/RP1A.200720.012)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }
        
        print(f"🚀 Sending to: {url_bio}")
        
        # Use aiohttp with timeout
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url_bio, headers=headers, data=encrypted_data) as response:
                response_text = await response.text()
                
                print(f"📡 Response status: {response.status}")
                
                if response.status == 200:
                    return {
                        "success": True,
                        "message": "Bio updated successfully!",
                        "region": lock_region,
                        "bio": bio_text
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Server error: {response.status} - {response_text[:100]}"
                    }
                
    except aiohttp.ClientError as e:
        print(f"❌ Network error: {e}")
        return {
            "success": False,
            "message": f"Network error: {str(e)[:80]}"
        }
    except asyncio.TimeoutError:
        print(f"❌ Request timeout")
        return {
            "success": False,
            "message": "Request timeout (10s)"
        }
    except Exception as e:
        print(f"❌ Bio update error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Error: {str(e)[:80]}"
        }

# Now add this command handler to your TcPChaT function
# Find where other commands are handled and add this:

def analyze_squad_packet(packet_json):
    """Analyze packet structure to find squad members"""
    
    print("\n🔍 ANALYZING SQUAD PACKET STRUCTURE")
    print("="*50)
    
    # Check if this is a squad data packet
    if '5' not in packet_json or 'data' not in packet_json['5']:
        print("❌ Not a squad data packet")
        return None
    
    squad_data = packet_json['5']['data']
    
    # Look for fields that could contain multiple players
    candidate_fields = []
    
    for field_num in squad_data:
        field_info = squad_data[field_num]
        if 'data' not in field_info:
            continue
            
        data_value = field_info['data']
        
        # Check if it's a list (likely contains multiple players)
        if isinstance(data_value, list):
            print(f"✅ Field {field_num}: LIST with {len(data_value)} items")
            candidate_fields.append((field_num, 'list', data_value))
            
            # Show first item structure
            if data_value and isinstance(data_value[0], dict):
                print(f"   First item keys: {list(data_value[0].keys())}")
                # Check if first item has UID (field 1)
                if '1' in data_value[0]:
                    uid = data_value[0]['1']['data']
                    print(f"   ↳ Contains UID: {uid}")
        
        # Check if it's a dict with numeric keys (0, 1, 2, 3...)
        elif isinstance(data_value, dict):
            keys = list(data_value.keys())
            numeric_keys = [k for k in keys if k.isdigit()]
            if len(numeric_keys) > 0:
                print(f"✅ Field {field_num}: DICT with numeric keys {numeric_keys[:5]}...")
                candidate_fields.append((field_num, 'dict', data_value))
    
    print("\n🎯 MOST LIKELY SQUAD MEMBERS FIELDS:")
    for field_num, field_type, data in candidate_fields:
        print(f"  Field {field_num} ({field_type})")
        
        if field_type == 'list':
            # Try to extract UIDs from list
            uids = []
            for item in data[:5]:  # Check first 5 items
                if isinstance(item, dict) and '1' in item:
                    uid = item['1']['data']
                    uids.append(uid)
            if uids:
                print(f"    ↳ Found UIDs: {uids}")
        
        elif field_type == 'dict':
            # Try to extract UIDs from dict
            uids = []
            for key in list(data.keys())[:5]:  # Check first 5 keys
                item = data[key]
                if isinstance(item, dict) and '1' in item:
                    uid = item['1']['data']
                    uids.append(uid)
            if uids:
                print(f"    ↳ Found UIDs: {uids}")
    
    return candidate_fields

def generic_extract(packet_json):
    """Generic search for UID and emote ID"""
    uid = None
    emote_id = None
    
    # Recursively search for UID (long number)
    def search(obj):
        nonlocal uid, emote_id
        
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == 'data' and isinstance(v, (int, str)) and str(v).isdigit():
                    # Check if it looks like a UID (long number)
                    num = int(v)
                    if 1000000 < num < 99999999999:  # Reasonable UID range
                        if not uid:  # First found is likely sender
                            uid = num
                        # Check if it's an emote ID (starts with 909...)
                        elif str(v).startswith('909') and len(str(v)) >= 9:
                            emote_id = num
                
                elif isinstance(v, dict):
                    search(v)
                elif isinstance(v, list):
                    for item in v:
                        search(item)
    
    search(packet_json)
    
    if uid:
        return {
            'sender_uid': uid,
            'emote_id': emote_id or 909051015,  # Default AK emote
            'packet_type': 'generic',
            'confidence': 'medium'
        }
    
    return None
    
async def auto_reply_with_emote(emote_info, key, iv):
    """Automatically reply with same emote"""
    
    try:
        # Get bot's UID (you need to set this)
        bot_uid = 14010319252  # Replace with your bot's actual UID
        
        sender_uid = emote_info['sender_uid']
        emote_id = emote_info['emote_id']
        
        # Send emote back to sender
        reply_packet = await Emote_k(sender_uid, emote_id, key, iv, region)
        
        if online_writer:
            online_writer.write(reply_packet)
            await online_writer.drain()
            
            print(f"🤖 Bot replied with emote {emote_id} to {sender_uid}")
            
    except Exception as e:
        print(f"❌ Auto-reply error: {e}")

def extract_squad_members_correct(packet_json):
    """Extract squad members from FULL squad packet"""
    
    print("\n🔍 EXTRACTING SQUAD MEMBERS")
    print("="*50)
    
    try:
        if ('5' not in packet_json or 
            'data' not in packet_json['5'] or 
            '2' not in packet_json['5']['data']):
            print("❌ Invalid packet structure")
            return []
        
        field2_data = packet_json['5']['data']['2']['data']
        
        squad_members = []
        
        # Field 2 has numeric keys: '1', '2', '3', '4', '5', etc.
        # Each key might be a squad member slot OR player data field
        
        # Let's check what each numeric key contains
        for key in field2_data:
            if not key.isdigit():
                continue
                
            item = field2_data[key]['data']
            print(f"\n📦 Key {key}: Type = {type(item)}")
            
            if isinstance(item, dict):
                # Check if this is a player object
                # Player objects usually have fields: 1=UID, 2=name, 4=rank, etc.
                if '1' in item and '2' in item:
                    try:
                        uid = item['1']['data']
                        name = item['2']['data']
                        
                        # Make sure it's a valid UID (not a small number)
                        if isinstance(uid, int) and uid > 1000000:
                            rank = item['4']['data'] if '4' in item else 0
                            
                            print(f"   ✅ PLAYER FOUND!")
                            print(f"      UID: {uid}")
                            print(f"      Name: {name}")
                            print(f"      Rank: {rank}")
                            
                            squad_members.append({
                                'slot': key,
                                'uid': uid,
                                'name': name,
                                'rank': rank
                            })
                        else:
                            print(f"   ❌ Not a UID: {uid}")
                            
                    except Exception as e:
                        print(f"   ❌ Error extracting player: {e}")
                else:
                    print(f"   ↳ Fields: {list(item.keys())[:5]}...")
            elif isinstance(item, (int, str)):
                print(f"   ↳ Value: {item}")
        
        print(f"\n🏆 TOTAL SQUAD MEMBERS FOUND: {len(squad_members)}")
        for member in squad_members:
            print(f"  • Slot {member['slot']}: {member['name']} (UID: {member['uid']})")
        
        return squad_members
        
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        import traceback
        traceback.print_exc()
        return []
        
async def analyze_packet_structure(data_hex, key, iv):
    """Analyze and display packet structure"""
    
    print(f"\n📦 PACKET ANALYSIS")
    print("="*50)
    
    # Basic info
    print(f"📏 Length: {len(data_hex)} characters")
    print(f"🔢 Header: {data_hex[:10]}")
    
    # Try to decode
    try:
        if len(data_hex) > 20:
            decoded = await DeCode_PackEt(data_hex[10:])
            packet_json = json.loads(decoded)
            
            print(f"✅ Successfully decoded!")
            print(f"📊 Packet type (field 1): {packet_json.get('1', 'Unknown')}")
            
            # Show structure
            print(f"\n📋 PACKET STRUCTURE:")
            print(f"Top-level fields: {list(packet_json.keys())}")
            
            # Show field 1 value
            if '1' in packet_json:
                print(f"  Field 1: {packet_json['1']}")
            
            # Show if it contains emote ID patterns
            import re
            emote_patterns = re.findall(r'909[0-9a-f]{6}', data_hex)
            if emote_patterns:
                print(f"\n🎭 EMOTE IDS FOUND IN HEX: {emote_patterns}")
            
            # Show UID patterns
            uid_patterns = re.findall(r'(\d{9,11})', data_hex)
            uids = [uid for uid in uid_patterns if not uid.startswith('909')]
            if uids:
                print(f"👤 UIDS FOUND IN HEX: {uids}")
            
            # Return the decoded structure
            return packet_json
            
        else:
            print("❌ Packet too short to decode")
            return None
            
    except Exception as e:
        print(f"❌ Decode error: {e}")
        return None

async def RedZed_SendInv(bot_uid, uid, key, iv):
    """Async version of send invite function"""
    try:
        fields = {
            1: 2, 
            2: {
                1: int(uid), 
                2: "IND", 
                3: 1, 
                4: 1, 
                6: "RedZedKing!!", 
                7: 330, 
                8: 1000, 
                9: 100, 
                10: "DZ", 
                12: 1, 
                13: int(uid), 
                16: 1, 
                17: {
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
                27: {
                    1: 11, 
                    2: int(bot_uid), 
                    3: 99999999999
                }, 
                28: {}, 
                31: {
                    1: 1, 
                    2: 32768
                }, 
                32: 32768, 
                34: {
                    1: bot_uid, 
                    2: 8, 
                    3: b"\x10\x15\x08\x0A\x0B\x13\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
                }
            }
        }
        
        # Convert bytes properly
        if isinstance(fields[2][34][3], str):
            fields[2][34][3] = b"\x10\x15\x08\x0A\x0B\x13\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
        
        # Use async versions of your functions
        packet = await CrEaTe_ProTo(fields)
        packet_hex = packet.hex()
        
        # Generate final packet
        final_packet = await GeneRaTePk(packet_hex, '0515', key, iv)
        
        return final_packet
        
    except Exception as e:
        print(f"❌ Error in RedZed_SendInv: {e}")
        import traceback
        traceback.print_exc()
        return None
        
async def freeze_emote_spam(uid, key, iv, region, chat_type, chat_id, sender_uid):
    """Send 3 freeze emotes in 1-second cycles for 10 seconds"""
    global freeze_running
    
    try:
        cycles = 0
        max_cycles = FREEZE_DURATION  # 10 seconds
        
        while freeze_running and cycles < max_cycles:
            # Send all 3 emotes in sequence
            for i, emote_id in enumerate(FREEZE_EMOTES):
                if not freeze_running:
                    break
                    
                try:
                    # Send emote
                    emote_packet = await Emote_k(int(uid), emote_id, key, iv, region)
                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_packet)
                    
                    print(f"❄️ Freeze emote {i+1}/{len(FREEZE_EMOTES)} sent: {emote_id}")
                    
                    # Small delay between emotes (0.3 seconds)
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    print(f"❌ Error sending freeze emote {i+1}: {e}")
            
            cycles += 1
            print(f"🌀 Freeze cycle {cycles}/{max_cycles} completed")
            
            # Wait for next cycle (total 1 second per cycle)
            remaining_time = 1.0 - (0.3 * len(FREEZE_EMOTES))
            if remaining_time > 0:
                await asyncio.sleep(remaining_time)
        
        print(f"✅ Freeze sequence completed: {cycles} cycles")
        return cycles
        
    except Exception as e:
        print(f"❌ Freeze function error: {e}")
        return 0
        
async def handle_freeze_completion(freeze_task, uid, sender_uid, chat_id, chat_type, key, iv):
    """Handle freeze command completion"""
    try:
        cycles_completed = await freeze_task
        
        completion_msg = f"""[B][C][00FFFF]❄️ FREEZE COMMAND COMPLETED!

🎯 Target: {uid}
⏱️ Duration: {cycles_completed} seconds
🎭 Emotes sent: {cycles_completed * 3}
❄️ Sequence: 
  • 909040004 (Ice)
  • 909050008 (Frozen)
  • 909000002 (Freeze)

✅ Status: Complete!
"""
        await safe_send_message(chat_type, completion_msg, sender_uid, chat_id, key, iv)
        
    except asyncio.CancelledError:
        print("🛑 Freeze command cancelled")
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Freeze error: {str(e)}\n"
        await safe_send_message(chat_type, error_msg, sender_uid, chat_id, key, iv)

async def test_emote_packet(target_uid, emote_id, key, iv, region="IND"):
    """Test if emote packet works and show structure"""
    
    print(f"\n🎭 TESTING EMOTE PACKET")
    print("="*50)
    
    # Create the packet using your function
    emote_packet = await Emote_k(target_uid, emote_id, key, iv, region)
    
    if not emote_packet:
        print("❌ Failed to create packet")
        return False
    
    # Convert to hex for analysis
    packet_hex = emote_packet.hex()
    
    print(f"📦 Packet created!")
    print(f"   Length: {len(packet_hex)} characters")
    print(f"   Header: {packet_hex[:20]}")
    
    # Try to decode it back
    try:
        if len(packet_hex) > 20:
            # Remove header (first 10 bytes = 20 hex chars)
            payload = packet_hex[20:]  # Skip header
            
            # Decrypt (you need to implement this)
            # For testing, let's see raw structure
            print(f"\n🔍 RAW PACKET STRUCTURE:")
            print(f"Full hex (first 200 chars):")
            print(packet_hex[:200] + "...")
            
            # Look for the UID in hex
            import re
            uid_hex = hex(target_uid)[2:]
            if uid_hex in packet_hex:
                print(f"✅ Target UID {target_uid} found in packet!")
            else:
                print(f"❌ Target UID not found in hex")
            
            # Look for emote ID
            emote_hex = hex(emote_id)[2:]
            if emote_hex in packet_hex:
                print(f"✅ Emote ID {emote_id} found in packet!")
            else:
                print(f"❌ Emote ID not found in hex")
        
        print(f"\n✅ Packet created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return False
        
async def send_and_monitor_emote(target_uid, emote_id, key, iv, region, reader):
    """Send emote and monitor response - FIXED VERSION"""
    
    print(f"\n🚀 SENDING TEST EMOTE")
    print(f"   👤 Target: {target_uid}")
    print(f"   🎭 Emote: {emote_id}")
    print("="*50)
    
    # 1. Create packet
    emote_packet = await Emote_k(target_uid, emote_id, key, iv, region)
    
    if not emote_packet:
        print("❌ Failed to create packet")
        return
    
    # 2. Send it
    print("📤 Sending packet...")
    if online_writer:
        online_writer.write(emote_packet)
        await online_writer.drain()
        print("✅ Packet sent!")
    else:
        print("❌ No connection")
        return
    
    # 3. Wait for response (SHORTER - 2 seconds)
    print("\n⏳ Waiting for response (2 seconds)...")
    
    responses = []
    start_time = time.time()
    
    while time.time() - start_time < 2:  # Reduced from 5 to 2 seconds
        try:
            # Read any response
            if reader:
                response = await asyncio.wait_for(reader.read(9999), timeout=0.1)
                if response:
                    resp_hex = response.hex()
                    responses.append(resp_hex)
                    
                    # Quick analysis
                    print(f"📥 Got response #{len(responses)}")
                    print(f"   Length: {len(resp_hex)} chars")
                    print(f"   Header: {resp_hex[:10]}")
                    
                    # Check if it's the emote echo
                    if '909' in resp_hex:
                        print(f"   🎭 Contains emote ID!")
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            # Silent error - don't print
            pass
    
    # 4. Summary
    print(f"\n📊 RESPONSE SUMMARY")
    print(f"Total responses: {len(responses)}")
    
    if len(responses) > 0:
        print("✅ SUCCESS! Server accepted your emote packet!")
    else:
        print("⚠️ No immediate response (might still be processing)")
        
async def handle_guest_generation(count, uid, chat_id, chat_type, key, iv):
    """Handle guest generation in background and send updates"""
    try:
        # Start generation
        accounts = await generate_and_save_accounts(count)
        
        # Send completion message
        if accounts:
            success_msg = f"""[B][C][FFFF00]✅ GUEST ACCOUNTS GENERATED!

📊 Generated: {len(accounts)}/{count} accounts
💾 Saved to: guest_accounts.json

📋 Format in file:
• uid: Account UID
• password: Account password
• name: BlackApis
• timestamp: Generation time

💡 Use accounts for:
• Multi-account spams
• Friend requests
• Testing purposes
"""
        else:
            success_msg = f"""[B][C][FF0000]❌ GENERATION FAILED!

📊 Requested: {count} accounts
❌ Generated: 0 accounts

💡 Try:
1. Check internet connection
2. API might be down
3. Try smaller count (like 5)
4. Try again later
"""
        
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
        
        # Optional: Send first account as preview
        if accounts:
            preview_msg = f"""[B][C][FFFF00]🔍 FIRST ACCOUNT PREVIEW:

👤 UID: {accounts[0]['uid']}
🔑 Pass: {accounts[0]['password']}
📛 Name: {accounts[0]['name']}

💡 Check guest_accounts.json for all accounts!
"""
            await safe_send_message(chat_type, preview_msg, uid, chat_id, key, iv)
            
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Generation error: {str(e)[:50]}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)        
        
async def start_auto_packet(key, iv, region):
    """Create start match packet"""
    fields = {
        1: 9,
        2: {
            1: 12480598706,
        },
    }
    
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"
        
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet_type, key, iv)
        
async def detect_and_hijack_emote(data_hex, key, iv, bot_uid, region):
    """Detect emote and hijack it by sending with bot's UID"""
    try:
        # Detect emote info
        emote_info = await extract_emote_info(data_hex, key, iv)
        
        if not emote_info or not emote_info.get('sender_uid'):
            return False
        
        sender_uid = emote_info['sender_uid']
        emote_id = emote_info['emote_id']
        
        print(f"\n🎭 EMOTE DETECTED FOR HIJACK!")
        print(f"   👤 Original Sender: {sender_uid}")
        print(f"   🎭 Emote ID: {emote_id}")
        
        # Don't hijack bot's own emotes
        if int(sender_uid) == bot_uid:
            print("⚠️ Skipping - bot's own emote")
            return False
        
        # HIJACK: Send emote with bot's UID instead
        print(f"🤖 HIJACKING EMOTE! Sending as bot {bot_uid}...")
        
        # Use either of your emote functions
        # Method 1: Using Emote_k (your second packet)
        hijack_packet = await Emote_k(
            int(bot_uid),  # Use BOT'S UID instead of sender's
            int(emote_id),  # Same emote ID
            key, iv, region
        )
        
        # Alternative: Using emote_send (your first packet)
        # hijack_packet = await create_hijacked_emote(bot_uid, emote_id, key, iv, region)
        
        if hijack_packet and online_writer:
            # Send the hijacked emote
            online_writer.write(hijack_packet)
            await online_writer.drain()
            
            print(f"✅ Emote hijacked! Bot {bot_uid} now appears to do emote {emote_id}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Emote hijack error: {e}")
        return False
        
async def SwitchLoneWolfDule(BotUid, key, iv):
    fields = {1: 17, 2: {1: BotUid, 2: 1, 3: 1, 4: 43, 5: "\u000b", 8: 1, 19: 1}}
    return await GenPacket((await CreateProtobufPacket(fields)).hex(), '0519', key, iv)        
        
async def KickTarget(target_uid, key, iv):
    fields = {1: 35, 2: {1: int(target_uid)}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515' , key, iv)
        
async def create_hijacked_emote(hijacker_uid, emote_id, key, iv, region):
    """Create emote packet that appears to come from hijacker"""
    try:
        # Using your Emote_k structure but with hijacker's UID
        fields = {
            1: 21,  # Emote packet type
            2: {
                1: 804266360,  # Some identifier (keep as is)
                2: 909000001,  # Base emote ID
                5: {
                    1: int(hijacker_uid),  # HIJACKER'S UID goes here
                    3: int(emote_id),      # The emote ID to perform
                }
            }
        }
        
        if region.lower() == "ind":
            packet = '0514'
        elif region.lower() == "bd":
            packet = "0519"
        else:
            packet = "0515"
            
        return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet, key, iv)
        
    except Exception as e:
        print(f"❌ Error creating hijacked emote: {e}")
        return None
            
def analyze_hex_packet(packet_hex):
    """Analyze hex packet structure"""
    
    print(f"\n🔬 HEX PACKET ANALYSIS")
    print("="*50)
    
    # Header analysis
    header = packet_hex[:10]
    print(f"Header (first 5 bytes): {header}")
    
    # Common headers:
    # 0514 = IND online packet
    # 0519 = BD online packet  
    # 1215 = Whisper packet
    # 1200 = Chat packet
    
    if header.startswith('05'):
        print("📡 Online connection packet")
    elif header.startswith('12'):
        print("💬 Whisper/Chat packet")
    
    # Look for UIDs (9-11 digit numbers in hex)
    import re
    
    # Find all sequences of 9+ hex digits
    hex_patterns = re.findall(r'[0-9a-f]{9,12}', packet_hex.lower())
    
    print(f"\n🔢 Hex sequences found:")
    for pattern in hex_patterns[:10]:  # Show first 10
        # Try to convert to decimal
        try:
            decimal = int(pattern, 16)
            if 1000000 < decimal < 99999999999:  # Reasonable UID range
                print(f"  {pattern} → {decimal} (Possible UID)")
            elif decimal > 900000000:  # Emote ID range
                print(f"  {pattern} → {decimal} (Possible emote ID)")
        except:
            print(f"  {pattern}")
    
    # Show packet content (first 200 chars)
    print(f"\n📝 Packet preview (first 200 chars):")
    print(packet_hex[:200])
    
    if len(packet_hex) > 200:
        print(f"... and {len(packet_hex) - 200} more characters")
        
def append_to_whitelist(uid_to_add):
    """Simple function to add UID to whitelist"""
    global WHITELISTED_UIDS
    
    uid_str = str(uid_to_add)
    
    if uid_str in WHITELISTED_UIDS:
        return False, f"UID {uid_str} already in whitelist"
    
    WHITELISTED_UIDS.add(uid_str)
    return True, f"✅ Added {uid_str} to whitelist"        
        
async def hijack_squad_emote(data_hex, key, iv, bot_uid, region, in_squad):
    """Only hijack emotes when bot is in a squad"""
    if not in_squad:
        return False
    
    try:
        # Extract emote info
        emote_info = await extract_emote_info(data_hex, key, iv)
        
        if not emote_info:
            return False
        
        sender_uid = emote_info['sender_uid']
        emote_id = emote_info['emote_id']
        
        print(f"\n🏆 SQUAD EMOTE HIJACK!")
        print(f"   👥 In squad: Yes")
        print(f"   👤 Original: {sender_uid}")
        print(f"   🎭 Emote: {emote_id}")
        
        # Create hijacked emote
        hijack_packet = await create_hijacked_emote(bot_uid, emote_id, key, iv, region)
        
        if hijack_packet and online_writer:
            online_writer.write(hijack_packet)
            await online_writer.drain()
            
            print(f"✅ Squad emote hijacked by bot {bot_uid}!")
            
            # Optional: Also send the original emote to maintain appearance
            #await asyncio.sleep(0.3)
            original_packet = await Emote_k(int(sender_uid), int(emote_id), key, iv, region)
            online_writer.write(original_packet)
            await online_writer.drain()
            
            print(f"✅ Also sent original emote to maintain cover")
            
            return True
            
    except Exception as e:
        print(f"❌ Squad hijack error: {e}")
    
    return False
    
async def send_friend_request_async(target_uid: str, count: int = 1) -> dict:
    """
    Main function to send friend requests from TCP bot
    
    Args:
        target_uid: Target player UID
        count: Number of requests (1 for single, >1 for bulk)
    
    Returns:
        Dictionary with results
    """
    try:
        if count == 1:
            # Single request using token.json
            token = load_jwt_token()
            if not token:
                return {"success": 0, "failed": 1, "error": "No token found"}
            
            success = send_friend_request_single(target_uid, token)
            
            if success:
                return {"success": 1, "failed": 0}
            else:
                return {"success": 0, "failed": 1}
                
        else:
            # Bulk requests using token_ind.json
            tokens = load_tokens_ind()
            if not tokens:
                return {"success": 0, "failed": 0, "error": "No tokens found"}
            
            max_count = min(count, len(tokens))
            results = {"success": 0, "failed": 0}
            
            print(f"📦 Sending {max_count} friend requests...")
            
            # Send requests sequentially (or use threading for faster)
            for i in range(max_count):
                token = tokens[i]['token']
                success = send_friend_request_single(target_uid, token)
                
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            
            return results
            
    except Exception as e:
        print(f"❌ Friend request error: {e}")
        return {"success": 0, "failed": 0, "error": str(e)}    

async def TcPOnLine(ip, port, key, iv, AutHToKen, reconnect_delay=0.5):
    global online_writer, last_status_packet, status_response_cache, senthi
    global insquad, joining_team, whisper_writer, region
 
    bot_uid = 14010319252
 
    if insquad is not None:
        insquad = None
    if joining_team is True:
        joining_team = False
    
    online_writer = None
    whisper_writer = None
    
    while True:
        try:
            print(f"Attempting to connect to {ip}:{port}...")
            reader, writer = await asyncio.open_connection(ip, int(port))
            online_writer = writer
            
            # --- AUTHENTICATION ---
            bytes_payload = bytes.fromhex(AutHToKen)
            online_writer.write(bytes_payload)
            await online_writer.drain()
            print("Authentication token sent. Listening for emotes...")
            
            # --- READING LOOP ---
            while True:
                data2 = await reader.read(9999)
                    
                if not data2: 
                    print("Connection closed by the server.")
                    break
                    
                data_hex = data2.hex()
      
                # Your existing code...
  
                
                
              # =================== EMOTE DETECTION ONLY ===================
                if data_hex.startswith("0500") and emote_hijack == True:
                    try:
                        # Try to detect emote
                        emote_info = await extract_emote_info(data_hex, key, iv)
                        
                        in_squad = insquad is not None
            

                

                        
                        if emote_info and emote_info.get('sender_uid'):
                            sender_uid = emote_info['sender_uid']
                            #sender_uid = BLOCK_EMOTE_UID
                            emote_id = emote_info['emote_id']
                            
                            
                            
                            print(f"\n🎯 EMOTE DETECTED!")
                            print(f"   👤 Sender UID: {sender_uid}")
                            print(f"   🎭 Emote ID: {emote_id}")
                            
                            # Don't respond to bot's own emotes
                            if int(sender_uid) != bot_uid:
                                print("🤖 Bot responding with dual emotes...")

                                #sender_uid = BLOCK_EMOTE_UID

                                # STEP 1: Send fixed emote 909035003 to the sender
                                print(f"  1️⃣ Sending emote 909035003 to {sender_uid}")
                                fixed_emote_packet = await Emote_k(
                                    int(sender_uid), 
                                    909035003,  # Fixed emote ID
                                    key, iv, region
                                )
                                if fixed_emote_packet and online_writer:
                                    online_writer.write(fixed_emote_packet)
                                    await online_writer.drain()
                                    #await asyncio.sleep(0.1)
                                
                                # STEP 2: Bot does the SAME emote that user did (to itself)
                                print(f"  2️⃣ Bot doing same emote {emote_id} to itself")
                                bot_self_emote = await Emote_k(
                                    bot_uid,  # Bot's own UID
                                    int(emote_id),  # Same emote user did
                                    key, iv, region
                                )
                                if bot_self_emote and online_writer:
                                    online_writer.write(bot_self_emote)
                                    await online_writer.drain()
                                    #await asyncio.sleep(0.01)

                                emote_to_sender = await Emote_k(int(BLOCK_EMOTE_UID), 909035003, key, iv, region)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_to_sender)

                                # STEP 3: Bot also sends the emote back to sender
                                print(f"  3️⃣ Mirroring emote {emote_id} back to {sender_uid}")
                                mirror_emote = await Emote_k(
                                    int(sender_uid),
                                    int(emote_id),  # Same emote back
                                    key, iv, region
                                )
                                if mirror_emote and online_writer:
                                    online_writer.write(mirror_emote)
                                    await online_writer.drain()
                                
                                print("✅ Dual emote response complete!")
                            
                            else:
                                print("⚠️ Skipping - bot's own emote")
                                
                    except Exception as e:
                        print(f"❌ Emote response error: {e}")
                        continue 
            
                    


                # =================== AUTO ACCEPT HANDLING ===================
                
                # Case 1: Squad is cancelled or left (6, 7 are often status/exit codes)
                if data_hex.startswith('0500') and insquad is not None and joining_team == False:
                    try:
                        # Assuming DeCode_PackEt and json.loads are available and correct
                        packet = await DeCode_PackEt(data_hex[10:])
                        packet_json = json.loads(packet)
                        
                        if packet_json.get('1') in [6, 7]: 
                             insquad = None
                             joining_team = False
                             print("Squad cancelled or exited (code 6/7).")
                             continue
                             
                    except Exception as e:
                        print(f"Error in auto-accept case 1: {e}")
                        pass
                
                # case 2
                # Case 2: Auto-accept for whitelisted users
                if data_hex.startswith("0500") and insquad is None and joining_team == False:
                    try:
                        packet = await DeCode_PackEt(data_hex[10:])
                        packet_json = json.loads(packet)
    
                        uid = packet_json['5']['data']['1']['data']
                        invite_uid = packet_json['5']['data']['2']['data']['1']['data']
                        squad_owner = packet_json['5']['data']['1']['data']  # Person inviting
                        code = packet_json['5']['data']['8']['data']
  

                        emote_id = 909040008
                        bot_uid = 2579372095
    
                        # 🎯 FIX: Check SQUAD_OWNER (person who clicked "invite")
                        if True:
                            print(f"✅ Whitelisted user {squad_owner} invited bot. Accepting...")
                        

                            print('sending join requests')

                            await accept_join(uid, 32768, key, iv)
                            
                            print('join requests sent')
                            
                            
                            await asyncio.sleep(0.1)
        

                            SendInv = await RedZed_SendInv(bot_uid, invite_uid, key, iv)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', SendInv)
                            inv_packet = await RejectMSGtaxt(squad_owner, uid, key, iv, region)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', inv_packet)
        
                            print(f"Received squad invite from {squad_owner}, accepting...")                  
                            Join = await ArohiAccepted(squad_owner, code, key, iv)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', Join)
                            

                            await asyncio.sleep(2)
                                                    
                            emote_to_sender = await Emote_k(int(uid), emote_id, key, iv, region)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_to_sender)
        
                            bot_emote = await Emote_k(int(bot_uid), emote_id, key, iv, region)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', bot_emote)
                            
                            
            
                            # Set squad status
                            insquad = True
                            print(f"🤖 Bot joined squad of {squad_owner}")
        
                            # ===== NEW: AUTO-WEAR BUNDLE ON JOIN =====
                            try:
                                # Choose random bundle from list
                                bundle_names = list(BUNDLE.keys())
                                if bundle_names:
                                    random_bundle = random.choice(bundle_names)
                                    bundle_id = BUNDLE[random_bundle]
                                    
                                    print(f"🎁 Auto-wearing bundle: {random_bundle}")
                                    
                                    # Send bundle packet
                                    bundle_packet_data = await bundle_packet_async(bundle_id, key, iv, region)
                                    if online_writer:
                                        online_writer.write(bundle_packet_data)
                                        await online_writer.drain()
                                        print(f"✅ Bundle {random_bundle} sent!")
                            except Exception as bundle_e:
                                print(f"❌ Auto-wear bundle error: {bundle_e}")
        
                        else:
                            try:
                                print(f"🚫 Bot is private! Ignoring invite from {squad_owner}")
                                 # Send quick reject message
                                bot_uid = 2579372095
                                message_text = f" Can't accept Your request Talk to NARUTO-CODEX"
                                private_msg_packet = await xSEndMsg(
                                    Msg=message_text,
                                    Tp=2,  # 2 = Private message
                                    Tp2=int(squad_owner),  # Recipient UID
                                    id=int(bot_uid),  # Sender UID (your bot)
                                    K=key,
                                    V=iv
                                )
                                print("got it")

                                if private_msg_packet and whisper_writer:
                                    # Send via Whisper connection (chat connection)
                                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', private_msg_packet)
                                else:
                                    print("can't do it")
                    
                                    
                            except Exception as e:
                                print(" got an error in can't accept")
    

                    except Exception as e:
                        print(f"Error in auto-accept: {e}")
                        insquad = None
                        joining_team = False
                        continue
                
                # =================== HANDLE KICK/RECONNECT ===================
                # Case 3: Bot was kicked and needs to re-join chat
                if data_hex.startswith('0500') and len(data_hex) > 1000:
                    try:
                        packet = await DeCode_PackEt(data_hex[10:])
                        packet_json = json.loads(packet)
                    
                        packet_type = packet_json.get('1')
        
                        # Detect ALL kick/leave packets
                        if packet_type in [6, 7, 8, 9, 10, 11, 12]:
                            print(f"🚪 Kick/Leave packet detected (Type: {packet_type}")
            
                            # RESET SQUAD STATUS
                            insquad = None
                            joining_team = False
            
                            print(f"✅ Bot reset after kick. Ready for new invites.")
                            
                            # Call rizak function on team leave/kick
                            try:
                                bot_uid = LoGinDaTaUncRypTinG.AccountUID if hasattr(LoGinDaTaUncRypTinG, 'AccountUID') else TarGeT
                                await handle_rizak_on_leave(bot_uid, chat_id, key, iv, XX)
                            except Exception as e:
                                print(f"❌ Rizak on leave error: {e}")
                            
                            # Try to extract squad info for possible reconnection
                            try:
                                if '5' in packet_json and 'data' in packet_json['5']:
                                    OwNer_UiD, CHaT_CoDe, SQuAD_CoDe = await GeTSQDaTa(packet_json)
                                    print(f"🔄 Attempting reconnection to squad {SQuAD_CoDe}...")
                    
                                    # Re-authenticate chat
                                    JoinCHaT = await AutH_Chat(3, OwNer_UiD, CHaT_CoDe, key, iv)
                                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', JoinCHaT)
                    
                                    print(f"✅ Chat re-authenticated for reconnection")
                            except:
                                print("⚠️ Could not extract squad info")
                                
                            continue  # Skip other handlers
        
                        # Also check for general squad data packets (for reconnection)
                        elif '5' in packet_json and 'data' in packet_json['5']:
                            try:
                                OwNer_UiD, CHaT_CoDe, SQuAD_CoDe = await GeTSQDaTa(packet_json)
                
                                # If we have squad data but insquad is None, try to reconnect
                                if insquad is None:
                                    print(f"🤖 Received squad data while not in squad. Attempting chat auth...")
                                    
                                    JoinCHaT = await AutH_Chat(3, OwNer_UiD, CHaT_CoDe, key, iv)
                                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', JoinCHaT)
                    
                                    # Optional welcome back message
                                    welcome_msg = """[B][C][FFFF00]🤖 Bot reconnected!"""
                                    P = await SEndMsG(0, welcome_msg, OwNer_UiD, OwNer_UiD, key, iv, region)
                                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                    
                            except:
                                pass  # Not a squad data packet
                
                    except Exception as e:
                        print(f"❌ Kick/reconnect handler error: {e}")
                        pass
                
                # case 5
                if insquad == True:
                    try:
                        # Assuming DeCode_PackEt, json.loads, GeTSQDaTa, AutH_Chat, SEndPacKeT are available
                        packet = await DeCode_PackEt(data_hex[10:])
                        packet_json = json.loads(packet)
                        
                        OwNer_UiD , CHaT_CoDe , SQuAD_CoDe = await GeTSQDaTa(packet_json)
                        
                        print(f"Received squad data for joining team, attempting chat auth for {OwNer_UiD}...")
                        JoinCHaT = await AutH_Chat(3 , OwNer_UiD , CHaT_CoDe, key,iv)
                        await SEndPacKeT(whisper_writer , online_writer , 'ChaT' , JoinCHaT)
                        
                        def get_random_color(): return "_" 
                        message = """[B][C]
[00FFFF]╔━━━─    [A80000]•[00FFFF]      ─━━╗
[00FFFF]    ✦ WELCOME TO ꫝʙʜɪㅤGᴍʀ TCP ✦
[00FFFF]╚━━━─[A80000] • [00FFFF]─━━━╝

[00FF00]🌟 Welcome To The Server 🌟

[FFD053]✨ Glad To Have You Here ✨

[FFD053]⚡ Respect Everyone • Stay Active ⚡

[FFFFFF]🚀 Use [A80000]/help[FFFFFF] To See All Commands 🚀

[A80000]◉━━━━━━━━━━━━━━◉"""
                        # In your auto-join (Old Handler) code, find this line:

                        P = await SEndMsG(0, message, OwNer_UiD, OwNer_UiD, key, iv, region)
                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                        
                        joining_team = False
                        insquad = None
                            
                    except Exception as e:
                        print(f"Error in joining_team chat auth: {e}")
                        # Removed the redundant inner try/except block.
                        pass
                
                if "0600" in data2.hex()[0:4] and len(data2.hex()) > 700:
                    accept_packet = f'08{data2.hex().split("08", 1)[1]}'
                    kk = get_available_room(accept_packet)
                    parsed_data = json.loads(kk)
                    #logging.info(parsed_data)

                    senthi = True

                if senthi == True:
                    
                    def get_random_color(): return "_" 
                    message =  """[B][C]
[00FFFF]╔━━━─    [A80000]•[00FFFF]      ─━━╗
[00FFFF]    ✦ WELCOME TO ꫝʙʜɪㅤGᴍʀ TCP ✦
[00FFFF]╚━━━─[A80000] • [00FFFF]─━━━╝

[00FF00]🌟 Welcome To The Server 🌟

[FFD053]✨ Glad To Have You Here ✨

[FFD053]⚡ Respect Everyone • Stay Active ⚡

[FFFFFF]🚀 Use [A80000]/help[FFFFFF] To See All Commands 🚀

[A80000]◉━━━━━━━━━━━━━━◉"""
                        # In your auto-join (Old Handler) code, find this line:

                    P = await SEndMsG(0, message, OwNer_UiD, OwNer_UiD, key, iv, region)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                    senthi = False

                # =================== STATUS HANDLER ===================
                if data_hex.startswith('0f00') and len(data_hex) > 100:
                    print(f"📡 Received status response packet")
    
                    try:
                        # Assuming the protocol structure: 0f00 + length bytes + 08 + actual proto data
                        # The split logic might need refinement based on the exact protocol
                        if '08' in data_hex:
                            proto_part = f'08{data_hex.split("08", 1)[1]}'
                        else:
                            print("⚠️ Status packet structure missing '08' marker.")
                            continue
        
                        # Assuming get_available_room is available
                        parsed_data = get_available_room(proto_part)
                        if parsed_data:
                            parsed_json = json.loads(parsed_data)
            
                            # Check if it's field 15 (player info)
                            if "2" in parsed_json and parsed_json["2"]["data"] == 15:
                                # Get player ID
                                player_id = parsed_json["5"]["data"]["1"]["data"]["1"]["data"]
                
                                # Assuming get_player_status is available
                                player_status = get_player_status(proto_part) 
                                print(f"✅ Parsed status for {player_id}: {player_status}")
                
                                # Create cache entry
                                cache_entry = {
                                    'status': player_status, 
                                    'packet': proto_part,
                                    'timestamp': time.time(),
                                    'full_packet': data_hex,
                                    'parsed_json': parsed_json
                                }
                
                                # --- SPECIAL CONDITION CHECK ---
                                try:
                                    StatusData = parsed_json
                                    if ("5" in StatusData and "data" in StatusData["5"] and 
                                        "1" in StatusData["5"]["data"] and "data" in StatusData["5"]["data"]["1"] and 
                                        "3" in StatusData["5"]["data"]["1"]["data"] and "data" in StatusData["5"]["data"]["1"]["data"]["3"] and 
                                        StatusData["5"]["data"]["1"]["data"]["3"]["data"] == 1 and 
                                        "11" in StatusData["5"]["data"]["1"]["data"] and "data" in StatusData["5"]["data"]["1"]["data"]["11"] and 
                                        StatusData["5"]["data"]["1"]["data"]["11"]["data"] == 1):
                
                                        print(f"🎯 SPECIAL CONDITION MET: Player {player_id} is in SOLO mode with special flag 11=1")
                                        cache_entry['special_state'] = 'SOLO_WITH_FLAG_1'
                
                                except Exception as cond_error:
                                    print(f"⚠️ Error checking special condition: {cond_error}")
                                # ------------------------------

                                # If in room, extract room ID
                                if "IN ROOM" in player_status:
                                    try:
                                        # Assuming get_idroom_by_idplayer is available
                                        room_id = get_idroom_by_idplayer(proto_part)
                                        if room_id:
                                            cache_entry['room_id'] = room_id
                                            print(f"🏠 Room ID extracted: {room_id}")
                                    except Exception as room_error:
                                        print(f"Failed to extract room ID: {room_error}")
                
                                # If in squad, extract leader
                                elif "INSQUAD" in player_status:
                                    try:
                                        # Assuming get_leader is available
                                        leader_id = get_leader(proto_part)
                                        if leader_id:
                                            cache_entry['leader_id'] = leader_id
                                            print(f"👑 Leader ID: {leader_id}")
                                    except Exception as leader_error:
                                        print(f"Failed to extract leader: {leader_error}")
                
                                # Save to FILE cache (Assuming save_to_cache is available)
                                save_to_cache(player_id, cache_entry)
                                print(f"✅ Saved to cache: {player_id} = {player_status}")
                
                    except Exception as e:
                        print(f"❌ Error parsing status: {e}")
                        import traceback
                        traceback.print_exc()
                
                # =================== END STATUS HANDLER ===================


            # --- CLEANUP AFTER INNER LOOP (Connection closed) ---
            if online_writer is not None:
                online_writer.close()
                await online_writer.wait_closed()
                online_writer = None
            
            if whisper_writer is not None:
                try:
                    whisper_writer.close()
                    await whisper_writer.wait_closed()
                except:
                    pass
                whisper_writer = None
                
            insquad = None
            joining_team = False
            
            print(f"Connection closed. Reconnecting in {reconnect_delay} seconds...")

        except ConnectionRefusedError:
            print(f"Connection refused by server at {ip}:{port}.")
        except asyncio.TimeoutError:
            print(f"Connection attempt to {ip}:{port} timed out.")
        except Exception as e:
            print(f"- ErroR With {ip}:{port} - {e}")
            traceback.print_exc() 
            
            # --- CLEANUP AFTER EXCEPTION ---
            if online_writer is not None:
                try:
                    online_writer.close()
                    await online_writer.wait_closed()
                except:
                    pass
                online_writer = None
            if whisper_writer is not None:
                try:
                    whisper_writer.close()
                    await whisper_writer.wait_closed()
                except:
                    pass
                whisper_writer = None
                
            insquad = None
            joining_team = False
            
        await asyncio.sleep(reconnect_delay)

async def send_keep_alive(key, iv, region):
    """Send keep-alive packet to maintain connection"""
    try:
        fields = {
            1: 99,  # Keep-alive packet type
            2: {
                1: int(time.time()),
                2: 1,  # Keep-alive flag
            }
        }
        
        if region.lower() == "ind":
            packet_type = '0514'
        elif region.lower() == "bd":
            packet_type = "0519"
        else:
            packet_type = "0515"
            
        packet = await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet_type, key, iv)
        return packet
    except Exception as e:
        print(f"❌ Keep-alive error: {e}")
        return None


async def send_likes_background_task(chat_type, sender_uid, chat_id, key, iv, target_uid, count=100, region="ME"):
    """
    Asynchronously runs the FreeFireBot (the main project's like bot) to send likes,
    or falls back to the external HTTP API if no local guest accounts are available.
    Runs completely in the background via asyncio.create_task (returning a Future),
    keeping the TCP chat connection fully responsive and non-blocking.
    """
    try:
        initial_msg = f"[B][C][00FFFF]⏳ Like Streak Initiated\nTarget UID: {target_uid}\nLikes Requested: {count}\nRegion: {region}\nRunning in background... 🚀"
        await safe_send_message(chat_type, initial_msg, sender_uid, chat_id, key, iv, region=region)
        
        # 1. Try to use local FreeFireBot if there are guest accounts
        has_local_guests = False
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "guests.db")
        
        try:
            if os.path.exists(db_path):
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM guests WHERE is_active = 1 AND region = ?", (region,))
                row = cursor.fetchone()
                active_count = row[0] if row else 0
                conn.close()
                if active_count > 0:
                    has_local_guests = True
        except Exception as e:
            print(f"Error checking guest db count: {e}")
            
        if has_local_guests and FreeFireBot is not None:
            print(f"Executing like streak locally using FreeFireBot: {count} likes to {target_uid}")
            bot = FreeFireBot()
            try:
                await bot.initialize()
                stats = await bot.send_likes(target_uid, count, region)
                success = stats.likes_sent
                failed = stats.likes_failed
                result_msg = f"""[B][C][00FF00]✅ Like Streak Completed
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━
[FFFF00]Target UID   : [FFFFFF]{target_uid}
[FFFF00]Region       : [FFFFFF]{region}
[FFFF00]Likes Sent   : [00FF00]{success}
[FFFF00]Likes Failed : [FF0000]{failed}
[00FFFF]━━━━━━━━━━━━━━━━━━━━━━━━"""
                await safe_send_message(chat_type, result_msg, sender_uid, chat_id, key, iv, region=region)
                return
            except Exception as e:
                print(f"Error running local FreeFireBot: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await bot.shutdown()
                
        # 2. Fallback to external API
        print(f"No local guests/bot found, falling back to external Like API for {target_uid}")
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            likes_result = await loop.run_in_executor(executor, send_likes, target_uid)
        await safe_send_message(chat_type, likes_result, sender_uid, chat_id, key, iv, region=region)
    except Exception as e:
        print(f"Error in send_likes_background_task: {e}")
        import traceback
        traceback.print_exc()
        try:
            await safe_send_message(chat_type, f"[B][C][FF0000]❌ Like Streak Error: {str(e)[:80]}", sender_uid, chat_id, key, iv, region=region)
        except:
            pass
        
                    

                            
async def TcPChaT(ip, port, AutHToKen, key, iv, LoGinDaTaUncRypTinG, ready_event, region , reconnect_delay=0.5):
    print(region, 'TCP CHAT')

    global whisper_writer , spammer_uid , spam_chat_id , spam_uid , online_writer , chat_id , XX , uid , Spy,data2, Chat_Leave, fast_spam_running, fast_spam_task, custom_spam_running, custom_spam_task, spam_request_running, spam_request_task, evo_fast_spam_running, evo_fast_spam_task, evo_custom_spam_running, evo_custom_spam_task, lag_running, lag_task, evo_cycle_running, evo_cycle_task, reject_spam_running, reject_spam_task, BLOCK_EMOTE_UID
    # At the VERY TOP of your file, with other globals:
    status_response_cache = {}
    cache_lock = asyncio.Lock()  # For thread safety
    while True:
        try:
            reader , writer = await asyncio.open_connection(ip, int(port))
            whisper_writer = writer
            bytes_payload = bytes.fromhex(AutHToKen)
            whisper_writer.write(bytes_payload)
            await whisper_writer.drain()
            ready_event.set()
            if LoGinDaTaUncRypTinG.Clan_ID:
                clan_id = LoGinDaTaUncRypTinG.Clan_ID
                clan_compiled_data = LoGinDaTaUncRypTinG.Clan_Compiled_Data
                print('\n - TarGeT BoT in CLan ! ')
                print(f' - Clan Uid > {clan_id}')
                print(f' - BoT ConnEcTed WiTh CLan ChaT SuccEssFuLy ! ')
                pK = await AuthClan(clan_id , clan_compiled_data , key , iv)
                if whisper_writer: whisper_writer.write(pK) ; await whisper_writer.drain()
            while True:
                data = await reader.read(9999)
                if not data: break
                
                if data.hex().startswith("120000"):

                    msg = await DeCode_PackEt(data.hex()[10:])
                    chatdata = json.loads(msg)
                    try:
                        response = await DecodeWhisperMessage(data.hex()[10:])
                        uid = response.Data.uid
                        chat_id = response.Data.Chat_ID
                        XX = response.Data.chat_type
                        inPuTMsG = response.Data.msg.lower()
                        MsG = response.Data.msg.lower()
                        original_msg = response.Data.msg

                    except:
                        response = None

                    # =================== STICKER DETECTION AND AUTO-REPLY WITH EMOTE ===================
                    try:
                        if "5" in chatdata and "data" in chatdata["5"]:
                            inner = chatdata["5"]["data"]
                            if "8" in inner and "data" in inner["8"]:
                                raw_data = inner["8"]["data"]
                                try:
                                    sticker_json = json.loads(raw_data)
                                    if sticker_json.get("type") == "Sticker":
                                        # Extract sender UID
                                        target_uid = inner["1"]["data"]
                                        # Choose a random emote from NUMBER_EMOTES
                                        if NUMBER_EMOTES:
                                            random_emote_key = random.choice(list(NUMBER_EMOTES.keys()))
                                            emote_id = NUMBER_EMOTES[random_emote_key]
                                            # Send emote to the sticker sender
                                            emote_packet = await Emote_k(int(target_uid), int(emote_id), key, iv, region)
                                            if emote_packet and online_writer:
                                                online_writer.write(emote_packet)
                                                await online_writer.drain()
                                except Exception as e:
                                    pass
                    except Exception as e:
                        pass

                    # ============ WHITELIST CHECK ============
                    if response:
                        await handle_greeting(inPuTMsG, uid, chat_id, response.Data.chat_type, key, iv, region)


                        
                        # AI Command -  
                        if inPuTMsG.strip().startswith('  '):
                            print('Processing AI command in any chat type')
                            
                            question = inPuTMsG[4:].strip()
                            if question:
                                initial_message = f"[B][C]{get_random_color()}\n🤖 AI is thinking...\n"
                                await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                                
                                # Use ThreadPoolExecutor to avoid blocking the async loop
                                loop = asyncio.get_event_loop()
                                with ThreadPoolExecutor() as executor:
                                    ai_response = await loop.run_in_executor(executor, talk_with_ai, question)
                                
                                # Format the AI response
                                ai_message = f"""
[B][C][FFFF00]🤖 AI Response:

[FFFFFF]{ai_response}

[C][B][FFB300]Question: [FFFFFF]{question}
"""
                                await safe_send_message(response.Data.chat_type, ai_message, uid, chat_id, key, iv)
                            else:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Please provide a question after  \nExample:   What is Free Fire?\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # Likes Command - /likes
                        if inPuTMsG.strip().startswith('/likes '):
                            print('Processing likes command in any chat type')
                            
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /likes (uid)\nExample: /likes 123456789\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
                                # Run the like streak asynchronously as a background task (Future/Task)
                                asyncio.create_task(
                                    send_likes_background_task(
                                        response.Data.chat_type,
                                        uid,
                                        chat_id,
                                        key,
                                        iv,
                                        target_uid,
                                        count=100,
                                        region=region
                                    )
                                )

                        # FREEZE COMMAND - /freeze [uid]
                        if inPuTMsG.strip().startswith('/freeze'):
                            print('Processing freeze command')
    
                            parts = inPuTMsG.strip().split()
    
                            if len(parts) < 2:
                                error_msg = f"""[B][C][00FFFF]❄️ FREEZE COMMAND

❌ Usage: /freeze (uid)
        
📝 Examples:
/freeze me - Freeze yourself
/freeze 123456789 - Freeze specific UID

🎯 What it does:
• Sends 3 ice/freeze emotes in sequence
• 1-second cycles for 10 seconds total
• Emotes: 909040004 → 909050008 → 909000002
• Creates a "freeze" effect!

💡 Use /stop_freeze to stop early
"""
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
                                
                                # Handle "me" or "self"
                                if target_uid.lower() in ['me', 'self', 'myself']:
                                    target_uid = str(response.Data.uid)
                                    target_name = "Yourself"
                                else:
                                    target_name = f"UID {target_uid}"
                                
                                # Stop any existing freeze task
                                global freeze_running, freeze_task
                                if freeze_task and not freeze_task.done():
                                    freeze_running = False
                                    freeze_task.cancel()
                                    await asyncio.sleep(0.5)
        
                                # Send initial message
                                initial_msg = f"""[B][C][00FFFF]❄️ FREEZE COMMAND STARTING!

🎯 Target: {target_name}
⏱️ Duration: {FREEZE_DURATION} seconds
🔄 Cycle: 1 second (3 emotes each)
🎭 Sequence: 
  1. 909040004 (Ice)
  2. 909050008 (Frozen) 
  3. 909000002 (Freeze)

⏳ Starting freeze sequence...
"""
                                await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
        
                                # Start freeze task
                                freeze_running = True
                                freeze_task = asyncio.create_task(
                                    freeze_emote_spam(target_uid, key, iv, region, response.Data.chat_type, chat_id, uid)
                                )
        
                                # Handle completion
                                asyncio.create_task(
                                    handle_freeze_completion(freeze_task, target_uid, uid, chat_id, response.Data.chat_type, key, iv)
                                )

                        if inPuTMsG.strip().startswith('/bio'):
                            print('📝 Processing bio change command')
    
                            parts = inPuTMsG.strip().split(maxsplit=1)
    
                            if len(parts) < 2:
                                error_msg = f"""[B][C][FF0000]❌ Usage: /bio (your bio text)

📝 Examples:
/bio Hello World!
/bio 🤖 Bot by APPLE GAMING FF 
/bio Level 70 | Pro Player
/bio Add me: APPLE GAMING FF 

✨ Features:
• Changes bot's profile bio instantly
• Supports emojis and special characters
• Max length: 50 characters

💡 Note: Bio changes appear immediately in profile!
"""
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                bio_text = parts[1]
                                
                                # Check length
                                if len(bio_text) > 50:
                                    error_msg = f"[B][C][FF0000]❌ Bio too long! Max 50 characters.\n📝 Your bio: {len(bio_text)} chars\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    return
        
                                # Send initial message
                                initial_msg = f"[B][C][FFFF00]📝 UPDATING BIO...\n📋 Bio: {bio_text[:30]}...\n⏳ Please wait...\n"
                                await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
        
                                # FIXED: Handle credentials properly
                                credentials = load_credentials_from_file("bot.txt")
                                if not credentials:
                                    error_msg = f"[B][C][FF0000]❌ Failed to load credentials from file!\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    return
            
                                try:
                                    Uid, Pw = credentials
                                except:
                                    # If credentials returns more than 2 values, take first 2
                                    Uid = credentials[0] if isinstance(credentials, (list, tuple)) else None
                                    Pw = credentials[1] if isinstance(credentials, (list, tuple)) and len(credentials) > 1 else None
        
                                if not Uid or not Pw:
                                    error_msg = f"[B][C][FF0000]❌ Invalid credentials format!\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    return
        
                                # Add retry logic for bio update
                                max_retries = 3
                                retry_delay = 2  # seconds
                                success = False
                                result = None
        
                                for attempt in range(max_retries):
                                    try:
                                        print(f"🔄 Bio update attempt {attempt + 1}/{max_retries}")
                
                                        # Get fresh token for each attempt
                                        open_id, access_token = await GeNeRaTeAccEss(Uid, Pw)
                                        if not open_id or not access_token:
                                            print(f"❌ Failed to generate access token on attempt {attempt + 1}")
                                            await asyncio.sleep(retry_delay)
                                            continue
                
                                        PyL = await EncRypTMajoRLoGin(open_id, access_token)
                                        MajoRLoGinResPonsE = await MajorLogin(PyL)
                                        MajoRLoGinauTh = await DecRypTMajoRLoGin(MajoRLoGinResPonsE)
                
                                        if not MajoRLoGinauTh or not MajoRLoGinauTh.token:
                                            print(f"❌ No token received on attempt {attempt + 1}")
                                            await asyncio.sleep(retry_delay)
                                            continue
                
                                        token = MajoRLoGinauTh.token
                                        print(f"🔑 Using token: {token[:20]}...")
                
                                        # Call bio update with retry
                                        result = await set_bio_directly_async_with_retry(token, bio_text, region)
                                        
                                        if result.get("success"):
                                            success = True
                                            break
                                        else:
                                            print(f"❌ Bio update failed on attempt {attempt + 1}: {result.get('message')}")
                                            if attempt < max_retries - 1:
                                                # Send progress update
                                                progress_msg = f"[B][C][FFFF00]🔄 Retrying... (Attempt {attempt + 2}/{max_retries})\n"
                                                await safe_send_message(response.Data.chat_type, progress_msg, uid, chat_id, key, iv)
                                                await asyncio.sleep(retry_delay)
                        
                                    except Exception as e:
                                        print(f"❌ Attempt {attempt + 1} error: {e}")
                                        if attempt < max_retries - 1:
                                            await asyncio.sleep(retry_delay)
                                        continue
        
                                # Send final result
                                if success:
                                    success_msg = f"""[B][C][FFFF00]✅ BIO UPDATED SUCCESSFULLY!

📝 Bio: {bio_text}
🌍 Region: {result.get('region', region)}
🔧 Attempts: {attempt + 1}/{max_retries}
🤖 Bot: Profile updated instantly!

💡 Check bot's profile to see new bio!
"""
                                else:
                                    success_msg = f"""[B][C][FF0000]❌ BIO UPDATE FAILED AFTER {max_retries} ATTEMPTS!

📝 Bio: {bio_text}
❌ Error: {result.get('message', 'All attempts failed')}

💡 Try:
1. Check bot's connection
2. Try shorter bio text
3. Wait 1 minute and try again
"""
        
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
            
                                                # /lw command - Auto Start Bot
                        if inPuTMsG.strip().startswith('/lw'):
                            print('Processing /lw auto-start command')
                            global auto_start_running, auto_start_teamcode, stop_auto, auto_start_task
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /lw (team_code)\nExample: /lw 123456\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                team_code = parts[1]
                                
                                # Check if numeric
                                if not team_code.isdigit():
                                    error_msg = f"[B][C][FF0000]❌ ERROR! Team code must be numbers only!\nExample: /lw 123456\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    continue
                                
                                # Check if already running
                                if auto_start_running:
                                    error_msg = f"[B][C][FF0000]❌ ERROR! Auto start already running for team {auto_start_teamcode}!\nUse /stop_auto to stop first.\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    continue
                                
                                # Start auto start
                                global auto_start_task, stop_auto
                                stop_auto = False
                                auto_start_running = True
                                auto_start_teamcode = team_code
                                
                                # Send initial message
                                initial_msg = f"""
[B][C][00FFFF]🤖 AUTO START BOT ACTIVATED!

🎯 Team Code: {team_code}
⚡ Action: Join → Start → Wait → Leave → Repeat
⏰ Start Spam: {start_spam_duration} seconds
⏳ Wait Time: {wait_after_match} seconds
🔄 Loop: Continuous 24x7

💡 To stop: /stop_auto
"""
                                await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
                                
                                # Start auto loop in background
                                auto_start_task = asyncio.create_task(
                                    auto_start_loop(team_code, uid, chat_id, response.Data.chat_type, key, iv, region)
                                )
                        # EVO CYCLE START COMMAND - /random
                        if inPuTMsG.strip().startswith('/random'):
                            print('Processing evo cycle start command in any chat type')
                            # Declare global variables

                            parts = inPuTMsG.strip().split()
                            uids = []
    
                            # Always use the sender's UID (the person who typed /random)
                            sender_uid = str(response.Data.uid)
                            uids.append(sender_uid)
                            print(f"Using sender's UID: {sender_uid}")
    
                            # Optional: Also allow specifying additional UIDs
                            if len(parts) > 1:
                                for part in parts[1:]:  # Skip the first part which is "/random"
                                    if part.isdigit() and len(part) >= 7 and part != sender_uid:  # UIDs are usually 7+ digits
                                        uids.append(part)
                                        print(f"Added additional UID: {part}")

                            # Stop any existing evo cycle
                            if evo_cycle_task and not evo_cycle_task.done():
                                evo_cycle_running = False
                                evo_cycle_task.cancel()
                                await asyncio.sleep(0.5)
    
                            # Start new evo cycle
                            evo_cycle_running = True
                            evo_cycle_task = asyncio.create_task(evo_cycle_spam(uids, key, iv, region))
    
                            # SUCCESS MESSAGE
                            if len(uids) == 1:
                                success_msg = f"[B][C][00FF00]✅ SUCCESS! Evolution emote cycle started!\n🎯 Target: Yourself\n🎭 Emotes: All 18 evolution emotes\n⏰ Delay: 5 seconds between emotes\n🔄 Cycle: Continuous loop until /sevos\n"
                            else:
                                success_msg = f"[B][C][00FF00]✅ SUCCESS! Evolution emote cycle started!\n🎯 Targets: Yourself + {len(uids)-1} other players\n🎭 Emotes: All 18 evolution emotes\n⏰ Delay: 5 seconds between emotes\n🔄 Cycle: Continuous loop until /sevos\n"
    
                            await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            print(f"Started evolution emote cycle for UIDs: {uids}")
                        if inPuTMsG.strip().startswith('/praisa'):
                            await handle_praisa_command(inPuTMsG, uid, chat_id, response.Data.chat_type, key, iv, region)
                        # EVO CYCLE STOP COMMAND - /sevos
                        if inPuTMsG.strip() == '/sevos':
                            if evo_cycle_task and not evo_cycle_task.done():
                                evo_cycle_running = False
                                evo_cycle_task.cancel()
                                success_msg = f"[B][C][00FF00]✅ SUCCESS! Evolution emote cycle stopped successfully!\n"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                print("Evolution emote cycle stopped by command")
                            else:
                                error_msg = f"[B][C][FF0000]❌ ERROR! No active evolution emote cycle to stop!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # Fast emote spam command - works in all chat types
                        if inPuTMsG.strip().startswith('/fast'):
                            print('Processing fast emote spam in any chat type')
                            
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 3:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /fast uid1 [uid2] [uid3] [uid4] emoteid\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                # Parse uids and emoteid
                                uids = []
                                emote_id = None
                                
                                for part in parts[1:]:
                                    if part.isdigit():
                                        if len(part) > 3:  # Assuming UIDs are longer than 3 digits
                                            uids.append(part)
                                        else:
                                            emote_id = part
                                    else:
                                        break
                                
                                if not emote_id and parts[-1].isdigit():
                                    emote_id = parts[-1]
                                
                                if not uids or not emote_id:
                                    error_msg = f"[B][C][FF0000]❌ ERROR! Invalid format! Usage: /fast uid1 [uid2] [uid3] [uid4] emoteid\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    # Stop any existing fast spam
                                    if fast_spam_task and not fast_spam_task.done():
                                        fast_spam_running = False
                                        fast_spam_task.cancel()
                                    
                                    # Start new fast spam
                                    fast_spam_running = True
                                    fast_spam_task = asyncio.create_task(fast_emote_spam(uids, emote_id, key, iv, region))
                                    
                                    # SUCCESS MESSAGE
                                    success_msg = f"[B][C][00FF00]✅ SUCCESS! Fast emote spam started!\nTargets: {len(uids)} players\nEmote: {emote_id}\nSpam count: 25 times\n"
                                    await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                
                        # QUICK EMOTE ATTACK COMMAND - /quick  [team_code] [emote_id] [target_uid?]
                        if inPuTMsG.strip().startswith('/quick '):
                            print('Processing quick emote attack command')
    
                            parts = inPuTMsG.strip().split()
    
                            if len(parts) < 3:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /quick  (team_code) [emote_id] [target_uid]\n\n[FFFFFF]Examples:\n[FFFF00]/quick  ABC123[FFFFFF] - Join, send Rings emote, leave\n[FFFF00]/quick ABC123[FFFFFF] - Ghost join, send emote, leave\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                team_code = parts[1]
        
                                # Set default values
                                emote_id = parts[0]
                                target_uid = str(response.Data.uid)  # Default: Sender's UID
        
                                # Parse optional parameters
                                if len(parts) >= 3:
                                    emote_id = parts[2]
                                if len(parts) >= 4:
                                    target_uid = parts[3]
        
                                # Determine target name for message
                                if target_uid == str(response.Data.uid):
                                    target_name = "Yourself"
                                else:
                                    target_name = f"UID {target_uid}"
        
                                initial_message = f"[B][C][FFFF00]⚡ QUICK EMOTE ATTACK!\n\n[FFFFFF]🎯 Team: [FFFF00]{team_code}\n[FFFFFF]🎭 Emote: [FFFF00]{emote_id}\n[FFFFFF]👤 Target: [FFFF00]{target_name}\n[FFFFFF]⏱️ Estimated: [FFFF00]2 seconds\n\n[FFFF00]Executing sequence...\n"
                                await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
        
                                try:
                                    # Try regular method first
                                    success, result = await ultra_quick_emote_attack(team_code, emote_id, target_uid, key, iv, region)
            
                                    if success:
                                        success_message = f"[B][C][FFFF00]✅ QUICK ATTACK SUCCESS!\n\n[FFFFFF]🏷️ Team: [FFFF00]{team_code}\n[FFFFFF]🎭 Emote: [FFFF00]{emote_id}\n[FFFFFF]👤 Target: [FFFF00]{target_name}\n\n[FFFF00]Bot joined → emoted → left! ✅\n"
                                    else:
                                        success_message = f"[B][C][FF0000]❌ Regular attack failed: {result}\n"
                                    
                                    await safe_send_message(response.Data.chat_type, success_message, uid, chat_id, key, iv)
            
                                except Exception as e:
                                    print("failed")
                                        
                        if inPuTMsG.strip().startswith('/xjoin '):
                            print('Processing xjoin command')
                            await handle_xjoin_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)
            
                        # Invite Command - /inv (creates 5-player group and sends request)
                        if inPuTMsG.strip().startswith('/inv'):
                            print('Processing invite command in any chat type')
                            
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /inv (uid)\nExample: /inv 123🙂45🙂67🙂89\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
                                initial_message = f"[B][C]{get_random_color()}\n and sending request to {xMsGFixinG(target_uid)}...\n"
                                await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                                
                                try:
                                    # Fast squad creation and invite for 5 players
                                    V = await SEnd_InV(5, int(target_uid), key, iv, region)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
                                    await asyncio.sleep(0.3)
                                    

                                    # SUCCESS MESSAGE
                                    success_message = f"[B][C][FFFF00]✅ SUCCESS! Group invitation sent successfully to {xMsGFixinG(target_uid)}!\n"
                                    await safe_send_message(response.Data.chat_type, success_message, uid, chat_id, key, iv)
                                    
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ ERROR sending invite: {str(e)}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        if inPuTMsG.strip().lower().startswith("/gender "):
                            try:
                                gp = inPuTMsG.strip().split(maxsplit=1)
                                gname = gp[1].strip() if len(gp) > 1 else "Unknown"
                                gresult = random.choice(GENDER_RESPONSES)
                                gmsg = f"[B][C][FF00FF]╔════════════════════╗\n║ 👤 Gender Check\n║\n║ [FFFFFF]{gname} => [00FFFF]{gresult}\n╚════════════════════╝"
                                await safe_send_message(response.Data.chat_type, gmsg, uid, chat_id, key, iv)
                            except Exception as e:
                                print(f"Error in /gender: {e}")
                        # Invite Command - /inv (creates 5-player group and sends request)
                        if inPuTMsG.strip().startswith('/snd'):
                            print('Processing invite command in any chat type')
                            
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /snd (uid)\nExample: /inv 123🙂45🙂67🙂89\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
                                initial_message = f"[B][C]{get_random_color()}\nCreating 5-Player Group and sending request to {target_uid}...\n"
                                await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                                
                                try:
                                    # Fast squad creation and invite for 5 players
                                    PAc = await OpEnSq(key, iv, region)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
                                    await asyncio.sleep(0.3)
                                    
                                    C = await cHSq(5, int(target_uid), key, iv, region)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)
                                    await asyncio.sleep(0.3)
                                    
                                    V = await SEnd_InV(5, int(target_uid), key, iv, region)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
                                    await asyncio.sleep(0.3)
                                    
                                    E = await ExiT(None, key, iv)
                                    await asyncio.sleep(2)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', E)
                                    
                                    # SUCCESS MESSAGE
                                    success_message = f"[B][C][FFFF00]✅ SUCCESS! 5-Player Group invitation sent successfully to {target_uid}!\n"
                                    await safe_send_message(response.Data.chat_type, success_message, uid, chat_id, key, iv)
                                    
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ ERROR sending invite: {str(e)}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                                #GET PLAYER LIKE
                        if inPuTMsG.strip().startswith('/like'):
                            print('Processing like command in any chat type')

                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /like <uid>\nExample: /like 123456789\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
                                # Run the like streak asynchronously as a background task (Future/Task)
                                asyncio.create_task(
                                    send_likes_background_task(
                                        response.Data.chat_type,
                                        uid,
                                        chat_id,
                                        key,
                                        iv,
                                        target_uid,
                                        count=100,
                                        region=region
                                    )
                                )



                        if inPuTMsG.startswith(("/6")):
                            # Process /6 command - Create 4 player group
                            initial_message = f"[B][C]{get_random_color()}\n\nCreating 6-Player Group...\n\n"
                            await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                            
                            # Fast squad creation and invite for 4 players
                            PAc = await OpEnSq(key, iv, region)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
                            
                            C = await cHSq(6, uid, key, iv, region)
                            await asyncio.sleep(0.3)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)
                            
                            V = await SEnd_InV(6, uid, key, iv, region)
                            await asyncio.sleep(0.3)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
                            
                            E = await ExiT(None, key, iv)
                            await asyncio.sleep(3.5)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', E)
                            
                            # SUCCESS MESSAGE
                            success_message = f"[B][C][FFFF00]✅ SUCCESS! 6-Player Group invitation sent successfully to {uid}!\n"
                            await safe_send_message(response.Data.chat_type, success_message, uid, chat_id, key, iv)

                        # Add these lines to your existing command dispatcher:

                        if inPuTMsG.startswith('/spamroom ') or inPuTMsG == '/spamroom':
                            await handle_room_spam_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        if inPuTMsG.startswith('/sr ') or inPuTMsG == '/sr':
                            await handle_sr_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        if inPuTMsG.startswith('/title'):
                            await handle_all_titles_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)
                            
                        # NEW COMMAND-/sticker
                        if MsG.strip().startswith('/sticker'):
                            packet = await send_sticker(uid, chat_id, key, iv)                   
                            await SEndPacKeT(whisper_writer, online_writer, 'ChaT', packet)

                            
                        # Command handler for remove
                        if inPuTMsG.strip().startswith('/wlremove'):
                            parts = inPuTMsG.strip().split()
    
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ Usage: /wlremove (uid)\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            target_uid = parts[1]
    
                            # Check owner
                            if str(response.Data.uid) != "2579372095":
                                error_msg = f"[B][C][FF0000]❌ Only bot owner can remove from whitelist!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
                            
                            success, message = remove_from_whitelist(target_uid)
    
                            if success:
                                bot_uid = 14485072134
        
                                # Create the private message packet
                                # Tp = 2 (Private message)
                                # Tp2 = target_uid (recipient)
                                # id = bot_uid (sender)
                                message_text = f"You Are Successfully Removed From Whitelist By {uid}"
                                private_msg_packet = await xSEndMsg(
                                    Msg=message_text,
                                    Tp=2,  # 2 = Private message
                                    Tp2=int(target_uid),  # Recipient UID
                                    id=int(bot_uid),  # Sender UID (your bot)
                                    K=key,
                                    V=iv
                                )
                                result_msg = f"[B][C][FFFF00]✅ {message}\n📊 Remaining: {len(WHITELISTED_UIDS)} UIDs\n"
                            else:
                                result_msg = f"[B][C][FF0000]❌ {message}\n"
                            
                            await safe_send_message(response.Data.chat_type, result_msg, uid, chat_id, key, iv)
                            
                        # Command to enable/disable whitelist only mode
                        if inPuTMsG.strip() == '/wlenable':
                            
                            WHITELIST_ONLY = True
                            msg = f"[B][C][FFFF00]✅ Whitelist-only mode ENABLED!\n🤖 Bot will only accept invites from whitelisted UIDs\n"
                            await safe_send_message(response.Data.chat_type, msg, uid, chat_id, key, iv)
                        
                        if inPuTMsG.strip() == '/wldisable':

                            WHITELIST_ONLY = False
                            msg = f"[B][C][FFFF00]⚠️ Whitelist-only mode DISABLED!\n🤖 Bot will accept invites from anyone\n"
                            await safe_send_message(response.Data.chat_type, msg, uid, chat_id, key, iv)
                            
                        # Add this command handler
                        if inPuTMsG.strip().startswith('/wladd'):
                            print('Processing whitelist add command')
    
                            parts = inPuTMsG.strip().split()
    
                            if len(parts) < 2:
                                error_msg = f"""[B][C][FF0000]❌ Usage: /wladd (uid)
        
📝 Examples:
/wladd 123456789 - Add UID to whitelist
/wladd 123456789 "Friend" - Add with note

🎯 What happens:
• UID can now invite bot to squad
• UID can use bot commands
• Bot auto-accepts invites from this UID
"""
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            target_uid = parts[1]
    
                            # Optional note
                            note = ""
                            if len(parts) > 2:
                                note = ' '.join(parts[2:])
    
                            # Check if sender is owner
                            if str(response.Data.uid) != "2579372095":  # Replace with your actual UID
                                error_msg = f"[B][C][FF0000]❌ Only bot owner can add to whitelist!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            # Add to whitelist
                            success, message = append_to_whitelist(target_uid, note)
    
                            # Send result
                            if success:
                                bot_uid = 14485072134
        
                                # Create the private message packet
                                # Tp = 2 (Private message)
                                # Tp2 = target_uid (recipient)
                                # id = bot_uid (sender)
                                message_text = f"You Are Successfully Added To Whitelist By {uid}"
                                private_msg_packet = await xSEndMsg(
                                    Msg=message_text,
                                    Tp=2,  # 2 = Private message
                                    Tp2=int(target_uid),  # Recipient UID
                                    id=int(bot_uid),  # Sender UID (your bot)
                                    K=key,
                                    V=iv
                                )
        
                                if private_msg_packet and whisper_writer:
                                    # Send via Whisper connection (chat connection)
                                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', private_msg_packet)
                                success_msg = f"""[B][C][FFFF00]✅ WHITELIST UPDATED!
                        
👤 Added: {target_uid}
📝 Note: {note if note else 'None'}
📊 Total whitelisted: {len(WHITELISTED_UIDS)}
"""
                            else:
                                success_msg = f"[B][C][FF0000]❌ {message}\n"
    
                            await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)    
                            
                        if inPuTMsG.strip() == '/wllist':
                            print('Processing whitelist view command')
    
                            # Check if owner
                            if str(response.Data.uid) != "2579372095":  # Your UID
                                error_msg = f"[B][C][FF0000]❌ Only bot owner can view whitelist!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            # Build whitelist message
                            total = len(WHITELISTED_UIDS)
    
                            whitelist_msg = f"""[B][C][FFFF00]📋 WHITELISTED UIDS

📊 Total: {total} UIDs
🔓 Whitelist enabled: {'YES' if WHITELIST_ONLY else 'NO'}

👑 Owner (always allowed):
• 2579372095

👥 Whitelisted UIDs:"""
    
                            # Add first 20 UIDs (to avoid message too long)
                            count = 0
                            for uid in WHITELISTED_UIDS:
                                if uid != "2579372095":  # Skip owner since already shown
                                    whitelist_msg += f"\n• {uid}"
                                    count += 1
                                    if count >= 20:
                                        remaining = total - 21  # -1 for owner, -20 shown
                                        if remaining > 0:
                                            whitelist_msg += f"\n... and {remaining} more"
                                        break
    
                            whitelist_msg += f"""

💡 Commands:
/wladd (uid) - Add to whitelist
/wlremove (uid) - Remove from whitelist
/wlenable - Enable whitelist only mode
/wldisable - Disable whitelist only mode
"""
    
                            await safe_send_message(response.Data.chat_type, whitelist_msg, uid, chat_id, key, iv)
                            
                        if inPuTMsG.startswith('t_31_p_veteran_wlcm_friend'):
                            print("got it")
                            
                        # Add this command too:
                        if inPuTMsG.strip() == '/viewguests':
                            print('Processing view guests command')
                            
                            try:
                                if not os.path.exists("guest_accounts.json"):
                                    error_msg = f"[B][C][FF0000]❌ No guest accounts found!\n[FFFFFF]Generate with /guest (count) first\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    return
        
                                with open("guest_accounts.json", 'r') as f:
                                    accounts = json.load(f)
                                
                                total = len(accounts)
        
                                # Show summary
                                summary_msg = f"""[B][C][FFFF00]📁 GUEST ACCOUNTS DATABASE

📊 Total accounts: {total}
📁 File: guest_accounts.json
📅 Last updated: {time.ctime(os.path.getmtime('guest_accounts.json'))}

💡 Use /guest (count) to add more
"""
                                await safe_send_message(response.Data.chat_type, summary_msg, uid, chat_id, key, iv)
        
                                # Show recent 5 accounts
                                if accounts:
                                    recent = accounts[-5:]  # Last 5 accounts
                                    recent_msg = "[B][C][FFFF00]📋 RECENT 5 ACCOUNTS:\n"
            
                                    for i, acc in enumerate(recent):
                                        recent_msg += f"[FFFFFF]{i+1}. UID: {acc['uid']} | Pass: {acc['password']}\n"
            
                                    await safe_send_message(response.Data.chat_type, recent_msg, uid, chat_id, key, iv)
            
                            except Exception as e:
                                error_msg = f"[B][C][FF0000]❌ Error: {str(e)[:50]}\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)    
                            
                        # Add this with your other command handlers:
                        if inPuTMsG.strip().startswith('/guest'):
                            print('Processing guest account generation command')
    
                            parts = inPuTMsG.strip().split()
    
                            if len(parts) < 2:
                                error_msg = f"""[B][C][FF0000]❌ Usage: /guest (count)
        
📝 Examples:
/guest 5 - Generate 5 guest accounts
/guest 10 - Generate 10 guest accounts
/guest 50 - Generate 50 guest accounts

🎯 Features:
• Generates random guest accounts
• Auto-retry on 503 errors (10 times)
• Saves to guest_accounts.json
• Shows progress in real-time

⚠️ Note: API may take time, be patient!
"""
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            count_input = parts[1]
    
                            if not count_input.isdigit():
                                error_msg = f"[B][C][FF0000]❌ Count must be a number!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            count = int(count_input)
                            
                            if count <= 0:
                                error_msg = f"[B][C][FF0000]❌ Count must be greater than 0!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            if count > 100:
                                error_msg = f"[B][C][FF0000]❌ Max 100 accounts at once!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            # Send initial message
                            initial_msg = f"""[B][C][FFFF00]🚀 GENERATING GUEST ACCOUNTS

📊 Count: {count} accounts
🔗 API: gen-by-black-api.vercel.app
⏳ Please wait...

💡 This may take {count * 3} seconds
⚠️ 503 errors auto-retry 10 times
"""
                            await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
                            
                            try:
                                # Run generation in background
                                asyncio.create_task(handle_guest_generation(count, uid, chat_id, response.Data.chat_type, key, iv))
        
                            except Exception as e:
                                error_msg = f"[B][C][FF0000]❌ Error starting generation: {str(e)[:50]}\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            
                        if inPuTMsG.startswith('/mimic_on'):
                            success_msg = f"[B][C][FF0000]The Mimic Is Now On\n"
                            await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            emote_hijack = True
                            
                        if inPuTMsG.startswith('/mimic_off'):
                            success_msg = f"[B][C][FF0000]The Mimic Is Now OFF\n"
                            await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            emote_hijack = False

                        if inPuTMsG.startswith('/block_emote'):
                             
                            parts = inPuTMsG.split()

                            if len(parts) > 1:
                                BLOCK_EMOTE_UID = parts[1]
                                success_msg = f"[B][C][FF0000]Block Emote Enabled For UID: {xMsGFixinG(BLOCK_EMOTE_UID)}\n"
                            else:
                                success_msg = f"[B][C][FF0000]Usage: /block_emote <uid>\n"

                            await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)

                        if inPuTMsG.startswith('/unblock_emote'):
                             

                            BLOCK_EMOTE_UID = 111111
                            success_msg = f"[B][C][00FF00]Emote Block Disabled\n"

                            await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)


                        # In your TcPChaT function, add this command handler:
                        if inPuTMsG.strip().startswith('/s_m '):
                            print('Processing private message command')
    
                            parts = inPuTMsG.strip().split(maxsplit=2)  # maxsplit=2 to keep message together
    
                            if len(parts) < 3:
                                error_msg = f"""[B][C][FF0000]❌ Usage: /s_m (target_uid) (message)
        
📝 Examples:
/s_m 123456789 Hello!
/s_m 123456789 How are you?
/s_m 123456789 Let's play together!

🔧 What it does:
• Sends private message to specified UID
• Works even if target is not in your squad
• Bot sends message from its account
• Target sees message in private chat
"""
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            target_uid = parts[1]
                            message_text = parts[2]
    
                            # Validate target UID
                            if not target_uid.isdigit() or len(target_uid) < 8:
                                error_msg = f"[B][C][FF0000]❌ Invalid UID! Must be 8+ digits\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            # Validate message length
                            if len(message_text) > 100:
                                error_msg = f"[B][C][FF0000]❌ Message too long! Max 100 characters\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            # Send initial confirmation
                            initial_msg = f"[B][C][FFFF00]📩 SENDING PRIVATE MESSAGE\n"
                            initial_msg += f"👤 To: {target_uid}\n"
                            initial_msg += f"📝 Message: {message_text[:30]}...\n"
                            initial_msg += f"⏳ Sending...\n"
    
                            await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
    
                            try:
                                # Get bot's UID from login data
                                bot_uid = 14010319252
        
                                # Create the private message packet
                                # Tp = 2 (Private message)
                                # Tp2 = target_uid (recipient)
                                # id = bot_uid (sender)
                                private_msg_packet = await xSEndMsg(
                                    Msg=message_text,
                                    Tp=2,  # 2 = Private message
                                    Tp2=int(target_uid),  # Recipient UID
                                    id=int(bot_uid),  # Sender UID (your bot)
                                    K=key,
                                    V=iv
                                )
        
                                if private_msg_packet and whisper_writer:
                                    # Send via Whisper connection (chat connection)
                                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', private_msg_packet)
            
                                    success_msg = f"""[B][C][FFFF00]✅ PRIVATE MESSAGE SENT!

👤 To: {target_uid}
📝 Message: {message_text}
✅ Status: Delivered

💡 Target will see this in their private messages!
"""
                                    await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                    print(f"✅ Private message sent to {target_uid}: {message_text}")
                                else:
                                    error_msg = f"[B][C][FF0000]❌ Failed to create message packet!\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
            
                            except Exception as e:
                                print(f"❌ Private message error: {e}")
                                error_msg = f"[B][C][FF0000]❌ Error: {str(e)[:50]}\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # In your TcPChaT function, add this:
                        if inPuTMsG.strip().startswith('/friend '):
                            print('Processing friend request command')
    
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"""[B][C][FF0000]❌ Usage: /friend (uid) [count]
        
📝 Examples:
/friend 123456789 - Send 1 friend request
/friend 123456789 5 - Send 5 friend requests

🔧 Features:
• Uses token.json for single request
• Uses token_ind.json for bulk requests
• Same encryption as Flask API
• Direct HTTP requests to Free Fire servers
"""
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            target_uid = parts[1]
    
                            # Validate UID
                            if not target_uid.isdigit() or len(target_uid) < 8:
                                error_msg = f"[B][C][FF0000]❌ Invalid UID! Must be 8+ digits\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            # Determine count
                            count = 1
                            if len(parts) > 2:
                                try:
                                    count = int(parts[2])
                                    if count > 100:
                                        count = 100
                                except:
                                    count = 1
    
                            # Send initial message
                            if count == 1:
                                initial_msg = f"[B][C][FFFF00]🤝 SENDING FRIEND REQUEST\n"
                            else:
                                initial_msg = f"[B][C][FFFF00]📦 SENDING {count} FRIEND REQUESTS\n"
    
                            initial_msg += f"🎯 Target: {target_uid}\n"
                            initial_msg += f"🔑 Source: {'token.json' if count == 1 else 'token_ind.json'}\n"
                            initial_msg += f"🔒 Encryption: AES-CBC + Varint Encoding\n"
                            initial_msg += f"⏳ Processing...\n"
    
                            await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
    
                            try:
                                # Get player info first
                                token = load_jwt_token()
                                player_name = "Unknown"
                                if token:
                                    player_name, _ = get_player_info(target_uid, token)
        
                                # Send friend requests
                                results = await send_friend_request_async(target_uid, count)
        
                                # Send result message
                                if results["success"] > 0:
                                    result_msg = f"""[B][C][FFFF00]✅ FRIEND REQUEST SUCCESS!

🎯 Player: {player_name}
🆔 UID: {target_uid}
✅ Successful: {results['success']}
❌ Failed: {results['failed']}
"""
                                    if count > 1:
                                        result_msg += f"📊 Total Attempted: {count}\n"
            
                                    result_msg += f"\n💡 Friend request(s) sent successfully!\n"
            
                                else:
                                    result_msg = f"""[B][C][FF0000]❌ FRIEND REQUEST FAILED

🎯 Player: {player_name}
🆔 UID: {target_uid}
❌ All requests failed

💡 Check:
1. Token files exist (token.json / token_ind.json)
2. Tokens are valid
3. Target UID is correct
4. Bot has internet connection
"""
        
                                await safe_send_message(response.Data.chat_type, result_msg, uid, chat_id, key, iv)
        
                            except Exception as e:
                                error_msg = f"[B][C][FF0000]❌ Friend request error: {str(e)[:50]}\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        if inPuTMsG.startswith('noob'):
                            await handle_alll_titles_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        if inPuTMsG.strip().startswith('/room_msg'):
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /kick (uid)\nExample: /kick 123456789\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                room_id = parts[1]

                                initial_message = f"[B][C]{get_random_color()}\nkicking {uid}...\n"
                                await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                                
                                try:
                                    # Fast squad creation and invite for 5 players
                                    PAc = await Create_xr_room_packet_fixed__(room_id, key, iv)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
                                    await asyncio.sleep(0.3)
                                except Exception as e:
                                    print(e)

                        # Replace the existing title handler with this
                        # Use the FINAL version
                        if inPuTMsG.strip().startswith('/kick'):
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /kick (uid)\nExample: /kick 123456789\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
                                initial_message = f"[B][C]{get_random_color()}\nkicking {target_uid}...\n"
                                await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                                
                                try:
                                    # Fast squad creation and invite for 5 players
                                    PAc = await KickTarget(target_uid, key, iv)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
                                    await asyncio.sleep(0.3)
                                except Exception as e:
                                    print(e)
                                    
                        if inPuTMsG.strip().startswith('/tester'):
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /kick (uid)\nExample: /kick 123456789\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
                                initial_message = f"[B][C]{get_random_color()}\nkicking {target_uid}...\n"
                                await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                                
                                try:
                                    # Fast squad creation and invite for 5 players
                                    PAc = await SwitchLoneWolfDule(target_uid, key, iv)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
                                    await asyncio.sleep(0.3)
                                except Exception as e:
                                    print(e)
                            
                        if inPuTMsG.strip().startswith('/kkick'):
                            print('Processing FINAL title command (friend method)')
                            await LagSquad(key, iv)

                        if inPuTMsG.startswith(("/3")):
                            # Process /3 command - Create 3 player group
                            initial_message = f"[B][C]{get_random_color()}\n\nCreating 3-Player Group...\n\n"
                            await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                            
                            # Fast squad creation and invite for 6 players
                            PAc = await OpEnSq(key, iv, region)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
                            
                            C = await cHSq(3, uid, key, iv, region)
                            await asyncio.sleep(0.3)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)
                            
                            V = await SEnd_InV(3, uid, key, iv, region)
                            await asyncio.sleep(0.3)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
                            
                            E = await ExiT(None, key, iv)
                            await asyncio.sleep(3.5)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', E)
                            
                            # SUCCESS MESSAGE
                            success_message = f"[B][C][FFFF00]✅ SUCCESS! 6-Player Group invitation sent successfully to {uid}!\n"
                            await safe_send_message(response.Data.chat_type, success_message, uid, chat_id, key, iv)

                        if inPuTMsG.startswith(("/4")):
                            # Process /3 command - Create 3 player group
                            initial_message = f"[B][C]{get_random_color()}\n\nCreating 3-Player Group...\n\n"
                            await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                            
                            # Fast squad creation and invite for 6 players
                            PAc = await OpEnSq(key, iv, region)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
                            
                            C = await cHSq(4, uid, key, iv, region)
                            await asyncio.sleep(0.3)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)
                            
                            V = await SEnd_InV(4, uid, key, iv, region)
                            await asyncio.sleep(0.3)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
                            
                            E = await ExiT(None, key, iv)
                            await asyncio.sleep(3.5)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', E)
                            
                            # SUCCESS MESSAGE
                            success_message = f"[B][C][FFFF00]✅ SUCCESS! 6-Player Group invitation sent successfully to {uid}!\n"
                            await safe_send_message(response.Data.chat_type, success_message, uid, chat_id, key, iv)

                        # In your TcPChaT function, look for the command handling section
                        # It might look something like this:

                        if inPuTMsG.startswith('/room '):
                            await handle_room_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        # Join Custom Room Command
                        if inPuTMsG.strip().startswith('/joinroom'):
                            print('Processing custom room join command')
    
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 3:
                                error_msg = f"[B][C][FF0000]❌ Usage: /joinroom (room_id) (password)\nExample: /joinroom 123456 0000\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                room_id = parts[1]
                                room_password = parts[2]
        
                                initial_msg = f"[B][C][FFFF00]🚀 Joining custom room...\n🏠 Room: {room_id}\n🔑 Password: {room_password}\n"
                                await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
        
                                try:
                                    # Join the custom room
                                    join_packet = await join_custom_room(room_id, room_password, key, iv, region)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
            
                                    success_msg = f"[B][C][FFFF00]✅ Joined custom room {room_id}!\n🤖 Bot is now in room chat!\n"
                                    await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
            
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ Failed to join room: {str(e)}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        if inPuTMsG.startswith(("/5")):
                            # Process /5 command in any chat type
                            initial_message = f"[B][C]{get_random_color()}\n\nSending Group Invitation...\n\n"
                            await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                            
                            # Fast squad creation and invite
                            PAc = await OpEnSq(key, iv, region)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
                            
                            C = await cHSq(5, uid, key, iv, region)
                            await asyncio.sleep(0.3)  # Reduced delay
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', C)
                            
                            V = await SEnd_InV(5, uid, key, iv, region)
                            await asyncio.sleep(0.3)  # Reduced delay
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
                            
                            E = await ExiT(None, key, iv)
                            await asyncio.sleep(3.5)  # Reduced from 3 seconds
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', E)
                            
                            # SUCCESS MESSAGE
                            success_message = f"[B][C][FFFF00]✅ SUCCESS! Group invitation sent successfully to {uid}!\n"
                            await safe_send_message(response.Data.chat_type, success_message, uid, chat_id, key, iv)

                        if inPuTMsG.strip() == "/admin":
                            # Process /admin command in any chat type
                            admin_message = """
[B][C][FF0000] কম দামে bot কিনার জন্য ভাবছেন নাকি?

নিজের নামে বট কিনতে চান?

আমার সাথে যোগাযোগ করুন

[B][C][FF0000]TELEGRAM CHANNEL: [FFFFFF]t.me/narutocodexofc

[B][C][FF0000]TELEGRAM GROUP: [FFFFFF]t.me/narutoXchats
"""
                            await safe_send_message(response.Data.chat_type, admin_message, uid, chat_id, key, iv)

                        # Add this with your other command handlers in the TcPChaT function
                        if inPuTMsG.strip().startswith('/multijoin'):
                            print('Processing multi-account join request')
    
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ Usage: /multijoin (target_uid)\nExample: /multijoin 123456789\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
        
                                if not target_uid.isdigit():
                                    error_msg = f"[B][C][FF0000]❌ Please write a valid player ID!\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    return
        
                                initial_msg = f"[B][C][FFFF00]🚀 Starting multi-join attack on {target_uid}...\n"
                                await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
        
                                try:
                                    # Try the fake multi-account method (more reliable)
                                    success_count, total_attempts = await real_multi_account_join(target_uid, key, iv, region)
            
                                    if success_count > 0:
                                        result_msg = f"""
[B][C][FFFF00]✅ MULTI-JOIN ATTACK COMPLETED!

🎯 Target: {target_uid}
✅ Successful Requests: {success_count}
📊 Total Attempts: {total_attempts}
⚡ Different squad variations sent!

💡 Check your game for join requests!
"""
                                    else:
                                        result_msg = f"[B][C][FF0000]❌ All join requests failed! Check bot connection.\n"
            
                                    await safe_send_message(response.Data.chat_type, result_msg, uid, chat_id, key, iv)
            
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ Multi-join error: {str(e)}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)



                        # Update the command handler
                        if inPuTMsG.strip().startswith('/reject'):
                            print('Processing reject spam command in any chat type')
    
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /reject (target_uid)\nExample: /reject 123456789\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
        
                                # Stop any existing reject spam
                                if reject_spam_task and not reject_spam_task.done():
                                    reject_spam_running = False
                                    reject_spam_task.cancel()
                                    await asyncio.sleep(0.5)
        
                                # Send start message
                                start_msg = f"[B][C][1E90FF]🌀 Started Reject Spam on: {target_uid}\n🌀 Packets: 150 each type\n🌀 Interval: 0.2 seconds\n"
                                await safe_send_message(response.Data.chat_type, start_msg, uid, chat_id, key, iv)
        
                                # Start reject spam in background
                                reject_spam_running = True
                                reject_spam_task = asyncio.create_task(reject_spam_loop(target_uid, key, iv))
        
                                # Wait for completion in background and send completion message
                                asyncio.create_task(handle_reject_completion(reject_spam_task, target_uid, uid, chat_id, response.Data.chat_type, key, iv))


                        if inPuTMsG.strip() == '/reject_stop':
                            if reject_spam_task and not reject_spam_task.done():
                                reject_spam_running = False
                                reject_spam_task.cancel()
                                stop_msg = f"[B][C][FFFF00]✅ Reject spam stopped successfully!\n"
                                await safe_send_message(response.Data.chat_type, stop_msg, uid, chat_id, key, iv)
                            else:
                                error_msg = f"[B][C][FF0000]❌ No active reject spam to stop!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                

                        # Individual command handlers for /s1 to /s8
                        if inPuTMsG.strip().startswith('/s1'):
                            await handle_badge_command('s1', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)
    
                        if inPuTMsG.strip().startswith('/s2'):
                            await handle_badge_command('s2', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)


                        if inPuTMsG.strip().startswith('/xspam'):
                            await handle_badge_command('s1', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)
                            await asyncio.sleep(1.5)
                            await handle_badge_command('s2', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)
                            await asyncio.sleep(1.5)
                            await handle_badge_command('s3', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)
                            await asyncio.sleep(1.5)
                            await handle_badge_command('s4', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)
                            await asyncio.sleep(1.5)
                            await handle_badge_command('s5', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)
                            await asyncio.sleep(1)


                        if inPuTMsG.strip().startswith('/s3'):
                            await handle_badge_command('s3', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        if inPuTMsG.strip().startswith('/s4'):
                            await handle_badge_command('s4', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        if inPuTMsG.strip().startswith('/s5'):
                            await handle_badge_command('s5', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        if inPuTMsG.strip().startswith('/s6'):
                            await handle_badge_command('s6', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        if inPuTMsG.strip().startswith('/s7'):
                            await handle_badge_command('s7', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        if inPuTMsG.strip().startswith('/s8'):
                            await handle_badge_command('s8', inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                                    
                                                                                                     
                        if inPuTMsG.strip().startswith('@joinroom'):
                            print('Processing custom room join command')
    
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 3:
                                error_msg = f"[B][C][FF0000]❌ Usage: /joinroom (room_id) (password)\nExample: /joinroom 123456 0000\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                room_id = parts[1]
                                room_password = parts[2]
        
                                initial_msg = f"[B][C][FFFF00]🚀 Joining custom room...\n🏠 Room: {room_id}\n🔑 Password: {room_password}\n"
                                await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
        
                                try:
                                    # Join the custom room
                                    join_packet = await join_custom_room(room_id, room_password, key, iv, region)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
            
                                    success_msg = f"[B][C][FFFF00]✅ Joined custom room {room_id}!\n🤖 Bot is now in room chat!\n"
                                    await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
            
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ Failed to join room: {str(e)}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        if inPuTMsG.strip().startswith('/createroom'):
                            print('Processing custom room creation')
    
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 3:
                                error_msg = f"[B][C][FF0000]❌ Usage: /createroom (room_name) (password) [players=4]\nExample: /createroom BOTROOM 0000 4\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                room_name = parts[1]
                                room_password = parts[2]
                                max_players = parts[3] if len(parts) > 3 else "4"
        
                                initial_msg = f"[B][C][FFFF00]🏠 Creating custom room...\n📛 Name: {room_name}\n🔑 Password: {room_password}\n👥 Max Players: {max_players}\n"
                                await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
        
                                try:
                                    # Create custom room
                                    create_packet = await create_custom_room(room_name, room_password, int(max_players), key, iv, region)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', create_packet)
            
                                    success_msg = f"[B][C][FFFF00]✅ Custom room created!\n🏠 Room: {room_name}\n🔑 Password: {room_password}\n👥 Max: {max_players}\n🤖 Bot is now hosting!\n"
                                    await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
            
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ Failed to create room: {str(e)}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)               
                        
                                                
                        # Add with other command handlers in TcPChaT
                        if inPuTMsG.strip().startswith('/arr'):
                            print('Processing entry emote command')
    
                            parts = inPuTMsG.strip().split()
    
                            if len(parts) < 2:
                                error_msg = f"""[B][C][FF0000]❌ Usage: /entry (uid)
                        Example: /entry 123456789
                        Example: /entry me (for yourself)

                        Effect: Sends arrival animation to player
"""
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
        
                                # Handle "me" or "self"
                                if target_uid.lower() in ['me', 'self', 'myself']:
                                    target_uid = str(response.Data.uid)
                                    target_name = "Yourself"
                                else:
                                    target_name = f"UID {target_uid}"
        
                                initial_msg = f"[B][C][FFFF00]🎬 Sending arrival animation to {target_name}...\n"
                                await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
        
                                try:
                                    # Send the entry emote packet
                                    entry_packet = await Send_Entry_Emote(int(target_uid), key, iv)
                                    
                                    if entry_packet:
                                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', entry_packet)
                
                                        success_msg = f"[B][C][FFFF00]✅ ARRIVAL ANIMATION SENT!\n"
                                        success_msg += f"[FFFFFF]👤 Target: {target_name}\n"
                                        success_msg += f"[FFFFFF]🎭 Emote ID: 912038002\n"
                                        success_msg += f"[FFFFFF]✨ Effect: Entry/Arrival Animation\n"
                
                                        await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                        print(f"✅ Sent entry emote to {target_uid}")
                                    else:
                                        error_msg = f"[B][C][FF0000]❌ Failed to create entry emote packet!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ Error sending entry emote: {str(e)[:50]}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            
                                                                                          # FIXED JOIN COMMAND
                        if inPuTMsG.startswith('!'):
                            # Process /join command in any chat type
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /join (team_code)\nExample: /join ABC123\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                CodE = parts[1]
                                uid = response.Data.uid  # Get the UID of person who sent the command
        
                                initial_message = f"[B][C]{get_random_color()}\nJoining squad with code: {CodE}...\n"
                                await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
        
                                try:
                                    # Try using the regular join method first
                                    EM = await GenJoinSquadsPacket(CodE, key, iv)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', EM)
            
                                    # Wait a bit for the join to complete
                                    await asyncio.sleep(2)
            
                                    # DUAL RINGS EMOTE - BOTH SENDER AND BOT
                                    try:
                                        await auto_rings_emote_dual(uid, key, iv, region)
                                    except Exception as emote_error:
                                        print(f"Dual emote failed but join succeeded: {emote_error}")
            
                                    # SUCCESS MESSAGE
                                    success_message = f"[B][C][FFFF00]✅ SUCCESS! Joined squad: {CodE}!\n💍 Dual Rings emote activated!\n🤖 Bot + You = 💕\n"
                                    await safe_send_message(response.Data.chat_type, success_message, uid, chat_id, key, iv)
            
                                except Exception as e:
                                    print(f"Regular join failed, trying ghost join: {e}")
                                    # If regular join fails, try ghost join
                                    try:
                                        # Get bot's UID from global context or login data
                                        bot_uid = LoGinDaTaUncRypTinG.AccountUID if hasattr(LoGinDaTaUncRypTinG, 'AccountUID') else TarGeT
                
                                        ghost_packet = await ghost_join_packet(bot_uid, CodE, key, iv)
                                        if ghost_packet:
                                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', ghost_packet)
                    
                                            # Wait a bit for ghost join to complete
                                            await asyncio.sleep(2)
                    
                                            # DUAL RINGS EMOTE - BOTH SENDER AND BOT
                                            try:
                                                await auto_rings_emote_dual(uid, key, iv, region)
                                            except Exception as emote_error:
                                                print(f"Dual emote failed but ghost join succeeded: {emote_error}")
                    
                                            success_message = f"[B][C][FFFF00]✅ SUCCESS! Ghost joined squad: {CodE}!\n💍 Dual Rings emote activated!\n🤖 Bot + You = 💕\n"
                                            await safe_send_message(response.Data.chat_type, success_message, uid, chat_id, key, iv)
                                        else:
                                            error_msg = f"[B][C][FF0000]❌ ERROR! Failed to create ghost join packet.\n"
                                            await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                    
                                    except Exception as ghost_error:
                                        print(f"Ghost join also failed: {ghost_error}")
                                        error_msg = f"[B][C][FF0000]❌ ERROR! Failed to join squad: {str(ghost_error)}\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                
                
                        if inPuTMsG.strip().startswith('/xggst'):
                            # Process / command in any chat type
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: / (team_code)\nExample: / ABC123\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                CodE = parts[1]
                                initial_message = f"[B][C]{get_random_color()}\nGhost joining squad with code: {CodE}...\n"
                                await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                                
                                try:
                                    # Get bot's UID from global context or login data
                                    bot_uid = LoGinDaTaUncRypTinG.AccountUID if hasattr(LoGinDaTaUncRypTinG, 'AccountUID') else TarGeT
                                    
                                    ghost_packet = await ghost_join_packet(bot_uid, CodE, key, iv)
                                    if ghost_packet:
                                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', ghost_packet)
                                        success_message = f"[B][C][FFFF00]✅ SUCCESS! Ghost joined squad with code: {CodE}!\n"
                                        await safe_send_message(response.Data.chat_type, success_message, uid, chat_id, key, iv)
                                    else:
                                        error_msg = f"[B][C][FF0000]❌ ERROR! Failed to create ghost join packet.\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                        
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ ERROR! Ghost join failed: {str(e)}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # NEW LAG COMMAND
                        if inPuTMsG.strip().startswith('/abra '):
                            print('Processing lag command in any chat type')
                            
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /lagx (team_code)\nExample: /lagx ABC123\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                team_code = parts[1]
                                
                                # Stop any existing lag task
                                if lag_task and not lag_task.done():
                                    lag_running = False
                                    lag_task.cancel()
                                    await asyncio.sleep(0.1)
                                
                                # Start new lag task
                                lag_running = True
                                lag_task = asyncio.create_task(lag_team_loop(team_code, key, iv, region))
                                
                                # SUCCESS MESSAGE
                                success_msg = f"[B][C][FFFF00]✅ SUCCESS! Lag attack started!\nTeam: {team_code}\nAction: Rapid join/leave\nSpeed: Ultra fast (milliseconds)\n"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)

                        # STOP LAG COMMAND
                        if inPuTMsG.strip() == '/stop lag':
                            if lag_task and not lag_task.done():
                                lag_running = False
                                lag_task.cancel()
                                success_msg = f"[B][C][FFFF00]✅ SUCCESS! Lag attack stopped successfully!\n"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            else:
                                error_msg = f"[B][C][FF0000]❌ ERROR! No active lag attack to stop!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                        if inPuTMsG.strip().startswith('/duo'):
                                await handle_duo_command(inPuTMsG, uid, chat_id, response.Data.chat_type, key, iv, region)
                        if inPuTMsG.startswith('/exit'):
                            # Process /exit command in any chat type
                            initial_message = f"[B][C]{get_random_color()}\nBO👽T বের হইছে কিন্তু...\n"
                            await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                            
                            leave = await ExiT(uid,key,iv)
                            await SEndPacKeT(whisper_writer , online_writer , 'OnLine' , leave)
                            
                            # SUCCESS MESSAGE
                            success_message = f"[B][C][FFFF00]✅ BO👽T কে বের করলা কেন মিয়া তুমি G👽A👽Y\n"
                            await safe_send_message(response.Data.chat_type, success_message, uid, chat_id, key, iv)

                        # =================== MAGIC COMMANDS ===================
                        if inPuTMsG.strip().startswith('/magic'):
                            print('Processing /magic command')
                            await handle_magic_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        if inPuTMsG.strip().startswith('/offmagic'):
                            print('Processing /offmagic command')
                            await handle_offmagic_command(uid, chat_id, key, iv, response.Data.chat_type)

                        # =================== LAGC COMMANDS ===================
                        if inPuTMsG.strip().startswith('/lagc'):
                            print('Processing /lagc command')
                            await handle_lagc_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        if inPuTMsG.strip().startswith('/stop_lagc'):
                            print('Processing /stop_lagc command')
                            await handle_stop_lagc_command(uid, chat_id, key, iv, response.Data.chat_type)

                        if inPuTMsG.strip().startswith('/start'):
                            # Process /s command in any chat type
                            initial_message = f"[B][C]{get_random_color()}\nStarting match...\n"
                            await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                            
                            start_packet = await start_auto_packet(key, iv, region)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', start_packet)
                            initiial_message = f"[B][C]{get_random_color()}\nStarting match...\n"
                            await safe_send_message(response.Data.chat_type, initiial_message, uid, chat_id, key, iv)
                            
        
                            await handle_tagx_command(inPuTMsG, uid, chat_id, response.Data.chat_type, key, iv, region)
                        if inPuTMsG.strip().startswith('/mg '):
                            print('Processing wave message command')
                          
                            parts = inPuTMsG.strip().split()
    
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ Usage: /mg (message) [repeats=5]\n"
                                error_msg += f"[FFFFFF]Example: /mg hello 3\n"
                                error_msg += f"[FFFFFF]Will send: h, he, hel, hell, hello, hell, hel, he, h\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                try:
                                    # Get message and optional repeats
                                    message_text = parts[1]
                                    repeats = 5  # Default
            
                                    if len(parts) > 2:
                                        repeats = int(parts[2])
            
                                    if repeats <= 0:
                                        error_msg = f"[B][C][FF0000]❌ Repeats must be > 0!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    elif repeats > 10:
                                        error_msg = f"[B][C][FF0000]❌ Max 10 repeats!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    elif len(message_text) < 2:
                                        error_msg = f"[B][C][FF0000]❌ Message must be at least 2 characters!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    else:
                                        global mg_spam_task
                                        if mg_spam_task and not mg_spam_task.done():
                                            global msg_spam_running
                                            msg_spam_running = False
                                            mg_spam_task.cancel()
                                            await asyncio.sleep(0.5)
                
                                        # Calculate total messages
                                        total_messages_per_cycle = (len(message_text) * 2) - 2
                                        total_messages = total_messages_per_cycle * repeats
                
                                        initial_msg = f"[B][C][FFFF00]🌊 WAVE MESSAGE STARTING!\n"
                                        initial_msg += f"[FFFFFF]Message: {message_text}\n"
                                        initial_msg += f"[FFFFFF]Repeats: {repeats} cycles\n"
                                        initial_msg += f"[FFFFFF]Pattern: h → he → hel → hell → hello → hell → hel → he → h\n"
                                        initial_msg += f"[FFFF00]Total messages: {total_messages}\n"
                                        await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
                                        
                                        # Start wave messages
                                        msg_spam_running = True
                                        mg_spam_task = asyncio.create_task(
                                            send_wave_messages(message_text, repeats, chat_id, key, iv, region)
                                        )
                
                                        # Handle completion
                                        asyncio.create_task(
                                            handle_wave_completion(mg_spam_task, message_text, repeats, uid, chat_id, response.Data.chat_type, key, iv)
                                        )
                
                                except ValueError:
                                    error_msg = f"[B][C][FF0000]❌ Invalid format!\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                        
                        if inPuTMsG.strip().startswith('/massage '):
                            print('Processing message spam command')
                            global msg_spam_task
                            parts = inPuTMsG.strip().split()
    
                            if len(parts) < 3:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /massage (message) (times)\n"
                                error_msg += f"[FFFFFF]Example: /massage Hello Team! 5\n"
                                error_msg += f"[FFFFFF]Will send 'Hello Team!' 5 times in team chat\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                try:
                                    # Extract message and times
                                    times = int(parts[-1]) # Last part is the number
            
                                    # Reconstruct the message (everything except first part and last part)
                                    message_text = ' '.join(parts[1:-1])
            
                                    if times <= 0:
                                        error_msg = f"[B][C][FF0000]❌ ERROR! Times must be greater than 0!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    
                                    elif not message_text.strip():
                                        error_msg = f"[B][C][FF0000]❌ ERROR! Message cannot be empty!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    else:
                                        # Stop any existing message spam
                                      
                                        if msg_spam_task and not msg_spam_task.done():
                                            
                                            msg_spam_running = False
                                            msg_spam_task.cancel()
                                            await asyncio.sleep(0.1)
                
                                        # Check if we have the chat_id from the message
                                        # If not, use the bot's UID from login data
                                        chat_id = chat_id
                
                                        # Send initial message
                                        initial_msg = f"[B][C][FFFF00]📢 MESSAGE SPAM STARTING!\n"
                                        initial_msg += f"[FFFFFF]Message: {message_text}\n"
                                        initial_msg += f"[FFFFFF]Times: {times}\n"
                                        initial_msg += f"[FFFFFF]Chat: Team/Squad Chat\n"
                                        initial_msg += f"[FFFF00]Sending messages...\n"
                                        await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
                
                                        # Start message spam
                                        msg_spam_running = True
                                        msg_spam_task = asyncio.create_task(
                                            msg_spam_loop(message_text, times, chat_id, key, iv, region)
                                        )
                
                                        # Wait for completion and send result
                                        asyncio.create_task(
                                            handle_msg_spam_completion(msg_spam_task, message_text, times, uid, chat_id, response.Data.chat_type, key, iv)
                                        )
                                        
                                except ValueError:
                                    error_msg = f"[B][C][FF0000]❌ ERROR! Invalid format!\n"
                                    error_msg += f"[FFFFFF]Usage: /massage (message) (times)\n"
                                    error_msg += f"[FFFFFF]Example: /massage Hello World! 10\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ ERROR: {str(e)}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # Add stop command
                        if inPuTMsG.strip() == '/stop msg':
                            if msg_spam_task and not msg_spam_task.done():
                                msg_spam_running = False
                                msg_spam_task.cancel()
                                success_msg = f"[B][C][FFFF00]✅ MESSAGE SPAM STOPPED!\n[FFFFFF]All message sending has been stopped.\n"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            else:
                                error_msg = f"[B][C][FF0000]❌ No active message spam to stop!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
        
                        # Add this to your command handlers in TcPChaT function:
                        if inPuTMsG.strip().startswith('/train'):
                            print('Processing training mode command')
                            await handle_training_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)
                            
                        # Add these to your command handlers in TcPChaT function:
                        # Add this to your command handlers in TcPChaT function:
                        if inPuTMsG.strip().startswith('/join_req '):
                            print('Processing /join_req command')
                            await handle_join_req_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type, LoGinDaTaUncRypTinG)
                        if inPuTMsG.strip().startswith('/infox'):
                            await handle_infox_command(inPuTMsG, uid, chat_id, response.Data.chat_type, key, iv, region)
                                #GET PLAYER INFO
                        if inPuTMsG.strip().startswith('/idjdjjnfjdo'):
                            print('Processing bio command in any chat type')

                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /infddjdo <uid>\nExample: /info 144🤫444🤫440🤫04\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
                                initial_message = f"[B][C]{get_random_color()}\nGetting Player Info...\n"
                                await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)

                                info_data = get_player_info(target_uid)

                                await send_full_player_info(info_data, response.Data.chat_type, uid, chat_id, key, iv)


                        if inPuTMsG.strip().startswith('/ghost'):
                            parts = inPuTMsG.strip().split()

                            if len(parts) < 3:
                                ghost_msg = """
[B][FF0000]❌ Usage Error
[B][FFFFFF]━━━━━━━━━━━━━━━━
[B][FFD700]Use: /ghost teamcode name
[B][00FFFF]Example: /ghost 4337272 ABHI
"""
                                await safe_send_message(response.Data.chat_type, ghost_msg, uid, chat_id, key, iv)

                            else:
                                teamcode = parts[1]
                                name = parts[2]

                                try:
                                    url = f"https://rizerxghostbd.onrender.com/x/{teamcode}/{name}"
                                    r = requests.get(url, timeout=10)
                                    data = r.json()

                                    if data.get("status") == "ok":
                                        ghost_msg = f"""
[B][00FF00]👻 GHOST SENT SUCCESS
[B][FFFFFF]━━━━━━━━━━━━━━━━━━
[B][FFD700]Team Code : {teamcode}
[B][00FFFF]Name : {name}
[B][00FFFF]{data.get("message")}
[B][FFFFFF]━━━━━━━━━━━━━━━━━━
[B][FF69B4]Developer : NARUTO-CODEX
"""
                                    else:
                                        ghost_msg = f"""
[B][FF0000]❌ API FAILED
[B][FFFFFF]━━━━━━━━━━━━━━━━━━
[B][FFD700]Team Code : {teamcode}
[B][00FFFF]Name : {name}
[B][FF0000]{data}
"""

                                except Exception as e:
                                    ghost_msg = f"""
[B][FF0000]❌ REQUEST ERROR
[B][FFFFFF]━━━━━━━━━━━━━━━━━━
[B][FFD700]Team Code : {teamcode}
[B][00FFFF]Name : {name}
[B][FF0000]{str(e)}
"""

                                await safe_send_message(response.Data.chat_type, ghost_msg, uid, chat_id, key, iv)

                        if inPuTMsG.strip().startswith('/lagx'):
                            parts = inPuTMsG.strip().split()

                            if len(parts) < 2:
                                lagx_msg = """
[B][FF0000]❌ Usage Error
[B][FFFFFF]━━━━━━━━━━━━━━━━
[B][FFD700]Use: /lagx teamcode
[B][00FFFF]Example: /lagx 606703
"""
                                await safe_send_message(response.Data.chat_type, lagx_msg, uid, chat_id, key, iv)

                            else:
                                teamcode = parts[1]

                                try:
                                    url = f"https://rizerxfuhx-tc-offline.onrender.com/join?teamcode={teamcode}"
                                    r = requests.get(url, timeout=10)
                                    data = r.text  # response string ধরলাম

                                    lagx_msg = f"{xMsGFixinG(data)}"

                                except Exception as e:
                                    lagx_msg = f"""
[B][FF0000]❌ REQUEST ERROR
[B][FFFFFF]━━━━━━━━━━━━━━━━━━
[B][FFD700]Team Code : {teamcode}
[B][FF0000]{str(e)}
"""

                                await safe_send_message(response.Data.chat_type, lagx_msg, uid, chat_id, key, iv)

                        if inPuTMsG.strip().startswith('/offline'):
                            parts = inPuTMsG.strip().split()

                            if len(parts) < 2:
                                offline_msg = """
[B][FF0000]❌ Usage Error
[B][FFFFFF]━━━━━━━━━━━━━━━━
[B][FFD700]Use: teamcode
[B][00FFFF]Example: /offline 606703
"""
                                await safe_send_message(response.Data.chat_type, offline_msg, uid, chat_id, key, iv)

                            else:
                                teamcode = parts[1]

                                try:
                                    url = f"http://rizerxfuhx-tc-offline.onrender.com/joinfuhx?teamcode={teamcode}"
                                    r = requests.get(url, timeout=10)
                                    data = r.text

                                    offline_msg = f"{xMsGFixinG(data)}"

                                except Exception as e:
                                    offline_msg = f"""
[B][FF0000]❌ REQUEST ERROR
[B][FFFFFF]━━━━━━━━━━━━━━━━━━
[B][FFD700]Team Code : {teamcode}
[B][FF0000]{str(e)}
"""

                                await safe_send_message(response.Data.chat_type, offline_msg, uid, chat_id, key, iv)


                        if inPuTMsG.strip().startswith('/em'):
                            parts = inPuTMsG.strip().split()
                            
                            # Check usage
                            if len(parts) < 3:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /em [team_code] [emote] or /em [team_code] [uid] [emote]\n"
                                error_msg += f"[FFFFFF]Examples:\n"
                                error_msg += f"[00FF00]/em ABC123 ak → Join team ABC123 and send 'ak' emote to yourself\n"
                                error_msg += f"[00FF00]/em ABC123 123456789 heart → Join team ABC123 and send 'heart' emote to UID 123456789\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                continue
                            
                            team_code = parts[1]
                            target_uids = []
                            emote_key = None
                            
                            # Determine if UID is provided
                            if len(parts) == 3:
                                # /em team_code emote → send to yourself
                                target_uids.append(int(response.Data.uid))
                                emote_key = parts[2].lower()
                            else:
                                # /em team_code uid emote → send to UID(s)
                                for i in range(2, len(parts) - 1):
                                    target_uids.append(int(parts[i]))
                                emote_key = parts[-1].lower()
                            
                            # Show "joining" emssage
#                            initial_message = f"[B][C]{get_random_color()}\n⏳ Joining squad {team_code}...\n"
#                            await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                            
                            try:
                                # Join squad
                                join_packet = await GenJoinSquadsPacket(team_code, key, iv)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
                                
                                await asyncio.sleep(0.1)
                                
                                # Send emotes
                                emote_id = None
                                if emote_key.isdigit() and emote_key in NUMBER_EMOTES:
                                    emote_id = NUMBER_EMOTES[emote_key]
                                elif emote_key in NAME_EMOTES:
                                    emote_id = NAME_EMOTES[emote_key]
                                
                                if not emote_id:
                                    error_msg = f"[B][C][FF0000]❌ Invalid emote: '{emote_key}'\nUse /e list names to see all available names\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    for target_uid in target_uids:
                                        H = await Emote_k(target_uid, int(emote_id), key, iv, region)
                                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                        await asyncio.sleep(0.1)
                                
                                # Leave squad
                                leave_packet = await ExiT(uid, key, iv)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)
                                
                                success_msg = f"[B][C][00FF00]✅ SUCCESS! Joined squad {team_code}, sent emote '{emote_key}' and left successfully!\n"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            
                            except Exception as e:
                                print(f"Error processing /em command: {e}")
                                error_msg = f"[B][C][FF0000]❌ ERROR! Failed to execute /em command: {str(e)[:50]}\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)


                        elif inPuTMsG.strip().startswith('/e'):
                            print(f'Processing emote command in chat type: {response.Data.chat_type}')
    
                            parts = inPuTMsG.strip().split()
    
                            # Check if user wants to list emotes or show help
                            if len(parts) == 1 or (len(parts) == 2 and parts[1].lower() == 'list'):
                                # Show available emotes
                                emote_list_msg = f"[B][C][FFFF00]🎭 EMOTE SYSTEM\n"
                                emote_list_msg += f"[FFFFFF]────────────────\n"
                                emote_list_msg += f"[FFFF00]📊 STATS:\n"
                                emote_list_msg += f"[FFFFFF]• Number emotes: 1-{len(NUMBER_EMOTES)}\n"
                                emote_list_msg += f"[FFFFFF]• Named emotes: {len(NAME_EMOTES)} names\n"
                                emote_list_msg += f"[FFFFFF]────────────────\n"
                                emote_list_msg += f"[FFFF00]🎯 USAGE:\n"
                                emote_list_msg += f"[FFFFFF]/e [number/name] → Send to yourself\n"
                                emote_list_msg += f"[FFFFFF]/e [uid] [number/name] → Send to UID\n"
                                emote_list_msg += f"[FFFFFF]────────────────\n"
                                emote_list_msg += f"[FFFF00]🔥 POPULAR NAMES:\n"
        
                                # Show popular named emotes
                                popular_names = ["ak", "m60", "p90", "scar", "famas", "heart", "love", "dance", "hello", "money"]
                                line = ""
                                for name in popular_names:
                                    if name.lower() in NAME_EMOTES:
                                        line += f"[FFFF00]{name}[FFFFFF], "
                                if line:
                                    emote_list_msg += line.rstrip(", ") + "\n"
        
                                emote_list_msg += f"[FFFFFF]────────────────\n"
                                emote_list_msg += f"[FFFF00]📖 EXAMPLES:\n"
                                emote_list_msg += f"[FFFFFF]/e ak → Send AK emote to yourself\n"
                                emote_list_msg += f"[FFFFFF]/e 123456789 heart → Send ❤️ to UID\n"
                                emote_list_msg += f"[FFFFFF]/e 123456789 1 → Send emote #1 to UID\n"
                                emote_list_msg += f"[FFFFFF]/e ring → Send ring emote to yourself\n"
                                emote_list_msg += f"[FFFFFF]/e list names → Show all named emotes\n"
        
                                # Check if user wants detailed name list
                                if len(parts) == 2 and parts[1].lower() == 'names':
                                    emote_list_msg += f"[FFFFFF]────────────────\n"
                                    emote_list_msg += f"[FFFF00]📝 ALL NAMED EMOTES:\n"
            
                                    # Show all named emotes in groups
                                    all_names = sorted(NAME_EMOTES.keys())
                                    for i in range(0, min(len(all_names), 30), 5):  # Show first 30 names
                                        group = all_names[i:i+5]
                                        emote_list_msg += f"[FFFFFF]{' | '.join(group)}\n"
            
                                    if len(all_names) > 30:
                                        emote_list_msg += f"[FFFFFF]... and {len(all_names) - 30} more\n"
        
                                await safe_send_message(response.Data.chat_type, emote_list_msg, uid, chat_id, key, iv)
                                continue
    
                            # Parse command
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /e [emote_name_or_number]\n"
                                error_msg += f"[FFFFFF]Examples:\n"
                                error_msg += f"[FFFF00]/e ak[FFFFFF] → AK emote to yourself\n"
                                error_msg += f"[FFFF00]/e 123456789 heart[FFFFFF] → ❤️ to UID\n"
                                error_msg += f"[FFFF00]/e 123456789 1[FFFFFF] → Emote #1 to UID\n"
                                error_msg += f"[FFFF00]/e ring[FFFFFF] → Send ring emote to yourself\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                continue
    
                            # Show "preparing" message
                            initial_message = f'[B][C]{get_random_color()}\n🎭 গরিব মানুষ BOT দিয়ে Emote দেয়.....\n'
                            await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                            
                            target_uids = []
                            emote_key = None
    
                            try:
                                # Determine if last part is emote key (could be number or name)
                                last_part = parts[-1].lower()
        
                                # Check if last part is an emote (number or name)
                                # Note: Your numbers go up to 417, so check for 3-digit numbers too
                                is_number = last_part.isdigit() and last_part in NUMBER_EMOTES
                                is_name = last_part in NAME_EMOTES
        
                                if is_number or is_name:
                                    # Case 1: /e ak or /e 1 (only emote - send to sender)
                                    if len(parts) == 2:
                                        emote_key = last_part
                                        target_uids.append(int(response.Data.uid))
            
                                    # Case 2: /e 123456789 heart (UID + emote)
                                    elif len(parts) == 3:
                                        target_uids.append(int(parts[1]))
                                        emote_key = last_part
            
                                    # Case 3: /e 111 222 333 ak (multiple UIDs + emote)
                                    else:
                                        for i in range(1, len(parts) - 1):
                                            target_uids.append(int(parts[i]))
                                        emote_key = last_part
                                else:
                                    # Last part is not a valid emote
                                    error_msg = f"[B][C][FF0000]❌ Invalid emote: '{last_part}'\n"
                                    error_msg += f"[FFFFFF]Use numbers (1-{len(NUMBER_EMOTES)}) or names like 'ak', 'heart', 'dance', 'ring'\n"
                                    error_msg += f"[FFFFFF]Use /e list names to see all available names\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    continue
        
                                # Get emote ID from either number or name dictionary
                                emote_id = None
                                emote_name_display = None
                                
                                if is_number:
                                    # Number-based emote
                                    emote_id = NUMBER_EMOTES.get(emote_key)
                                    emote_name_display = f"#{emote_key}"
                                else:
                                    # Name-based emote
                                    emote_id = NAME_EMOTES.get(emote_key)
                                    emote_name_display = emote_key
        
                                if not emote_id:
                                    error_msg = f"[B][C][FF0000]❌ Emote '{emote_name_display}' not found!\n"
                                    if emote_key.isdigit():
                                        error_msg += f"[FFFFFF]Available numbers: 1-{len(NUMBER_EMOTES)}\n"
                                    else:
                                        error_msg += f"[FFFFFF]Use /e list names to see all available names\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    continue
        
                                # Send emotes
                                success_count = 0
                                failed_uids = []
        
                                for target_uid in target_uids:
                                    try:
                                        H = await Emote_k(target_uid, int(emote_id), key, iv, region)
                                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                        success_count += 1
                                        await asyncio.sleep(0.1)
                                    except Exception as e:
                                        print(f"Error sending emote to {target_uid}: {e}")
                                        failed_uids.append(str(target_uid))
        
                                # Success message
                                if success_count > 0:
                                    if target_uids[0] == int(response.Data.uid):
                                        target_list = "Yourself"
                                    elif len(target_uids) == 1:
                                        target_list = str(target_uids[0])
                                    else:
                                        target_list = f"{len(target_uids)} players"
            
                                    success_msg = f"[B][C][FFFF00]✅ EMOTE SENT!\n"
                                    success_msg += f"[FFFFFF]────────────────\n"
                                    success_msg += f"[FFFF00]🎭 Emote: {emote_name_display}\n"
                                    success_msg += f"[FFFF00]🆔 ID: {emote_id}\n"
                                    success_msg += f"[FFFF00]👤 Target: {target_list}\n"
                                    success_msg += f"[FFFF00]📊 Status: {success_count}/{len(target_uids)} successful\n"
            
                                    if failed_uids:
                                        success_msg += f"[FF0000]❌ Failed: {', '.join(failed_uids)}\n"
            
                                    success_msg += f"[FFFFFF]────────────────\n"
            
                                    await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                else:
                                    error_msg = f"[B][C][FF0000]❌ Failed to send emote to any target!\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    
                            except ValueError as ve:
                                print("ValueError:", ve)
                                error_msg = f"[B][C][FF0000]❌ Invalid format!\n"
                                error_msg += f"[FFFFFF]UIDs must be numbers (like 123456789)\n"
                                error_msg += f"[FFFFFF]Examples: /e ak, /e 123456789 heart, /e 1, /e ring\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            except Exception as e:
                                print(f"Error processing /e command: {e}")
                                error_msg = f"[B][C][FF0000]❌ Error: {str(e)[:50]}\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                                #GALI SPAM MESSAGE 
                        # Add at the top with other global variables
                        BLOCKED_NAMES = [
    "jisan", "Jisan", "JISAN", "jisan", "Jisan", "jisan", "jisan", "jisan123x", 
    "jisan123", "JISAN1", "jisan", "jisan@123", "Jisan1", "jisan@1", 
    "jisan#", "#jisan", "@jisan", "@Jisan", "#Jisan", "jisan@FF", "jisan_", 
    "jisan#", "fux", "Fux", "JISAN#", "JISAN@", "@jisan@", "jisan#123", 
    "jisan", "JisanfF", "jisan_FF", "FayEz_jisan", "fAyEz_jisan", 
    "jisan01", "adil", "fHUXfF", "jisan@FF", "jisan_#", "JISAN123", 
    "jisan!", "#jisan", "Jisan_123", "jisan#_1", "JISAN1#", "jisan", 
    "jisan@!", "jisan@_123", "jisan_FF_", "jisan@FayEz", "@JISAN1", 
    "@jisan01", "FAYEZjisan", "jisan", "FayEz_jisan_", "fUyEz_jisan", 
    "jisan!@", "@jisan01", "#FayEz_jisan", "fAyEz_jisan@", "@Jisan123", 
    "fahx", "fuh**", "fayez!jisan", "jisan", "jisan#FayEz", 
    "Jisan@FayEz", "fAyEz#jisan", "jisan", "gop gop fayez", 
    "fHUXfayez", "@jisan", "#fayezjisan", "fHUXfayez", "f@yez", 
    "jisan!!", "jisan_ff", "jisan", "@jisan", "fayez67", 
    "JISAN_FayEz", "@fayez_jisan", "FAYEয", "ফায়ez", 
    "fayezjisan", "JISAN", "@Jisan_FayEz", "ফায়েয", 
    "ফুহক্স", "jisan.", "fayez ullah hawlader", "FUH X", "ফায়েজ" ]
    # Add your actual name

                        # Then in the /gop command handler, add this check:
                        if inPuTMsG.strip().startswith('/gopgop '):
                            print('Processing /gopgop command')

                            try:
                                parts = inPuTMsG.strip().split(maxsplit=1)

                                if len(parts) < 2:
                                    error_msg = (
                                        "[B][C][FF0000]❌ ERROR! Usage:\n"
                                        "/gopgop <name>\n"
                                        "Example: /gopgop hater"
                                    )
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    name = parts[1].strip()
            
                                    # ADD THIS CHECK - Prevent targeting yourself
                                    if name.lower() in [n.lower() for n in BLOCKED_NAMES]:
                                        error_msg = (
                                            f"[B][C][FF0000]এই খান🤫কির ছেলে!\n"
                                            f"[FFFFFF] তো🤫র আ🤫ব্বু🤫কে গা🤫লি দিতে আ🤫সছোস "
                                            f"[FF0000]তোর মা🤫কে চু🤫দী\n"
                                            f"[FFFFFF]বোকাচো🤫দা, তোর মা🤫কে কন🤫ডম লাগিয়ে চু🤫দি "
                                        )
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                        continue
            
                                    # Rest of your code continues here...
                                    messages = [
                                        "{Name} [B][C][00FFFF]উলা ল🫡ইট্টা বইট্টা মা🫡গির পোলা, তর মা🫡য়রে আসমানে চু🫡দি, জমিনে চু🫡দি, উড়ায়য়া চু🫡দি, ঘুড়ায়য়া চু🫡দি রে খা🤫নকি মা🫡গির পুলা!!!",
                                        "{Name} [B][C][00FFFF]নাউজুবিল্লা দিয়া করলাম শুরু, তোর মার পু🫡টকিতে ডু🫡কামু ২টা গরু। গরু নাকি ডাকে হাম্বা? তোর মার ভো🫡দায় ডু🫡কামু ২টা ইলেক্ট্রিকের খাম্বা। খাম্বার আছে নাকি তার? তোর মার বুদায় দিমু জোরে ২ডা পার!! পার যদি হয় শক্ত, তোর মার বো🫡দা দিয়া বাইর হইবো গরগরাইয়া রক্ত। রক্তের কালার যদি হয় লাল, তোর মা🫡রে আমি চু🫡দি চিরকাল!!",
                                        "{Name} [B][C][00FFFF] আমি গালি জানি না, গালি গেছি ভুইলা। তোর মায়ের চু🫡দমু ছায়া, বে-লাউ খুইলা। তোর আবাল জাতের মায়ের চু🫡দি!!",
                                        "{Name} [B][C][00FFFF] তোর মায়ের ভো🫡দায় শুটকি মাছের গন্ধ। তোর মায়ের চু🫡ইদা অনলাইনের করমু অন্ধ।",
                                        "{Name} [B][C][00FFFF] এই চু🫡দানি বুদানি মা🫡গির ঝি, তুই নাকি ফ্রী ফায়ার কামলা? তর মার বুদার ভিতর আজকে করমু হামলা।",
                                        "[B][C][00FFFF] রাম চু🫡দলাম, লখোন চু🫡দলাম, চু🫡দলাম হনুমান। তোর মা🫡য়েরে অনলাইনে চু🫡ইদা হইছি মসজিদে ইমাম। ব্যাশা জাতের আম্মুরে চু🫡দি!!!!",
                                        "{Name} [B][C][00FFFF]তুই নাকি অনলাইনের কিং? তোর মা🫡য়ের ভো🫡দার মধ্যে দিমু আমি গরম গরম ডিম, খা🫡নকি মা🫡গির পোলা। সেই ডিম যদি হয় নষ্ট, তোর মায়ের ভো🫡দা চু🫡ইদা করুম নষ্ট।",
                                        "{Name} [B][C][00FFFF]নাউজুবিল্লাহ বিল্লা করলাম শুরু, আমি নাকি চু🫦দার গুরু। চু🫦দায় চু🫦দায় ভো🫦দা লড়ে, দুদে খায় বাড়ি আবাল। তর মা🫦রে চু🫦দতে চু🫦দতে নিয়া যামু তর নানার বাড়ি। নানার বাড়ি আছে নাকি তর মামু? তর কচি বইনের দুদুটা আমি কামরা🫦ইয়া কামরা🫦ইয়া খামু।!!",
                                        "{Name} [B][C][00FFFF] কিরে ফকিন্নি মা🫦গির পোলা? যদি কস তর বাড়ি কুমিল্লা, তর মায়ে চু🫦দি ভাই ব্রাদার মিল্লা। যদি কস তর বাড়ি পাবনা, তর মা🫦রে চু🫦দতে নাই কোনো ভাবনা। যদি কস তর বাড়ি সাভার, তর মা🫦রে পু🫦টকি মারমু একশো এক বার!!!",
                                        "{Name} [B][C][00FFFF] দেক, আকাশ ভরা তারা। তোর মা🫦রে চু🫦দমু, তোর ধো🫦ন হবে খার। আকাশের অনেক তারার ভিড়ে, তোর মা🫦রে চু🫦দসি নেশার ঘরে।!!",
                                        "{Name} [B][C][00FFFF] তোর মার বো🫦দা নি কালা? চু🫦ইদা করমু জ্বা🫦লা-ফালা।!",
                                        "{Name} [B][C][00FFFF]  রাতে দেখি তারা, দিনে দেখি সূর্য। তোর মা-বোনের মুখে ডেলে দিবো এক ফোটা বী🫦র্যও।!",
                                        "{Name} [B][C][00FFFF]আম পাতা জোড়া, তোর মা🫦রে চু🫦দমু উড়া-দুড়া। জল পড়ে পাতা নড়ে, তোর মার ভো🫦দার কথা মনে পড়ে।!!",

                                        "{Name} [B][C][00FFFF] ভয়েজ শোন মন দিয়ে, তোর কচি বোনরে চু🫦দুম আমার ৫৬ ইঞ্চি ধ🫦ন দিয়ে।!",
                                        "{Name} [B][C][00FFFF] এক একে এক, মাকে চু🫦দি খা🫦ড়ায় খা🫦ড়ায় দেখ।!!",
                                        "{Name} [B][C][00FFFF] দুই একে দুই, তোর বই🫦নের ভো🫦দার ভিতর ঢু🫦কাই সুই!!"
                                            ]

                                    # Send each message one by one with random color
                                    for msg in messages:
                                        colored_message = f"[B][C]{get_random_color()} {msg.replace('{Name}', name.upper())}"
                                        await safe_send_message(response.Data.chat_type, colored_message, uid, chat_id, key, iv)
                                        await asyncio.sleep(2)

                            except Exception as e:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Something went wrong:\n{str(e)}"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)                        
                                
                        # Add this with your other command handlers in the TcPChaT function

                        # EVO CYCLE START COMMAND - @evos
                        # EVO CYCLE START COMMAND - @evos
                        # EVO CYCLE START COMMAND - @evos
                        if inPuTMsG.strip().startswith('@evos'):
                            print('Processing evo cycle start command in any chat type')
    
                            parts = inPuTMsG.strip().split()
                            uids = []
    
                            # Always use the sender's UID (the person who typed @evos)
                            sender_uid = str(response.Data.uid)
                            uids.append(sender_uid)
                            print(f"Using sender's UID: {sender_uid}")
    
                            # Optional: Also allow specifying additional UIDs
                            if len(parts) > 1:
                                for part in parts[1:]:  # Skip the first part which is "@evos"
                                    if part.isdigit() and len(part) >= 7 and part != sender_uid:  # UIDs are usually 7+ digits
                                        uids.append(part)
                                        print(f"Added additional UID: {part}")

                            # Stop any existing evo cycle
                            if evo_cycle_task and not evo_cycle_task.done():
                                evo_cycle_running = False
                                evo_cycle_task.cancel()
                                await asyncio.sleep(0.5)
    
                            # Start new evo cycle
                            evo_cycle_running = True
                            evo_cycle_task = asyncio.create_task(
                                evo_cycle_spam(uids, key, iv, region, LoGinDaTaUncRypTinG)
                            )
    
                            # SUCCESS MESSAGE
                            if len(uids) == 1:
                                success_msg = f"""[c][b][A80000]◉━━━━━━━━━━━━━━━◉
[A80000][b][c]💠  [00FFFF]EVO CYCLE ACTIVATED! 

[A80000]◎ [b][c][FFD053] Status:[b][c][ffffff] ✅ SUCCESS!

[A80000]◎ [b][c][FFD053] Target:[b][c][ffffff] Yourself 🎯

[A80000]◎ [b][c][FFD053] Emotes:[b][c][ffffff] All 18 Evolution Emotes 🎭

[A80000]◎ [b][c][FFD053] Delay:[b][c][ffffff] 5 Seconds Between Emotes ⏰

[A80000]◎ [b][c][FFD053] Cycle:[b][c][ffffff] Continuous Loop [DA70D6](Until @sevos) 🔄
 [b][c][A80000]◉━━━━━━━━━━━━━━━◉"""
                            else:
                                success_msg = f"""[c][b][A80000]◉━━━━━━━━━━━━━━◉
[A80000][b][c]💠  [00FFFF]EVO CYCLE ACTIVATED! 

[A80000]◎ [b][c][FFD053] Status:[b][c][ffffff] ✅ SUCCESS!

[A80000]◎ [b][c][FFD053] Target:[b][c][ffffff] Yourself 🎯

[A80000]◎ [b][c][FFD053] Emotes:[b][c][ffffff] All 18 Evolution Emotes 🎭

[A80000]◎ [b][c][FFD053] Delay:[b][c][ffffff] 5 Seconds Between Emotes ⏰

[A80000]◎ [b][c][FFD053] Cycle:[b][c][ffffff] Continuous Loop [DA70D6](Until @sevos) 🔄
 [b][c][A80000]◉━━━━━━━━━━━━━━◉"""
    
                            await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            print(f"Started evolution emote cycle for UIDs: {uids}")
                        
                        # EVO CYCLE STOP COMMAND - @sevos
                        if inPuTMsG.strip() == '@sevos':
                            if evo_cycle_task and not evo_cycle_task.done():
                                evo_cycle_running = False
                                evo_cycle_task.cancel()
                                success_msg = f"[B][C][EAC154]✅ SUCCESS! Evolution emote cycle stopped successfully!\n"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                print("Evolution emote cycle stopped by command")
                            else:
                                error_msg = f"[B][C][A80000]❌ ERROR! No active evolution emote cycle to stop!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # Fast emote spam command - works in all chat types
                        if inPuTMsG.strip().startswith('/fast'):
                            print('Processing fast emote spam in any chat type')
                            
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 3:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /fast uid1 [uid2] [uid3] [uid4] emoteid\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                # Parse uids and emoteid
                                uids = []
                                emote_id = None
                                
                                for part in parts[1:]:
                                    if part.isdigit():
                                        if len(part) > 3:  # Assuming UIDs are longer than 3 digits
                                            uids.append(part)
                                        else:
                                            emote_id = part
                                    else:
                                        break
                                
                                if not emote_id and parts[-1].isdigit():
                                    emote_id = parts[-1]
                                
                                if not uids or not emote_id:
                                    error_msg = f"[B][C][FF0000]❌ ERROR! Invalid format! Usage: /fast uid1 [uid2] [uid3] [uid4] emoteid\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    # Stop any existing fast spam
                                    if fast_spam_task and not fast_spam_task.done():
                                        fast_spam_running = False
                                        fast_spam_task.cancel()
                                    
                                    # Start new fast spam
                                    fast_spam_running = True
                                    fast_spam_task = asyncio.create_task(fast_emote_spam(uids, emote_id, key, iv, region))
                                    
                                    # SUCCESS MESSAGE
                                    success_msg = f"[B][C][FFFF00]✅ SUCCESS! Fast emote spam started!\nTargets: {len(uids)} players\nEmote: {emote_id}\nSpam count: 25 times\n"
                                    await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)

                        # Custom emote spam command - works in all chat types
                        if inPuTMsG.strip().startswith('/p'):
                            print('Processing custom emote spam in any chat type')
                            
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 4:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /p (uid) (emote_id) (times)\nExample: /p 123456789 909000001 10\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                try:
                                    target_uid = parts[1]
                                    emote_id = parts[2]
                                    times = int(parts[3])
                                    
                                    if times <= 0:
                                        error_msg = f"[B][C][FF0000]❌ ERROR! Times must be greater than 0!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    elif times > 1000:
                                        error_msg = f"[B][C][FF0000]❌ ERROR! Maximum 100 times allowed for safety!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    else:
                                        # Stop any existing custom spam
                                        if custom_spam_task and not custom_spam_task.done():
                                            custom_spam_running = False
                                            custom_spam_task.cancel()
                                         
                                        
                                        # Start new custom spam
                                        custom_spam_running = True
                                        custom_spam_task = asyncio.create_task(custom_emote_spam(target_uid, emote_id, times, key, iv, region))
                                        
                                        # SUCCESS MESSAGE
                                        success_msg = f"[B][C][FFFF00]✅ SUCCESS! Custom emote spam started!\nTarget: {target_uid}\nEmote: {emote_id}\nTimes: {times}\n"
                                        await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                        
                                except ValueError:
                                    error_msg = f"[B][C][FF0000]❌ ERROR! Invalid number format! Usage: /p (uid) (emote_id) (times)\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ ERROR! {str(e)}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    
                        # Spam request command - works in all chat types
                        # Spam request command - works in all chat types

                        # Spam request command - works in all chat types
                        if inPuTMsG.strip().startswith('/spm_inv'):
                            print('Processing spam invite with cosmetics')
    
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ Usage: /spm_inv (uid)\nExample: /spm_inv 123456789\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
        
                                # Stop any existing spam request
                                if spam_request_task and not spam_request_task.done():
                                    spam_request_running = False
                                    spam_request_task.cancel()
                                    await asyncio.sleep(0.5)
        
                                # Start new spam request WITH COSMETICS
                                spam_request_running = True
                                spam_request_task = asyncio.create_task(spam_request_loop_with_cosmetics(target_uid, key, iv, region))
        
                                # SUCCESS MESSAGE
                                success_msg = f"[B][C][FFFF00]✅ COSMETIC SPAM STARTED!\n🎯 Target: {target_uid}\n📦 Requests: 30\n🎭 Features: V-Badges + Cosmetics\n⚡ Each invite has different cosmetics!\n"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)

                        # Stop spam request command - works in all chat types
                        if inPuTMsG.strip() == '/stop spm_inv':
                            if spam_request_task and not spam_request_task.done():
                                spam_request_running = False
                                spam_request_task.cancel()
                                success_msg = f"[B][C][FFFF00]✅ SUCCESS! Spam request stopped successfully!\n"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            else:
                                error_msg = f"[B][C][FF0000]❌ ERROR! No active spam request to stop!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # In TcPChaT function, update  /status command:
                        if inPuTMsG.strip().startswith('/status'):
                            print('Processing status command')
    
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ Usage:  /status (player_uid)\nExample:  /status 123456789\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                return
    
                            target_uid = parts[1]
    
                            # DEBUG: Show cache before clearing
                            print(f"\n🔍 BEFORE clearing cache:")
                            debug_file_cache()
                            
                            # Clear old cache entry first
                            clear_cache_entry(target_uid)
    
                            # Send initial message
                            initial_msg = f"[B][C][FFFF00]🔍 Checking status of {fix_num(target_uid)}...\n"
                            await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
                            
                            try:
                                # Create and send status request
                                status_packet = await createpacketinfo(target_uid, key, iv)
                                if not status_packet:
                                    error_msg = f"[B][C][FF0000]❌ Failed to create status packet!\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    return
        
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', status_packet)
                                print(f"📤 Sent status request for {target_uid}")
        
                                # Wait for response - check FILE cache
                                max_retries = 12  # Increased for reliability
                                response_received = False
        
                                for attempt in range(max_retries):
                                    print(f"⏳ Checking file cache... attempt {attempt + 1}/{max_retries}")
            
                                    # Check FILE cache
                                    cache_data = load_from_cache(target_uid)
                                    if cache_data:
                                        print(f"🎯 FOUND in file cache! Status: {cache_data['status']}")
                                        response_received = True
                
                                        # DEBUG: Show what we found
                                        print(f"📦 Cache data keys: {list(cache_data.keys())}")
                
                                        # Build response
                                        status_msg = f"[B][C][FFFF00]📊 PLAYER STATUS\n"
                                        status_msg += f"────────────────\n"
                                        status_msg += f"👤 UID: {fix_num(target_uid)}\n"
                                        status_msg += f"📊 Status: {cache_data['status']}\n"
                
                                        # Add specific info
                                        if "IN ROOM" in cache_data['status']:
                                            if 'room_id' in cache_data:
                                                status_msg += f"🏠 Room ID: {fix_num(cache_data['room_id'])}\n"
                                                status_msg += f"💡 Use: /roomspam {target_uid}\n"
                                                room_id_msg = f"{fix_num(cache_data['room_id'])}"
                                                await safe_send_message(response.Data.chat_type, room_id_msg, uid, chat_id, key, iv)
                                            else:
                                                status_msg += f"🏠 Room ID: Not available\n"
                
                                        elif "INSQUAD" in cache_data['status']:
                                            if 'leader_id' in cache_data:
                                                status_msg += f"👑 Leader: {fix_num(cache_data['leader_id'])}\n"
                    
                                            # Try to get squad size
                                            try:
                                                if 'parsed_json' in cache_data:
                                                    parsed = cache_data['parsed_json']
                                                    if '5' in parsed and 'data' in parsed['5']:
                                                        squad_data = parsed['5']['data']['1']['data']
                                                        if '9' in squad_data and 'data' in squad_data['9']:
                                                            members = squad_data['9']['data']
                                                            max_members = squad_data['10']['data'] + 1
                                                            status_msg += f"👥 Squad: {members}/{max_members}\n"
                                            except:
                                                pass
                
                                        elif "OFFLINE" in cache_data['status']:
                                            status_msg += f"🔴 Player is offline\n"
                
                                        elif "INGAME" in cache_data['status']:
                                            status_msg += f"🎮 Player is in a match\n"
                
                                        elif "SOLO" in cache_data['status']:
                                            status_msg += f"👤 Player is solo\n"
                
                                        status_msg += f"────────────────\n"
                                        status_msg += f"✅ Real-time data\n"
                
                                        await safe_send_message(response.Data.chat_type, status_msg, uid, chat_id, key, iv)

                                        # DEBUG: Show cache after success
                                        print(f"\n✅ AFTER successful response:")
                                        debug_file_cache()
                
                                        break
            
                                    # Wait between checks
                                    await asyncio.sleep(0.5)
                                                        
                                if not response_received:
                                    # DEBUG: Show cache state on failure
                                    print(f"\n❌ FAILED after {max_retries} tries")
                                    debug_file_cache()
            
                                    error_msg = f"[B][C][FF0000]❌ STATUS CHECK FAILED\n"
                                    error_msg += f"────────────────\n"
                                    error_msg += f"👤 UID: {fix_num(target_uid)}\n"
                                    error_msg += f"📛 No response from server\n"
                                    error_msg += f"────────────────\n"
                                    error_msg += f"💡 Possible issues:\n"
                                    error_msg += f"• Player is offline\n"
                                    error_msg += f"• Server is busy\n"
                                    error_msg += f"• Try again in 10 seconds\n"
            
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
            
                            except Exception as e:
                                print(f"❌ Status command error: {e}")
                                import traceback
                                traceback.print_exc()
        
                                error_msg = f"[B][C][FF0000]❌ Error: {str(e)[:50]}\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # NEW EVO COMMANDS
                        if inPuTMsG.strip().startswith('/evo '):
                            print('Processing evo command in any chat type')
                            
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /evo uid1 [uid2] [uid3] [uid4] number(1-21)\nExample: /evo 123456789 1\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                # Parse uids and number
                                uids = []
                                number = None
                                
                                for part in parts[1:]:
                                    if part.isdigit():
                                        if len(part) <= 2:  # Number should be 1-21 (1 or 2 digits)
                                            number = part
                                        else:
                                            uids.append(part)
                                    else:
                                        break
                                
                                if not number and parts[-1].isdigit() and len(parts[-1]) <= 2:
                                    number = parts[-1]
                                
                                if not uids or not number:
                                    error_msg = f"[B][C]{get_random_color()}\n🎭 গরিব মানুষ BOT দিয়ে Emote দেয়.....\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    try:
                                        number_int = int(number)
                                        if number_int not in EMOTE_MAP:
                                            error_msg = f"[B][C][FF0000]❌ ERROR! Number must be between 1-21 only!\n"
                                            await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                        else:
                                            initial_message = f"[B][C]{get_random_color()}\nSending evolution emote {number_int}...\n"
                                            await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                                            
                                            success, result_msg = await evo_emote_spam(uids, number_int, key, iv, region)
                                            
                                            if success:
                                                success_msg = f"[B][C][FFFF00]✅ SUCCESS! {result_msg}\n"
                                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                            else:
                                                error_msg = f"[B][C][FF0000]❌ ERROR! {result_msg}\n"
                                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                            
                                    except ValueError:
                                        error_msg = f"[B][C][FF0000]❌ ERROR! Invalid number format! Use 1-21 only.\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        if inPuTMsG.strip().startswith('/evo_fast '):
                            print('Processing evo_fast command in any chat type')
                            
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /evo_fast uid1 [uid2] [uid3] [uid4] number(1-21)\nExample: /evo_fast 123456789 1\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                # Parse uids and number
                                uids = []
                                number = None
                                
                                for part in parts[1:]:
                                    if part.isdigit():
                                        if len(part) <= 2:  # Number should be 1-21 (1 or 2 digits)
                                            number = part
                                        else:
                                            uids.append(part)
                                    else:
                                        break
                                
                                if not number and parts[-1].isdigit() and len(parts[-1]) <= 2:
                                    number = parts[-1]
                                
                                if not uids or not number:
                                    error_msg = f"[B][C][FF0000]❌ ERROR! Invalid format! Usage: /evo_fast uid1 [uid2] [uid3] [uid4] number(1-21)\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    try:
                                        number_int = int(number)
                                        if number_int not in EMOTE_MAP:
                                            error_msg = f"[B][C][FF0000]❌ ERROR! Number must be between 1-21 only!\n"
                                            await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                        else:
                                            # Stop any existing evo_fast spam
                                            if evo_fast_spam_task and not evo_fast_spam_task.done():
                                                evo_fast_spam_running = False
                                                evo_fast_spam_task.cancel()
                                                await asyncio.sleep(0.5)
                                            
                                            # Start new evo_fast spam
                                            evo_fast_spam_running = True
                                            evo_fast_spam_task = asyncio.create_task(evo_fast_emote_spam(uids, number_int, key, iv, region))
                                            
                                            # SUCCESS MESSAGE
                                            emote_id = EMOTE_MAP[number_int]
                                            success_msg = f"[B][C][FFFF00]✅ SUCCESS! Fast evolution emote spam started!\nTargets: {len(uids)} players\nEmote: {number_int} (ID: {emote_id})\nSpam count: 25 times\nInterval: 0.1 seconds\n"
                                            await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                            
                                    except ValueError:
                                        error_msg = f"[B][C][FF0000]❌ ERROR! Invalid number format! Use 1-21 only.\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

# ================= BUNDLE COMMAND START =================
   # ================= FINAL BUNDLE COMMAND (FAST) =================
                        if inPuTMsG.strip().startswith('/b'):
                            print('Processing bundle command')
    
                            parts = inPuTMsG.strip().split()
                            
                            if len(parts) < 2:
                                # Show available bundles
                                bundle_list = """[B][C][00FF00]🎁 AVAILABLE BUNDLES 🎁
[FF6347]━[32CD32]━[7B68EE]━[FF4500]━[1E90FF]━[ADFF2F]━[FF69B4]━[8A2BE2]━[DC143C]━[FF8C00]━[BA55D3]━[7CFC00]━[FFC0CB]
[FFFFFF]• midnight
[FFFFFF]• aurora
[FFFFFF]• naruto  
[FFFFFF]• paradox
[FFFFFF]• frostfire
[FFFFFF]• rampage
[FFFFFF]• cannibal
[FFFFFF]• devil
[FFFFFF]• scorpio
[FFFFFF]• dreamspace
[FFFFFF]• itachi
[FFFFFF]• OB54jisan
[FF6347]━[32CD32]━[7B68EE]━[FF4500]━[1E90FF]━[ADFF2F]━[FF69B4]━[8A2BE2]━[DC143C]━[FF8C00]━[BA55D3]━[7CFC00]━[FFC0CB]
[00FF00]Usage: /b [name]
[FFFFFF]Example: /b midnight"""
                                await safe_send_message(response.Data.chat_type, bundle_list, uid, chat_id, key, iv)
                            else:
                                bundle_name = parts[1].lower()
        
                                # All bundles use the same ID: 914000002
                                bundle_id = BUNDLE.get(bundle_name)
        
                                initial_msg = f"[B][C][00FF00]🎁 Sending {bundle_name}\n"
                                await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
        
                                try:
                                    # Create bundle packet
                                    bundle_packet = await bundle_packet_async(bundle_id, key, iv, region)
            
                                    if bundle_packet and online_writer:
                                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', bundle_packet)
                                        success_msg = f"[B][C][00FF00]✅ Done: {bundle_name}"
                                        await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                    else:
                                        error_msg = f"[B][C][FF0000]❌ Failed to create bundle packet!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ Error sending bundle: {str(e)[:50]}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # =========================================
                        # NEW EVO_CUSTOM COMMAND
                        if inPuTMsG.strip().startswith('/evo_c '):
                            print('Processing evo_c command in any chat type')
                            
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 3:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /evo_c uid1 [uid2] [uid3] [uid4] number(1-21) time(1-100)\nExample: /evo_c 123456789 1 10\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                # Parse uids, number, and time
                                uids = []
                                number = None
                                time_val = None
                                
                                for part in parts[1:]:
                                    if part.isdigit():
                                        if len(part) <= 2:  # Number or time should be 1-100 (1, 2, or 3 digits)
                                            if number is None:
                                                number = part
                                            elif time_val is None:
                                                time_val = part
                                            else:
                                                uids.append(part)
                                        else:
                                            uids.append(part)
                                    else:
                                        break
                                
                                # If we still don't have time_val, try to get it from the last part
                                if not time_val and len(parts) >= 3:
                                    last_part = parts[-1]
                                    if last_part.isdigit() and len(last_part) <= 3:
                                        time_val = last_part
                                        # Remove time_val from uids if it was added by mistake
                                        if time_val in uids:
                                            uids.remove(time_val)
                                
                                if not uids or not number or not time_val:
                                    error_msg = f"[B][C][FF0000]❌ ERROR! Invalid format! Usage: /evo_c uid1 [uid2] [uid3] [uid4] number(1-21) time(1-100)\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    try:
                                        number_int = int(number)
                                        time_int = int(time_val)
                                        
                                        if number_int not in EMOTE_MAP:
                                            error_msg = f"[B][C][FF0000]❌ ERROR! Number must be between 1-21 only!\n"
                                            await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                        elif time_int < 1 or time_int > 100:
                                            error_msg = f"[B][C][FF0000]❌ ERROR! Time must be between 1-100 only!\n"
                                            await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                        else:
                                            # Stop any existing evo_custom spam
                                            if evo_custom_spam_task and not evo_custom_spam_task.done():
                                                evo_custom_spam_running = False
                                                evo_custom_spam_task.cancel()
                                                await asyncio.sleep(0.5)
                                            
                                            # Start new evo_custom spam
                                            evo_custom_spam_running = True
                                            evo_custom_spam_task = asyncio.create_task(evo_custom_emote_spam(uids, number_int, time_int, key, iv, region))
                                            
                                            # SUCCESS MESSAGE
                                            emote_id = EMOTE_MAP[number_int]
                                            success_msg = f"[B][C][FFFF00]✅ SUCCESS! Custom evolution emote spam started!\nTargets: {len(uids)} players\nEmote: {number_int} (ID: {emote_id})\nRepeat: {time_int} times\nInterval: 0.1 seconds\n"
                                            await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                            
                                    except ValueError:
                                        error_msg = f"[B][C][FF0000]❌ ERROR! Invalid number/time format! Use numbers only.\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

# ================= BUNDLE COMMAND START =================
   # ================= FINAL BUNDLE COMMAND (FAST) =================
                        if inPuTMsG.strip().startswith('/bundle'):
                            print('Processing bundle command')
    
                            parts = inPuTMsG.strip().split()
                            
                            if len(parts) < 2:
                                # Show available bundles
                                bundle_list = """[B][C][00FF00]🎁 AVAILABLE BUNDLES 🎁
[FF6347]━[32CD32]━[7B68EE]━[FF4500]━[1E90FF]━[ADFF2F]━[FF69B4]━[8A2BE2]━[DC143C]━[FF8C00]━[BA55D3]━[7CFC00]━[FFC0CB]
[FFFFFF]• midnight
[FFFFFF]• aurora
[FFFFFF]• naruto  
[FFFFFF]• paradox
[FFFFFF]• frostfire
[FFFFFF]• rampage
[FFFFFF]• cannibal
[FFFFFF]• devil
[FFFFFF]• scorpio
[FFFFFF]• dreamspace
[FFFFFF]• itachi
[FFFFFF]• OB54jisan 
[FF6347]━[32CD32]━[7B68EE]━[FF4500]━[1E90FF]━[ADFF2F]━[FF69B4]━[8A2BE2]━[DC143C]━[FF8C00]━[BA55D3]━[7CFC00]━[FFC0CB]
[00FF00]Usage: /bundle [name]
[FFFFFF]Example: /bundle midnight"""
                                await safe_send_message(response.Data.chat_type, bundle_list, uid, chat_id, key, iv)
                            else:
                                bundle_name = parts[1].lower()
        
                                # All bundles use the same ID: 914000002
                                bundle_id = BUNDLE.get(bundle_name)
        
                                initial_msg = f"[B][C][00FF00]🎁 Sending {bundle_name}\n"
                                await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
        
                                try:
                                    # Create bundle packet
                                    bundle_packet = await bundle_packet_async(bundle_id, key, iv, region)
            
                                    if bundle_packet and online_writer:
                                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', bundle_packet)
                                        success_msg = f"[B][C][00FF00]✅ Done: {bundle_name}"
                                        await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                    else:
                                        error_msg = f"[B][C][FF0000]❌ Failed to create bundle packet!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ Error sending bundle: {str(e)[:50]}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                        # ===============================================================
   # ================= FINAL ANIMATION COMMAND (FAST) =================
                        if inPuTMsG.strip().startswith('/animation'):
                            print('Processing bundle command')
    
                            parts = inPuTMsG.strip().split()
                            
                            if len(parts) < 2:
                                # Show available bundles
                                bundle_list = """[B][C][00FF00]🎁 AVAILABLE ANIMATION 🎁
[FF6347]━[32CD32]━[7B68EE]━[FF4500]━[1E90FF]━[ADFF2F]━[FF69B4]━[8A2BE2]━[DC143C]━[FF8C00]━[BA55D3]━[7CFC00]━[FFC0CB]
[FFFFFF]• midnight
[FFFFFF]• aurora
[FFFFFF]• naruto  
[FFFFFF]• paradox
[FFFFFF]• frostfire
[FFFFFF]• rampage
[FFFFFF]• cannibal
[FFFFFF]• devil
[FFFFFF]• scorpio
[FFFFFF]• dreamspace
[FFFFFF]• itachi
[FFFFFF]• OB54ABHI 
[FF6347]━[32CD32]━[7B68EE]━[FF4500]━[1E90FF]━[ADFF2F]━[FF69B4]━[8A2BE2]━[DC143C]━[FF8C00]━[BA55D3]━[7CFC00]━[FFC0CB]
[00FF00]Usage: /animation [name]
[FFFFFF]Example: /animation midnight"""
                                await safe_send_message(response.Data.chat_type, bundle_list, uid, chat_id, key, iv)
                            else:
                                bundle_name = parts[1].lower()
        
                                # All bundles use the same ID: 914000002
                                bundle_id = BUNDLE.get(bundle_name)
        
                                initial_msg = f"[B][C][00FF00]🎁 Sending {bundle_name}\n"
                                await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
        
                                try:
                                    # Create bundle packet
                                    bundle_packet = await animation_packet(bundle_id, key, iv)
            
                                    if bundle_packet and online_writer:
                                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', bundle_packet)
                                        success_msg = f"[B][C][00FF00]✅ Done: {bundle_name}"
                                        await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                                    else:
                                        error_msg = f"[B][C][FF0000]❌ Failed to create bundle packet!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ Error sending bundle: {str(e)[:50]}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)


                        if inPuTMsG.strip().startswith('/look'):
                            print('Processing combo command')

                            parts = inPuTMsG.strip().split()
                            
                            if len(parts) < 2:
                                bundle_list = """[B][C][00FF00]🎁 AVAILABLE LOOK 🎁
[FFFFFF]1 • rampage
[FFFFFF]2 • cannibal
[FFFFFF]3 • devil  
[FFFFFF]4 • scorpio
[FFFFFF]5 • frostfire
[FFFFFF]6 • paradox
[FFFFFF]7 • naruto
[FFFFFF]8 • aurora
[FFFFFF]9 • midnight
[FFFFFF]10 • itachi
[FFFFFF]11 • dreamspace
[FFFFFF]12 • OB54ABHI 

[00FF00]Usage: /look [name/number]
[FFFFFF]Example: /look midnight
[FFFFFF]Example: /look 9"""
                                
                                await safe_send_message(response.Data.chat_type, bundle_list, uid, chat_id, key, iv)

                            else:
                                bundle_input = parts[1].lower()
                                bundle_id = BUNDLE.get(bundle_input)

                                if not bundle_id:
                                    await safe_send_message(response.Data.chat_type, "[FF0000]❌ Invalid bundle!", uid, chat_id, key, iv)
                                    return

                                delay_time = delay_map.get(bundle_input, 3.0)

                                await safe_send_message(
                                    response.Data.chat_type,
                                    f"[00FF00]🎬 Combo Start: {bundle_input}\n[00FF00]⏱ Delay: {delay_time}s",
                                    uid, chat_id, key, iv
                                )

                                try:
                                    # 🔥 Animation
                                    anim_packet = await animation_packet(bundle_id, key, iv)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', anim_packet)

                                    # ⏱ Delay (dynamic)
                                    await asyncio.sleep(delay_time)

                                    # 🎁 Bundle
                                    bundle_packet = await bundle_packet_async(bundle_id, key, iv, region)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', bundle_packet)

                                    await safe_send_message(
                                        response.Data.chat_type,
                                        f"[00FF00]✅ Done Combo: {bundle_input}",
                                        uid, chat_id, key, iv
                                    )

                                except Exception as e:
                                    error_msg = f"[FF0000]❌ Error: {str(e)[:50]}"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

# ==================== /luck COMMAND ====================
                        if inPuTMsG.strip() == "/luck":
                            luck_messages = [
                                "আজ তুমি আজ social গেলেই Mia khalifa কে GF বানাতে  পারবে ....!! ⚡",
                                "আজ তোমার mach এ C2k পড়বে 🔥",
                                "আজ social  যাওয়ার সাথে 4 ফুটা যুক্ত মেয়ে পাবে 100%🏆",
                                "আজ বন্ধুদের সাথে Mai khalifa কে করতে পারবে.....আরে দেখা রে..!! 😎",
                                "আজ কিছু জিনিস ভাগ্যক্রমে ভালো হবে...!! যেমন join sing এ সাথে দেখা হবে তোমার 🍀"
                            ]
                            selected_message = random.choice(luck_messages)
                            admin_message = (
                                f"[C][B][00FFFF]╔════════════════════╗\n"
                                f"║  ╭──────────────╮\n"
                                f"║  │[FF0000] ভাগ্য পরীক্ষা কেন্দ্র         │\n"
                                f"║  ╰──────────────╯\n"
                                f"║\n"
                                f"║ [FFFFFF]✨ {selected_message}\n"
                                f"║ ────────────────\n"
                                f"║ ⚡ [FFFF00] NARUTO-CODEX ⚡\n"
                                f"╚════════════════════╝"
                            )
                            await safe_send_message(response.Data.chat_type, admin_message, uid, chat_id, key, iv)


# ==================== /coin COMMAND ====================
                        if inPuTMsG.strip().startswith('/coin'):
                            result = random.choice(["Heads", "Tails"])
                            coin_result = "[B][C][00FF00]● HEADS ●" if result=="Heads" else "[B][C][FF4500]● TAILS ●"
                            current_time = datetime.now().strftime("%I:%M %p")
                            coin_message = (
                                f"[B][C][00FFFF]╔════════════════════╗\n"
                                f"║ 🎲 Coin Flip Result\n"
                                f"║\n"
                                f"║ {coin_result}\n"
                                f"║ 🕒 Time: [FFB300]{current_time}\n"
                                f"║ 🙋 Flipped by: [FFFF00]@\n"
                                f"║ ▪ Try again: /coin\n"
                                f"╚════════════════════╝"
                            )
                            await safe_send_message(response.Data.chat_type, coin_message, uid, chat_id, key, iv)


# ==================== /dice COMMAND ====================
                        if inPuTMsG.strip().startswith('/dice'):
                            dice_roll = random.randint(1,6)
                            colors = {1:"FFFF00", 2:"FF0000", 3:"00FFFF", 4:"00FF00", 5:"00FFFF", 6:"FFFFFF"}
                            dice_message = (
                                f"[B][C][{colors[dice_roll]}]╔════════════════════╗\n"
                                f"║ 🎲 Dice Roll Result\n"
                                f"║\n"
                                f"║ [FFFFFF]You rolled: [B]{dice_roll}[/B]\n"
                                f"║ ▪ Roll again: /dice\n"
                                f"╚════════════════════╝"
                            )
                            await safe_send_message(response.Data.chat_type, dice_message, uid, chat_id, key, iv)

# ==================== /dhadha COMMAND ====================
                        if inPuTMsG.strip() == "/dhadha":
                            dha_messages = [
                                "গেমে ঢোকার আগে সবাই আমাকে খোঁজে, কিন্তু এনিমি সামনে আসলে সবাই আমাকে গালি দেয়! আমি কে? ",
                                "কখনো আমি লাল, কখনো আমি নীল, আমার ভেতরে গেলেই তোমার শরীর হবে ঢিল! আমি কে? ",
                                "দেখতে আমি ছোট, কিন্তু আমার পেটে অনেক লুট! আমাকে দেখলে সবাই দৌড়ে আসে। আমি কে? ",
                                "সবাই আমাকে মারতে চায়, কিন্তু আমি মরে গেলে সবাই খুশি হয়। আমি কে?', 'a': 'লবির এনিমি বা বট! 🤖",
                                "'আমার চোখ নেই কিন্তু আমি দেখি, আমার পা নেই কিন্তু আমি ঘুরি। আমার কাজ শুধু তোমার ভুল ধরা! আমি কে? "
                                "' তিন জনে ধরে একজনে মারে "
                            ]
                            selected_message = random.choice(dha_messages)
                            dhadha_message = (
                                f"[C][B][00FFFF]╔══════════╗\n"
                                f"║  ╭────────────╮\n"
                                f"║  │[FF69B4] ম জ দি মা গ  ধাঁ ধা 🤔       │\n"
                                f"║  ╰───────────╯\n"
                                f"║\n"
                                f"║ [FFFFFF]✨ {selected_message}\n"
                                f"║ ────────────\n"
                                f"║ ⚡ [FF00FF] NARUTO-CODEX BOT⚡\n"
                                f"╚════════════╝"
                            )
                            await safe_send_message(response.Data.chat_type, dhadha_message, uid, chat_id, key, iv)

#GALI SPAM MESSAGE 
                        # Add at the top with other global variables
                        BLOCKED_NAMES = [
    "jisan", "Jisan", "JISAN", "jisan", "Jisan", "jisan", "jisan", "jisan123x", 
    "jisan123", "JISAN1", "jisan", "jisan@123", "Jisan1", "jisan@1", 
    "jisan#", "#jisan", "@jisan", "@Jisan", "#Jisan", "jisan@FF", "jisan_", 
    "jisan#", "fux", "Fux", "JISAN#", "JISAN@", "@jisan@", "jisan#123", 
    "jisan", "JisanfF", "jisan_FF", "FayEz_jisan", "fAyEz_jisan", 
    "jisan01", "adil", "fHUXfF", "jisan@FF", "jisan_#", "JISAN123", 
    "jisan!", "#jisan", "Jisan_123", "jisan#_1", "JISAN1#", "jisan", 
    "jisan@!", "jisan@_123", "jisan_FF_", "jisan@FayEz", "@JISAN1", 
    "@jisan01", "FAYEZjisan", "jisan", "FayEz_jisan_", "fUyEz_jisan", 
    "jisan!@", "@jisan01", "#FayEz_jisan", "fAyEz_jisan@", "@Jisan123", 
    "fahx", "fuh**", "fayez!jisan", "jisan", "jisan#FayEz", 
    "Jisan@FayEz", "fAyEz#jisan", "jisan", "gop gop fayez", 
    "fHUXfayez", "@jisan", "#fayezjisan", "fHUXfayez", "f@yez", 
    "jisan!!", "jisan_ff", "jisan", "@jisan", "fayez67", 
    "JISAN_FayEz", "@fayez_jisan", "FAYEয", "ফায়ez", 
    "fayezjisan", "JISAN", "@Jisan_FayEz", "ফায়েয", 
    "ফুহক্স", "jisan.", "fayez ullah hawlader", "FUH X", "ফায়েজ" ]
    # Add your actual name

                        # Then in the /gop command handler, add this check:
                        await handle_gop_command(inPuTMsG, uid, chat_id, response.Data.chat_type, key, iv, region)

                                #GALI SPAM MESSAGE 
                        await handle_love_command(inPuTMsG, uid, chat_id, response.Data.chat_type, key, iv, region)
                        # Stop evo_fast spam command
                        if inPuTMsG.strip() == '/stop evo_fast':
                            if evo_fast_spam_task and not evo_fast_spam_task.done():
                                evo_fast_spam_running = False
                                evo_fast_spam_task.cancel()
                                success_msg = f"[B][C][FFFF00]✅ SUCCESS! Evolution fast spam stopped successfully!\n"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            else:
                                error_msg = f"[B][C][FF0000]❌ ERROR! No active evolution fast spam to stop!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # Stop evo_custom spam command
                        if inPuTMsG.strip() == '/stop evo_c':
                            if evo_custom_spam_task and not evo_custom_spam_task.done():
                                evo_custom_spam_running = False
                                evo_custom_spam_task.cancel()
                                success_msg = f"[B][C][FFFF00]✅ SUCCESS! Evolution custom spam stopped successfully!\n"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            else:
                                error_msg = f"[B][C][FF0000]❌ ERROR! No active evolution custom spam to stop!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # In your TcPChaT function, add:
                        if inPuTMsG.strip() == '/ss':
                            print('Processing start match command')
                            await handle_start_match_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)
                            
                            
                        # FIXED HELP MENU SYSTEM - Now detects commands properly
                        # IMPROVED HELP MENU SYSTEM - AUTOMATIC MULTI-PART
                        # IMPROVED HELP MENU SYSTEM - TREE STYLE FORMAT
                        # =================== COMPLETE HELP MENU (ALL COMMANDS) ===================
                        # =================== COMPLETE HELP MENU (SEPARATE PARTS) ===================
                        # =================== COMPLETE HELP MENU (SEPARATE PARTS) ===================
                         # =================== WORKING COMMANDS HELP MENU ===================
                         # =================== WORKING COMMANDS HELP MENU ===================
                        if inPuTMsG.strip().lower() in ("help", "/help", "1", "abhi", "x"):
                            print(f"Help command detected from UID: {uid} in chat type: {XX}")
                            try:
                                p1 = """[c][b][A80000][c]◉━━━━━━━━━◉
[A80000][b][c]◉  [FFFFFF]NARUTO HELP MENU 01: 

[A80000]◎ [b][c][FFD053] Invite Player: [b][c][ffffff]/inv [b][c]

[A80000]◎ [b][c][FFD053] 3 Player Group: [b][c][ffffff]/3 [b][c]

[A80000]◎ [b][c][FFD053] 4 Player Group: [b][c][ffffff]/4 [b][c]

[A80000]◎ [b][c][FFD053] 5 Player Group: [b][c][ffffff]/5 [b][c]

[A80000]◎ [b][c][FFD053] 6 Player Group: [b][c][ffffff]/6 [b][c]

[A80000]◎ [b][c][FFD053] 5 Player Squad: [b][c][ffffff]/snd [uid] [b][c]
 [b][c][A80000][c]◉━━━━━━━━━━◉"""

                                await safe_send_message(response.Data.chat_type, p1, uid, chat_id, key, iv)
                                await asyncio.sleep(0.2)
        

                                p2 = """[c][b][A80000]◉━━━━━━━━━◉
[A80000][b][c]◉  [FFFFFF]NARUTO HELP MENU 02: 

[A80000]◎ [b][c][00FFFF] Spam Invite: [b][c][ffffff]/spam_group [uid] [b][c]

[A80000]◎ [b][c][00FFFF] Join by UID: [b][c][ffffff]/join_req [uid] [b][c]

[A80000]◎ [b][c][00FFFF] Join by Code: [b][c][ffffff]/join [tc] [b][c]

[A80000]◎ [b][c][00FFFF] Exit Squad: [b][c][ffffff]/exit [b][c]

[A80000]◎ [b][c][00FFFF] Fast Emote: [b][c][ffffff]2*200 [b][c]
 [b][c][A80000]◉━━━━━━━━━━◉"""

                                await safe_send_message(response.Data.chat_type, p2, uid, chat_id, key, iv)
                                await asyncio.sleep(0.2)            

                                p3 = """[c][b][A80000]◉━━━━━━━━━◉
[A80000][b][c]◉  [FFFFFF]NARUTO HELP MENU 03:                                                                  

[b][c][A80000]◎ [b][c][DA70D6] Auto Evo Emote: [b][c][ffffff]@evos

[b][c][A80000]◎ [b][c][DA70D6] Off Evo Emote: [b][c][ffffff]@sevos

[b][c][A80000]◎ [b][c][DA70D6] Evo to Player: [b][c][ffffff]/evo [uid] [num]

[b][c][A80000]◎ [b][c][DA70D6] Evo Single: [b][c][ffffff]/Evo [name]

[b][c][A80000]◎ [b][c][DA70D6] Number to Emote: [b][c][ffffff][1-4]10

[b][c][A80000]◎ [b][c][DA70D6] No-Bot Emote: [b][c][ffffff]/em [tc] [num]
 [b][c][A80000]◉━━━━━━━━━━◉"""
                                await safe_send_message(response.Data.chat_type, p3, uid, chat_id, key, iv)
                                await asyncio.sleep(0.2)            
                                                

                                p4 = """[c][b][A80000]◉━━━━━━━━◉
[A80000][b][c]◉  [FFFFFF]NARUTO HELP MENU 04:                                                                 

[b][c][A80000]◎ [b][c][FFD700] Start Match: [ffffff]/start1

[b][c][A80000]◎ [b][c][FFD700] Duo Check by UID: [ffffff]/duo [uid]

[b][c][A80000]◎ [FFD700] Respect by Name: [b][c][ffffff]/praisa [name]

[b][c][A80000]◎ [FFD700] Lonewolf 1v1: [ffffff]/lw [tc]

[b][c][A80000]◎ [b][c][FFD700] Love by Name: [b][c][ffffff]/love [name]

[b][c][A80000]◎ [FFD700] Gender Check: [b][c][ffffff]/gender [name]
 [b][c][A80000]◉━━━━━━━━━━◉"""
                                await safe_send_message(response.Data.chat_type, p4, uid, chat_id, key, iv)
                                await asyncio.sleep(0.2)

                                p5 = """[c][b][A80000]◉━━━━━━━━◉
[A80000][b][c]◉  [FFFFFF]NARUTO HELP MENU 05:                                                                  

[b][c][A80000]◎ [b][c][00FFFF] Magic Colour: [b][c][ffffff]/magic 

[b][c][A80000]◎ [b][c][00FFFF] Call Me Noob: [b][c][ffffff]/noob 

[b][c][A80000]◎ [b][c][00FFFF] Send Title: [b][c][ffffff]/title 

[b][c][A80000]◎ [b][c][00FFFF] Send Sticker: [b][c][ffffff]/sticker 

[b][c][A80000]◎ [b][c][00FFFF] Freeze UID: [b][c][ffffff]/freeze [uid]
 [b][c][A80000]◉━━━━━━━━━━━◉"""

                                await safe_send_message(response.Data.chat_type, p5, uid, chat_id, key, iv)
                                await asyncio.sleep(0.2)

                                p6 = """[c][b][A80000]◉━━━━━━━━━◉
[A80000][b][c]◉  [FFFFFF]NARUTO HELP MENU 06:                                                                  

[b][c][A80000]◎ [b][c][DA70D6] Craftland: [b][c][ffffff]/s1 [uid]

[b][c][A80000]◎ [b][c][DA70D6] New V-Bdg: [b][c][ffffff]/s2 [uid]

[b][c][A80000]◎ [b][c][DA70D6] Moderator: [b][c][ffffff]/s3 [uid]

[b][c][A80000]◎ [b][c][DA70D6] Small V-B: [b][c][ffffff]/s4 [uid]

[b][c][A80000]◎ [b][c][DA70D6] Pro Badge: [b][c][ffffff]/s5 [uid]

[b][c][A80000]◎ [b][c][DA70D6] All Badge: [b][c][ffffff]/xspam [uid]
 [b][c][A80000][c]◉━━━━━━━━━━◉"""

                                await safe_send_message(response.Data.chat_type, p6, uid, chat_id, key, iv)
                                await asyncio.sleep(0.2)


                                p7 = """[c][b][A80000]◉━━━━━━━━━━◉
[A80000][b][c]◉  [FFFFFF]NARUTO HELP MENU 07:                                                                  

[b][c][A80000]◎ [b][c][FFD700] Normal Gali: [b][c][ffffff]/gop [name]

[b][c][A80000]◎ [b][c][FFD700] Danger Gali: [b][c][ffffff]/gopgop [name]

[b][c][A80000]◎ [b][c][FFD700] Respect Cmd: [b][c][ffffff]/praisa [name]

[b][c][A80000]◎ [b][c][FFD700] Style Text: [b][c][ffffff]/mg [text]

[b][c][A80000]◎ [b][c][FFD700] Bundle Auto: [b][c][ffffff]/magicbundle [tc]

[b][c][A80000]◎ [b][c][FFD700] Ghost Join: [b][c][ffffff]/ghost [tc] [name]
 [b][c][A80000]◉━━━━━━━━━━━◉"""

                                await safe_send_message(response.Data.chat_type, p7, uid, chat_id, key, iv)
                                await asyncio.sleep(0.2)
                            




                                p8 = """[c][b][A80000]◉━━━━━━━━━◉
[A80000][b][c]◉  [FFFFFF]NARUTO HELP MENU 08:                                                                  

[b][c][A80000]◎ [b][00FFFF] Offline Team: [b][c][ffffff]/offline [tc]

[b][c][A80000]◎ [b][c][00FFFF] Evo Bundle List: [b][c][ffffff]/b

[b][c][A80000]◎ [b][c][00FFFF] Evo Animation: [b][c][ffffff]/animation

[b][c][A80000]◎ [b][c][00FFFF] Evo Combo Bundle: [b][c][ffffff]/look
 [b][c][A80000][c]◉━━━━━━━━━━━◉"""
                                await safe_send_message(response.Data.chat_type, p8, uid, chat_id, key, iv)
                                await asyncio.sleep(0.2)

                                p9 = """[c][b][A80000]◉━━━━━━━━━◉
[A80000][b][c]◉  [FFFFFF]NARUTO HELP MENU 09:                                                                  

[b][c][A80000]◎ [b][c][DA70D6] Emote Block: [b][c][ffffff]/block_emote [uid]

[b][c][A80000]◎ [b][c][DA70D6] Emote Unblock: [b][c][ffffff]/unblock_emote [uid]

[b][c][A80000]◎ [b][c][DA70D6] Player Team Info: [b][c][ffffff]/status [uid]

[b][c][A80000]◎ [b][c][DA70D6] Invite Lag ID: [b][c][ffffff]/ABHIlag [uid]

[b][c][A80000]◎ [b][c][DA70D6] Join Room: [b][c][ffffff]/xjoin [room_id] [pass]
 [b][c][A80000][c]◉━━━━━━━━━━━◉"""
                                await safe_send_message(response.Data.chat_type, p9, uid, chat_id, key, iv)
                                await asyncio.sleep(0.2)

                                p10 = """[c][b][A80000]◉━━━━━━━━━◉
[A80000][b][c]◉  [FFFFFF]NARUTO HELP MENU 10:                                                                  

[b][c][A80000]◎ [b][c][FFD700] Coin Toss Game: [b][c][ffffff]/coin

[b][c][A80000]◎ [b][c][FFD700] Bangla Dhadha: [b][c][ffffff]/dhadha

[b][c][A80000]◎ [b][c][FFD700] UID Info: [b][c][ffffff]/info [uid]

[b][c][A80000]◎ [b][c][FFD700] Admin Info: [b][c][ffffff]/admin

[b][c][A80000]◎ [b][c][FFD700] Kick Player: [b][c][ffffff]/kick [uid]

[b][c][A80000]◎ [b][c][FFD700] Note: Bot must be leader
 [b][c][A80000][c]◉━━━━━━━━━━━◉"""
                                await safe_send_message(response.Data.chat_type, p10, uid, chat_id, key, iv)
                                await asyncio.sleep(0.2)


                                p11 = """[00FFFF][b][c]◉━━━━━━━━━━━◉
[1E90FF]• [FFD053]Developer: [FFFFFF]ꫝʙʜɪㅤGᴍʀ
[1E90FF]• [FFD053]System: [FFFFFF]AUTOMATION
[1E90FF]• [FFD053]Role: [FFFFFF]DEV & CONTROLLER
[1E90FF]• [FFD053]BOT Owner : [FFFFFF]ꫝʙʜɪㅤGᴍʀ
[1E90FF]• [FFD053]Telegram : [FFFFFF]@narutocodexff
[1E90FF]• [FFD053]TikTok : [FFFFFF]@
[1E90FF]• [FFD053]YouTube : [FFFFFF]@jeet_live
[00FFFF][b][c]◉━━━━━━━━━━━◉"""
                                await safe_send_message(response.Data.chat_type, p11, uid, chat_id, key, iv)
                            except Exception as e:
                                print(f"Error sending help messages: {e}")
                                import traceback
                                traceback.print_exc()                        
                        # =================== NEW COMMANDS ===================
                        # restart command
                        if inPuTMsG.strip() == '.***':
                            print('Processing restart command')
                            await handle_restart_command(uid, chat_id, key, iv, response.Data.chat_type)

                        # +AI command - enable AI mode and call AI API
                        if inPuTMsG.strip() == '+AI':
                            print('Processing +AI command')
                            await handle_ai_on_command(uid, chat_id, key, iv, response.Data.chat_type)

                        # -AI command - disable AI mode globally
                        if inPuTMsG.strip() == '-AI':
                            print('Processing -AI command')
                            await handle_ai_off_command(uid, chat_id, key, iv, response.Data.chat_type)

                        # /private command
                        if inPuTMsG.strip() == '/private':
                            print('Processing private command')
                            await handle_private_command(uid, chat_id, key, iv, response.Data.chat_type)

                        # /_man command - calls rizak function
                        if inPuTMsG.strip() == '/_man':
                            print('Processing ghost_man command')
                            await handle_ghost_man_command(uid, chat_id, key, iv, response.Data.chat_type)

                        # =================== NEW FEATURE COMMANDS ===================
                        # /addfriend command
                        if inPuTMsG.strip().startswith('/addfriend '):
                            print('Processing addfriend command')
                            await handle_addfriend_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        # /visit command
                        if inPuTMsG.strip().startswith('/visit '):
                            print('Processing visit command')
                            await handle_visit_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        # /check command
                        if inPuTMsG.strip().startswith('/check '):
                            print('Processing check command')
                            await handle_check_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        # /spam_group command
                        if inPuTMsG.strip().startswith('/spam_group '):
                            print('Processing spam_group command')
                            await handle_spam_group_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        # /b_power command
                        if inPuTMsG.strip().startswith('/bundle_power'):
                            print('Processing bundle_power command')
                            await handle_bundle_power_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        # /_inv command
                        if inPuTMsG.strip().startswith('/_inv '):
                            print('Processing ghost_inv command')
                            await handle_ghost_inv_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        # /world_fast command
                        if inPuTMsG.strip() == '/world_fast':
                            print('Processing world_fast command')
                            await handle_world_fast_command(uid, chat_id, key, iv, region, response.Data.chat_type)

                        # /world command
                        if inPuTMsG.strip().startswith('/world '):
                            print('Processing world command')
                            await handle_world_command(inPuTMsG, uid, chat_id, key, iv, region, response.Data.chat_type)

                        # /worlds command
                        if inPuTMsG.strip() == '/worlds':
                            print('Processing worlds command')
                            await handle_worlds_command(uid, chat_id, key, iv, region, response.Data.chat_type)

                        # =================== ABHI NAME DETECTION ===================
                        # Detect variations of ABHI in message (case-insensitive)
                        if "/ABHI" in original_msg.lower():
                            print("ABHI name detected! Sending colored ASCII art...")
                            # Send 17 times with different colors
                            colors = ["[FF9000]", "[00FF00]", "[FFC0CB]", "[FF0000]", "[FF0000]", "[FFFF00]", "[FFA500]", "[8B0000]", "[FF7F50]", "[F0F8FF]", "[FF6347]", "[800080]", "[000080]", "[4B0082]", "[00FFFF]", "[000000]", "[F0F8FF]"]
                            ascii_art = """

 ██╗   ██╗   █████╗   ██████╗    ██╗  ██████╗ 
 ██║   ██║  ██╔══██╗ ██╔════╝  ██║  ██╔══██╗
 ███████║  ███████║ ╚█████╗   ██║   ██████╔╝
 ██╔══██║  ██╔══██║ ╚═══██╗   ██║   ██╔══██╗
 ██║   ██║  ██║   ██║ ██████╔╝  ██║   ██████╔╝
 ╚═╝  ╚═╝   ╚═╝  ╚═╝  ╚═════╝   ╚═╝    ╚═════╝
                              
"""
                            for i in range(17):
                                color = colors[i % len(colors)]
                                colored_msg = f"[B][C][{color}]{ascii_art}"
                                await safe_send_message(response.Data.chat_type, colored_msg, uid, chat_id, key, iv)
                                await asyncio.sleep(0.1)  # Small delay between messages

                        # =================== NUMBER COMMAND HANDLER ===================
                        # Check if the message is a number or number*count pattern
                        if inPuTMsG.strip().isdigit() or (inPuTMsG.strip().count('*') == 1 and inPuTMsG.strip().split('*')[0].isdigit() and inPuTMsG.strip().split('*')[1].isdigit()):
                            print("Number command detected")
                            number_part = inPuTMsG.strip()
                            emote_id = None
                            times = 1
                            
                            if '*' in number_part:
                                parts = number_part.split('*')
                                number = parts[0]
                                times = int(parts[1])
                                if times > 100:
                                    times = 100  # Limit to 100
                            else:
                                number = number_part
                            
                            # Check if number is in NUMBER_EMOTES (1-based)
                            if number in NUMBER_EMOTES:
                                emote_id = NUMBER_EMOTES[number]
                                emote_name = f"#{number}"
                            else:
                                # Check if number is an evo emote number (1-21)
                                try:
                                    num = int(number)
                                    if 1 <= num <= 21:
                                        emote_id = EMOTE_MAP[num]
                                        emote_name = f"evo{num}"
                                except:
                                    pass
                            
                            if emote_id:
                                # Send initial message
                                if times == 1:
                                    msg = f"[B][C][FFFFFF] ওই কি👽রে.. ওই কিরে... ম👽ধু ম👽ধু রস👽মালাই"
                                else:
                                    msg = f"[B][C][FFFFFF] ওই কি👽রে.. ওই কিরে... ম👽ধু ম👽ধু রস👽মালাই"
                                await safe_send_message(response.Data.chat_type, msg, uid, chat_id, key, iv)
                                
                                # Send emote(s)
                                for _ in range(times):
                                    try:
                                        H = await Emote_k(int(uid), int(emote_id), key, iv, region)
                                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                        await asyncio.sleep(0.05)  # Very fast
                                    except Exception as e:
                                        print(f"Error sending number emote: {e}")
                                        break
                                
                                success_msg = f"[B][C][FFFFFF] ওই কি👽রে.. ওই কিরে... ম👽ধু ম👽ধু রস👽মালাই"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            else:
                                # Not a valid emote number
                                pass  # Ignore, not a valid number command

                        # =================== STICKER DETECTION ===================
                        # Check if the message is a sticker (contains "StickerStr")
                        if original_msg and "StickerStr" in original_msg:
                            print("Sticker detected! Sending random emote...")
                            # Get a random emote from NUMBER_EMOTES
                            if NUMBER_EMOTES:
                                random_number = random.choice(list(NUMBER_EMOTES.keys()))
                                emote_id = NUMBER_EMOTES[random_number]
                                # Send the emote to the sender
                                try:
                                    H = await Emote_k(int(uid), int(emote_id), key, iv, region)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                    # Also send a message
                                    sticker_reply = "[B][C][FFFF00] NARUTO-CODEX STYLE TCP"
                                    await safe_send_message(response.Data.chat_type, sticker_reply, uid, chat_id, key, iv)
                                    print(f"✅ Sent emote #{random_number} in response to sticker")
                                except Exception as e:
                                    print(f"Error sending emote for sticker: {e}")

                        # =================== AI AUTO-REPLY ===================
                        # Auto-reply to non-command messages if AI is enabled
                        if response and ai_auto_reply_enabled and inPuTMsG and not inPuTMsG.strip().startswith('/') and not inPuTMsG.strip().startswith('+') and not inPuTMsG.strip().startswith('-') and not inPuTMsG.strip().startswith('@'):
                            # Only reply if message is not a command
                            await ai_auto_reply(inPuTMsG, uid, chat_id, key, iv, response.Data.chat_type)

                        # =================== NEW FEATURE: /ABHIlag COMMAND ===================
                        # Ultra-fast squad size switching between 5 and 6 for 65 seconds
                        if inPuTMsG.strip().startswith('/ABHIag '):
                            print('Processing /ABHIlag command')
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ Usage: /ABHIlag (target_uid)\nExample: /ABHIlag 123456789\n\n🎯 This command will:\n• Invite the target UID\n• Rapidly switch squad size between 5 and 6 players\n• Continue for 65 seconds without leaving the squad\n• Ultra-fast (millisecond intervals)\n• Use /stop chatspam to stop early"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
                                if not target_uid.isdigit():
                                    error_msg = f"[B][C][FF0000]❌ Invalid UID! Must be numbers only."
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    # Stop any existing chatspam
                                    global chatspam_running, chatspam_task
                                    if 'chatspam_task' in globals() and chatspam_task and not chatspam_task.done():
                                        chatspam_running = False
                                        chatspam_task.cancel()
                                        await asyncio.sleep(0.1)
                                    # Start new chatspam
                                    chatspam_running = True
                                    chatspam_task = asyncio.create_task(chatspam_loop(target_uid, key, iv, region))
                                    success_msg = f"[B][C][FFFF00]✅ CHATSPAM STARTED!\n🎯 Target: {target_uid}\n🔄 Switching between 5 and 6 players\n⏱️ Duration: 65 seconds\n⚡ Speed: Millisecond intervals\n💡 Use /stop chatspam to stop"
                                    await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)

                        # Stop chatspam command
                        if inPuTMsG.strip() == '/stop chatspam':
                            if 'chatspam_task' in globals() and chatspam_task and not chatspam_task.done():
                                chatspam_running = False
                                chatspam_task.cancel()
                                stop_msg = f"[B][C][FFFF00]✅ CHATSPAM STOPPED!\n"
                                await safe_send_message(response.Data.chat_type, stop_msg, uid, chat_id, key, iv)
                            else:
                                error_msg = f"[B][C][FF0000]❌ No active chatspam to stop!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # =================== NEW FEATURE: /info COMMAND (Player Information) ===================
                        if inPuTMsG.strip().startswith('/info '):
                            print('Processing /info command')
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ Usage: /info (player_uid)\nExample: /info 123456789\n\nShows detailed player information (name, level, rank, etc.)"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
                                if not target_uid.isdigit():
                                    error_msg = f"[B][C][FF0000]❌ Invalid UID! Must be numbers only."
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    initial_msg = f"[B][C][FFFF00]🔍 Fetching player information for UID {target_uid}...\n⏳ Please wait..."
                                    await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
                                    # Get token from token.json
                                    token = load_jwt_token()
                                    if not token:
                                        error_msg = f"[B][C][FF0000]❌ No valid token found. Please ensure token.json exists."
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    else:
                                        # Use detailed player info function
                                        info_text = get_detailed_player_info(target_uid, token)
                                        await safe_send_message(response.Data.chat_type, info_text, uid, chat_id, key, iv)

                        response = None
                            
            whisper_writer.close() ; await whisper_writer.wait_closed() ; whisper_writer = None
                    
                    	
                    	
        except Exception as e: print(f"ErroR {ip}:{port} - {e}") ; whisper_writer = None
        await asyncio.sleep(reconnect_delay)

# =================== NEW API CALL FUNCTIONS ===================
async def call_api(url, timeout=20):
    """Generic async API caller with timeout"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    # Remove JSON brackets and formatting
                    # Remove any JSON-like brackets, quotes, etc.
                    import re
                    text = re.sub(r'[{}"\[\]\\]', '', text)
                    text = re.sub(r'[,:]', ' ', text)
                    text = ' '.join(text.split())  # Normalize whitespace
                    return text
                else:
                    return f"Error: HTTP {response.status}"
    except asyncio.TimeoutError:
        return f"Error: Request timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {str(e)}"

async def handle_addfriend_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /addfriend command"""
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        error_msg = f"[B][C][FF0000]❌ Usage: /addfriend (target_uid)\nExample: /addfriend 123456789\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    target_uid = parts[1]
    # Load credentials from bot.txt
    credentials = load_credentials_from_file("bot.txt")
    if not credentials or len(credentials) < 2:
        error_msg = f"[B][C][FF0000]❌ Failed to load credentials from bot.txt\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    bot_uid, bot_pass = credentials[0], credentials[1]
    # Build API URL
    api_url = f"https://rizerxaddfriend.vercel.app/adding_friend?uid={bot_uid}&password={bot_pass}&friend_uid={target_uid}"
    await safe_send_message(chat_type, f"[B][C][FFFF00]📤 Sending friend request...\n🎯 Target: {target_uid}\n⏳ Please wait (timeout 80s)...", uid, chat_id, key, iv)
    response_text = await call_api(api_url, timeout=80)
    await safe_send_message(chat_type, f"[B][C][FFFF00]✅ Friend Request Result:\n\n{response_text}", uid, chat_id, key, iv)

async def handle_visit_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /visit command"""
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        error_msg = f"[B][C][FF0000]❌ Usage: /visit (uid)\nExample: /visit 123456789\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    target_uid = parts[1]
    api_url = f""
    await safe_send_message(chat_type, f"[B][C][FFFF00]👀 Visiting player {target_uid}...", uid, chat_id, key, iv)
    response_text = await call_api(api_url, timeout=20)
    await safe_send_message(chat_type, f"[B][C][FFFF00]Visit Result:\n\n{response_text}", uid, chat_id, key, iv)

async def handle_check_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /check command (ban check) - returns pretty printed text"""
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        error_msg = f"[B][C][FF0000]❌ Usage: /check (uid)\nExample: /check 123456789\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    target_uid = parts[1]
    api_url = f""
    await safe_send_message(chat_type, f"[B][C][FFFF00]🔍 Checking ban status for UID {target_uid}...", uid, chat_id, key, iv)
    response_text = await call_api(api_url, timeout=20)
    # Clean the response text (remove JSON artifacts and escape sequences)
    import re
    # Remove Unicode escape sequences like u0280
    cleaned = re.sub(r'u[0-9a-fA-F]{4}', '', response_text)
    # Remove any leftover backslashes and quotes
    cleaned = re.sub(r'[\\"\']', '', cleaned)
    # Collapse multiple spaces
    cleaned = ' '.join(cleaned.split())
    # Format nicely
    result_msg = f"[B][C][FFFF00]📋 BAN CHECK RESULT\n━━━━━━━━━━━━━━━━━━\n[D3D3D3]{cleaned}\n━━━━━━━━━━━━━━━━━━"
    await safe_send_message(chat_type, result_msg, uid, chat_id, key, iv)

async def handle_spam_group_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /spam_group command - send rapid invites for 1 minute"""
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        error_msg = f"[B][C][FF0000]❌ Usage: /spam_group (target_uid)\nExample: /spam_group 123456789\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    target_uid = parts[1]
    await safe_send_message(chat_type, f"[B][C][FFFF00]🚀 Starting spam_group on {target_uid} for 60 seconds...\n⏱️ This will send ~7-8 invites per second.", uid, chat_id, key, iv)
    # Run for 60 seconds
    start_time = time.time()
    count = 0
    while time.time() - start_time < 60:
        try:
            # Open squad
            PAc = await OpEnSq(key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
            # Invite
            V = await SEnd_InV(5, int(target_uid), key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
            # Leave squad quickly
            await asyncio.sleep(0.05)
            E = await ExiT(None, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', E)
            count += 1
            # Very short delay to achieve high speed
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Spam group error: {e}")
    await safe_send_message(chat_type, f"[B][C][FFFF00]✅ Spam_group completed!\n📊 Sent approximately {count} invites to {target_uid} in 60 seconds.", uid, chat_id, key, iv)

async def handle_bundle_power_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /bundle_power command - send animation packet then bundle packet after 3 seconds"""
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        # Show available bundles
        bundle_list = """[B][C][00FF00]🎁 AVAILABLE BUNDLES 🎁
[FF6347]━[32CD32]━[7B68EE]━[FF4500]━[1E90FF]━[ADFF2F]━[FF69B4]━[8A2BE2]━[DC143C]━[FF8C00]━[BA55D3]━[7CFC00]━[FFC0CB]
[D3D3D3]• midnight-ace
[D3D3D3]• aurora
[D3D3D3]• naruto  
[D3D3D3]• paradox
[D3D3D3]• frostfire
[D3D3D3]• rampage
[D3D3D3]• wolf
[D3D3D3]• devil
[D3D3D3]• scorpio
[D3D3D3]• dreamspace
[D3D3D3]• itachi
[D3D3D3]• OB54ABHI
[FF6347]━[32CD32]━[7B68EE]━[FF4500]━[1E90FF]━[ADFF2F]━[FF69B4]━[8A2BE2]━[DC143C]━[FF8C00]━[BA55D3]━[7CFC00]━[FFC0CB]
[00FF00]Usage: /bundle_power [bundle_name]
[D3D3D3]Example: /bundle_power midnight-ace"""
        await safe_send_message(chat_type, bundle_list, uid, chat_id, key, iv)
        return
    bundle_name = parts[1].lower()
    bundles = {
        "midnight-ace": 914048001,
        "aurora": 914047002,
        "naruto": 914047001,
        "paradox": 914044001,
        "frostfire": 914042001,
        "rampage": 914000002,
        "wolf": 914000003,
        "devil": 914038001,
        "scorpio": 914039001,
        "dreamspace": 914051001,
        "itachi": 914050001,
        "OB54ABHI": 914053001
    }
    if bundle_name not in bundles:
        error_msg = f"[B][C][FF0000]❌ Invalid bundle name! Use /bundle_power to see list."
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    bundle_id = bundles[bundle_name]
    await safe_send_message(chat_type, f"[B][C][FFFF00]🎁 Wearing bundle {bundle_name.upper()}...\n⏳ Sending animation packet...", uid, chat_id, key, iv)
    # Send animation packet (using bundle_packet_async? We'll use a simple packet with field 88)
    # For animation, we'll use the same packet as bundle but with different structure? Actually original /b just sends one packet.
    # We'll replicate the animation packet from the provided code: it uses field 1: 88, 2: {1: {1: bundle_id, 2: 1}, 2: 2}
    anim_packet = await bundle_packet_async(bundle_id, key, iv, region)
    if online_writer:
        online_writer.write(anim_packet)
        await online_writer.drain()
    # Wait 3 seconds
    await asyncio.sleep(3)
    # Send bundle packet again (same as animation? But original /b just sends once. We'll send again to be safe)
    bundle_packet_data = await bundle_packet_async(bundle_id, key, iv, region)
    if online_writer:
        online_writer.write(bundle_packet_data)
        await online_writer.drain()
    await safe_send_message(chat_type, f"[B][C][00FF00]✅ WEARED BUNDLE ✔️ {bundle_name.upper()}", uid, chat_id, key, iv)

async def handle_ghost_inv_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /_inv command - call ghost invite API"""
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        error_msg = f"[B][C][FF0000]❌ Usage: /_inv (teamcode)\nExample: /_inv 88888\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    teamcode = parts[1]
    api_url = f""
    await safe_send_message(chat_type, f"[B][C][FFFF00]👻 Sending ghost invite for team {teamcode}...", uid, chat_id, key, iv)
    response_text = await call_api(api_url, timeout=20)
    await safe_send_message(chat_type, f"[B][C][FFFF00]Ghost Invite Result:\n\n{response_text}", uid, chat_id, key, iv)

async def handle_world_fast_command(uid, chat_id, key, iv, region, chat_type):
    """Handle /world_fast command - send GLobaL packet"""
    try:
        # GLobaL function as defined
        async def GLobaL(T="RizerisGay", K=key, V=iv):
            fields = {1: 3, 2: {2: 5, 3: f"{T}"}}
            return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '1215', K, V)
        packet = await GLobaL("RizerisGay", key, iv)
        if packet and online_writer:
            online_writer.write(packet)
            await online_writer.drain()
            await safe_send_message(chat_type, "[B][C][FFFF00]✅ World Fast packet sent!", uid, chat_id, key, iv)
        else:
            await safe_send_message(chat_type, "[B][C][FF0000]❌ Failed to send World Fast packet.", uid, chat_id, key, iv)
    except Exception as e:
        await safe_send_message(chat_type, f"[B][C][FF0000]❌ Error: {str(e)}", uid, chat_id, key, iv)

async def handle_world_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    """Handle /world command - send GenJoinGlobaL packet"""
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        error_msg = f"[B][C][FF0000]❌ Usage: /world (owner_uid) (code)\nExample: /world 123456789 ABC123\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    owner = parts[1]
    code = parts[2] if len(parts) > 2 else "0"
    try:
        async def GenJoinGlobaL(owner, code, is_rizer_gay=True, K=key, V=iv):
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
            return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', K, V)
        packet = await GenJoinGlobaL(int(owner), code, True, key, iv)
        if packet and online_writer:
            online_writer.write(packet)
            await online_writer.drain()
            await safe_send_message(chat_type, "[B][C][FFFF00]✅ World packet sent!", uid, chat_id, key, iv)
        else:
            await safe_send_message(chat_type, "[B][C][FF0000]❌ Failed to send World packet.", uid, chat_id, key, iv)
    except Exception as e:
        await safe_send_message(chat_type, f"[B][C][FF0000]❌ Error: {str(e)}", uid, chat_id, key, iv)

async def handle_worlds_command(uid, chat_id, key, iv, region, chat_type):
    """Handle /worlds command - send both GLobaL and GenJoinGlobaL packets simultaneously"""
    try:
        async def GLobaL(T="RizerisGay", K=key, V=iv):
            fields = {1: 3, 2: {2: 5, 3: f"{T}"}}
            return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '1215', K, V)
        async def GenJoinGlobaL(owner, code, is_rizer_gay=True, K=key, V=iv):
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
            return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', K, V)
        packet1 = await GLobaL("RizerisGay", key, iv)
        packet2 = await GenJoinGlobaL(uid, "0", True, key, iv)  # Use sender's uid as owner? Could be any
        if packet1 and online_writer:
            online_writer.write(packet1)
            await online_writer.drain()
        if packet2 and online_writer:
            online_writer.write(packet2)
            await online_writer.drain()
        await safe_send_message(chat_type, "[B][C][FFFF00]✅ Both World packets sent!", uid, chat_id, key, iv)
    except Exception as e:
        await safe_send_message(chat_type, f"[B][C][FF0000]❌ Error: {str(e)}", uid, chat_id, key, iv)

# =================== AI AUTO-REPLY FUNCTION ===================
async def ai_auto_reply(message, sender_uid, chat_id, key, iv, chat_type):
    """Auto-reply using AI API"""
    global ai_last_reply_time
    current_time = time.time()
    if current_time - ai_last_reply_time < ai_reply_cooldown:
        return
    ai_last_reply_time = current_time
    # Get AI response
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        ai_response = await loop.run_in_executor(executor, talk_with_ai, message)
    # Send response
    ai_message = f"[B][C][FFFF00]🤖 AI: {ai_response}"
    await safe_send_message(chat_type, ai_message, sender_uid, chat_id, key, iv)

async def handle_ai_on_command(uid, chat_id, key, iv, chat_type):
    """Handle +AI command to enable AI auto-reply"""
    global ai_auto_reply_enabled
    ai_auto_reply_enabled = False
    await safe_send_message(chat_type, "[B][C][FFFF00]✅ AI Auto-Reply ENABLED! Bot will respond to messages using AI.", uid, chat_id, key, iv)

async def handle_ai_off_command(uid, chat_id, key, iv, chat_type):
    """Handle -AI command to disable AI auto-reply"""
    global ai_auto_reply_enabled
    ai_auto_reply_enabled = False
    await safe_send_message(chat_type, "[B][C][FFFF00]❌ AI Auto-Reply DISABLED.", uid, chat_id, key, iv)

# =================== NEW FUNCTION: /ABHIlag LOOP (fixed: no leave at end, added small delays) ===================
chatspam_running = False
chatspam_task = None

async def chatspam_loop(target_uid, key, iv, region):
    """Ultra-fast squad size switching between 5 and 6 players for 65 seconds without leaving"""
    global chatspam_running
    # Ensure bot is not in a squad; create a new squad first
    try:
        # Open squad
        open_packet = await OpEnSq(key, iv, region)
        if open_packet and online_writer:
            online_writer.write(open_packet)
            await online_writer.drain()
            await asyncio.sleep(0.2)
        else:
            print("Failed to open squad for chatspam")
            return
        # Set squad size to 5 and send invite
        c5 = await cHSq(5, int(target_uid), key, iv, region)
        if c5 and online_writer:
            online_writer.write(c5)
            await online_writer.drain()
        invite5 = await SEnd_InV(5, int(target_uid), key, iv, region)
        if invite5 and online_writer:
            online_writer.write(invite5)
            await online_writer.drain()
        await asyncio.sleep(0.05)
    except Exception as e:
        print(f"Error initializing chatspam: {e}")
        return
    # Start rapid switching between 5 and 6 for 65 seconds
    start_time = time.time()
    duration = 65
    count = 0
    while chatspam_running and (time.time() - start_time) < duration:
        try:
            # Switch to size 6
            c6 = await cHSq(6, int(target_uid), key, iv, region)
            if c6 and online_writer:
                online_writer.write(c6)
                await online_writer.drain()
            invite6 = await SEnd_InV(6, int(target_uid), key, iv, region)
            if invite6 and online_writer:
                online_writer.write(invite6)
                await online_writer.drain()
            # Small delay to avoid connection reset
            await asyncio.sleep(0.05)
            # Switch back to size 5
            c5 = await cHSq(5, int(target_uid), key, iv, region)
            if c5 and online_writer:
                online_writer.write(c5)
                await online_writer.drain()
            invite5 = await SEnd_InV(5, int(target_uid), key, iv, region)
            if invite5 and online_writer:
                online_writer.write(invite5)
                await online_writer.drain()
            await asyncio.sleep(0.05)
            count += 1
            # Optional: print progress every 10 cycles
            if count % 10 == 0:
                print(f"Chatspam cycle {count} completed")
        except Exception as e:
            print(f"Chatspam error: {e}")
            await asyncio.sleep(0.1)
    # DO NOT LEAVE THE SQUAD - stay in squad
    chatspam_running = False
    print(f"Chatspam finished after {count} cycles (squad remains)")

# =================== DETAILED PLAYER INFO FUNCTION ===================
def get_detailed_player_info(uid, token):
    """Get detailed player info as formatted string using existing get_player_info but extended"""
    try:
        url = "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"
        encrypted_uid = enc(uid)
        edata = bytes.fromhex(encrypted_uid)
        headers = {
            'User-Agent': "Dalvik/2.1.0",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Authorization': f"Bearer {token}",
            'Content-Type': "application/x-www-form-urlencoded",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': "OB54"
        }
        response = requests.post(url, data=edata, headers=headers, verify=False, timeout=10)
        if response.status_code != 200:
            return f"❌ Failed to get info for UID {uid} (HTTP {response.status_code})"
        info = decode_player_info(response.content)
        data = json.loads(json_format.MessageToJson(info))
        account = data.get("AccountInfo", {})
        # Extract fields
        name = account.get("PlayerNickname", "Unknown")
        level = account.get("Level", "N/A")
        exp = account.get("Exp", "N/A")
        rank = account.get("Rank", "N/A")
        avatar = account.get("Avatar", "N/A")
        title = account.get("Title", "N/A")
        clan = account.get("ClanName", "None")
        # Format nicely
        result = f"""
[B][C][FFFF00]📊 PLAYER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[D3D3D3]👤 Name     : [FFFF00]{name}
[D3D3D3]🆔 UID      : [FFFF00]{uid}
[D3D3D3]📈 Level    : [FFFF00]{level}
[D3D3D3]⭐ Rank     : [FFFF00]{rank}
[D3D3D3]🎭 Avatar   : [FFFF00]{avatar}
[D3D3D3]🏷️ Title    : [FFFF00]{title}
[D3D3D3]🏰 Clan     : [FFFF00]{clan}
[D3D3D3]✨ Exp      : [FFFF00]{exp}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return result
    except Exception as e:
        return f"❌ Error getting player info: {str(e)}"

async def MaiiiinE():
    # Load credentials from file
    print("📁 Loading credentials from bot.txt...")
    credentials = load_credentials_from_file("bot.txt")
    
    if not credentials:
        print("❌ Failed to load credentials!")
        print("💡 Please create bot.txt with your UID and password")
        print("📝 Format: uid=YOUR_UID,password=YOUR_PASSWORD")
        return None
    
    try:
        Uid, Pw = credentials
    except:
        # Handle case where credentials returns more than 2 values
        if isinstance(credentials, (list, tuple)) and len(credentials) >= 2:
            Uid = credentials[0]
            Pw = credentials[1]
        else:
            print("❌ Invalid credentials format!")
            return None
    
    print("✅ Credentials loaded successfully")
    
    # Get access token from Free Fire
    open_id, access_token = await GeNeRaTeAccEss(Uid, Pw)
    if not open_id or not access_token: 
        print("❌ Error - Invalid Account (Check UID/Password)") 
        return None
    
    # Encrypt and send login request
    PyL = await EncRypTMajoRLoGin(open_id, access_token)
    MajoRLoGinResPonsE = await MajorLogin(PyL)
    if not MajoRLoGinResPonsE: 
        print("❌ Target Account => Banned / Not Registered!") 
        return None
    
    # Decrypt login response
    MajoRLoGinauTh = await DecRypTMajoRLoGin(MajoRLoGinResPonsE)
    global TarGeT
    TarGeT = MajoRLoGinauTh.account_uid
    # Get JWT token from response
    token = MajoRLoGinauTh.token
    if not token:
        print("❌ No authentication token received!")
        return None
    
    # ✅ CRITICAL: SAVE TOKEN TO token.json FILE
    try:
        import json
        import time
        from datetime import datetime
        
        # Get region from login response
        region = getattr(MajoRLoGinauTh, 'region', 'IND')
        
        token_data = {
            "token": token,
            "saved_at": time.time(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bot_uid": str(Uid),
            "region": region,
            "source": "main.py_bot_login"
        }
        
        with open("token.json", "w") as f:
            json.dump(token_data, f, indent=2)
        
        print("✅ Token saved to token.json")
        print(f"📝 Token info: Region={region}, UID={Uid}")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not save token to file: {e}")
        import traceback
        traceback.print_exc()
    
    # Continue with normal bot setup
    UrL = MajoRLoGinauTh.url
    
    # Clear screen and show status
    os.system('clear')
    print(r"""
 ██╗   ██╗   █████╗   ██████╗    ██╗ ██████╗ 
 ██║   ██║  ██╔══██╗ ██╔════╝  ██║ ██╔══██╗
 ███████║  ███████║ ╚█████╗   ██║ ██████╔╝
 ██╔══██║  ██╔══██║ ╚═══██╗   ██║ ██╔══██╗
 ██║   ██║  ██║   ██║ ██████╔╝  ██║ ██████╔╝
 ╚═╝  ╚═╝   ╚═╝  ╚═╝  ╚═════╝   ╚═   ╚═════╝
""")
    print("=" * 50)
    print("🤖 NARUTO-CODEX - INITIALIZING")
    print("=" * 50)
    print("🔄 Starting TCP Connections...")
    print("📡 Connecting to Free Fire servers...")
    print("🌐 Server connection established")
    
    region = getattr(MajoRLoGinauTh, 'region', 'IND')
    ToKen = token  # Use the saved token
    TarGeT = MajoRLoGinauTh.account_uid
    key = MajoRLoGinauTh.key
    iv = MajoRLoGinauTh.iv
    timestamp = MajoRLoGinauTh.timestamp
    
    print(f"🔐 Authentication successful")
    print(f"👤 Account UID: {TarGeT}")
    print(f"🌍 Region: {region}")
    print(f"🔑 Token: {ToKen[:30]}...")
    
    # Get login data for server IPs
    LoGinDaTa = await GetLoginData(UrL, PyL, ToKen)
    if not LoGinDaTa: 
        print("❌ Error - Getting Ports From Login Data!") 
        return None
    
    LoGinDaTaUncRypTinG = await DecRypTLoGinDaTa(LoGinDaTa)
    
    # Get server IPs and ports
    OnLinePorTs = LoGinDaTaUncRypTinG.Online_IP_Port
    ChaTPorTs = LoGinDaTaUncRypTinG.AccountIP_Port
    
    print(f"📡 Online Server: {OnLinePorTs}")
    print(f"💬 Chat Server: {ChaTPorTs}")
    
    # Split IPs and ports
    OnLineiP, OnLineporT = OnLinePorTs.split(":")
    ChaTiP, ChaTporT = ChaTPorTs.split(":")
    
    # Get account name
    acc_name = LoGinDaTaUncRypTinG.AccountName
    print(f"👋 Welcome, {acc_name}!")
    
    # Create authentication token for TCP connections
    AutHToKen = await xAuThSTarTuP(int(TarGeT), ToKen, int(timestamp), key, iv)
    
    # Create event for chat ready
    ready_event = asyncio.Event()
    
    # Start bot tasks
    print("\n🚀 Starting bot services...")
    
    task1 = asyncio.create_task(TcPChaT(ChaTiP, ChaTporT, AutHToKen, key, iv, LoGinDaTaUncRypTinG, ready_event, region))
    task2 = asyncio.create_task(TcPOnLine(OnLineiP, OnLineporT, key, iv, AutHToKen))  
 
    
    # Show loading animation
    os.system('clear')
    print("🤖 ꫝʙʜɪㅤ BOT - STARTING")
    print("=" * 50)
    
    for i in range(1, 4):
        dots = "." * i
        print(f"🔄 Loading{dots}")
        time.sleep(0.3)
    
    os.system('clear')
    print("🤖 NARUTO BOT - CONNECTING")
    print("=" * 50)
    print("┌────────────────────────────────────┐")
    print("│ ██████████████████████████████████ │")
    print("└────────────────────────────────────┘")
    
    # Wait for chat connection to be ready
    print("\n⏳ Waiting for chat connection...")
    try:
        await asyncio.wait_for(ready_event.wait(), timeout=10)
        print("✅ Chat connection established!")
    except asyncio.TimeoutError:
        print("⚠️ Chat connection timeout, continuing...")
    
    # Final status display
    os.system('clear')
    print(r"""
 ██╗   ██╗   █████╗   ██████╗    ██╗  ██████╗ 
 ██║   ██║  ██╔══██╗ ██╔════╝  ██║  ██╔══██╗
 ███████║  ███████║ ╚█████╗   ██║   ██████╔╝
 ██╔══██║  ██╔══██║ ╚═══██╗   ██║   ██╔══██╗
 ██║   ██║  ██║   ██║ ██████╔╝  ██║   ██████╔╝
 ╚═╝  ╚═╝   ╚═╝  ╚═╝  ╚═════╝   ╚═╝    ╚═════╝
""")
    print("=" * 50)
    print("🤖 ꫝʙʜɪㅤGᴍʀ BOT - ONLINE")
    print("=" * 50)
    print(f"🔹 UID: {TarGeT}")
    print(f"🔹 Name: {acc_name}")
    print(f"🔹 Region: {region}")
    print(f"🔹 Status: 🟢 READY")
    print(f"🔹 Chat Server: {ChaTiP}:{ChaTporT}")
    print(f"🔹 Online Server: {OnLineiP}:{OnLineporT}")
    print("=" * 50)
    print("💡 Commands available in squad/guild chat")
    print("💡 Type /help for command list")
    print("=" * 50)
    
    # Test cache file write
    print("\n📊 System Check:")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📁 Cache file: {CACHE_FILE}")
    
    try:
        test_data = {'test': 'ok', 'timestamp': time.time()}
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(test_data, f)
        print("✅ Cache file write test: PASSED")
    except Exception as e:
        print(f"⚠️ Cache file write test: {e}")
    
    # Check token.json exists
    if os.path.exists("token.json"):
        print("✅ token.json file exists")
        try:
            with open("token.json", "r") as f:
                token_info = json.load(f)
            age = time.time() - token_info.get('saved_at', 0)
            print(f"✅ Token age: {age:.1f} seconds")
        except:
            print("⚠️ Could not read token.json")
    else:
        print("❌ token.json not found!")
    
    print("\n🎯 Bot is now running...")
    print("📡 Listening for commands and invitations")
    
    # Keep all tasks running
    try:
        await asyncio.gather(task1, task2)
    except asyncio.CancelledError:
        print("\n🛑 Bot tasks cancelled")
    except Exception as e:
        print(f"\n❌ Error in bot tasks: {e}")
        import traceback
        traceback.print_exc()
    
    return None


if __name__ == '__main__':
    manager = multiprocessing.Manager()
    status_response_cache = manager.dict()
    asyncio.run(StarTinG())