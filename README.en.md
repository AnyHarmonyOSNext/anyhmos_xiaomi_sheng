# Xiaomi Pad 6S Pro 12.4 · HarmonyOS NEXT

[简体中文](README.md) · [Building](docs/BUILDING.md) · [Source map](docs/SOURCE_MAP.md) · [Testing](docs/VERIFICATION.md) · [Provenance and licensing](docs/PROVENANCE.md)

A HarmonyOS NEXT port for the Xiaomi Pad 6S Pro 12.4 (**sheng**). A compatibility layer connects HarmonyOS to the tablet's display, touch input, audio and wireless hardware. The system can reach the HarmonyOS desktop and run selected system and third-party applications.

This repository contains the component sources currently in use, startup configuration and build tools. Several features still need work; the table below describes their current status.

## Feature status

| Feature | Working today | Remaining work |
| --- | --- | --- |
| Boot and desktop | The system boots to the desktop, opens windows and takes system screenshots. | Boot takes about three minutes. Some applications and services still stall or crash, and long-term stability needs improvement. |
| Display | Full-screen output works. The early fault that only displayed the top of the screen has been fixed. | Bars, white screens and wake failures have occurred. Repeated screen transitions and extended use need further testing. |
| GPU and refresh rate | Mesa/Turnip/Zink graphics support is integrated. The display runs at 3048×2032 and 120Hz, using the kernel's native GPU governor. | 144Hz is unfinished. Graphics performance, format support and synchronization need improvement. A 120Hz display mode does not mean every application renders at 120fps. |
| Touch and responsiveness | Coordinates and everyday touch interaction work. A service stall causing a one-to-two-second delay when tapping applications has been fixed. | Some application launches and animations still stutter. Sampling, multitouch, edge input and resume behavior need more testing. |
| Brightness | Manual brightness adjustment works. | Automatic brightness, minimum brightness and resume behavior need testing. |
| Power and volume buttons | A short power press turns the screen off or on; a long press opens the shutdown menu. Volume buttons are connected to the system. | Button behavior across lock, suspend and repeated interactions needs broader testing. Deep-sleep power consumption has not been evaluated. |
| Wi-Fi | Password entry, network connection and internet access work. A 5GHz, 160MHz Wi-Fi 6 connection has been tested. | Occasional slowdowns or connection failures remain. Roaming, standby reconnection, hotspot mode and long-term reliability need testing. |
| Wi-Fi generation display | The status bar can show the Wi-Fi 6 badge for the actual connection. | A real Wi-Fi 7 connection has not been tested. |
| Bluetooth | Switching Bluetooth on and off, enabling it again and discovering nearby devices work. | Pairing, headset playback and calls, keyboards, mice and BLE are not fully tested. The device does not support NearLink. |
| Speakers and audio | Music, video audio, playback after pause and boot-animation sound work. | Audio quality, all speaker channels, extended playback, headphones, USB audio and Bluetooth audio need testing. Recording is unfinished. |
| Video and images | Some software decoding paths work. Selected system and third-party applications display video and images. | Hardware video decoding is unfinished. Some applications and formats still fail or stutter. |
| Keyboard | The keyboard appears and accepts input, including Wi-Fi passwords. | More applications, web input fields and languages need testing. |
| Third-party and preload applications | Preload installation is integrated. Some startup blocks showing “application data is being decrypted” have been fixed; applications including Douyin can open and display content. | Some applications remain on their splash screen or crash. Login and features that depend on web pages still have problems. |
| User data | The entire userdata partition mounts directly as `/data`. The first-run setup wizard is retained. | Upgrade, rollback and fresh-device initialization procedures need further work. |
| Battery and charging status | Real battery and charging readings are available. The system no longer shows a constant 100%. | Charging-state changes, thermal behavior, fast charging, battery life and standby drain need testing. |
| Time synchronization | Network time synchronization works. | Offline time, time zones and time displayed in some parts of the interface remain inconsistent. |
| USB debugging | Tools provide command execution, file transfer and screenshots. | Communication can still stop after rebooting or USB state changes. Connection reliability needs improvement. |
| A/B boot | The system can mark a boot successful after the desktop is ready. | Full OTA and A/B update support is unfinished. |
| Web pages and WebView | Not working correctly yet. | Some pages fail to open or remain blank. Douyin web login can remain on a loading screen. |
| Security and encryption | Software compatibility implementations support selected services and applications. | TEE, hardware-backed keys, lock credentials and HUKS are incomplete. Stock-equivalent security is unavailable; payment and DRM features are unverified. |
| Camera, microphone, sensors and accessories | Unfinished. | Camera capture, recording, sensors, stylus and keyboard accessories need individual adaptation and testing. |
| Cross-device features | Unfinished. | Device discovery, connections and cross-device functionality need further adaptation. |

## Changes to the three boot partitions

| Partition | Changes |
| --- | --- |
| `boot` | Uses a 5.15.178 GKI kernel matching the device's official system configuration and symbol versions, with interfaces required for HarmonyOS inter-process communication. |
| `init_boot` | Provides a minimal startup entry, creates the required paths and hands control to the program in `vendor_boot`. |
| `vendor_boot` | Stores the compatibility layer and configuration in the ramdisk, loading display, touch, wireless, audio and system-service adaptations during boot. |

## Source layout

- `compat/`: component sources, interfaces and shared dependencies.
- `runtime/`: startup scripts and runtime configuration.
- `patches/donor/`: patch recipes for original HarmonyOS libraries, with file hashes and checks at each modification point.
- `external/`: upstream source information, kernel and Mesa patches, and licenses.
- `tools/`: build and source verification tools.
- `output/`: host scripts for debugging, transfers, screenshots, backups and recovery.
- `tests/`, `analysis/` and `evidence/`: test cases and records with private information removed.

Each component retains the implementation currently in use and its required dependencies. See the [source map](docs/SOURCE_MAP.md) for details, and `SOURCE-SELECTION.json`, `SOURCE-MANIFEST.json` and `SHA256SUMS` for file inventories and checksums.

## Building and use

Builds use WSL. Follow the [build instructions](docs/BUILDING.md) to prepare the SDK, upstream sources and link dependencies, then list the available targets:

```sh
python3 tools/build_current.py --list
```

UserIAM components are built with `tools/build_useriam.py`. The repository provides build steps for the compatibility layer and related components. A complete ROM also requires separately prepared system images, firmware and applications, which are not distributed here.

Use the tools under `output/` for the system's USB debug connection, running commands sequentially. Before flashing, back up this device's three boot partitions and check the device model and image checksums. See the [testing documentation](docs/VERIFICATION.md) for test coverage and records.

## Reporting issues and credits

Include the commit used, reproduction steps and logs with private information removed. Do not submit passwords or tokens.

This port draws on [AnyHarmonyOS](https://github.com/YiKongk/AnyHarmonyOS) and other projects. See [provenance and licensing](docs/PROVENANCE.md) for source attribution and modifications. This is a community port, unaffiliated with Xiaomi, Huawei or the upstream projects' official device support.
