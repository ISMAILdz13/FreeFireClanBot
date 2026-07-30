# ClanGloryBot Test Suite

Comprehensive tests for the Free Fire Clan Glory Bot.

## Running

```bash
# From the repo root:
python3 tests/run_tests.py

## Test Files

- test_xC4.py — Crypto, protobuf encoding/decoding, varint, AES
- test_packets.py — Packet construction, region routing, GeneRaTePk
- test_bot_logic.py — Bot logic: squad formation, solo mode, state management
- test_decode.py — Packet decoding with captured f2=18 match data
- test_config.py — Config file validation (regions, guests, settings)
