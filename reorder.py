import asyncio
import re
import sys
import traceback

import requests
from aiohttp import ClientSession

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0'

REFERER = 'https://cbjpeg.stream.highwebmedia.com'

HEADERS = {
    'User-agent': USER_AGENT,
    'Referer': REFERER
}

TIMEOUT = (3.05, 9.05)


def search(pattern, string):
    result = re.search(pattern, string, re.MULTILINE | re.DOTALL)
    if (result is None) or (result.group(0) is None):
        return ""

    return result.group(1)


def exception_handler(request, exception):
    print("Request failed:", request.url)
    print(exception)
    traceback.print_exc()


class Room:
    def __init__(self, room_data):
        self.data = room_data
        self.img_url = search(r'<img src="(.*?)\?[0-9]*"', room_data)
        slash_pos = self.img_url.rfind('/')
        self.model_name = self.img_url[slash_pos + 1: -4]
        self.priority = 0


def get_room_list(filename, text):
    model_list = []
    for match_obj in re.finditer(r'<li class="room_list_room"(.*?)</ul>.+?</div>.+?</li>', text,
                                 re.MULTILINE | re.DOTALL):
        model_room = match_obj.group(1)
        model_list.append(Room(model_room))

    http_session = requests.Session()
    http_session.headers.update(HEADERS)

    total = len(model_list)
    try:
        i = 1
        for model in model_list:
            try:
                print(f'{filename} : {i} of {total}')
                i += 1

                playlist_url = f"https://edge144.stream.highwebmedia.com/live-hls/amlst:{model.model_name}/playlist.m3u8"
                response = http_session.get(playlist_url, timeout=TIMEOUT)

                lines = response.text.splitlines()

                resolutions = [line for line in lines if not line.startswith("#")]
                if len(resolutions) == 0:
                    continue

                chunks = resolutions[-1].split('_')
                if len(chunks) < 3:
                    print("Can't parse", resolutions[-1], "for model", model.model_name, "Response:", response)
                    continue

                best_bandwidth = chunks[2]
                model.priority = int(best_bandwidth[1:])
            except BaseException as error:
                print("GetPlayList exception model: " + model.model_name)
                print(error)
                traceback.print_exc()
    finally:
        http_session.close()

    return model_list


async def fetch(url, session):
    async with session.get(url) as response:
        if response.status != 200:
            # print(response.status, url)
            return b''
        return await response.read()


async def bound_fetch(sem, url, session):
    # Getter function with semaphore.
    async with sem:
        return await fetch(url, session)


async def fetch_playlists(model_list):
    # create instance of Semaphore
    sem = asyncio.Semaphore(16)
    tasks = []
    async with ClientSession() as session:
        for model in model_list:
            playlist_url = f"https://edge144.stream.highwebmedia.com/live-hls/amlst:{model.model_name}/playlist.m3u8"
            task = asyncio.ensure_future(bound_fetch(sem, playlist_url, session))
            tasks.append(task)

        return await asyncio.gather(*tasks)


def get_room_list_async(filename, text):
    model_list = []
    for match_obj in re.finditer(r'<li class="room_list_room"(.*?)</ul>.+?</div>.+?</li>', text,
                                 re.MULTILINE | re.DOTALL):
        model_room = match_obj.group(1)
        model_list.append(Room(model_room))

    print(filename, ':', len(model_list))

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(fetch_playlists(model_list))
    results = zip(model_list, loop.run_until_complete(future))

    for model, response in results:
        if len(response) == 0:
            continue

        lines = response.decode('utf-8').splitlines()

        resolutions = [line for line in lines if not line.startswith("#")]
        if len(resolutions) == 0:
            continue

        chunks = resolutions[-1].split('_')
        if len(chunks) < 3:
            print("Can't parse", resolutions[-1], "for model", model.model_name, "Response:", response)
            continue

        best_bandwidth = chunks[2]
        model.priority = int(best_bandwidth[1:])

    return model_list


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)

    filepath = sys.argv[1]
    files = sys.argv[2: -1]
    output = sys.argv[-1]

    html = ''
    with open(filepath, 'rb') as f:
        html = f.read().decode('utf-8')

    matched = re.search(r'<ul id="room_list" class="list">(.*?)<ul class="paging">', html, re.MULTILINE | re.DOTALL)
    if (matched is None) or (matched.group(0) is None):
        print(f"{filepath} : Room list not found")
        sys.exit(0)

    models = matched.group(1)
    start, end = matched.span()

    room_list = get_room_list_async(filepath, models)

    for file in files:
        txt = ''
        with open(file, 'rb') as f:
            txt = f.read().decode('utf-8')

        m = re.search(r'<ul id="room_list" class="list">(.*?)<ul class="paging">', txt, re.MULTILINE | re.DOTALL)
        if (m is None) or (m.group(0) is None):
            print(f"{file} : Room list not found")
            continue

        rooms = m.group(1)
        room_list += get_room_list_async(file, rooms)

    room_list.sort(key=lambda x: x.priority, reverse=True)

    head = html[:start]
    tail = html[end:]
    # remove ads
    found = re.search(r'<div class="ad">\s+?<div class="remove_ads">.*?<div class="searching-overlay".*?</div>',
                      head, re.MULTILINE | re.DOTALL)
    ads_start1, ads_end1 = found.span()
    found = re.search(r'<div class="banner">.*?<div class="overlay" id="overlay"></div>',
                      tail, re.MULTILINE | re.DOTALL)

    ads_start2, ads_end2 = found.span()

    with open(output, 'wb') as f:
        f.write(head[:ads_start1].encode('utf-8'))
        f.write(head[ads_end1:].encode('utf-8'))
        f.write(b'<ul id="room_list" class="list">\n')
        for room in room_list:
            f.write(b'<li class="room_list_room"')
            f.write(room.data.replace(f'<a href="/{room.model_name}/">',
                                      f'<a href="https://chaturbate.com/{room.model_name}/">')
                    .encode('utf-8'))
            f.write(b'</ul>\n</div>\n</li>\n')
        f.write(b'</ul>\n<ul class="paging">\n')
        f.write(tail[:ads_start2].encode('utf-8'))
        f.write(tail[ads_end2:].encode('utf-8'))
