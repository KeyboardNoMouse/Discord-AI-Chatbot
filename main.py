import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_chats = {}


def split_message(text, limit=2000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]


@bot.event
async def on_ready():
    print(f"{bot.user} is online")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    async with message.channel.typing():
        try:
            user_id = message.author.id
            user_input = message.content

            if user_id not in user_chats:
                user_chats[user_id] = model.start_chat(history=[])

            chat = user_chats[user_id]

            response = await chat.send_message_async(user_input)
            text = response.text

            for chunk in split_message(text):
                await message.channel.send(chunk)

        except Exception as e:
            print(e)
            await message.channel.send("⚠️ Something went wrong.")


@bot.command()
async def reset(ctx):
    user_chats.pop(ctx.author.id, None)
    await ctx.send("🧠 Memory cleared.")


@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency*1000)}ms")


bot.run(DISCORD_TOKEN)
