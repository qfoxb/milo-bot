# Milobot, the Milohax Art Conversion bot
# Written by femou, qfoxb and glitchgod
# Copyright 2023

__version__ = "2.1"


# ENVs
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")
BOT_CHANNEL = int(os.getenv("CHANNEL_ID"))
LOG_LEVEL = os.getenv("LOG_LEVEL")

# Setting up logging
import logging
import logging.handlers
from colorlog import ColoredFormatter

logformat = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(logformat)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
log = logging.getLogger('discord')
log.setLevel(LOG_LEVEL)
log.addHandler(stream)

log.info("Logging started!")

# Checking versions
beta = "false" # set beta to False -  will be overwritten if it is actually beta
from packaging import version
import requests

GitVersion = requests.get(
    'https://github.com/qfoxb/milo-bot/raw/main/latest.version',
    allow_redirects=True
    )

if version.parse(__version__) > version.parse(GitVersion.content.decode("utf-8")):
    log.warning("Beta version. Things may be unstable.")
    beta = "true"

elif version.parse(__version__) == version.parse(GitVersion.content.decode("utf-8")):
    log.info("Running latest.")
    
elif version.parse(__version__) < version.parse(GitVersion.content.decode("utf-8")):
    log.critical("An update is available. Please update to the latest version.")
        
# Importing the rest
import subprocess
import discord
from discord.ext import commands
import random
import magic
from glob import glob
import sys
import asyncio
import zipfile
import shutil

# File Arguments
quotes_file = 'status_quotes.txt'
conversion_quotes_file = 'conversion_quotes.txt'
superfreq = "superfreq"
swap_bytes = "convert.py"
forgetool = "ForgeTool.exe"
supportedFormats = ["image/jpeg", "image/png", "image/webp"]
if sys.platform.startswith("win"):
    python = "python"
else:
    python = "python3"

# Path Arguments
current_directory = os.path.dirname(os.path.abspath(__file__))
superfreq_path = os.path.join(current_directory, superfreq)
swap_bytes_path = os.path.join(current_directory, swap_bytes)
quotes_path = os.path.join(current_directory, quotes_file)
conversion_quotes_path = os.path.join(current_directory, conversion_quotes_file)
forgetool_path = os.path.join(current_directory, forgetool)

# Checking files

if not glob('superfreq*'):
    if sys.platform.startswith('win'):
        log.warning("Superfreq not found. Downloading Mackiloha.")

        try:
            Mackiloha = requests.get(
            'https://github.com/PikminGuts92/Mackiloha/releases/download/v1.2.0/Mackiloha_v1.2.0-win-x64.zip',
            allow_redirects=True
            )
        except Exception:
            log.critical("Failed to download superfreq. Exiting.")
            sys.exit()
        Mackiloha.filepath = os.path.join(current_directory, "mackiloha.zip")
        Mackiloha.folderpath = os.path.join(current_directory, "mackiloha")
        print(Mackiloha.folderpath+"\\superfreq*")
        with open(Mackiloha.filepath,"wb") as f:
            f.write(Mackiloha.content)
            f.close()

        with zipfile.ZipFile(Mackiloha.filepath, "r") as zip:
            zip.extractall(Mackiloha.folderpath)
        superfreq_folderpath = glob(Mackiloha.folderpath+"\\superfreq*")[0]
        os.rename(superfreq_folderpath, superfreq_path)
        shutil.rmtree(Mackiloha.folderpath)
        os.remove(Mackiloha.filepath)
        log.warning("Superfreq installed.")
    else:
        log.critical("Superfreq not found. Please download at https://github.com/PikminGuts92/Mackiloha/releases/")
        log.critical("Exiting.")
        sys.exit()

if not glob('forgetool*'):
    log.critical("ForgeTool not found! Forge support will be disabled.")
    isForgeEnabled = False
else:
    forgeFileList = []
    forgeFileMissing = False
    if not glob('LibForge*'):
        forgeFileMissing = True
        forgeFileList.append("LibForge")
    if not glob('MidiCS*'):
        forgeFileMissing = True
        forgeFileList.append("MidiCS")
    if not glob('DtxCS*'):
        forgeFileMissing = True
        forgeFileList.append("DtxCS")
    if not glob('GameArchives*'):
        forgeFileMissing = True
        forgeFileList.append("GameArchives")
    if forgeFileMissing:
        log.critical("ForgeTool is missing these critical files: "+str(forgeFileList).translate({ord(i): None for i in "'[]"}))
        log.critical("Please add these files in the program's directory. ForgeTool support will be disabled.")
        isForgeEnabled = False
    else:
        isForgeEnabled = True

if not glob('tmp/'):
    os.mkdir("tmp/")
    log.info("Created temporary directory.")
else:
    for file in glob("tmp/*"):
        os.remove(file)
    log.info("Removed temporary files from previous run.")

# Setting up discord
load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def status_task():
    while True:
        random_status = random.choice(open(quotes_path).readlines())
        await client.change_presence(activity=discord.Game(name=random_status))
        await asyncio.sleep(60)


@client.event
async def on_ready():
    log.info(f'Bot has logged in as {client.user}.')
    client.loop.create_task(status_task()) 

@client.event
async def on_message(message):
    if message.author == client.user:  
        return
    if message.author.bot:
        return
    
    if client.user.mention in message.content.split():
        await message.channel.send(f'milo (and forge) harmonix. Running version {__version__}, '+' Ping: {0}ms\n'.format(round(client.latency * 1000, 1)))

    if message.channel.id != BOT_CHANNEL and message.guild:
        return
    
    if len(message.attachments) == 0:
        return
    elif len(message.attachments) > 1:
        message.channel.send("**I can only process 1 file at a time. Only the first file will be processed.**")

    file_url_base = str(message.attachments[0].url)
    file_url = file_url_base.split('?')[0]
    height = message.attachments[0].height
    width = message.attachments[0].width
    file_extension = file_url.rsplit('.', 1)[1] # Copy File URL to get the extension later

    file_format = None
    file_id = random.randrange(10000000000001)
    file_url_format = file_url.rpartition('.')[-1]
    file_path = f"tmp/{file_id}.{file_url_format}"

    # Extension sorting

    FileExtensionValue = 0
    
    file = requests.get(file_url_base, allow_redirects=True)
    with open(file_path, "wb") as f:
            f.write(file.content)
            f.close()

    if file_extension.find('_ps3') > -1:
        FileExtensionValue = file_extension.find('_ps3')
        file_format = 'ps3'
    elif file_extension.find('_xbox') > -1:
        FileExtensionValue = file_extension.find('_xbox')
        file_format = 'xbox'
    elif file_extension.find('_nx') > -1:
        FileExtensionValue = file_extension.find('_nx')
        file_format = 'nx'
    elif file_extension.find('_wii') > -1:
        FileExtensionValue = file_extension.find('_nx')
        file_format = 'wii'
    elif file_extension.find('_pc') > -1:
        FileExtensionValue = file_extension.find('_pc')
        file_format = 'xbox'
        FileExtensionValue = file_extension.find('png')
        if FileExtensionValue == -1:
            await message.channel.send("**This file is not supposed by either tool!**")
            os.remove(file_path)
            return
    elif magic.from_file(file_path, mime=True) in supportedFormats:
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
        await message.channel.send('Could not find a valid file format. Debug: ' + file_extension + " " + file_url)
        os.remove(file_path)
        return

    if file_format == 'nx' and isForgeEnabled == False:
        await message.channel.send("Unable to process file: Forgetool is missing.")
        os.remove(file_path)
        return
    
    os.chdir(current_directory)
    
    line = random.choice(open(conversion_quotes_path).readlines())
    if os.path.isfile("totalconversions.txt"):
        with open("totalconversions.txt", "r") as f:
            totalconversions = int(f.read())
        with open("totalconversions.txt", "w") as f:
            f.write(str(totalconversions+1))
    else:
        with open("totalconversions.txt", "w") as f:
            f.write("1")
    await message.channel.send(f'{line}')

    match file_format:
        case "png":
            xbox_path = f"tmp/{file_id}.png_xbox"
            wii_path = f"tmp/{file_id}.png_wii"
            ps3_path = f"tmp/{file_id}.png_ps3"

            try:
                superfreq_result1 = subprocess.run([superfreq_path, "png2tex", file_path, xbox_path, "--platform", "x360", "--miloVersion", "26"], stderr=subprocess.PIPE)
                superfreq_result2 = subprocess.run([superfreq_path, "png2tex", file_path, wii_path, "--platform", "wii", "--miloVersion", "26"], stderr=subprocess.PIPE)
                subprocess.run([python, swap_bytes_path, xbox_path, ps3_path])
                await message.channel.send(file=discord.File(xbox_path))
                await message.channel.send(file=discord.File(ps3_path))
                await message.channel.send(file=discord.File(wii_path))
            except FileNotFoundError:
                await message.channel.send("**FileNotFoundError: Superfreq failed to process image**")
                log.warning(superfreq_result1.stderr.decode("utf-8"))
                await message.channel.send("```\n"+superfreq_result1.stderr.decode("utf-8")+"\n```")
                log.warning(superfreq_result2.stderr.decode("utf-8"))
                await message.channel.send("```\n"+superfreq_result2.stderr.decode("utf-8")+"\n```")
            except Exception as error: 
                await message.channel.send(f"**An error occured. {error}**")
                log.warning(superfreq_result1.stderr.decode("utf-8"))
                await message.channel.send("```\n"+superfreq_result1.stderr.decode("utf-8")+"\n```")
                log.warning(superfreq_result2.stderr.decode("utf-8"))
                await message.channel.send("```\n"+superfreq_result2.stderr.decode("utf-8")+"\n```")
            os.remove(ps3_path)
            os.remove(xbox_path)
            os.remove(wii_path)
            os.remove(file_path) # Cleanup
            return


        case "xbox":
            # await message.channel.send("Using superfreq") # Redo this soon when a toggle is made for forge and milo
            file_path = str(f"tmp/{file_id}.png")
            xbox_path = str(f"tmp/{file_id}.{file_url.rsplit('.', 1)[1]}")

            xbox = requests.get(file_url_base, allow_redirects=True)
            with open(xbox_path, "wb") as f:
                f.write(xbox.content)
            try:
                superfreq_result1 = subprocess.run([superfreq_path, "tex2png", xbox_path, file_path, "--platform", "x360", "--miloVersion", "26"], stderr=subprocess.PIPE)
                await message.channel.send(file=discord.File(file_path))
            except FileNotFoundError:
                await message.channel.send("**FileNotFoundError: Superfreq failed to process image**")
                log.warning(superfreq_result1.stderr.decode("utf-8"))
                await message.channel.send("```\n"+superfreq_result1.stderr.decode("utf-8")+"\n```")
            except Exception as error: 
                await message.channel.send(f"**An error occured. {error}**")
                log.warning(superfreq_result1.stderr.decode("utf-8"))
                await message.channel.send("```\n"+superfreq_result1.stderr.decode("utf-8")+"\n```")
            os.remove(xbox_path)
            os.remove(file_path) # Cleanup
            return

        case "ps3":
            # await message.channel.send("Using superfreq") # Redo this soon when a toggle is made for forge and milo
            file_path = str(f"tmp/{file_id}.png")
            ps3_path = str(f"tmp/{file_id}.{file_url.rsplit('.', 1)[1]}")

            ps3 = requests.get(file_url_base, allow_redirects=True)
            with open(ps3_path, "wb") as f:
                f.write(ps3.content)
            try:
                superfreq_result1 = subprocess.run([superfreq_path, "tex2png", ps3_path, file_path, "--platform", "ps3", "--miloVersion", "26"], stderr=subprocess.PIPE)
                await message.channel.send(file=discord.File(file_path))
            except FileNotFoundError:
                await message.channel.send("**FileNotFoundError: Superfreq failed to process image**")
                log.warning(superfreq_result1.stderr.decode("utf-8"))
                await message.channel.send("```\n"+superfreq_result1.stderr.decode("utf-8")+"\n```")
            except Exception as error: 
                await message.channel.send(f"**An error occured.**\n{error}")
                log.warning(superfreq_result1.stderr.decode("utf-8"))
                await message.channel.send("```\n"+superfreq_result1.stderr.decode("utf-8")+"\n```")
            os.remove(ps3_path)
            os.remove(file_path) # Cleanup
            return

        case "nx":
            # await message.channel.send("Using forgetool") # Redo this soon when a toggle is made for forge and milo
            file_path = str(f"tmp/{file_id}.png")
            nx_path = str(f"tmp/{file_id}.{file_url.rsplit('.', 1)[1]}")

            nx = requests.get(file_url_base, allow_redirects=True)
            with open(nx_path, "wb") as f:
                f.write(nx.content)
            try:
                forgetool_result1 = subprocess.run([forgetool_path, "tex2png", nx_path, file_path], stderr=subprocess.PIPE)
                if os.path.getsize(file_path) > 1:
                    await message.channel.send(file=discord.File(file_path))
                else:
                    await message.channel.send("**Error: Forgetool failed to process the image.**")
                    log.warning(forgetool_result1.stderr.decode("utf-8"))
                    await message.channel.send("```\n"+forgetool_result1.stderr.decode("utf-8")+"\n```")
            except FileNotFoundError:
                await message.channel.send("**FileNotFoundError: Forgetool failed to process image**")
                log.warning(forgetool_result1.stderr.decode("utf-8"))
                await message.channel.send("```\n"+forgetool_result1.stderr.decode("utf-8")+"\n```")
                os.remove(nx_path)
                os.remove(file_path)
                return
            except Exception as error: 
                log.warning(forgetool_result1.stderr.decode("utf-8"))
                await message.channel.send("```\n"+forgetool_result1.stderr.decode("utf-8")+"\n```")
                await message.channel.send(f"**An error occured.\n**{error}")
                os.remove(nx_path)
                os.remove(file_path)
            os.remove(nx_path)
            os.remove(file_path) # Cleanup
            return

        case "wii":
            file_path = str(f"tmp/{file_id}.png")
            wii_path = str(f"tmp/{file_id}.{file_url.rsplit('.', 1)[1]}")

            wii = requests.get(file_url_base, allow_redirects=True)
            with open(wii_path, "wb") as f:
                f.write(wii.content)
            try:
                superfreq_result1 = subprocess.run([superfreq_path, "tex2png", wii_path, file_path, "--platform", "wii", "--miloVersion", "26"], stderr=subprocess.PIPE)
                await message.channel.send(file=discord.File(file_path))
            except FileNotFoundError:
                await message.channel.send("**FileNotFoundError: Superfreq failed to process image**")
                log.warning(superfreq_result1.stderr.decode("utf-8"))
                await message.channel.send("```\n"+superfreq_result1.stderr.decode("utf-8")+"\n```")
            except Exception as error: 
                await message.channel.send(f"**An error occured.**\n{error}")
                log.warning(superfreq_result1.stderr.decode("utf-8"))
                await message.channel.send("```\n"+superfreq_result1.stderr.decode("utf-8")+"\n```")
            os.remove(wii_path)
            os.remove(file_path) # Cleanup
            return

        case _:
            await message.channel.send('**An unexpected error happened with the file format.**')
            log.critical(f"Script somehow failed to process the right file format for fileid {file_id} or the format was not properly implemented yet.")
            for file in glob("tmp/*"):
                os.remove(file)
            return

client.run(TOKEN, log_handler=None) 
