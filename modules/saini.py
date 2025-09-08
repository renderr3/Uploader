import os 
import re 
import time 
import mmap 
import datetime 
import aiohttp 
import aiofiles 
import asyncio 
import logging 
import requests 
import tgcrypto 
import subprocess 
import concurrent.futures 
from math import ceil 
from utils import progress_bar 
from pyrogram import Client, filters 
from pyrogram.types import Message 
from io import BytesIO 
from pathlib import Path
from Crypto.Cipher import AES 
from Crypto.Util.Padding import unpad 
from base64 import b64decode

def duration(filename): result = subprocess.run( ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE ) output = result.stdout.decode().strip()

try:
    return float(output)
except ValueError:
    err = result.stderr.decode().strip()
    raise FileNotFoundError(
        f"ffprobe failed for {filename}. Output: {output} Error: {err}"
    )

def get_mps_and_keys(api_url): response = requests.get(api_url) response_json = response.json() mpd = response_json.get('MPD') keys = response_json.get('KEYS') return mpd, keys

def exec(cmd): process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) output = process.stdout.decode() print(output) return output

def pull_run(work, cmds): with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor: print("Waiting for tasks to complete") fut = executor.map(exec, cmds)

async def aio(url, name): k = f'{name}.pdf' async with aiohttp.ClientSession() as session: async with session.get(url) as resp: if resp.status == 200: f = await aiofiles.open(k, mode='wb') await f.write(await resp.read()) await f.close() return k

async def download(url, name): ka = f'{name}.pdf' async with aiohttp.ClientSession() as session: async with session.get(url) as resp: if resp.status == 200: f = await aiofiles.open(ka, mode='wb') await f.write(await resp.read()) await f.close() return ka

async def pdf_download(url, file_name, chunk_size=1024 * 10): if os.path.exists(file_name): os.remove(file_name) r = requests.get(url, allow_redirects=True, stream=True) with open(file_name, 'wb') as fd: for chunk in r.iter_content(chunk_size=chunk_size): if chunk: fd.write(chunk) return file_name

... (keeping other helper functions unchanged for brevity)

async def send_vid(bot: Client, m: Message, cc, filename, vidwatermark, thumb, name, prog, channel_id): subprocess.run(f'ffmpeg -i "{filename}" -ss 00:00:10 -vframes 1 "{filename}.jpg"', shell=True) await prog.delete(True) reply1 = await bot.send_message(channel_id, f"📩 Uploading Video 📩:-\n<blockquote>{name}</blockquote>") reply = await m.reply_text(f"Generate Thumbnail:\n<blockquote>{name}</blockquote>") try: if thumb == "/d": thumbnail = f"{filename}.jpg" else: thumbnail = thumb

if vidwatermark == "/d":
        w_filename = f"{filename}"
    else:
        w_filename = f"w_{filename}"
        font_path = "vidwater.ttf"
        subprocess.run(
            f'ffmpeg -i "{filename}" -vf "drawtext=fontfile={font_path}:text=\'{vidwatermark}\':fontcolor=white@0.3:fontsize=h/6:x=(w-text_w)/2:y=(h-text_h)/2" -codec:a copy "{w_filename}"',
            shell=True
        )
        
except Exception as e:
    await m.reply_text(str(e))

try:
    dur = int(duration(w_filename))
except FileNotFoundError as e:
    await m.reply_text(f"Error getting duration: {e}")
    dur = 0

start_time = time.time()

try:
    await bot.send_video(channel_id, w_filename, caption=cc, supports_streaming=True, height=720, width=1280, thumb=thumbnail, duration=dur, progress=progress_bar, progress_args=(reply, start_time))
except Exception:
    await bot.send_document(channel_id, w_filename, caption=cc, progress=progress_bar, progress_args=(reply, start_time))
os.remove(w_filename)
await reply.delete(True)
await reply1.delete(True)
os.remove(f"{filename}.jpg")


