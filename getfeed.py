import asyncio
import json
import os
import random
import re
import shutil
import sys
import time
import traceback

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
THRESHOLD = 3096000

EDGES = [81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99,
         100, 101, 102, 103, 104, 106, 108, 110, 111, 112, 113, 115, 116, 117, 118, 119, 120, 123, 124, 125, 126,
         133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 150, 151, 152, 153, 154, 155, 156,
         157, 158, 159, 160, 161, 162, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179,
         180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201,
         202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223,
         224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244,
         248, 249, 250, 251, 252, 254, 256, 259, 260, 261, 266, 267, 270, 271, 272, 273,
         274, 275, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297,
         298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319,
         320, 321, 322, 323, 324, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341,
         342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352]

random.seed()


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
    try:
        async with session.get(url) as response:
            if response.status != 200:
                if response.status != 403:
                    print(response.status, url)

                if response.status == 503:
                    return '503'

                return b''

            return await response.read()
    except BaseException as error:
        print(error)
        traceback.print_exc()
        return b''


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


async def done():
    return "Done"


async def fetch_playlists(model_list):
    # create instance of Semaphore
    sem = asyncio.Semaphore(16)
    tasks = []
    rnd_sample = random.sample(EDGES, len(model_list))
    async with ClientSession() as session:
        for rnd, model in zip(rnd_sample, model_list):
            if model.model_name in CACHE_DICT:
                model.bps = CACHE_DICT[model.model_name]
                tasks.append(asyncio.ensure_future(done()))
                continue

            playlist_url = f"https://edge{rnd}.stream.highwebmedia.com/live-hls/amlst:{model.model_name}/playlist.m3u8"
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

        if response == 'Done':
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
        model.log = ''
        CACHE_DICT[model.model_name] = model.bps

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
            if THRESHOLD >= room.bps:
                break
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
