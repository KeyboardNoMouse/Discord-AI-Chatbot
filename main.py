import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import aiohttp

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_IDS = set(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else set()
MEMORY_FILE = "sky_memory.json"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

DEFAULT_SYSTEM_PROMPT = (
    "You are Sky, a helpful, friendly, and witty Discord bot assistant. "
    "Keep responses concise and conversational unless the user needs detail. "
    "You can analyze images, answer questions, and remember the conversation context."
)

# ── State ──────────────────────────────────────────────────────────────────────

user_chats: dict[int, genai.ChatSession] = {}
user_message_counts: dict[int, int] = {}
system_prompt: str = DEFAULT_SYSTEM_PROMPT
bot_start_time = datetime.utcnow()

def load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_memory(data: dict):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

persistent_memory: dict = load_memory()

# ── Helpers ────────────────────────────────────────────────────────────────────

def split_message(text: str, limit: int = 2000) -> list[str]:
    return [text[i:i+limit] for i in range(0, len(text), limit)]

def get_chat(user_id: int) -> genai.ChatSession:
    if user_id not in user_chats:
        history = persistent_memory.get(str(user_id), {}).get("history", [])
        formatted = []
        for entry in history[-20:]:  # Load last 20 turns max
            formatted.append({"role": entry["role"], "parts": [entry["text"]]})
        user_chats[user_id] = model.start_chat(history=formatted)
    return user_chats[user_id]

def record_message(user_id: int, role: str, text: str):
    key = str(user_id)
    if key not in persistent_memory:
        persistent_memory[key] = {"history": []}
    persistent_memory[key]["history"].append({
        "role": role,
        "text": text,
        "ts": datetime.utcnow().isoformat()
    })
    # Keep only last 100 turns per user
    persistent_memory[key]["history"] = persistent_memory[key]["history"][-100:]
    save_memory(persistent_memory)
    user_message_counts[user_id] = user_message_counts.get(user_id, 0) + 1

async def download_image(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ── Bot setup ──────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # slash command tree

# ── Events ─────────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ {bot.user} is online | Slash commands synced")
    print(f"   Admins: {ADMIN_IDS or 'none configured'}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    async with message.channel.typing():
        try:
            user_id = message.author.id
            chat = get_chat(user_id)

            # Build the prompt parts
            parts = []

            # Include system prompt on first message
            if user_message_counts.get(user_id, 0) == 0:
                parts.append(f"[System: {system_prompt}]\n\n")

            # Handle image attachments
            image_parts = []
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext)
                       for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp")):
                    img_bytes = await download_image(attachment.url)
                    image_parts.append({
                        "mime_type": "image/png",
                        "data": img_bytes
                    })

            user_text = message.content or "(no text)"
            parts.append(user_text)

            # If images present, use generate_content (vision) instead of chat
            if image_parts:
                vision_model = genai.GenerativeModel("gemini-2.5-flash")
                prompt_parts = image_parts + [user_text]
                response = await asyncio.to_thread(
                    vision_model.generate_content, prompt_parts
                )
                text = response.text
            else:
                response = await chat.send_message_async("".join(parts))
                text = response.text

            record_message(user_id, "user", user_text)
            record_message(user_id, "model", text)

            for chunk in split_message(text):
                await message.channel.send(chunk)

        except Exception as e:
            print(f"[on_message error] {e}")
            await message.channel.send("⚠️ Something went wrong. Try again or use `!reset`.")

# ── Prefix commands ─────────────────────────────────────────────────────────────

@bot.command(name="reset", help="Clear your conversation memory with Sky.")
async def reset(ctx: commands.Context):
    user_chats.pop(ctx.author.id, None)
    key = str(ctx.author.id)
    if key in persistent_memory:
        persistent_memory[key]["history"] = []
        save_memory(persistent_memory)
    await ctx.send("🧠 Memory cleared. Fresh start!")

@bot.command(name="ping", help="Check Sky's latency.")
async def ping(ctx: commands.Context):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

@bot.command(name="summarize", help="Summarize your conversation so far.")
async def summarize(ctx: commands.Context):
    key = str(ctx.author.id)
    history = persistent_memory.get(key, {}).get("history", [])
    if not history:
        await ctx.send("📭 No conversation history to summarize yet.")
        return
    async with ctx.typing():
        try:
            convo_text = "\n".join(
                f"{e['role'].capitalize()}: {e['text']}" for e in history[-30:]
            )
            prompt = f"Summarize this conversation briefly in 3-5 bullet points:\n\n{convo_text}"
            response = await asyncio.to_thread(model.generate_content, prompt)
            await ctx.send(f"📋 **Conversation Summary**\n{response.text}")
        except Exception as e:
            print(f"[summarize error] {e}")
            await ctx.send("⚠️ Couldn't summarize right now.")

@bot.command(name="history", help="Show how many messages you've sent.")
async def history_cmd(ctx: commands.Context):
    key = str(ctx.author.id)
    count = len(persistent_memory.get(key, {}).get("history", []))
    await ctx.send(f"💬 You have **{count}** messages in your history with Sky.")

@bot.command(name="skyhelp", help="Show all Sky commands.")
async def sky_help(ctx: commands.Context):
    embed = discord.Embed(
        title="🌌 Sky — Command Reference",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Chat", value="Just type normally to chat with Sky.", inline=False)
    embed.add_field(name="Images", value="Attach an image and type your question.", inline=False)
    embed.add_field(
        name="Prefix commands",
        value=(
            "`!reset` — Clear your memory\n"
            "`!summarize` — Summarize your chat\n"
            "`!history` — Message count\n"
            "`!ping` — Latency check\n"
            "`!skyhelp` — This menu"
        ),
        inline=False
    )
    embed.add_field(
        name="Slash commands",
        value=(
            "`/ask` — Ask Sky anything\n"
            "`/reset` — Clear your memory\n"
            "`/ping` — Latency check\n"
            "`/summarize` — Summarize chat"
        ),
        inline=False
    )
    if is_admin(ctx.author.id):
        embed.add_field(
            name="🔐 Admin commands",
            value=(
                "`!status` — Bot stats\n"
                "`!resetall` — Reset all users\n"
                "`!skysetprompt <text>` — Set system prompt"
            ),
            inline=False
        )
    embed.set_footer(text="Sky Bot • Powered by Gemini 2.5 Flash")
    await ctx.send(embed=embed)

# ── Admin commands ─────────────────────────────────────────────────────────────

@bot.command(name="status", help="[Admin] Show bot statistics.")
async def status(ctx: commands.Context):
    if not is_admin(ctx.author.id):
        await ctx.send("🔒 Admin only.")
        return
    uptime = datetime.utcnow() - bot_start_time
    hours, rem = divmod(int(uptime.total_seconds()), 3600)
    mins = rem // 60
    total_users = len(persistent_memory)
    total_msgs = sum(
        len(v.get("history", [])) for v in persistent_memory.values()
    )
    embed = discord.Embed(title="📊 Sky Bot Status", color=discord.Color.green())
    embed.add_field(name="Uptime", value=f"{hours}h {mins}m")
    embed.add_field(name="Active sessions", value=str(len(user_chats)))
    embed.add_field(name="Total users (memory)", value=str(total_users))
    embed.add_field(name="Total messages", value=str(total_msgs))
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms")
    embed.add_field(name="System prompt", value=system_prompt[:200] + ("…" if len(system_prompt) > 200 else ""), inline=False)
    await ctx.send(embed=embed)

@bot.command(name="resetall", help="[Admin] Reset all user memories.")
async def resetall(ctx: commands.Context):
    if not is_admin(ctx.author.id):
        await ctx.send("🔒 Admin only.")
        return
    user_chats.clear()
    persistent_memory.clear()
    save_memory(persistent_memory)
    await ctx.send(f"🗑️ All user memories cleared by {ctx.author.mention}.")

@bot.command(name="skysetprompt", help="[Admin] Set Sky's system prompt.")
async def skysetprompt(ctx: commands.Context, *, prompt: str):
    global system_prompt
    if not is_admin(ctx.author.id):
        await ctx.send("🔒 Admin only.")
        return
    system_prompt = prompt
    user_chats.clear()  # Reset sessions so new prompt takes effect
    await ctx.send(f"✅ System prompt updated. All sessions reset.\n```{prompt[:300]}```")

# ── Slash commands ─────────────────────────────────────────────────────────────

@tree.command(name="ping", description="Check Sky's latency.")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

@tree.command(name="reset", description="Clear your conversation memory with Sky.")
async def slash_reset(interaction: discord.Interaction):
    user_chats.pop(interaction.user.id, None)
    key = str(interaction.user.id)
    if key in persistent_memory:
        persistent_memory[key]["history"] = []
        save_memory(persistent_memory)
    await interaction.response.send_message("🧠 Memory cleared. Fresh start!", ephemeral=True)

@tree.command(name="ask", description="Ask Sky a question.")
@app_commands.describe(question="What do you want to ask?")
async def slash_ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    try:
        user_id = interaction.user.id
        chat = get_chat(user_id)
        prefix = f"[System: {system_prompt}]\n\n" if user_message_counts.get(user_id, 0) == 0 else ""
        response = await chat.send_message_async(prefix + question)
        text = response.text
        record_message(user_id, "user", question)
        record_message(user_id, "model", text)
        chunks = split_message(f"**You asked:** {question}\n\n{text}")
        await interaction.followup.send(chunks[0])
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)
    except Exception as e:
        print(f"[slash_ask error] {e}")
        await interaction.followup.send("⚠️ Something went wrong.")

@tree.command(name="summarize", description="Summarize your conversation with Sky.")
async def slash_summarize(interaction: discord.Interaction):
    key = str(interaction.user.id)
    history = persistent_memory.get(key, {}).get("history", [])
    if not history:
        await interaction.response.send_message("📭 No conversation history yet.", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        convo_text = "\n".join(
            f"{e['role'].capitalize()}: {e['text']}" for e in history[-30:]
        )
        prompt = f"Summarize this conversation briefly in 3-5 bullet points:\n\n{convo_text}"
        response = await asyncio.to_thread(model.generate_content, prompt)
        await interaction.followup.send(f"📋 **Conversation Summary**\n{response.text}")
    except Exception as e:
        print(f"[slash_summarize error] {e}")
        await interaction.followup.send("⚠️ Couldn't summarize right now.")

# ── Run ────────────────────────────────────────────────────────────────────────

bot.run(DISCORD_TOKEN)
