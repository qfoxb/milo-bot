# Milohax Art Swap bot written by femou and qfoxb. (c) 2023
import discord
import logging
import os
from dotenv import load_dotenv
import requests
import random
import asyncio

load_dotenv()
TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True

# Arguments
bot_channel = int(os.getenv("CHANNEL_ID"))

client = discord.Client(intents=intents)
async def status_task():
    while True:
        random_status = random.choice(open('status_quotes.txt').readlines())
        await client.change_presence(activity=discord.Game(name=random_status))
        await asyncio.sleep(60)
        random_status = random.choice(open('status_quotes.txt').readlines())
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
        await message.chanenl.send('Please input a larger image.')
        return 
    if bin(width).count("1") != 1:
        await message.channel.send('Invalid image size, the height and width must be a power of 2 (256, 512, etc.)')
        return
    if width < 4:
        await message.chanenl.send('Please input a larger image.')
        return 
    if image_url[-4:] != '.png':
        await message.channel.send('Invalid image format, the image must be a PNG.')
        return

    line = random.choice(open('conversion_quotes.txt').readlines())
    await message.channel.send(f'{line}')
    image = requests.get(image_url, allow_redirects=True)
    image_id = random.randrange(10000000000001) 
    with open(f"{image_id}.png", "wb") as f:
        f.write(image.content) # Nice
    os.system(f"superfreq png2tex {image_id}.png {image_id}.png_xbox --platform x360 --miloVersion 26")
    os.system(f"python convert.py {image_id}.png_xbox {image_id}.png_ps3")
    await message.channel.send(file=discord.File(f"./{image_id}.png_xbox"))
    await message.channel.send(file=discord.File(f"./{image_id}.png_ps3"))
    os.remove(f"./{image_id}.png_xbox")
    os.remove(f"./{image_id}.png_ps3")
    os.remove(f"./{image_id}.png") # Cleanup

client.run(TOKEN) 