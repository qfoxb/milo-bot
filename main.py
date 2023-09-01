# Milohax Art Swap bot written by femou and qfoxb. (c) 2023
import os
import subprocess

packages = ["discord", "python-dotenv", "requests"]

for package in packages:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call(["pip", "install", package])
import discord
import logging
from dotenv import load_dotenv
import requests
import random
import asyncio

load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
current_directory = os.path.dirname(os.path.abspath(__file__))

# Arguments
bot_channel = int(os.getenv("CHANNEL_ID"))
quotes_file = 'status_quotes.txt'
conversion_quotes_file = 'conversion_quotes.txt'
superfreq = "superfreq"
swap_bytes = "convert.py"
superfreq_path = os.path.join(current_directory, superfreq)
swap_bytes_path = os.path.join(current_directory, swap_bytes)

quotes_path = os.path.join(current_directory, quotes_file)
conversion_quotes_path = os.path.join(current_directory, conversion_quotes_file)
client = discord.Client(intents=intents)
async def status_task():
    while True:
        random_status = random.choice(open(quotes_path).readlines())
        await client.change_presence(activity=discord.Game(name=random_status))
        await asyncio.sleep(60)
        random_status = random.choice(open(quotes_path).readlines())
        await client.change_presence(activity=discord.Game(name=random_status))
        await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f'Bot has logged in as {client.user}.')
    client.loop.create_task(status_task())
@client.event
async def on_message(message):
    if message.author == client.user:  
        return
    
    for mentions in message.mentions:
        if mentions == client.user:
            await message.channel.send('milo harmonix')
        
    if message.channel.id != bot_channel and message.guild:
        return
    
    if len(message.attachments) == 0:
        return

    image_url = message.attachments[0].url
    height = message.attachments[0].height
    width = message.attachments[0].width
    #print(bin(height)+" "+bin(width)+" "+image_url[-4:])
    if bin(height).count("1") != 1:
        await message.channel.send('Invalid image size, the height and width must be a power of 2 (256, 512, etc.)')
        return
    if height < 4:
        await message.channel.send('Please input a larger image.')
        return 
    if bin(width).count("1") != 1:
        await message.channel.send('Invalid image size, the height and width must be a power of 2 (256, 512, etc.)')
        return
    if width < 4:
        await message.channel.send('Please input a larger image.')
        return 
    if image_url[-4:] != '.png':
        await message.channel.send('Invalid image format, the image must be a PNG.')
        return
    os.chdir(current_directory)
    
    line = random.choice(open(conversion_quotes_path).readlines())
    image_id = random.randrange(10000000000001)
    image_path = f"{image_id}.png"
    xbox_path = f"{image_id}.png_xbox"
    ps3_path = f"{image_id}.png_ps3"

    await message.channel.send(f'{line}')
    image = requests.get(image_url, allow_redirects=True)

    with open(image_path, "wb") as f:
        f.write(image.content)
    subprocess.run([superfreq_path, "png2tex", image_path, xbox_path, "--platform", "x360", "--miloVersion", "26"])
    subprocess.run([f"python", swap_bytes_path, xbox_path, ps3_path])
    await message.channel.send(file=discord.File(xbox_path))
    await message.channel.send(file=discord.File(ps3_path))
    os.remove(f"./{image_id}.png_xbox")
    os.remove(f"./{image_id}.png_ps3")
    os.remove(f"./{image_id}.png") # Cleanup

client.run(TOKEN) 
