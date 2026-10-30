# Xiaomi Pad 6S Pro 12.4 · HarmonyOS NEXT

[简体中文](README.md) · [Building](docs/BUILDING.md) · [Source map](docs/SOURCE_MAP.md) · [Verification](docs/VERIFICATION.md) · [Provenance](docs/PROVENANCE.md)

An experimental HarmonyOS NEXT port for the Xiaomi Pad 6S Pro 12.4 (**sheng**). A compatibility layer connects the Harmony userspace to the device hardware, and a real Harmony desktop is running. Within the current `super`, only `vendor_dlkm` remains stock Xiaomi.

**Current accepted build: v146, October 31, 2026.** Each component retains its most complete implementation included in the usable baseline, plus required dependencies. Older implementations, duplicates, failed experiments and chronological build chains have been removed from the current tree.

## What was actually tested

The selected tree compiled 37 direct targets and the UserIAM backend, adapter and driver in WSL. A v146 test image incorporated 34 rebuilt runtime files. The device was backed up, `vendor_boot_a` was written from TWRP, the complete partition readback matched its SHA-256, and the device was rebooted. The rebuilt minimal init is byte-identical to the existing entry. Kernel and Mesa artifacts were retained from the matching validated baseline; full kernel/Mesa builds were not repeated.

Automatic startup completed at approximately **171.73 seconds**. Logs cover desktop unlocking, a native system capture and Wi-Fi/audio/Bluetooth startup. The user confirmed that **the previously expected working features remain normal**, then authorized publication. This does not establish fixes for previously unfinished features, exhaustive performance testing or long-term stability.

Test-image SHA-256: `6bdb19aa74a42de27ba32e6e23fcf87f1944acd23be604a8f99785400453b901`. Images, proprietary system libraries, firmware, apps, user data and private raw logs are excluded. See `analysis/rebuilt-source-v146-verification.json`.

## Detailed support status

“Working” is limited to the listed scenarios. Overall v146 acceptance does not replace an exhaustive independent regression of every feature.

| Feature | Status | Verified behavior | Remaining work / limits |
| --- | --- | --- | --- |
| Boot, desktop and windows | Working, stability incomplete | Native init/services, SceneBoard and the actual desktop run. Multiple native captures and reboots reached the desktop. The latest v146 bootstrap completed in about 172 seconds. | Slow boot, service/application waits and historical freezes/reboots remain concerns. No sustained stress qualification. |
| Physical display | Working | Dual-DSI / dual-plane scanout and full UI output; the early top-strip-only fault was addressed. | Historical bars, white screens and wake issues are not considered permanently eliminated. Full display lifecycle testing remains. |
| GPU and graphics interfaces | Partial | Mesa/Turnip/Zink and Harmony graphics integration have produced real desktop/application frames and pixel comparisons. | Not full stock GPU parity. Formats, synchronization, WebView and performance remain incomplete. |
| Refresh rate | 120Hz baseline verified | Kernel mode reports `3048×2032 @ 120Hz`; the native GPU governor is retained. | **144Hz is unfinished.** Scanout at 120Hz does not prove sustained application rendering at 120fps or low touch-to-photon latency. Added GPU frequency policies were reverted. |
| Touch | Working | Xiaomi THP input reaches Harmony MMI; the user confirmed usable coordinates and interaction. | No complete qualification of sampling rate, tail latency, multitouch, edges or resume behavior. |
| Delayed application taps | One concrete stall fixed | SceneBoard synchronous Binder calls were blocked by optional MSDP distributed initialization. A measured `MMI up → SceneBoard tap` interval dropped from about 1922ms to about 7ms after the targeted change; the user confirmed improvement. The change was persisted. | This interval is not touch-to-photon latency. Other animation stalls, cold launches and input-method/application waits are not all fixed. |
| Brightness control | Working | UI/HDI and kernel backlight units were adapted; the user confirmed brightness adjustment. | Automatic brightness, minimum brightness and full-range/resume regressions are incomplete. |
| Short power-button screen-off | **Working; user acceptance received** | v145 persistently fixes wake-order FSM conflicts and late DRM frames reapplying `ACTIVE=1`. The user's latest physical test confirms screen-off works. Wake calls and a restored desktop also have logs/capture evidence from this round. | Prolonged screen-off, repeated physical-button cycles, deep-sleep power and abnormal recovery still need independent tests. Earlier explicit ON requests had possible manual interference and are not treated as proof of a remaining automatic-wake fault. |
| Long power press and volume keys | Partial | The user confirmed the long-press shutdown menu; key mapping and framework delivery have historical checks. | All screens, lock states and suspend scenarios have not been revalidated. A working long press does not establish working short-press screen-off. |
| Wi-Fi connectivity | Working, reliability incomplete | Device association, password entry, actual WPA COMPLETED and network access were demonstrated; a 5GHz / 160MHz / Wi-Fi 6 connection was recorded. | User reports of slow or lost connectivity require further work. Throughput, roaming, standby reconnection, hotspot and long-term reliability are not qualified. |
| Wi-Fi generation reporting | Wi-Fi 6 verified | Real hardware capability and negotiated link information reach the framework, and the original status bar displays the Wi-Fi 6 badge. | EHT advertised by the driver does not prove a Wi-Fi 7 connection. **No real Wi-Fi 7 AP connection was validated.** No invented 7/Plus labels. |
| Bluetooth | Partial | Original firmware initialization, native Bluetooth and Fusion integration; settings toggle, OFF→ON and discovery of a nearby device were verified on v139. | Pairing, A2DP/HFP, headsets/keyboards, end-to-end BLE and sustained reliability remain unverified. Correcting the donor's NearLink declaration does not add NearLink hardware. |
| Speakers and audio service | Working, limited coverage | Native PAL/AGM backend integration; the user heard music/video audio and confirmed pause/resume playback on v142. | Audio quality, every channel, route, volume and format, long playback, headphones, USB/Bluetooth audio and recording are not fully verified. |
| Boot-animation sound | Verified | v143 addressed a missing imported boot reason that made the original player force volume to zero. The user confirmed both replay and sound during a real reboot. | This is not a claim that all animation performance, boot paths or media backends are complete. |
| Video/image decoding | Partial software path | Real native/third-party video frames; targeted YUV/RGB metadata, crop and alpha fixes; native NDK HEIC pixel comparisons. | **Hardware video decoding is unfinished.** Some applications/formats still fail or stutter. One playing video is not full media support. |
| Input method | Working, compatibility incomplete | The user confirmed a real keyboard appears and accepts a WLAN password. | All applications, web fields, languages and sustained use are not qualified. |
| Third-party and preload apps | Partial | Installation of 14 preload packages was checked. Real account/storage unlocking moved selected apps beyond the “application data is being decrypted” gate; apps including Douyin can show actual content. | Arbitrary HAP compatibility is not promised. Splash stalls, first-run flows, crashes, login and WebView dependencies remain. Application packages are not included. |
| Userdata mount | Working | The whole physical `userdata` partition mounts as `/data`, replacing the earlier image-file approach. The setup wizard is preserved. | Fresh-device formatting, upgrades and rollback need separate procedures. Fresh initialization may erase data and requires review. |
| Battery and charge status | Real readings verified | Original battery HDI, SA3302 and public NDK API compared with sysfs; the status bar no longer reports a constant 100%. A matched 94% and plugged type were checked. | Physical unplug callbacks, thermal policy, fast-charge negotiation, battery life and standby drain lack independent acceptance tests. |
| Time | Partial | Network synchronization of real UTC time has been observed. | Offline RTC initialization, timezone/12–24-hour presentation and inconsistent clocks in some UI locations remain open. |
| USB debug channel | Usable, residual issues | Device tty reopening and host batch parsing fixes; multiple cold/normal reboots returned complete command responses. | Role changes and in-flight requests may still lose communication. This is not standard ADB. A COM port enumerating does not prove requests work. Commands have an approximately 60-second execution limit. |
| A/B boot-success marking | Conditionally verified | The original BootControl HAL marked successful boots after real desktop/unlock gates; v145 also logged completion and marking. | Not a complete OTA/A/B upgrade implementation. Do not bypass acceptance gates or assume unlimited reboots are safe. |
| TEE, HUKS and security | Incomplete | Software/no-TEE compatibility research and selected integration sources exist. | **No stock-equivalent trusted security.** Lock credentials, hardware-backed keys, DRM/protected content, payment/authentication and security integrity are not certified or promised. |
| WebView, web pages and login | **Not fixed** | Specific renderer namespace and native-window 1×1 size regressions were diagnosed; isolated EGL fixtures show improvements. | Real pages still render white or fail to open; Douyin login remains broken. v144 is not an accepted solution. |
| Camera, microphone, sensors and other peripherals | Incomplete / unverified | Selected interface, startup and diagnostic sources exist. | No complete camera imaging, microphone capture, full sensor, stylus or keyboard-accessory acceptance tests. Phone feature lists do not automatically apply to this tablet. |
| Distributed features | Incomplete | Optional initialization stalls were avoided for local responsiveness; the current local fallback is retained. | SoftBus/DeviceManager, identity/security prerequisites and cross-device functionality remain incomplete. Avoiding a wait does not implement distributed features. |

## Changes to the three boot partitions

| Partition | Current changes |
| --- | --- |
| `boot` | A 5.15.178 GKI kernel matching sheng's official 303 configuration and symbol versions, with exports required by Harmony IPC. |
| `init_boot` | A minimal PID1 entry establishes paths and hands control to the program in `vendor_boot`. The entry rebuilt in this round is byte-identical to the existing one. |
| `vendor_boot` | Ramdisk payloads under `/sheng-compat-v118/` and `/sheng-audio-v1/` persistently load startup, display, input, wireless, audio and framework adaptations. v146 contains the rebuilt runtime files and matching integrity configuration. |

## Current sources

- `compat/`: selected component sources, interface headers and shared dependencies.
- `runtime/`: startup scripts and configuration matching accepted v146, with compatible runtime filenames.
- `patches/donor/`: donor-library recipes with whole-file SHA-256 and before/after byte guards.
- `external/`: pinned upstream revisions, required Mesa/kernel patches, overlays and licenses.
- `tools/`: direct builds and source-inventory utilities; `output/*.ps1`: host debugging, backup and recovery tools.
- `tests/`, `analysis/` and `evidence/`: required tests and sanitized verification records.

Selected implementations are display/power v145, buffer v130, Turnip v128, EGL v126, touch service-v2, audio v142, Wi-Fi generation v134, Bluetooth v139 plus the v141 capability correction, battery v131, database/memory management v2 and USB probe v121. They form one current baseline. Both UserIAM 4.0 backend and 4.1 adapter are required ABI layers. Older numbers in runtime filenames do not mean multiple historical implementations are retained. See `SOURCE-SELECTION.json`, `SOURCE-MANIFEST.json` and `SHA256SUMS` for selection and hashes.

## Building and use

Read [BUILDING.md](docs/BUILDING.md), configure matching SDK, upstream, libdrm, PAL, OpenSSL and donor-link inputs, then inspect targets with `tools/build_current.py --list`. UserIAM builds through `tools/build_useriam.py`. This remains a development source tree rather than a one-command full-ROM build from a clean environment.

The COM probe is not standard ADB. Use the command, transfer and screenshot scripts under `output/`, with serial requests executed sequentially. Preserve this device's own boot-partition trio and verify image hashes before flashing. Other-device images or test results are not interchangeable.

Report versions, reproduction steps and sanitized logs; exclude credentials, tokens and private data. Attribution, including [AnyHarmonyOS](https://github.com/YiKongk/AnyHarmonyOS), is described in [PROVENANCE.md](docs/PROVENANCE.md). This is not an official Xiaomi, Huawei or upstream-project port.
