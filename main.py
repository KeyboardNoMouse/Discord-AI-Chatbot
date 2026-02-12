import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Load Environment Variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 2. Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 3. Setup Discord Intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to store conversation history per user
# Structure: {user_id: ChatSessionObject}
user_chats = {}

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online and ready to chat!')

@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # OPTIONAL: Only reply if the bot is mentioned or in a specific channel
    # if bot.user not in message.mentions:
    #     return

    # Check if the message is a command (starts with !)
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return

    # --- CHATBOT LOGIC ---
    async with message.channel.typing():
        try:
            user_id = message.author.id
            user_input = message.content

            # A. Retrieve or create a chat session for this user
            if user_id not in user_chats:
                user_chats[user_id] = model.start_chat(history=[])
            
            chat_session = user_chats[user_id]

            # B. Generate Response
            response = await chat_session.send_message_async(user_input)
            response_text = response.text

            # C. Handle Discord's 2000 Character Limit
            if len(response_text) > 2000:
                # Split text into chunks of 2000 characters
                for i in range(0, len(response_text), 2000):
                    await message.channel.send(response_text[i:i+2000])
            else:
                await message.channel.send(response_text)

        except Exception as e:
            print(f"Error: {e}")
            await message.channel.send("I encountered an error processing that request.")

# Add a reset command to clear history
@bot.command()
async def reset(ctx):
    if ctx.author.id in user_chats:
        del user_chats[ctx.author.id]
        await ctx.send("🧠 Memory cleared! Starting a fresh conversation.")
    else:
        await ctx.send("No active conversation to clear.")

bot.run(DISCORD_TOKEN)