# Milohax Art Conversion bot written by femou and qfoxb. (c) 2023

version = "1.6"

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

async def update_check():
    while True:
        latestver = requests.get('https://github.com/qfoxb/mhx-bot/raw/main/latest.version', allow_redirects=True)
        with open("latest.version", "wb") as f:
            f.write(latestver.content)
        await asyncio.sleep(10800) # 3 Hours

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

@client.event
async def on_ready():
    print(f'Bot has logged in as {client.user}.')
    client.loop.create_task(status_task())
    client.loop.create_task(update_check())

@client.event
async def on_message(message):
    if message.author == client.user:  
        return
    
    for mentions in message.mentions:
        if mentions == client.user:
            # Checking version
            latestver = open('latest.version').read()
            if version == latestver:
                await message.channel.send(f'milo harmonix. Running version {version}, '+' Ping: {0}ms\n'.format(round(client.latency * 1000, 1)))
            elif version > latestver:
                await message.channel.send(f'milo harmonix. Running version {version}, '+' Ping: {0}ms\n'.format(round(client.latency * 1000, 1))+'The bot version is incorrect, please ping the devs to fix this.')
            else:
                await message.channel.send(f'milo harmonix. Running version {version}, '+' Ping: {0}ms\n'.format(round(client.latency * 1000, 1))+f'*An update is available! Latest version: {latestver}*')

    if message.channel.id != bot_channel and message.guild:
        return
    
    if len(message.attachments) == 0:
        if message.content == "$ff" or message.content == "$fileformat":
            await message.channel.send('File formats supported:\n`.png` -> `.png_xbox` & `.png_ps3`\n`.png_xbox`, `.bmp_xbox` or `.png_ps3` -> `.png`')
            return
        return

    file_url = message.attachments[0].url
    height = message.attachments[0].height
    width = message.attachments[0].width

    #print(bin(height)+" "+bin(width)+" "+file_url[-4:])
    
    file_format = None

    if file_url[-4:] == '.png':
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
        file_format = 'png'
    elif file_url[-9:] == '.png_xbox' or file_url[-9:] == '.bmp_xbox':
        file_format = 'xbox'
    elif file_url[-8:] == '.png_ps3' or file_url[-8:] == '.bmp_ps3':
        file_format = 'ps3'
    else:
        await message.channel.send('Invalid file format submitted. Run $ff to see the file format currently supported.')
        return

    os.chdir(current_directory)
    
    line = random.choice(open(conversion_quotes_path).readlines())
    file_id = random.randrange(10000000000001)

    await message.channel.send(f'{line}')

    if file_format == 'png':
        file_path = f"./{file_id}.png"
        xbox_path = f"./{file_id}.png_xbox"
        ps3_path = f"./{file_id}.png_ps3"

        file = requests.get(file_url, allow_redirects=True)
        with open(file_path, "wb") as f:
            f.write(file.content)
        subprocess.run([superfreq_path, "png2tex", file_path, xbox_path, "--platform", "x360", "--miloVersion", "26"])
        subprocess.run([f"python", swap_bytes_path, xbox_path, ps3_path])
        await message.channel.send(file=discord.File(xbox_path))
        await message.channel.send(file=discord.File(ps3_path))
        os.remove(ps3_path)
        os.remove(xbox_path)
        os.remove(file_path) # Cleanup

    elif file_format == 'xbox':
        file_path = str(f"./{file_id}.png")
        
        xbox_path = str(f"./{file_id}.{file_url[-8:]}") #Using file_url[-8:] is not a good idea if any other formatting gets added. Updating the method to get file format/name should be considered.

        xbox = requests.get(file_url, allow_redirects=True)
        with open(xbox_path, "wb") as f:
            f.write(xbox.content)
        subprocess.run([superfreq_path, "tex2png", xbox_path, file_path, "--platform", "x360", "--miloVersion", "26"])
        await message.channel.send(file=discord.File(file_path))
        os.remove(xbox_path)
        os.remove(file_path) # Cleanup

    elif file_format == 'ps3':
        file_path = str(f"./{file_id}.png")
        ps3_path = str(f"./{file_id}.{file_url[-7:]}")

        ps3 = requests.get(file_url, allow_redirects=True)
        with open(ps3_path, "wb") as f:
            f.write(ps3.content)
        subprocess.run([superfreq_path, "tex2png", ps3_path, file_path, "--platform", "ps3", "--miloVersion", "26"])
        await message.channel.send(file=discord.File(file_path))
        os.remove(ps3_path)
        os.remove(file_path) # Cleanup

    elif file_format == None:
        await message.channel.send('**An unexpected error happened with the file format.**')
        return

client.run(TOKEN) 
