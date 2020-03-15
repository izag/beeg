import asyncio
import json
import os
import re
import shutil
import sys
import time

from aiohttp import ClientSession

HEADERS = {
    'User-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
    'Referer': 'https://sex-videochat.net/chaturbate/',
    'Host': 'sex-videochat.net',
    'X-Requested-With': 'XMLHttpRequest'
}

OUTPUT = "output.html"
CACHE = "cache.js"
CACHE_DICT = {}


def search(pattern, string):
    result = re.search(pattern, string, re.MULTILINE | re.DOTALL)
    if (result is None) or (result.group(0) is None):
        return ""

    return result.group(1)


class Room:
    def __init__(self, room_data):
        self.img_url = search(r'data-original="(.*?)"', room_data)
        slash_pos = self.img_url.rfind('/')
        self.model_name = self.img_url[slash_pos + 1: -4]
        self.bps = 0
        self.users = 0
        usr = search(r'([0-9]+) польз', room_data)
        if len(usr) > 0:
            self.users = int(usr)
        self.log = ''

    def __str__(self):
        return f"""
        <li class="room_list_room" >
        <a href="https://chaturbate.com/{self.model_name}/">
        <img src="https://roomimg.stream.highwebmedia.com/ri/{self.model_name}.jpg" width="180" height="135" class="png" />
        </a>
        <div class="details">
        <div class="title">
        <a href="https://chaturbate.com/{self.model_name}/"> {self.model_name}</a>
        </div>
        <ul class="sub-info">
        <li class="cams">{self.bps}</li>
        <li class="cams">{self.users}</li>
        </ul>
        <ul class="subject">
        <li>{self.log}</li>
        </ul>
        </div>
        </li>
        """


async def fetch(url, session):
    async with session.get(url) as response:
        if response.status != 200:
            if response.status != 403:
                print(response.status, url)

            if response.status == 503:
                return '503'

            return b''

        return await response.read()


async def bound_fetch(sem, url, session):
    # Getter function with semaphore.
    async with sem:
        return await fetch(url, session)


async def fetch_feed(start, finish):
    # create instance of Semaphore
    sem = asyncio.Semaphore(16)
    tasks = []
    async with ClientSession(headers=HEADERS) as session:
        for page in range(start, finish + 1):
            url = f"https://sex-videochat.net/getfeeddata/chaturbate/?page={page}"
            task = asyncio.ensure_future(bound_fetch(sem, url, session))
            tasks.append(task)

        return await asyncio.gather(*tasks)


async def fetch_playlists(model_list):
    # create instance of Semaphore
    sem = asyncio.Semaphore(4)
    tasks = []
    async with ClientSession() as session:
        for model in model_list:
            playlist_url = f"https://edge144.stream.highwebmedia.com/live-hls/amlst:{model.model_name}/playlist.m3u8"
            task = asyncio.ensure_future(bound_fetch(sem, playlist_url, session))
            tasks.append(task)

        return await asyncio.gather(*tasks)


def get_feeds(start, finish):
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(fetch_feed(start, finish))
    return loop.run_until_complete(future)


def update_models_bps(model_list, tries):
    if len(model_list) == 0:
        return

    print("try #", tries)

    if tries > 1:
        time.sleep(1)

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(fetch_playlists(model_list))
    results = zip(model_list, loop.run_until_complete(future))

    failed = []
    for model, response in results:
        if len(response) == 0:
            model.log = 'Playlist is empty'
            continue

        if response == '503':
            failed.append(model)
            continue

        lines = response.decode('utf-8').splitlines()

        resolutions = [line for line in lines if not line.startswith("#")]
        if len(resolutions) == 0:
            model.log = 'Resolutions not found'
            continue

        chunks = resolutions[-1].split('_')
        if len(chunks) < 3:
            model.log = f"Can't parse {resolutions[-1]} for model {model.model_name} Response: {response}"
            continue

        best_bandwidth = chunks[2]
        model.bps = int(best_bandwidth[1:])

    update_models_bps(failed, tries + 1)


def get_room_list(text):
    model_list = []
    for match_obj in re.finditer(r'<div class="col-lg-2 col-md-4 col-sm-6 col-6 entry">\s*?'
                                 r'<div class="thumbnail">(.*?)</div>\s*?</div>\s*?</div>\s*?</div>', text,
                                 re.MULTILINE | re.DOTALL):
        model_room = match_obj.group(1)
        model_list.append(Room(model_room))

    update_models_bps(model_list, 1)

    return model_list


def dump_cache(rooms):
    cache_dict = {}
    for model in rooms:
        if model.bps == 0:
            continue

        cache_dict[model.model_name] = model.bps

    with open(CACHE, "w") as f:
        json.dump(cache_dict, f, indent=4)


def print_results(rooms, page):
    with open("head.html", 'rb') as src, open(OUTPUT, 'wb') as dest:
        shutil.copyfileobj(src, dest)

    with open(OUTPUT, 'ab') as f:
        for room in rooms:
            f.write(str(room).encode('utf-8'))

    with open("tail.html", 'rb') as src, open(OUTPUT, 'ab') as dest:
        shutil.copyfileobj(src, dest)

    shutil.copyfile(OUTPUT, page)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(1)

    beg = int(sys.argv[1])
    fin = int(sys.argv[2])
    fileout = sys.argv[3]

    if os.path.exists(CACHE):
        with open(CACHE, 'r') as f:
            CACHE_DICT = json.load(f)

    feeds = get_feeds(beg, fin)

    room_list = []
    i = beg
    for feed in feeds:
        print(i)
        i += 1
        room_list += get_room_list(feed.decode('utf-8'))

    room_list.sort(key=lambda x: (x.bps, x.users), reverse=True)

    for room in room_list:
        if room.bps == 0:
            continue

        CACHE_DICT[room.model_name] = room.bps

    with open(CACHE, "w") as f:
        json.dump(CACHE_DICT, f, indent=4)

    print_results(room_list, fileout)
