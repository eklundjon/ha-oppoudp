# OPPO Control Protocol — Reference (all generations)

A distilled reference for OPPO's player control protocol, from the DV-98xH DVD
players through the UDP-20x UHD players. Kept here because OPPO Digital shut down
in 2018 and the original documents are disappearing from the web.

The integration targets the **UDP-20x**, but the command core is shared across
the whole lineage, which matters for the "classic players over serial" idea (see
the [architecture doc](ARCHITECTURE.md)). Command codes are interface facts; this
is our own organized summary, not a copy of OPPO's documents.

**Sourced from** (extracted from the original PDFs where reachable):
[DV-983H](https://www.oppodigital.com/support/dv983h/download/DV-983H%20RS232%20Protocol.pdf),
[BDP-83](https://www.oppodigital.com/Download/BDP83/BDP83_RS232_Protocol.pdf),
[UDP-20x](http://download.oppodigital.com/UDP203/OPPO_UDP-20X_RS-232_and_IP_Control_Protocol.pdf),
cross-checked against the [openHAB Oppo binding](https://github.com/openhab/openhab-addons/tree/main/bundles/org.openhab.binding.oppo).

## Lineage

The `#CCC<CR>` command scheme has been remarkably stable across OPPO's players —
the UDP-20x doc itself calls its protocol "an extended version of the original
BDP-83 protocol," and the BDP-83 in turn inherited the DV-98xH scheme:

| Generation | Example models | Era | Transport | Responses | Push |
|-----------|----------------|-----|-----------|-----------|------|
| **DVD** | DV-980H, DV-983H | ~2007–08 | RS-232 only | plain text | — (pull only) |
| **BD gen 1** | BDP-83 | 2009 | RS-232 | `@OK` / `@ER` | — (pull only) |
| **BD gen 2–3** ★ | BDP-93/95, BDP-103/105 | 2011–13 | RS-232 (+ app IP) | `@OK` / `@ER` | — (pull only) |
| **UHD** | UDP-203, UDP-205 | 2016–17 | RS-232 **and** IP | `@OK` / `@ER` | **`U**` verbose** |

★ The BDP-9x/10x column is **inferred** from the lineage (a superset of BDP-83
plus 3D and expanded HDMI-mode commands, minus the UHD-only layer); that specific
protocol PDF wasn't recovered. Treat its cells as "inherits BD gen 1 + 3D."

## Transports & framing

- **Command (all generations):** `#` (0x23) + 3-char code + optional ` params` +
  `<CR>` (0x0D). Max ~25 bytes. Serial is **9600 8N1**, no flow control.
- **Responses evolved:**
  - DVD: plain English text — `POWER ON`, `Volume is 12`, `DV983H-05-0303`.
  - BD onward: prefixed `@OK …` / `@ER …` (or `ER OVERTIME` for a busy device).
- **IP (UDP-20x):** TCP **port 23** (not telnet — needs whole packets), plus UDP
  discovery. Earlier players are serial-only.

### Discovery (UDP-20x only)

The player multicasts to **`239.255.255.251:7624` every ~10 s**:

```
Notify: OPPO Player Start
Server Name: OPPO UDP-203
```

…with its IP and control port. **No serial/MAC** is exposed — the config entry
keys on host/IP, not a serial (see below for how the *model* is still detected).

### Verbose mode (UDP-20x only)

`SVM` sets the reporting level: `0` off, `2` unsolicited status changes, `3` adds
a per-second `UTC` time update. Level 3 is needed for live playback position.
DVD and BD players have **no push** — state must be polled.

## Command matrix

Legend: ✓ documented · — not present · ★ inferred (BD gen 2–3). Grouped;
numeric/nav keys collapsed. "10x" = BDP-9x/10x.

### Power · tray · transport
| Command | DVD | BDP-83 | 10x★ | UDP-20x |
|---|:--:|:--:|:--:|:--:|
| `POW` `PON` `POF` power | ✓ | ✓ | ✓ | ✓ |
| `EJT` tray | ✓ | ✓ | ✓ | ✓ |
| `DIM` front-panel dimmer | — | ✓ | ✓ | ✓ |
| `PLA` `PAU` `STP` | ✓ | ✓ | ✓ | ✓ |
| `PRE` `NXT` prev/next | ✓ | ✓ | ✓ | ✓ |
| `REV` `FWD` scan | ✓ | ✓ | ✓ | ✓ |
| `SFF` `SLW` `SRV` discrete slow/fast | ✓ | — | — | — |

### Volume · navigation
| Command | DVD | BDP-83 | 10x★ | UDP-20x |
|---|:--:|:--:|:--:|:--:|
| `VUP` `VDN` `MUT` | ✓ | ✓ | ✓ | ✓ |
| `NUP` `NDN` `NLT` `NRT` `SEL` | ✓ | ✓ | ✓ | ✓ |
| `RET` return · `MNU` menu · `TTL` title · `OSD` | ✓ | ✓ | ✓ | ✓ |
| `HOM` home | — | ✓ | ✓ | ✓ |
| `PUP` `PDN` page | — | ✓ | ✓ | ✓ |
| `NU0`–`NU9` `CLR` `GOT` | ✓ | ✓ | ✓ | ✓ |
| `RED` `GRN` `BLU` `YLW` color keys ⁑ | — | — | — | ✓ |

### Playback modes · A/V
| Command | DVD | BDP-83 | 10x★ | UDP-20x |
|---|:--:|:--:|:--:|:--:|
| `RPT`/`SRP` repeat · `SRH` seek | ✓ | ✓ | ✓ | ✓ |
| `ATB` A-B · `SUB` `AUD` `ANG` | ✓ | ✓ | ✓ | ✓ |
| `ZOM`/`SZM` zoom | ✓ ᶻ | ✓ | ✓ | ✓ |
| `SHF` shuffle | — | ✓ | ✓ | ✓ |
| `HDM`/`SHD` HDMI resolution | ✓ | ✓ | ✓ | ✓ |
| `M3D` 2D/3D | — | — | ✓ | ✓ |
| `HDR` HDR menu/mode | — | — | — | ✓ |
| `SIS` input-source select (HDMI-in etc.) | — | — | — | ✓ |
| `SDP` `SDI` `SPN` SACD/HDMI options | — | ✓ | ✓ | ✓ |
| `APP` `SSA` app / screen-saver | — | — | — | ✓ |

ᶻ DVD has the `ZOM` remote key but no `SZM` set command. ⁑ BD players have color
keys physically, but BDP-83's doc defines no discrete command for them.

### Queries (`Q**`)
| Query | DVD | BDP-83 | 10x★ | UDP-20x |
|---|:--:|:--:|:--:|:--:|
| `QPW` power · `QVR` firmware | ✓ | ✓ | ✓ | ✓ |
| `QVL` vol · `QHD` resolution · `QDT` disc | ✓ | ✓ | ✓ | ✓ |
| `QTK` `QCH` track/chapter | ✓ | ✓ | ✓ | ✓ |
| `QTE` `QTR` `QCE` `QCR` `QEL` `QRE` times | ✓ | ✓ | ✓ | ✓ |
| `QAT` audio · `QST` subtitle | ✓ | ✓ | ✓ | ✓ |
| `QPL` play status | — | ✓ | ✓ | ✓ |
| `QSF` sound field · `QEQ` EQ mode | ✓ | — | — | — |
| `Q3D` 3D status | — | — | ✓ | ✓ |
| `QHR` `QHS` HDR · `QIS` input · `QAR` aspect | — | — | — | ✓ |
| `QSH` `QOP` `QRP` `QZM` settings | — | — | — | ✓ |
| `QCD` CDDB · `QFN` `QFT` `QTN` `QTA` `QTP` `QDS` `QDR` media/files | — | — | — | ✓ |

### Set (`S**`) & verbose updates (`U**`)
| Command | DVD | BDP-83 | 10x★ | UDP-20x |
|---|:--:|:--:|:--:|:--:|
| `SVL` `SHD` `SRP` `SRH` | ✓ | ✓ | ✓ | ✓ |
| `SZM` `SHF` `DPL` `RST` `SYS` | — | ✓ | ✓ | ✓ |
| `SVM` verbose · `SIS` `SHR` `SSH` `SOP` `STC` `SSA` `APP` `SSD` | — | — | — | ✓ |
| `U**` push: `UPW UPL UVL UDT UAT UST UIS U3D UAR UTC UVO` | — | — | — | ✓ |

### DVD-only remote codes (DV-98xH)
Dropped by the Blu-ray line: `BMK` bookmark · `CAP` capture · `EQR`/`QEQ` EQ ·
`SFD`/`QSF` sound field · `KBD` on-screen keyboard · `BRW` browse · `PLP` · `N10`.

## Status value notes (UDP-20x)

`UPL`/`QPL` playback strings contain **spaces** (enum values must match exactly):
`PLAY` `PAUSE` `STOP` `HOME MENU` `MEDIA CENTER` `SCREEN SAVER` `DISC MENU`
`SETUP` · tray `OPEN`/`CLOSE` · step `STPF`/`STPR` · speeds `FFWn`/`FRVn`/`SFWn`/`SRVn`.
Disc types: `UHBD BDMV DVDV DVDA SACD CDDA DATA VCD2 SVCD UNKW`.

## Detecting the hardware generation

**We can auto-detect the model — no need to ask the user in the common case.**
`#QVR` (query firmware version) exists in **every** generation and its response is
**model-prefixed**:

| Model | `#QVR` response |
|---|---|
| DV-983H | `DV983H-05-0303` |
| BDP-83 | `OK BDP83-14-0306` |
| UDP-20x | `UDP20X-54-1127` |

**Detection algorithm:**

1. Connect (over whichever transport).
2. Send `#QVR<CR>`.
3. Read the response; strip an optional `@OK ` / `OK ` prefix.
4. Take the token before the first `-` and map it to a generation:
   - `DV9…` → DVD (plain-text responses, pull-only, no HDR/3D/input, verbose N/A)
   - `BDP8…` → BD gen 1 (`@OK`, `QPL`, no 3D)
   - `BDP9…` / `BDP1…` → BD gen 2–3 (adds 3D)
   - `UDP2…` → UHD (full: IP, verbose push, HDR, input source)
5. **Fallback:** an unrecognized prefix → assume the shared core (transport +
   `QPW`/`QVR`/`QVL`/`QDT` + basic playback) and optionally prompt the user.

Because `#QVR` and the core command set are transport-agnostic, this works
identically over IP or serial — which is what makes supporting the classic
serial-only players a small addition once the serialx transports land.

## Implementation notes

- The vendored SDK models the **UDP-20x** superset; its enum *values* must match
  the exact wire strings (including spaces).
- Older players need **polling** (no `U**` push) and a **plain-text response
  parser** (no `@OK` prefix on the DVD generation).
- A separate, **undocumented** HTTP/JSON API (UDP-20x port 436, `NOTIFY OREMOTE
  LOGIN`) powers OPPO's mobile app with file browsing; not part of the RS-232/IP
  protocol and out of scope here.
