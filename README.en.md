# Xiaomi Pad 6S Pro 12.4 · HarmonyOS NEXT port development sources

[简体中文](README.md) · [Build notes](docs/BUILDING.md) · [Provenance and licenses](docs/PROVENANCE.md) · [Verification](docs/VERIFICATION.md)

An experimental port of the HarmonyOS NEXT userspace to the Xiaomi Pad 6S Pro 12.4, codename **sheng**, using a separate compatibility layer for the device hardware. Within the current `super`, only `vendor_dlkm` remains stock Xiaomi. A real HarmonyOS desktop, touch input, selected applications, Wi-Fi and speaker playback have been demonstrated. Power management, WebView, performance and peripheral support remain incomplete.

**Snapshot: October 30, 2026, Asia/Shanghai.** This repository contains source files, patches, configurations and build records. It does not include a flashable full ROM, proprietary Huawei system sources, stock images, firmware binaries, user data or account tokens. Historical directories include failed and reverted experiments; they are not cumulative installation instructions.

## Current versions

| Version | Role | What is established |
| --- | --- | --- |
| v118 | Payload layout baseline | Main compatibility payload moved into `vendor_boot`; `init_boot` retains a minimal entry point. |
| v143 | Reference baseline before the power work | Desktop boot, video speaker playback and boot sound have separate device checks. WebView remains broken. |
| v144 | Isolated EGL/WebView experiment | Resize/first-swap failures were reproduced and partly fixed in native fixtures. Real web pages remain white; no persistent v144 release was flashed. |
| **v145** | **Current persistent version; screen-off confirmed by the user** | Image readback matches, and the device boots to the desktop. Correct wake-call ordering and suppression of late frames while OFF have been observed. **The user's latest physical test confirms screen-off now works.** |

These are development round numbers. Not every round was flashed, validated or suitable for daily use. v145 image SHA-256: `bf39eaa2f45386d09621a9a4cfbbd4725e673cb046fb777d277a40eea70e6895`; v143: `74ee88b754f0d62fbd44df964a925d8ca8aaca3592e18ae01aae7ef46ebc4d58`. Neither image is included in this source package.

## Detailed support status

A feature validated in one round is not a claim that every scenario works. Unless stated otherwise, earlier feature checks have not all been repeated on v145.

| Feature | Status | Verified behavior | Remaining work / limits |
| --- | --- | --- | --- |
| Boot, desktop and windows | Working, stability incomplete | Native init/services, SceneBoard and the actual desktop run. Multiple native captures and reboots reached the desktop. The latest v145 bootstrap completed in about 172 seconds. | Slow boot, service/application waits and historical freezes/reboots remain concerns. No sustained stress qualification. |
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
| Userdata mount | Working | The whole physical `userdata` partition mounts as `/data`, replacing the earlier image-file approach. The setup wizard is preserved. | Fresh-device formatting, upgrades and rollback need separate procedures. Historical initialization tools may erase data and require review. |
| Battery and charge status | Real readings verified | Original battery HDI, SA3302 and public NDK API compared with sysfs; the status bar no longer reports a constant 100%. A matched 94% and plugged type were checked. | Physical unplug callbacks, thermal policy, fast-charge negotiation, battery life and standby drain lack independent acceptance tests. |
| Time | Partial | Network synchronization of real UTC time has been observed. | Offline RTC initialization, timezone/12–24-hour presentation and inconsistent clocks in some UI locations remain open. |
| USB debug channel | Usable, residual issues | Device tty reopening and host batch parsing fixes; multiple cold/normal reboots returned complete command responses. | Role changes and in-flight requests may still lose communication. This is not standard ADB. A COM port enumerating does not prove requests work. Commands have an approximately 60-second execution limit. |
| A/B boot-success marking | Conditionally verified | The original BootControl HAL marked successful boots after real desktop/unlock gates; v145 also logged completion and marking. | Not a complete OTA/A/B upgrade implementation. Do not bypass acceptance gates or assume unlimited reboots are safe. |
| TEE, HUKS and security | Incomplete | Software/no-TEE compatibility research and selected integration sources exist. | **No stock-equivalent trusted security.** Lock credentials, hardware-backed keys, DRM/protected content, payment/authentication and security integrity are not certified or promised. |
| WebView, web pages and login | **Not fixed** | Specific renderer namespace and native-window 1×1 size regressions were diagnosed; isolated EGL fixtures show improvements. | Real pages still render white or fail to open; Douyin login remains broken. v144 is not an accepted solution. |
| Camera, microphone, sensors and other peripherals | Incomplete / unverified | Selected interface, startup and diagnostic sources exist. | No complete camera imaging, microphone capture, full sensor, stylus or keyboard-accessory acceptance tests. Phone feature lists do not automatically apply to this tablet. |
| Distributed features | Incomplete | Optional initialization stalls were avoided for local responsiveness; research is retained. | SoftBus/DeviceManager, identity/security prerequisites and cross-device functionality remain incomplete. Avoiding a wait does not implement distributed features. |

## Boot partition changes

| Partition | Changes |
| --- | --- |
| `boot` | Replaces the kernel with a 5.15.178 GKI build matching sheng's official 303 configuration and symbol versions, adding the kernel exports required by the Harmony IPC module. |
| `init_boot` | Replaces the startup entry with the minimal v118 PID1 program, which establishes required paths and hands control to the startup program in `vendor_boot`. |
| `vendor_boot` | Adds the main `/sheng-compat-v118/` and audio `/sheng-audio-v1/` payloads to the ramdisk, containing startup programs, adaptation libraries, modules and configuration. Display, touch, wireless, audio and framework fixes load persistently from here; v145 updates display power handling and the wake helper. |

## Source map

- `compat/`: display, touch, audio, wireless, framework, power and kernel adaptation sources/configurations, including historical versions for review.
- `tools/`: builds, original-binary patch recipes, image verification and diagnostic/development tools.
- `external/custom/`: custom graphics, IPC, UserIAM and other sources recovered from the WSL work area.
- `external/patches/` and `external/overlays/`: tracked differences and additional sources relative to recorded public upstream revisions.
- `external/upstream-sources.json` and `external/licenses/`: upstream URLs, exact commits and original license texts.
- `analysis/`: selected patches, configuration and build-verification reports, without private raw device logs.
- `output/*.ps1`: host-side script source, without images, device backups or platform-tool binaries.
- `docs/`: build boundaries, component index and validation notes. `SOURCE-MANIFEST.json` records packaged file sizes and hashes.

The user-accepted screen-off fix starts at `tools/build_screen_power_v145.py`, `tools/native_display_wake_v2.cpp` and `tools/build_vendor_screen_power_v145.py`. WebView v144, reverted GPU policies and speculative DSC experiments remain historical/experimental material. Their presence is not an instruction to enable them.

## Building and reporting issues

Read [BUILDING.md](docs/BUILDING.md) first. This is a **development source snapshot**, not yet a one-command reproducible full-ROM build. Prepare proprietary stock/donor inputs, SDKs, toolchains and baseline images independently and lawfully. Historical scripts retain development layout assumptions, expected input hashes and paths requiring configuration.

Debug each stage: `raw events → MMI → system services → DMS/RenderService → HDI/VDI → DRM/backlight`. A system screenshot proves composed content, not physical screen-off. Negotiated link speed is not measured network throughput. A successful return value is not proof of audible sound or visible output.

Issue reports should include version, reproduction steps, expected/actual behavior and sanitized logs. Do not upload Wi-Fi passwords, tokens, user data, stock images or extracted proprietary libraries. Attribution and derivation, especially [AnyHarmonyOS](https://github.com/YiKongk/AnyHarmonyOS), are documented in [PROVENANCE.md](docs/PROVENANCE.md). This is not an official Xiaomi, Huawei or upstream-project port.
