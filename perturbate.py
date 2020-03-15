import json
import re
import shutil
import sys
import time
import traceback

import requests

HEADERS = {
    'User-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
    'Referer': 'https://sex-videochat.net/chaturbate/',
    'Host': 'sex-videochat.net',
    'X-Requested-With': 'XMLHttpRequest'
}

OUTPUT = "output.html"
CACHE = "cache.js"
CACHE_DICT = {}
TIMEOUT = (3.05, 9.05)


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


def get_feeds(start, finish):
    http_session = requests.Session()
    http_session.headers.update(HEADERS)

    model_list = []
    try:
        for page in range(start, finish + 1):
            try:
                print(page)
                url = f"https://sex-videochat.net/getfeeddata/chaturbate/?page={page}"
                response = http_session.get(url, timeout=TIMEOUT)
                model_list += get_room_list(response.text)
            except BaseException as error:
                print(f"Get feed exception on page: {page}")
                print(error)
                traceback.print_exc()
    finally:
        http_session.close()

    return model_list


def update_models_bps(session, model_list, tries):
    if len(model_list) == 0:
        return

    print("try #", tries)

    failed = []
    for model in model_list:
        try:
            if model.model_name in CACHE_DICT:
                model.bps = CACHE_DICT[model.model_name]
                continue

            print(model.model_name)

            playlist_url = f"https://edge144.stream.highwebmedia.com/live-hls/amlst:{model.model_name}" \
                           f"/playlist.m3u8"
            response = session.get(playlist_url, timeout=TIMEOUT)
            time.sleep(0.5)

            if response.status_code != 200:
                model.log = f'Status code is {response.status_code}'
                print(response.status_code, playlist_url)

                if response.status_code == 503:
                    failed.append(model)
                    time.sleep(1)

                continue

            lines = response.text.splitlines()

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
        except BaseException as error:
            print(f"Update bps for model exception: {model.model_name}")
            print(error)
            traceback.print_exc()

    update_models_bps(session, failed, tries + 1)


def get_room_list(text):
    model_list = []
    for match_obj in re.finditer(r'<div class="col-lg-2 col-md-4 col-sm-6 col-6 entry">\s*?'
                                 r'<div class="thumbnail">(.*?)</div>\s*?</div>\s*?</div>\s*?</div>', text,
                                 re.MULTILINE | re.DOTALL):
        model_room = match_obj.group(1)
        model_list.append(Room(model_room))

    http_session = requests.Session()
    http_session.headers.update(HEADERS)

    try:
        update_models_bps(http_session, model_list, 1)
    finally:
        http_session.close()

    return model_list


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

    with open(CACHE, 'r') as f:
        CACHE_DICT = json.load(f)

    room_list = get_feeds(beg, fin)

    room_list.sort(key=lambda x: (x.bps, x.users), reverse=True)

    with open(CACHE, "w") as f:
        json.dump(CACHE_DICT, f, indent=4)

    print_results(room_list, fileout)
