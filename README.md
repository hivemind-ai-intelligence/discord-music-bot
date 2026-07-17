<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=32&duration=3000&pause=1000&color=5865F2&center=true&vCenter=true&width=600&lines=%F0%9F%8E%B5+Shandip's+Music+Bot;48+Slash+Commands;YouTube+%2B+Spotify+Streaming;Custom+Name+Styles+%F0%9F%8E%A8" alt="Typing SVG" />
</p>

<p align="center">
  <a href="https://discord.gg/your-server"><img src="https://img.shields.io/badge/Discord-Support%20Server-5865F2?style=for-the-badge&logo=discord&logoColor=white" /></a>
  <a href="https://github.com/hivemind-ai-intelligence/discord-music-bot"><img src="https://img.shields.io/github/stars/hivemind-ai-intelligence/discord-music-bot?style=for-the-badge&logo=github&color=FEE75C" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/discord.py-2.3%2B-5865F2?style=flat-square&logo=discord" />
  <img src="https://img.shields.io/badge/Wavelink-3.3%2B-FF6B6B?style=flat-square" />
  <img src="https://img.shields.io/badge/Lavalink-v4-00FFAA?style=flat-square" />
  <img src="https://img.shields.io/badge/Render-Ready-46E3B7?style=flat-square&logo=render" />
  <img src="https://img.shields.io/badge/Bug_Free-%E2%9C%93-57F287?style=flat-square" />
  <img src="https://img.shields.io/badge/Prefix-m!-gray?style=flat-square" />
  <img src="https://img.shields.io/badge/Updated-July%202026-FFA500?style=flat-square" />
</p>

---

## ✨ Features

| 🎵 Music (23) | 🎨 Name Styles (7) | ⚙️ General (7) | 😂 Fun (6) | 🛠️ Utility (5) |
|:---:|:---:|:---:|:---:|:---:|
| YouTube Streaming | 12 Fonts × 6 Effects | Ping, Stats, Help | Jokes, Memes | Avatar, Banner |
| Queue Management | 15 Presets | Invite, Info | 8ball, Flip | Server/User Info |
| Audio Filters | Interactive Setup | Uptime, Vote | Dice, RPS | Emoji Info |
| 24/7 Mode | REST API Powered | | | |

---

## 📦 Quick Setup

```bash
git clone https://github.com/hivemind-ai-intelligence/discord-music-bot.git
cd discord-music-bot
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your bot token + Lavalink details
python main.py
```

> ⚡ **Done.** Bot auto-syncs all slash commands on startup.

---

## 💻 Platform-Specific Guides

<details open>
<summary><b>🪟 Windows</b></summary>

```powershell
# Install Python 3.10+ from python.org
# ☑️ CHECK "Add Python to PATH" during install

python --version
git clone https://github.com/hivemind-ai-intelligence/discord-music-bot.git
cd discord-music-bot
pip install -r requirements.txt
copy .env.example .env
notepad .env
python main.py
```

> **Tip:** Keep terminal open. Bot stops when you close it.

</details>

<details>
<summary><b>🐧 Linux / VPS</b></summary>

```bash
sudo apt update && sudo apt install python3 python3-pip git -y
git clone https://github.com/hivemind-ai-intelligence/discord-music-bot.git
cd discord-music-bot
pip3 install -r requirements.txt
cp .env.example .env && nano .env

# Run with screen (survives logout)
screen -S musicbot
python3 main.py
# Ctrl+A, D to detach

# Or use systemd for auto-restart:
sudo nano /etc/systemd/system/musicbot.service
```
```ini
[Unit]
Description=Discord Music Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/discord-music-bot
ExecStart=/usr/bin/python3 main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable --now musicbot
```

</details>

<details>
<summary><b>📱 Termux (Android)</b></summary>

```bash
pkg update && pkg upgrade -y
pkg install python python-pip git -y
git clone https://github.com/hivemind-ai-intelligence/discord-music-bot.git
cd discord-music-bot
pip install -r requirements.txt
cp .env.example .env && nano .env
python main.py
```

> 📱 Phone must stay awake. Use `termux-wake-lock`. Use the free public Lavalink from `.env.example`.

</details>

---

## 🚀 Deploy to Render (Free)

| Setting | Value |
|---------|-------|
| **Runtime** | Python 3 |
| **Build** | `pip install -r requirements.txt` |
| **Start** | `python main.py` |
| **Type** | **Background Worker** (Free) |

**Env Variables:**
| Key | Value |
|-----|-------|
| `DISCORD_TOKEN` | Your bot token |
| `LAVALINK_HOST` | `lavalink-v4.triniumhost.com` |
| `LAVALINK_PORT` | `443` |
| `LAVALINK_PASSWORD` | `free` |
| `LAVALINK_SECURE` | `true` |

---

## 🎵 Complete Command List

<details open>
<summary><b>🎵 Music (23 commands)</b></summary>

| Command | Description |
|---------|-------------|
| `/play <song>` | Search & play from YouTube |
| `/pause` | Pause playback |
| `/resume` | Resume playback |
| `/skip` | Skip current track |
| `/stop` | Stop & disconnect VC |
| `/loop` | Toggle queue loop |
| `/queue` | View full queue |
| `/shuffle` | Shuffle queue |
| `/remove <pos>` | Remove track by position |
| `/clearqueue` | Clear entire queue |
| `/volume <0-100>` | Set volume with visual bar |
| `/nowplaying` | Current track details |
| `/seek <seconds>` | Jump to timestamp |
| `/restart` | Restart current track |
| `/join` | Bot joins your VC |
| `/leave` | Bot leaves VC |
| `/autoplay` | Toggle autoplay |
| `/lyrics` | Search lyrics links |
| `/bassboost` | Toggle bass boost |
| `/speed <0.5-3.0>` | Playback speed |
| `/move <from> <to>` | Move in queue |
| `/save` | DM current track |
| `/history` | Recently played |
| `/24-7` | Never disconnect |

</details>

<details>
<summary><b>🎨 Name Styles (7 commands)</b></summary>

| Command | Description |
|---------|-------------|
| `/namestyle set` | Interactive setup |
| `/namestyle reset` | Reset to default |
| `/namestyle list` | 12 fonts & 6 effects |
| `/namestyle presets` | 15 ready styles |
| `/namestyle preview` | Preview a preset |
| `/namestyle current` | Current style |
| `/namestyle info` | Rules & limits |

</details>

> **Prefix:** `m!` also works (`m!play`, `m!skip`, etc.) — **48 total commands**

---

## 🏗️ Project Structure

```
music-bot/
├── main.py              ← Entry point + Lavalink
├── requirements.txt     ← discord.py, wavelink, aiohttp
├── Procfile             ← Render deployment
├── .env.example         ← Config template
├── .gitignore
│
├── cogs/
│   ├── music.py         ← 🎵 23 music commands
│   ├── namestyle.py     ← 🎨 7 name style commands
│   ├── general.py       ← ⚙️ 7 general commands
│   ├── fun.py           ← 😂 6 fun commands
│   └── utility.py       ← 🛠️ 5 utility commands
│
├── utils/
│   ├── helpers.py       ← Emojis, formatting, bars
│   ├── namestyle_data.py← Fonts, effects, presets
│   └── db.py            ← JSON guild settings
│
└── data/                ← Auto-created (gitignored)
```

---

## 🔧 Bot Setup (Discord)

1. [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**
2. **Bot** tab → **Reset Token** → Copy to `.env`
3. **Privileged Gateway Intents**: Enable ALL 3
4. **OAuth2 → URL Generator**: `bot` + `applications.commands`, permissions: `2184261185`
5. Open URL → Invite to your server

---

## 🐛 Troubleshooting

<details>
<summary><b>Bot offline?</b></summary>
Check DISCORD_TOKEN in .env is correct. Check intents in Developer Portal.
</details>

<details>
<summary><b>Music not working?</b></summary>
Lavalink must be running. Check LAVALINK_HOST/PORT. Free public one may go down — have a backup.
</details>

<details>
<summary><b>Disconnects after 2 min?</b></summary>
Use `/24-7` to disable auto-disconnect. Or change `inactive_timeout` in code.
</details>

<details>
<summary><b>Name styles failing?</b></summary>
Bot needs **Change Nickname** permission. Rate limit: ~2/min. Gradient needs exactly 2 colors.
</details>

---

## 📝 Author's Note

> Built from scratch with love in Kolkata. The music engine is adapted from production-grade REO Bot code, rewritten for standalone deployment. Name Styles modeled after Bot-NameStyles by itsfizys.
>
> **No premium walls.** All features — URL playback, queues, filters, 24/7 — are free forever.
>
> Every command tested for edge cases: timeouts, empty queues, invalid URLs, concurrent usage.

**Built by [Shandip](https://github.com/hivemind-ai-intelligence)** • July 2026 • 🇮🇳 Kolkata

---

<p align="center">
  <sub>Found this useful? ⭐ the repo — it keeps me motivated!</sub>
</p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=5865F2&height=100&section=footer"/>
</p>
