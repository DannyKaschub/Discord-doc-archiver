# Discord Document Archiver Bot

Ein automatisierter Python-Bot, der auf einem Raspberry Pi läuft. Er empfängt hochgeladene PDF-Dokumente aus einem Discord-Channel und legt sie auf dem Pi im Dateisystem ab.

## Hardware & System
* **Plattform:** Raspberry Pi
* **OS:** Raspberry Pi OS (Linux)
* **Betrieb:** Ausgelegt für 24/7-Dauerbetrieb im Heimnetzwerk

## Features
* Asynchrones Handling von Datei-Uploads über `discord.py`
* Sichere Speicherung von Konfigurationsdaten (Tokens via `config.py`)
* Leichtgewichtiger Backend-Prozess für die ARM-Architektur des Pi

## Setup
1. Repository auf den Raspberry Pi klonen
2. `config.py` mit eigenem `DISCORD_TOKEN` und `SAVE_DIRECTORY` anlegen
3. `python3 annabot.py` ausführen
