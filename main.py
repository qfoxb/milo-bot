# Milobot, the Milohax Art Conversion bot
# Written by femou, qfoxb and glitchgod
# Copyright 2023

version = "2.0 Beta "

# Setting up logging
import logging
import logging.handlers

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.WARNING)
handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=1,
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Checking if we have the imports
import subprocess
import importlib
packages = ["discord.py", "python-dotenv", "requests", "python-magic", "python-magic-bin"]

for package in packages:
    try:
        importlib.import_module(package)
    except ImportError:
        subprocess.check_call(["pip", "install", package])
        
# Importing the rest
import discord
from discord.ext import commands
from dotenv import load_dotenv
import requests
import random
import asyncio
import magic
import os
import copy

# ENVs
load_dotenv()
TOKEN = os.getenv("TOKEN")
BOT_CHANNEL = int(os.getenv("CHANNEL_ID"))

# File Arguments
quotes_file = 'status_quotes.txt'
conversion_quotes_file = 'conversion_quotes.txt'
superfreq = "superfreq"
swap_bytes = "convert.py"
forgetool = "ForgeTool"

# Path Arguments
current_directory = os.path.dirname(os.path.abspath(__file__))
superfreq_path = os.path.join(current_directory, superfreq)
swap_bytes_path = os.path.join(current_directory, swap_bytes)
quotes_path = os.path.join(current_directory, quotes_file)
conversion_quotes_path = os.path.join(current_directory, conversion_quotes_file)
forgetool_path = os.path.join(current_directory, forgetool)

# Setting up discord
load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    if message.author == client.user:  
        return
    
    for mentions in message.mentions:
        if mentions == client.user:
            await message.channel.send(f'milo (and forge) harmonix. Running version {version}, '+' Ping: {0}ms\n'.format(round(client.latency * 1000, 1)))

    if message.channel.id != BOT_CHANNEL and message.guild:
        return
    
    if len(message.attachments) == 0:
        return
    elif len(message.attachments) > 1:
        message.channel.send("**I can only process 1 file at a time. The first file will be processed.**")


    file_url = str(message.attachments[0].url)
    file_url = file_url.split('?')[0]
    height = message.attachments[0].height
    width = message.attachments[0].width
    file_extension = copy.deepcopy(file_url) # Copy File URL to get the extension later

    file_format = None

    file_id = random.randrange(10000000000001)
    file_url_format = file_url.rpartition('.')[-1]
    file_path = f"./{file_id}.{file_url_format}"

    file = requests.get(file_url, allow_redirects=True)
    with open(file_path, "wb") as f:
            f.write(file.content)
            f.close()

    #Initialize the mess
    FileExtensionValue = 0
    ipodBMP = 0
    file_extension = file_extension[79:] # get file name

    #This blob is where platforms are sorted for tex2png
    if file_extension.find('_ps3') > -1:
        FileExtensionValue = file_extension.find('_ps3')
        file_format = 'ps3'
    elif file_extension.find('_xbox') > -1:
        FileExtensionValue = file_extension.find('_xbox')
        file_format = 'xbox'
    elif file_extension.find('_nx') > -1:
        FileExtensionValue = file_extension.find('_nx')
        file_format = 'nx'
    elif file_extension.find('_pc') > -1:
        ipodBMP = 1
        print(f'Treating _pc as _xbox')  
        FileExtensionValue = file_extension.find('_pc')
        file_format = 'xbox'
        FileExtensionValue = file_extension.find('png')
        if FileExtensionValue == -1:
            await message.channel.send("**bmp_pc is not supported by superfreq or ForgeTool.**")
            return

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
            try:
                os.remove(nx_path)
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
            try:
                os.remove(nx_path)
            except FileNotFoundError:
                await message.channel.send("**.png_ps3 file not found.**")
            return
        os.remove(ps3_path)
        os.remove(xbox_path)
        os.remove(file_path) # Cleanup



    ##########################################################################################################################################
    ### since i have redone the console checking system, the lines below with "{file_url[-8:]}" needs to be fixed as it might cause issues ###
    ##########################################################################################################################################

    elif file_format == 'xbox':
        # await message.channel.send("Using superfreq") # Redo this soon when a toggle is made for forge and milo
        file_path = str(f"./{file_id}.png")
        xbox_path = str(f"./{file_id}.{file_url[-8:]}")

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
                await message.channel.send("**The processed file could not be found, superfreq most likely failed to process the image.**")
        os.remove(xbox_path)
        os.remove(file_path) # Cleanup

    elif file_format == 'ps3':
        # await message.channel.send("Using superfreq") # Redo this soon when a toggle is made for forge and milo
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
                await message.channel.send("**The processed file could not be found, superfreq most likely failed to process the image.**")
        os.remove(ps3_path)
        os.remove(file_path) # Cleanup

    elif file_format == 'nx':
        # await message.channel.send("Using forgetool") # Redo this soon when a toggle is made for forge and milo
        file_path = str(f"./{file_id}.png")
        nx_path = str(f"./{file_id}.{file_url[-7:]}")

        nx = requests.get(file_url, allow_redirects=True)
        with open(nx_path, "wb") as f:
            f.write(nx.content)
        try:
            subprocess.run([forgetool_path, "tex2png", nx_path, file_path])
            await message.channel.send(file=discord.File(file_path))
        except FileNotFoundError:
            await message.channel.send("**Error: The processed file could not be found, superfreq most likely failed to process the image.**")
            try:
                os.remove(nx_path)
            except FileNotFoundError:
                await message.channel.send("**Could not find the original file while trying to delete it.**")
            return
        except Exception as error: 
            await message.channel.send(f"**An error occured.\n**{error}")
            try:
                os.remove(nx_path)
            except FileNotFoundError:
                await message.channel.send("**Could not find the original file while trying to delete it.**")
                return
            try:
                os.remove(file_path)
            except FileNotFoundError:
                await message.channel.send("**The processed file could not be found, superfreq most likely failed to process the image.**")
        os.remove(nx_path)
        os.remove(file_path) # Cleanup


    elif file_format == None:
        await message.channel.send('**An unexpected error happened with the file format.**')
        return

client.run(TOKEN) 
