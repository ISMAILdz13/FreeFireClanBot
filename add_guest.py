#!/usr/bin/env python3
"""
Add Guest Accounts — Termux Edition
====================================
Generates fresh Free Fire guest accounts from your phone (works where
server/cloud IPs are blocked by Garena).

Usage on Termux:
  python3 add_guest.py              # Generate 5 accounts
  python3 add_guest.py --count 10   # Generate 10 accounts
  python3 add_guest.py --manual     # Manually add existing UID+password

Requirements:
  pip install pycryptodome requests
"""

import argparse
import json
import os
import random
import hashlib
import hmac
import time
import requests
import urllib3
urllib3.disable_warnings()

GUESTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "guests.json")

# Garena OAuth constants
HEX_KEY = "32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533"
HMAC_KEY = bytes.fromhex(HEX_KEY)
CLIENT_SECRET = HMAC_KEY.decode("ascii")
CLIENT_ID = "100067"

OAUTH_V2_URL = "https://ffmconnect.live.gop.garenanow.com/api/v2/oauth/guest/token:grant"
OAUTH_V1_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
REGISTER_URL = "https://connect.garena.com/oauth/guest/register"

UA_REGISTER = "GarenaMSDK/4.0.19P10(I2404 ;Android 15;en;US;)"
UA_OAUTH_V2 = "GarenaMSDK/4.0.19P10(I2404 ;Android 15;en;US;)"
UA_OAUTH_V1 = "GarenaMSDK/4.0.19P8(ASUS_Z01QD ;Android 12;en;US;)"


def rand_password():
    return ''.join(random.choices('0123456789abcdef', k=32))


def register_guest():
    """Register a new guest account. Works from mobile/Termux IPs."""
    password = rand_password()
    sig = hmac.new(HMAC_KEY, password.encode(), hashlib.sha1).hexdigest()

    # Step 1: Register
    r = requests.post(REGISTER_URL,
        headers={
            "Authorization": f"Signature {sig}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": UA_REGISTER,
            "Accept-Encoding": "gzip",
            "Connection": "Keep-Alive",
        },
        data={
            "password": password,
            "client_id": CLIENT_ID,
            "client_type": "2",
            "response_type": "token",
            "signature": sig,
        },
        timeout=30, verify=False)

    if r.status_code != 200:
        return None

    data = r.json()
    uid = data.get("uid")
    if not uid:
        return None

    # Step 2: Token grant (v2 first, v1 fallback)
    for url, headers, payload in [
        (OAUTH_V2_URL, {"Content-Type": "application/json; charset=utf-8", "User-Agent": UA_OAUTH_V2},
         {"client_id": int(CLIENT_ID), "client_secret": CLIENT_SECRET,
          "password": password, "client_type": 2, "response_type": "token", "uid": int(uid)}),
        (OAUTH_V1_URL, {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": UA_OAUTH_V1},
         {"uid": uid, "password": password, "response_type": "token",
          "client_type": "2", "client_secret": CLIENT_SECRET, "client_id": CLIENT_ID}),
    ]:
        try:
            if "json" in headers.get("Content-Type", ""):
                r2 = requests.post(url, json=payload, headers=headers, timeout=15, verify=False)
            else:
                r2 = requests.post(url, data=payload, headers=headers, timeout=15, verify=False)
            if r2.status_code == 200:
                j = r2.json()
                odata = j.get("data", j)
                open_id = odata.get("open_id")
                access_token = odata.get("access_token")
                if open_id and access_token:
                    return {"uid": str(uid), "password": password,
                            "open_id": open_id, "access_token": access_token,
                            "region": "ME"}
        except:
            continue

    return None


def load_guests():
    if os.path.exists(GUESTS_FILE):
        with open(GUESTS_FILE) as f:
            return json.load(f)
    return []


def save_guests(guests):
    os.makedirs(os.path.dirname(GUESTS_FILE), exist_ok=True)
    with open(GUESTS_FILE, "w") as f:
        json.dump(guests, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Add Free Fire guest accounts (Termux)")
    parser.add_argument("--count", type=int, default=5, help="Number of accounts to generate")
    parser.add_argument("--manual", action="store_true", help="Manually add UID+password")
    parser.add_argument("--list", action="store_true", help="List current guests")
    args = parser.parse_args()

    if args.list:
        guests = load_guests()
        print(f"Current guests: {len(guests)}")
        for i, g in enumerate(guests):
            print(f"  [{i+1}] UID: {g['uid']}")
        return

    guests = load_guests()

    if args.manual:
        print("Manual entry mode — enter UID and password for each account")
        print("Press Ctrl+C to stop\n")
        try:
            while True:
                uid = input("UID (or empty to stop): ").strip()
                if not uid:
                    break
                password = input("Password: ").strip()
                if not password:
                    break
                guest = {"uid": uid, "password": password, "open_id": "", "access_token": "", "region": "ME"}
                guests.append(guest)
                print(f"  ✓ Added UID {uid}\n")
        except KeyboardInterrupt:
            pass
        save_guests(guests)
        print(f"\nTotal guests: {len(guests)}")
        return

    print(f"Generating {args.count} guest accounts...")
    print("(This works from Termux/phone — may fail from cloud/server IPs)\n")

    success = 0
    for i in range(args.count):
        print(f"[{i+1}/{args.count}] Registering...")
        guest = register_guest()
        if guest:
            guests.append(guest)
            save_guests(guests)  # Save after each success
            print(f"  ✓ UID: {guest['uid']}")
            success += 1
        else:
            print(f"  ✗ Failed (Garena may block this IP)")
        time.sleep(2)

    print(f"\n{'='*40}")
    print(f"  Generated: {success}/{args.count}")
    print(f"  Total guests: {len(guests)}")
    print(f"{'='*40}")

    if success == 0:
        print("\n⚠ Registration failed from this IP.")
        print("Try running on your phone via Termux, or use --manual to add accounts manually.")
        print("You can also extract guest accounts from the Free Fire app and add them with --manual.")


if __name__ == "__main__":
    main()
