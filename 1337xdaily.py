#@markdown **1337x Telegram Uploader**
from bs4 import BeautifulSoup
from time import sleep,time
import subprocess
import os
import random
import subprocess
from telegram import Bot, InputMediaVideo
from telegram.ext import Updater
import math
from seedrcc import Login,Seedr
from time import sleep
import urllib.parse
from urllib.parse import unquote
import requests
from telegram.error import RetryAfter

Username  = "herobenhero5@gmail.com" #@param {type:"string"}
Password  = "zyHyuTfaGiC6:uP" #@param {type:"string"}

account = Login(Username, Password)
account.authorize()
seedr = Seedr(token=account.token)

API_SERVER_URL = 'http://localhost:8081/bot'
TELEGRAM_TOKEN = '5942550686:AAEkBVyp0U0zhP3z7ylmw4m2KS-pTD9UyZQ'
chat_id = '-1002080818562' #@param {type:"string"}

def convert_size(size_bytes):
    """Convert the size in bytes to a more human-readable format."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_video_duration(file_path):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    output = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
    return int(float(output))

def generate_thumbnail(video_path, time, thumbnail_path):
    cmd = f'ffmpeg -i "{video_path}" -ss {time} -vframes 1 "{thumbnail_path}"'
    subprocess.call(cmd, shell=True)

def send_video_file(file_path, thumbnail_path):
    print(f"Sending {file_path} to Telegram")

    time = '00:00:01'
    # generate_thumbnail(file_path, time, thumbnail_path)

    if not os.path.exists(file_path):
        print(f'File {file_path} not found.')
        return

    updater = Updater(token=TELEGRAM_TOKEN, use_context=True, base_url=API_SERVER_URL)
    bot = updater.bot

    duration = get_video_duration(file_path)
    thumbnail_path='Thumbnail.jpg'

    retries = 5  # Adjust the number of retries based on your needs
    for attempt in range(retries):
        try:
            with open(file_path, 'rb') as file, open(thumbnail_path, 'rb') as thumb:
                bot.send_video(chat_id=chat_id, video=file, duration=duration, thumb=thumb, timeout=999, caption=file_path)
            print(f'Video {file_path} sent successfully!')
            os.remove(file_path)
            break  # Exit the loop if successful
        except RetryAfter as e:
            sleep_time = e.retry_after  # Get the required wait time from the exception
            print(f"Rate limit exceeded. Sleeping for {sleep_time} seconds and retrying.")
            sleep(sleep_time * 2 ** attempt)  # Exponential backoff
        except Exception as e:
            print(f"Error sending video: {e}")
            sleep(60)
            # break  # Exit the loop on other errors

def aria2_download(filename, link):
    print(f"Downloading {filename} with {link}")

    command = f"aria2c -o '{filename}' --summary-interval=1 --max-connection-per-server=2 '{link}'"

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    process.wait()

    send_video_file(filename, filename +'.jpg')

def seedr_download(MagneticURL):
  add=seedr.addTorrent(MagneticURL)
  if add["result"]==True:
    table=seedr.listContents()
    i = 0
    last_progress = -1
    while len(table['torrents']) != 0 and i < 30:
        for torrent in table['torrents']:
            size = convert_size(torrent['size'])
            print(f"{torrent['id']}: {torrent['name']}, {size}, {torrent['progress']}%")
            if last_progress != torrent['progress']:
                i = 0
                last_progress = torrent['progress']
        table = seedr.listContents()
        sleep(1)
        i += 1
        if i==15:
          seedr.deleteTorrent(torrent['id'])
          break

    if len(table['folders']) != 0:
        print("Completed torrents:")
        for folder in table['folders']:
            print()
            size = convert_size(folder['size'])
            print(f"{folder['id']}: {folder['name']}, {size}")
            table=seedr.listContents(folder['id'])
            # seedr.deleteFolder(folder['id'])
            if len(table['files']) == 0:
                print("No files in this folder.")
            else:
                print("\tFiles:")
                for file in table['files']:
                    print(f"\t{file['folder_file_id']}: {file['name']}, {convert_size(file['size'])}, Video={file['play_video']}")
                    if file['play_video']==True:
                      if file['size'] / (1024**3) < 1.95:
                          link=seedr.fetchFile(file['folder_file_id'])
                          # print('\t',link["url"])
                          quoted_link = urllib.parse.unquote(link["url"])
                          encoded_url = urllib.parse.quote(quoted_link, safe=':/?&=()[]')
                          # print(encoded_url)
                          aria2_download(file['name'],encoded_url)
                      else:
                        print(f"File size {convert_size(file['size'])} is Greater than 2GB")
            seedr.deleteFolder(folder['id'])

def get_magnetic_urls(URL):
  # Send an HTTP request to the web server
  response = requests.get(URL)

  # Parse the HTML code of the web page
  soup = BeautifulSoup(response.text, 'html.parser')

  # Find all the <a> elements on the page that have a "magnet" href attribute
  magnetic_links = soup.find_all('a', href=lambda x: x and x.startswith('magnet:'))
  magnets=[]
  # Print the text of each magnetic link
  for link in magnetic_links:
    magnets.append(link['href'])
  return magnets

def delete_all():
    #@title **List All**
    table=seedr.listContents()
    if len(table['torrents']) != 0:
        for torrent in table['torrents']:
            seedr.deleteTorrent(torrent['id'])
    if len(table['folders']) != 0:
        for folder in table['folders']:
            seedr.deleteFolder(folder['id'])

import requests
from bs4 import BeautifulSoup
from time import time, sleep

def get_mirrors():
    links = [
        "https://www.1337x.st",
        "https://1377x.to",
        "https://www.13377x.tw/"
    ]
    return links

Site = "https://1337x.to" #@param {type:"string"}
filename = "magnet_links_1337x.txt"

def scrape_links(site_url):
    response = requests.get(site_url+'/popular-movies')
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=lambda x: x and x.startswith('/torrent/') and x.endswith('/'))
    return links

existing_magnet_links = set()

for mirror_site in get_mirrors():
    links = scrape_links(mirror_site)
    
    if links:
        break  # If links are found, exit the loop
# print(mirror_site)
# print(links)
if not links:
    print("No links found on any mirror site. Exiting.")
else:
    try:
        with open(filename, "r") as file:
            existing_magnet_links = set(file.read().splitlines())
    except FileNotFoundError:
        pass  # No existing file, so the set remains empty
    try:
        with open(filename, "a") as file:
            # start_time = time()
            for link in links:
                magnets = get_magnetic_urls(mirror_site+link['href'])
                # print(magnets)
                # break
                for magnet in magnets:
                    # print(magnet)
                    if magnet not in existing_magnet_links:
                        seedr_download(magnet)
                        file.write(magnet + "\n")
                        existing_magnet_links.add(magnet)
    
                # elapsed_time = time() - start_time
                # if elapsed_time > 0.2 * 60 * 60:  # 2.5 hours in seconds
                #     print("Stopping script after 2.5 hours.")
                #     break
    except Exception as e:
        print(e)
