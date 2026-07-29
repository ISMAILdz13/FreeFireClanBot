# Clan Glory Bot — Test Results & Documentation

## Date: 2026-07-30

## Exploit: Clash Squad Exit Glitch

### How it works:
1. 4 guest accounts join a clan (ID: 3100938923)
2. Squad leader (auto-selected = connections[0]) opens squad
3. Leader invites all other members automatically
4. Members auto-join the squad
5. All members queue for Clash Squad match (FS packet)
6. Wait for matchmaking (~15 seconds)
7. ALL members immediately exit/withdraw (ExiT packet)
8. System awards glory points for participation even on exit
9. Wait for glory to credit (~5 seconds)
10. Re-queue immediately

### Fully Automatic — No Manual Leader
- Leader is auto-selected as connections[0] (first guest)
- All steps run without user intervention
- Auto-reconnect if TCP drops
- Auto-requeue after each cycle

### Test Results (2026-07-30):

| Component        | Status | Details |
|-----------------|--------|---------|
| MajorLogin      | ✅ WORKING | loginbp.ggpolarbear.com, port 443 |
| GetLoginData    | ✅ WORKING | Returns TCP server IPs |
| TCP Online      | ⏳ PENDING | 98.98.162.73:39698 (non-443, needs Termux/paid) |
| TCP Chat        | ⏳ PENDING | 98.98.162.69:39800 (non-443, needs Termux/paid) |
| AuthClan        | ⏳ PENDING | Requires TCP connection |
| OpEnSq          | ⏳ PENDING | Requires TCP connection |
| SEnd_InV        | ⏳ PENDING | Requires TCP connection |
| GenJoinSquads   | ⏳ PENDING | Requires TCP connection |
| FS (start match)| ⏳ PENDING | Requires TCP connection |
| ExiT (exit)     | ⏳ PENDING | Requires TCP connection |

### Guest Accounts:
| # | UID | Open ID | Status |
|---|-----|---------|--------|
| 1 | 5842511863 | 14c795ca2e7da7c7... | MajorLogin ✅ |
| 2 | 5842511867 | 6c25c9e6ab74750a... | MajorLogin ✅ |
| 3 | 5842511864 | 5b492ac52f22bd3e... | MajorLogin ✅ |
| 4 | 5870428608 | d0de0e45d33c103a... | MajorLogin ✅ |
| 5 | 5870429859 | ee560aae38730aa4... | Available (backup) |

### Timing:
- Per cycle: ~23 seconds (15s matchmaking + 5s post-exit + 3s requeue)
- 200 cycles: ~76 minutes
- 500 cycles: ~191 minutes (~3.2 hours)

### Usage:
```bash
python3 clan_glory_bot.py --clan-id 3100938923 --region ME --cycles 200
```

### Note:
TCP connections to Free Fire game servers use non-443 ports (e.g., 39698, 39800).
On free plans, only HTTPS (port 443) is allowed.
Run from Termux on your phone or use a paid plan for full network access.

---

## Like Bot — Test Results (2026-07-29)

### Status: ✅ FULLY WORKING

### LikeProfile API:
- Format: TCP bot style `08{uid_varint}10{region_code}` (NOT string region)
- Region code: 7 = ME (varint, not string "ME")
- Endpoint: clientbp.ggpolarbear.com/LikeProfile (port 443)
- AES key/IV: Original (Yg&tc%DEuh6%Zc^8 / 6oyZDr22E3ychjM%)
- Auth: JWT from MajorLogin

### Results:
- 15/15 likes sent successfully to UID 3476575559
- 5 guests × 3 likes each
- All HTTP 200 responses
- 0 failures

### Region Codes:
| Region | Code |
|--------|------|
| ME     | 7    |
| IND    | 1    |
| BR     | 2    |
| SG     | 3    |
| TH     | 4    |
| PH     | 5    |
| VN     | 6    |
| RU     | 8    |
| US     | 9    |
