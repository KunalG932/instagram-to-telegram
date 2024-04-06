from configparser import ConfigParser
import requests
import os
import socks
import time
from instagram_private_api import Client, errors as instaErrors
from telethon import TelegramClient, errors
from datetime import datetime as dt, timedelta

config = ConfigParser()
config.read('conf.ini')

# Instagram API setup
user_name = config['INSTAGRAM']['username']
password = config['INSTAGRAM']['password']
target_username = config['INSTAGRAM']['target_username']
feed_wait_time = config['INSTAGRAM'].getint('feedWaitTime')

# Telegram Client Setup
api_id = config['TELEGRAM']['api_id']
api_hash = config['TELEGRAM']['api_hash']
target_group = config['TELEGRAM'].getint('telegram_destination_group_id')
session_file = '6737395815:AAEuiDpU0QL0-1pG0R4B6XzmA_Fj5SSyeCU'

# Proxy Setup
proxy_enabled = config['PROXY'].getboolean('enable')
proxy_server = config['PROXY']['server'].encode() if proxy_enabled else '159.89.49.60'
proxy_port = config['PROXY'].getint('port') if proxy_enabled else 31264

telegram_client = TelegramClient(session_file, api_id, api_hash, proxy=(socks.SOCKS5, proxy_server, proxy_port)) if proxy_enabled else TelegramClient(session_file, api_id, api_hash)


# Helper functions
def create_timestamp(sec=0, mins=0, hours=0, days=0):
    now = dt.now() - timedelta(seconds=sec, minutes=mins, hours=hours, days=days)
    timestamp = int(time.mktime(now.timetuple()))
    return timestamp


def download_img(url):
    if not os.path.isdir('./tmp'):
        os.mkdir('./tmp')
    response = requests.get(url)
    file_path = './tmp/file.jpg'
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return file_path


def send_item(file_path, text=None):
    try:
        telegram_client.loop.run_until_complete(telegram_client.send_message(target_group, text, file=file_path))
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except errors.rpcerrorlist.ChatIdInvalidError:
        print('[-] Invalid Target id...')
        return False


# Main function
def main():
    try:
        print('[+] Starting the Telegram client...')
        telegram_client.start()
        print('[+] Telegram client started...')

        while True:
            print('[+] Getting Instagram feeds....')
            try:
                user_feed = insta_client.username_feed(target_username, min_timestamp=create_timestamp(sec=feed_wait_time + 5))
            except instaErrors.ClientCheckpointRequiredError:
                print('[-] Instagram has detected bot behaviour...')
                print('[-] Bot is going to sleep... Please login using the browser then restart bot...')
                time.sleep(6000)
                print('[-] Quitting bot...')
                exit()

            list_of_items = user_feed['items']
            if list_of_items:
                print('[+] New Instagram feeds found...\n[+] Sending feeds to Telegram group...')
                for item in list_of_items:
                    text = item['caption']['text'] if 'caption' in item else None
                    item_type = item['media_type']
                    if item_type == 1:
                        item_url = item['image_versions2']['candidates'][0]['url']
                        img_path = download_img(item_url)
                        sent = send_item(img_path, text=text)
                    elif item_type == 2:
                        item_url = item['video_versions'][0]['url']
                        sent = send_item(item_url, text=text)
                    if sent:
                        print('[+] Feed sent...')
                    else:
                        print('[-] Feed not sent... Please quit the bot...')
                        break
            else:
                print('[+] No new feeds found...')
            print(f'[+] Waiting for {feed_wait_time} Seconds before checking the feed again...')
            time.sleep(feed_wait_time)
    except KeyboardInterrupt:
        print('[+] Quitting bot... Please wait...')
        exit()


# Start execution
if __name__ == "__main__":
    print('[+] Starting the bot...')
    try:
        main()
    except KeyboardInterrupt:
        print('[+] Quitting bot...')
        exit()
