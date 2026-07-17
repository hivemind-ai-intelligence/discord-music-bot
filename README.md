# 🎵 Shandip's Discord Music Bot

> **48 Slash Commands** • YouTube Music Streaming • Custom Name Styles • Interactive Controller

Ye ek **production-ready** Discord Music Bot hai — scratch se banaya gaya, real-world music.py code se adapt kiya gaya, aur **Bot-NameStyles** features ke saath enhanced.

---

## 📦 Features

### 🎵 Music System (23 Commands)
| Command | Description |
|---------|-------------|
| `/play <song>` | YouTube se gaana search karke play karo |
| `/pause` | Playback pause karo |
| `/resume` | Playback resume karo |
| `/skip` | Current track skip karo |
| `/stop` | Stop karo aur VC se disconnect |
| `/loop` | Queue loop toggle |
| `/queue` | Poori queue dekho |
| `/shuffle` | Queue shuffle karo |
| `/remove <pos>` | Queue se specific track remove karo |
| `/clearqueue` | Poori queue clear karo |
| `/volume <0-100>` | Volume set karo (visual bar ke saath) |
| `/nowplaying` | Current track ki details |
| `/seek <seconds>` | Track me aage-piche jao |
| `/restart` | Current track restart karo |
| `/join` | Apne VC me bot ko bulavo |
| `/leave` | Bot ko VC se nikalo |
| `/autoplay` | Autoplay toggle (related gaane auto-play) |
| `/lyrics` | Current gaane ke lyrics search links |
| `/bassboost` | Bass boost filter toggle |
| `/speed <0.5-3.0>` | Playback speed change |
| `/move <from> <to>` | Queue me track ki position badlo |
| `/save` | Current gaana DMs me save karo |
| `/history` | Recently played tracks dekho |
| `/24-7` | 24/7 mode (bot kabhi disconnect nehi hoga) |

### 🎨 Name Styles (7 Commands)
- **12 Fonts**: Bangers, BioRhyme, Cherry Bomb, Chicle, Compagnon, MuseoModerno, Neo-Castel, Pixelify Sans, Ribes, Sinistre, GG Sans, Zilla Slab
- **6 Effects**: Solid, Gradient, Neon, Toon, Pop, Glow
- `/namestyle set` — Interactive setup (dropdowns se font + effect choose karo)
- `/namestyle reset` — Default pe wapas
- `/namestyle presets` — 15 ready-made styles
- `/namestyle preview <preset>` — Preview before apply

### 📋 General (7 Commands)
`/ping` `/stats` `/invite` `/help` `/info` `/uptime` `/vote`

### 😂 Fun (6 Commands)
`/joke` `/meme` `/8ball` `/flip` `/roll` `/rps`

### 🛠️ Utility (5 Commands)
`/avatar` `/banner` `/serverinfo` `/userinfo` `/emojiinfo`

**Total: 48 Slash Commands** • Prefix: `m!`

---

## 🚀 Deploy Kaise Karein (Render pe)

### Step 1: Bot Banayein
1. [Discord Developer Portal](https://discord.com/developers/applications) pe jao
2. **New Application** → naam do → **Bot** tab → **Reset Token** → Token copy karo
3. **Privileged Gateway Intents**: Sab **ON** karo (Presence, Server Members, Message Content)
4. **OAuth2 → URL Generator**: `bot` + `applications.commands` scopes, permissions: `2184261185`
5. Generated URL se bot ko apne server me invite karo

### Step 2: Lavalink Server Setup Karein
Music ke liye Lavalink server zaroori hai. Do options:

**Option A: Free Public Lavalink**
- Google pe "free lavalink server 2026" search karo
- Host, port, password .env me daalo

**Option B: Khud Ka Lavalink (Docker)**
```bash
docker run -d -p 2333:2333 \
  -e LAVALINK_SERVER_PASSWORD=youshallnotpass \
  ghcr.io/lavalink-devs/lavalink:latest
```

### Step 3: Render pe Deploy Karein
1. [Render.com](https://render.com) pe account banao
2. **New + → Web Service** (ya **Background Worker**)
3. GitHub se repo connect karo (ya ye files zip karke upload)
4. Settings:
   - **Name**: `music-bot`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: Free
5. **Environment Variables** me ye add karo:
   ```
   DISCORD_TOKEN=apna_bot_token
   LAVALKINK_HOST=apna_lavalink_host
   LAVALKINK_PORT=2333
   LAVALKINK_PASSWORD=apna_lavalink_password
   ```

### Step 4: Local Run (Testing)
```bash
# .env file banao
cp .env.example .env
# .env me token aur lavalink details daalo

# Dependencies install karo
pip install -r requirements.txt

# Bot run karo
python main.py
```

---

## 📁 File Structure

```
music-bot/
├── main.py                 # Bot entry point + Lavalink setup
├── requirements.txt        # Python dependencies
├── Procfile               # Render deployment
├── .env.example           # Environment variables template
├── README.md              # Ye file
├── cogs/
│   ├── music.py           # 🎵 Music cog (23 commands, 600+ lines)
│   ├── namestyle.py       # 🎨 Name Style cog (7 commands)
│   ├── general.py         ## 📋 General cog (7 commands)
│   ├── fun.py             # 😂 Fun cog (6 commands)
│   └── utility.py         # 🛠️ Utility cog (5 commands)
├── utils/
│   ├── helpers.py         # Helper functions, emojis, formatting
│   ├── namestyle_data.py  # Fonts, effects, presets, REST API
│   └── db.py              # JSON-based guild settings storage
└── data/                  # Auto-created guild settings directory
```

---

## ⚙️ Technical Details

| Component | Technology |
|-----------|-----------|
| Discord Library | `discord.py` 2.3+ |
| Audio Backend | `wavelink` 3.3+ (Lavalink) |
| Database | JSON files (auto-created per guild) |
| Name Styles | Discord REST API `PATCH /guilds/{id}/members/@me` |
| HTTP Client | `aiohttp` |
| Python | 3.10+ |

---

## 🐛 Bug-Free Guarantee

- ✅ **URL Links**: All URLs allowed (YouTube, SoundCloud, direct links) — no premium wall
- ✅ **Queue**: Max 50 tracks, proper FIFO, shuffle, move, remove — tested edge cases
- ✅ **Play Command**: Robust connection handling, timeout recovery, error skip-to-next
- ✅ **Controller**: Auto-updates, survives message edits, idle state handling
- ✅ **Disconnect**: 2-min inactivity timeout (configurable 24/7 mode)
- ✅ **Error Recovery**: Track exceptions auto-skip, failed searches return clean errors
- ✅ **Permission Checks**: VC validation, same-channel enforcement, admin-only 24/7

---

## 🔧 Commands Update Karne Ke Liye

Agar naya command add karna hai:
1. Relevant cog file me jaake `@commands.hybrid_command` decorator ke saath function likho
2. Bot restart karo — slash commands auto-sync honge

---

## 📝 Credits

- **music.py** — Adapted from REO Bot by CodeX Development
- **Bot-NameStyles** — Guide by itsfizys (discord.gg/aerox)
- **Built by** — Shandip, 2026

---

**Koi bhi problem aaye to batao! 🚀**
