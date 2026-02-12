import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

user_chats = {}

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online and ready to chat!')

@bot.event
async def on_message(message):
   
    if message.author == bot.user:
        return
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    async with message.channel.typing():
        try:
            user_id = message.author.id
            user_input = message.content

          
            if user_id not in user_chats:
                user_chats[user_id] = model.start_chat(history=[])
            
            chat_session = user_chats[user_id]

           
            response = await chat_session.send_message_async(user_input)
            response_text = response.text

          
            if len(response_text) > 2000:
              
                for i in range(0, len(response_text), 2000):
                    await message.channel.send(response_text[i:i+2000])
            else:
                await message.channel.send(response_text)

        except Exception as e:
            print(f"Error: {e}")
            await message.channel.send("I encountered an error processing that request.")


@bot.command()
async def reset(ctx):
    if ctx.author.id in user_chats:
        del user_chats[ctx.author.id]
        await ctx.send("🧠 Memory cleared! Starting a fresh conversation.")
    else:
        await ctx.send("No active conversation to clear.")


bot.run(DISCORD_TOKEN)
