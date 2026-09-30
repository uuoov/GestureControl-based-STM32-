# Gesture-Controlled Music Player

> An embedded-system course project by **Leo Leung**, combining STM32 gesture sensing with a PC-side music player.

## Overview

This project connects an STM32F10x-based controller to a desktop music player. The embedded side reads gesture and 3D position data from an **MGC3130** gesture sensor, displays device status on an OLED, and exchanges control/status data over UART. A Python controller on the PC side receives sensor data, maps gestures to playback actions, and sends song information and control state back to the MCU.

## What it demonstrates

- STM32F10x firmware development with the Standard Peripheral Library
- MGC3130 gesture sensing over I2C
- Gesture and X/Y/Z position acquisition
- UART serial communication at 115200 baud
- Modbus-style register mapping for gesture, volume, current song, and song name
- SSD1306 OLED display integration
- PC-side Python music playback/controller logic
- Embedded + desktop application integration

## Gesture mapping

| Gesture | Action |
| --- | --- |
| Left | Previous song |
| Right | Next song |
| Up | Volume up |
| Down | Volume down |
| Clockwise circle | Single-song loop |
| Counter-clockwise circle | Playlist loop |

## System flow

```mermaid
flowchart LR
    Sensor["MGC3130 Gesture Sensor"] -->|I2C| MCU["STM32F10x"]
    MCU --> OLED["SSD1306 OLED"]
    MCU -->|UART: X,Y,Z + commands| PC["Python Controller"]
    PC --> Player["Desktop Music Player"]
    Player -->|song / volume / state| PC
    PC -->|control state| MCU
```

## Repository structure

```text
GestureControl-based-STM32-/
├── App/
│   ├── Main/          # Main loop and periodic task scheduling
│   ├── OLED/          # OLED display
│   └── ...
├── HW/
│   ├── Gesture/       # MGC3130 driver
│   └── Modbus/        # Register/protocol handling
├── FW/                # STM32 standard peripheral library
├── ARM/               # CMSIS / startup / system files
├── Project/           # Keil project files
└── music_player_controller.py
```

## Open-source references and acknowledgements

This project was developed by **Leo Leung** and includes a substantial STM32-side port and secondary implementation based on open-source references.

The MGC3130 gesture-sensing workflow references **[Corebb / RealCorebb's bbGesture](https://github.com/RealCorebb/bbGesture)**. The bbGesture project provides hardware design resources, Arduino examples, PC tools, and an MGC3130 library adapted from DFRobot.

The upstream MGC3130 library is **[DFRobot_MGC3130](https://github.com/DFRobot/DFRobot_MGC3130)**, originally credited by DFRobot to **Yangfeng (Feng Yang)** and released under the MIT License.

Based on these references, **Leo Leung** ported and reworked the workflow for the STM32F10x platform and implemented the embedded-system integration, including:

- hardware I2C communication with the MGC3130;
- sensor reset and data-ready handling;
- gesture and X/Y/Z position acquisition;
- UART communication between the MCU and PC;
- OLED status display;
- playback-control state handling;
- PC-side music-controller interaction.

STM32 Standard Peripheral Library and CMSIS components remain third-party vendor dependencies and retain their original authorship and licensing.

## Notes

Some generated Keil build artifacts remain in the historical project tree. New work should avoid committing generated build outputs.

## Author

**Leo Leung**  
Biomedical Engineering · Embedded Systems · AI Tools
