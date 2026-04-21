# 🌌 Sky — Discord AI Bot

Sky is a smart Discord bot powered by **Gemini 2.5 Flash**. It supports multi-turn conversations, image analysis, slash commands, persistent memory, and admin controls.

---

## 🚀 Setup

### 1. Clone / extract the files
Place `sky_bot.py`, `requirements.txt`, and `.env` in the same folder.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file
```env
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
ADMIN_IDS=123456789,987654321
```
- Get your Discord token from the [Discord Developer Portal](https://discord.com/developers/applications)
- Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/)
- `ADMIN_IDS` is a comma-separated list of Discord user IDs who can use admin commands (optional)

### 4. Enable Discord Intents
In the Developer Portal → your app → **Bot** tab:
- Enable **Message Content Intent**
- Enable **Server Members Intent** (optional)

### 5. Run the bot
```bash
python sky_bot.py
```

---

## 💬 Commands

### User commands

| Command | Type | Description |
|---|---|---|
| (just type) | Chat | Talk to Sky naturally |
| (attach image) | Chat | Analyze an image with a question |
| `!reset` | Prefix | Clear your conversation memory |
| `!summarize` | Prefix | Summarize your conversation |
| `!history` | Prefix | Show your message count |
| `!ping` | Prefix | Check bot latency |
| `!skyhelp` | Prefix | Show full help menu |
| `/ask` | Slash | Ask Sky a question |
| `/reset` | Slash | Clear your memory |
| `/summarize` | Slash | Summarize your chat |
| `/ping` | Slash | Check bot latency |

### Admin commands (requires `ADMIN_IDS` in `.env`)

| Command | Description |
|---|---|
| `!status` | Show bot stats (uptime, users, messages) |
| `!resetall` | Wipe all user memories |
| `!skysetprompt <text>` | Change Sky's system prompt live |

---

## 🖼️ Image Analysis

Simply attach a **PNG, JPG, JPEG, GIF, or WEBP** image to your message and ask a question. Sky will use Gemini Vision to analyze it automatically.

**Example:**
> *[attaches a photo of food]* "What dish is this and how do I make it?"

---

## 🧠 Persistent Memory

Conversations are saved to `sky_memory.json` in the same directory. This means:
- Sky remembers context across bot restarts
- The last **100 turns** per user are stored
- Use `!reset` to clear your own history
- Admins can use `!resetall` to wipe everything

---

## ⚙️ Configuration

You can customize Sky's personality by editing `DEFAULT_SYSTEM_PROMPT` in `sky_bot.py`, or change it live as an admin with:
```
!skysetprompt You are Sky, a sarcastic but helpful assistant...
```

---

## 📁 File Structure

```
sky_bot/
├── sky_bot.py          # Main bot code
├── requirements.txt    # Python dependencies
├── .env                # Your secrets (never share this!)
├── sky_memory.json     # Auto-created on first run
└── README.md           # This file
```

---

## 🛠️ Requirements

- Python 3.10+
- discord.py 2.3+
- google-generativeai 0.7+
- aiohttp 3.9+

---

## 📝 License

Free to use and modify for personal and educational projects.
