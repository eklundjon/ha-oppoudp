# OPPO UDP-20x Control Protocol — Reference

A distilled reference for the OPPO UDP-203 / UDP-205 **RS-232 & IP Control Protocol**
(firmware `UDP20X-54-1127`, last revised by OPPO 2017-12-18), kept here because
OPPO Digital shut down in 2018 and the original document
(`download.oppodigital.com/UDP203/OPPO_UDP-20X_RS-232_and_IP_Control_Protocol.pdf`)
is no longer hosted.

This is our own summary of the wire protocol for maintainer reference — not a copy
of OPPO's document. Command codes are interface facts; for exact parameter tables
consult an archived copy of the original PDF. A second, cross-checking implementation
lives in the [openHAB Oppo binding](https://github.com/openhab/openhab-addons/tree/main/bundles/org.openhab.binding.oppo).

## Transports

| Transport | Details |
|-----------|---------|
| RS-232 | 9600 baud, 8 data bits, no parity, 1 stop bit, no flow control |
| IP | TCP **port 23** (fixed). *Not* telnet — the server needs each command as a single packet; a telnet client fragments keystrokes and breaks it. |

## Message framing

- **Command:** `#` (0x23) + 3-char code + optional ` ` + parameters + `\r` (0x0D). Max ~25 bytes total. `#` must never appear in a parameter.
- **Response:** prefixed `@OK` (success, optionally with data) or `@ER` (error), terminated by `\r`.
- **Verbose echo:** at verbose 0 the command code is not echoed in the response; set verbose ≥ 1 for parseable responses.

## Discovery

The player advertises itself by **UDP multicast to `239.255.255.251:7624`, every ~10 seconds**:

```
Notify: OPPO Player Start
Server Name: OPPO UDP-203
```

…and includes its IP address and control port. A controller joins the group, reads
the announcement, then opens the TCP control connection to `<ip>:23`.

> **No stable hardware identifier.** The announcement carries only the IP and a
> *model-based* "Server Name" — there is **no serial number or MAC** anywhere in this
> protocol. This is why the integration keys its config entry on host/IP, not a serial.

## Verbose mode (`SVM`)

| Level | Behavior |
|-------|----------|
| 0 | Off (default). Responses omit the echoed command code. |
| 1 | Verbose responses (command code echoed). |
| 2 | Unsolicited status-change updates (power, playback, volume, disc/audio/subtitle, input, 3D, aspect). |
| 3 | Everything in 2, **plus** a per-second `UTC` playback-time update. |

Level **3** is required for live playback-position tracking.

## Command categories

Codes are grouped by first letter. Full member lists live in the vendored SDK
(`custom_components/oppo_udp/oppoudpsdk/codes.py`).

### Remote / direct codes (IR-equivalent)
Transport (`PLA` `PAU` `STP` `PRE` `NXT` `REV` `FWD`), power (`POW` `PON` `POF` `EJT`),
volume (`VUP` `VDN` `MUT`), navigation (`NUP` `NDN` `NLT` `NRT` `SEL` `RET` `HOM` `MNU`
`OSD` `PUP` `PDN`), numerics (`NU0`–`NU9` `CLR` `GOT`), color keys (`RED` `GRN` `BLU` `YLW`),
media (`AUD` `SUB` `ANG` `ZOM` `RPT` `PIP` `HDR` `SRC` …). UDP-20x adds `HDR` / `INH` / `RLH`.

### Query codes (`Q**`) — one-shot status reads
`QPW` power · `QVR` firmware · `QVL` volume · `QHD` HDMI resolution · `QPL` playback status ·
`QTK`/`QCH` title/chapter · `QTE`/`QTR`/`QCE`/`QCR`/`QEL`/`QRE` elapsed/remaining times ·
`QDT` disc type · `QAT` audio type · `QST` subtitle · `QSH` subtitle shift · `QOP` OSD position ·
`QRP` repeat · `QZM` zoom · `QHR` HDR · `Q3D` 3D · `QHS` HDR status · `QIS` input source ·
`QVM` verbose · `QCD` CDDB id · `QFT`/`QFN` file format/name · `QTN`/`QTA`/`QTP` track name/album/performer ·
`QDS`/`QDR` directory listing · `QAR` aspect ratio.

### Set codes (`S**`) — configure state
`SVM` verbose · `SVL` volume · `SHD` HDMI mode · `SHR` HDR · `SZM` zoom · `SRP` repeat ·
`SRH` seek · `SSH` subtitle shift · `SOP` OSD position · `STC` time-display type ·
`SIS` input source · `SSA` screen saver · `SSD`/`SDP` SACD priority/output · `APP` launch app.

### Update codes (`U**`) — pushed in verbose mode
**Verbose 2:** `UPW` power · `UPL` playback status · `UVL` volume · `UDT` disc type ·
`UAT` audio type · `UST` subtitle · `UIS` input source · `U3D` 3D · `UAR` aspect ratio.
**Verbose 3 adds:** `UTC` time code (per second) · `UVO` video resolution (source + output).

## Status value notes

`UPL`/`QPL` playback strings the player emits (some contain **spaces**, which matters
for exact enum matching):

`PLAY` · `PAUSE` · `STOP` · `HOME MENU` · `MEDIA CENTER` · `SCREEN SAVER` ·
`DISC MENU` · `SETUP` · tray `OPEN`/`CLOSE` · frame-step `STPF`/`STPR` ·
speed modes `FFWn`/`FRVn`/`SFWn`/`SRVn` (n = 1–5).

Disc types: `UHBD` `BDMV` `DVDV` `DVDA` `SACD` `CDDA` `DATA` `VCD2` `SVCD` `UNKW`.

## Implementation notes

- The vendored SDK models this protocol; its enum **values** must match these exact
  strings (including spaces). Coverage of the code set is complete; value correctness
  should be audited against this table.
- A separate, **undocumented** HTTP/JSON API (port 436, activated by a
  `NOTIFY OREMOTE LOGIN` broadcast) exists and powers OPPO's mobile app with file
  browsing and play-by-path. It is *not* part of the official RS-232/IP protocol and
  would require reverse-engineering to use.
