# Milohax Art Conversion bot written by femou and qfoxb. (c) 2023

version = "1.92"

import sys
if (sys.version).split(" ")[0] == "3.12.0":
    print("This version of Python is unsupported. Please revert to 3.11")
    sys.exit()

import os
import subprocess
packages = ["discord.py", "python-dotenv", "requests", "python-magic"]

for package in packages:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call(["pip", "install", package])
import discord
from dotenv import load_dotenv
import requests
import random
import asyncio
import magic

async def update_check():
    while True:
        latestver = requests.get('https://github.com/qfoxb/mhx-bot/raw/main/latest.version', allow_redirects=True)
        with open("latest.version", "wb") as f:
            f.write(latestver.content)
            f.close()
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
                await message.channel.send(f'milo harmonix. Running version {version}, '+' Ping: {0}ms\n'.format(round(client.latency * 1000, 1))+'The bot version seems to be ahead of the latest release. This could be a bug.')
            else:
                await message.channel.send(f'milo harmonix. Running version {version}, '+' Ping: {0}ms\n'.format(round(client.latency * 1000, 1))+f'*An update is available! Latest version: {latestver}*')

    if message.channel.id != bot_channel and message.guild:
        return
    
    if len(message.attachments) == 0:
        return

    file_url = str(message.attachments[0].url)
    file_url = file_url.split('?')[0]
    height = message.attachments[0].height
    width = message.attachments[0].width

    #print(bin(height)+" "+bin(width)+" "+file_url[-4:])
    
    file_format = None

    file_id = random.randrange(10000000000001)
    file_url_format = file_url.rpartition('.')[-1]
    file_path = f"./{file_id}.{file_url_format}"

    file = requests.get(file_url, allow_redirects=True)
    with open(file_path, "wb") as f:
            f.write(file.content)
            f.close()

    #print(magic.from_file(file_path, mime=True))

    if file_url[-9:] == '.png_xbox' or file_url[-9:] == '.bmp_xbox':
        file_format = 'xbox'
    elif file_url[-8:] == '.png_ps3' or file_url[-8:] == '.bmp_ps3':
        file_format = 'ps3'
    elif magic.from_file(file_path, mime=True) == "image/jpeg" or magic.from_file(file_path, mime=True) == "image/png" or magic.from_file(file_path, mime=True) == "image/webp":
        if bin(height).count("1") != 1:
            await message.channel.send('Invalid image size, the height and width must be a power of 2 (256, 512, etc.)')
            os.remove(file_path)
            return
        if height < 4:
            await message.channel.send('Please input a larger image.')
            os.remove(file_path)
            return 
        if bin(width).count("1") != 1:
            await message.channel.send('Invalid image size, the height and width must be a power of 2 (256, 512, etc.)')
            os.remove(file_path)
            return
        if width < 4:
            await message.channel.send('Please input a larger image.')
            os.remove(file_path)
            return 
        file_format = 'png'
    else:
        await message.channel.send('Could not find a valid file to format.')
        os.remove(file_path)
        return

    os.chdir(current_directory)
    
    line = random.choice(open(conversion_quotes_path).readlines())

    await message.channel.send(f'{line}')

    if file_format == 'png':
        xbox_path = f"./{file_id}.png_xbox"
        ps3_path = f"./{file_id}.png_ps3"

        try:
            subprocess.run([superfreq_path, "png2tex", file_path, xbox_path, "--platform", "x360", "--miloVersion", "26"])
            subprocess.run([f"python", swap_bytes_path, xbox_path, ps3_path])
            await message.channel.send(file=discord.File(xbox_path))
            await message.channel.send(file=discord.File(ps3_path))
        except FileNotFoundError:
            await message.channel.send("**Error: One of the processed file could not be found, superfreq most likely failed to process the image.**")
            try:
                os.remove(file_path)
            except FileNotFoundError:
                await message.channel.send("**Could not find the original file while trying to delete it.**")
                return # Under this scenario it's extremly likely that xbox and ps3 file were not created, so it's not worth checking and potentially clogging chat with errors.
            try:
                os.remove(xbox_path)
            except FileNotFoundError:
                await message.channel.send("**.png_xbox file not found.**")
            try:
                os.remove(ps3_path)
            except FileNotFoundError:
                await message.channel.send("**.png_ps3 file not found.**")
            return
        except Exception as error: 
            await message.channel.send(f"**An error occured. {error}**")
            try:
                os.remove(file_path)
            except FileNotFoundError:
                await message.channel.send("**Could not find the original file while trying to delete it.**")
                return # See line 140
            try:
                os.remove(xbox_path)
            except FileNotFoundError:
                await message.channel.send("**.png_xbox file not found.**")
            try:
                os.remove(ps3_path)
            except FileNotFoundError:
                await message.channel.send("**.png_ps3 file not found.**")
            return
        os.remove(ps3_path)
        os.remove(xbox_path)
        os.remove(file_path) # Cleanup

    elif file_format == 'xbox':
        file_path = str(f"./{file_id}.png")
        
        xbox_path = str(f"./{file_id}.{file_url[-8:]}") #Using file_url[-8:] is not a good idea if any other formatting gets added. Updating the method to get file format/name should be considered.

        xbox = requests.get(file_url, allow_redirects=True)
        with open(xbox_path, "wb") as f:
            f.write(xbox.content)
        try:
            subprocess.run([superfreq_path, "tex2png", xbox_path, file_path, "--platform", "x360", "--miloVersion", "26"])
            await message.channel.send(file=discord.File(file_path))
        except FileNotFoundError:
            await message.channel.send("**Error: The processed file could not be found, superfreq most likely failed to process the image.**")
            try:
                os.remove(xbox_path)
            except FileNotFoundError:
                await message.channel.send("**Could not find the original file while trying to delete it.**")
            return
        except Exception as error: 
            await message.channel.send(f"**An error occured.\n**{error}")
            try:
                os.remove(xbox_path)
            except FileNotFoundError:
                await message.channel.send("**Could not find the original file while trying to delete it.**")
                return
            try:
                os.remove(file_path)
            except FileNotFoundError:
                await message.channel.send("**The processed file could not be found, superfreq most likely also failed to process the image.**")
        os.remove(xbox_path)
        os.remove(file_path) # Cleanup

    elif file_format == 'ps3':
        file_path = str(f"./{file_id}.png")
        ps3_path = str(f"./{file_id}.{file_url[-7:]}")

        ps3 = requests.get(file_url, allow_redirects=True)
        with open(ps3_path, "wb") as f:
            f.write(ps3.content)
        try:
            subprocess.run([superfreq_path, "tex2png", ps3_path, file_path, "--platform", "ps3", "--miloVersion", "26"])
            await message.channel.send(file=discord.File(file_path))
        except FileNotFoundError:
            await message.channel.send("**Error: The processed file could not be found, superfreq most likely failed to process the image.**")
            try:
                os.remove(ps3_path)
            except FileNotFoundError:
                await message.channel.send("**Could not find the original file while trying to delete it.**")
            return
        except Exception as error: 
            await message.channel.send(f"**An error occured.**\n{error}")
            try:
                os.remove(ps3_path)
            except FileNotFoundError:
                await message.channel.send("**Could not find the original file while trying to delete it.**")
                return
            try:
                os.remove(file_path)
            except FileNotFoundError:
                await message.channel.send("**The processed file could not be found, superfreq most likely also failed to process the image.**")
        os.remove(ps3_path)
        os.remove(file_path) # Cleanup

    elif file_format == None:
        await message.channel.send('**An unexpected error happened with the file format.**')
        return

client.run(TOKEN) 
