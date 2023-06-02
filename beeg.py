import asyncio
import datetime
import io
import logging
import os
import random
import sys
import time
import traceback
from collections import deque
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Thread
from tkinter import Tk, Button, ttk, W, E, Label, DISABLED, NORMAL, Menu, END, HORIZONTAL, \
    BooleanVar, Checkbutton, Toplevel, Listbox, Scrollbar, LEFT, Y, SINGLE, BOTH, RIGHT, VERTICAL, Frame, Entry, \
    StringVar, Canvas
from urllib.parse import urljoin

import aiohttp
import clipboard
import requests
from PIL import Image, ImageTk
from aiohttp import ClientSession, ClientConnectorError, ServerTimeoutError
from requests import RequestException

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0'

REFERER = 'https://cbjpeg.stream.highwebmedia.com'

proxies = None

REMEMBER_PROXIES = False

HEADERS = {
    'User-Agent': USER_AGENT,
    'Referer': REFERER
}

TIMEOUT = (3.05, 9.05)
DELAY = 2000
PAD = 5
MAX_FAILS = 6
N_REPEAT = 3
OUTPUT = os.path.join(os.path.expanduser("~"), "tmp1")
LOGS = "./logs/"

ALL_TIME = 0
HOUR = 60 * 60
TWO_HOURS = 2 * HOUR
SIX_HOURS = 6 * HOUR
HALF_DAY = 12 * HOUR
DAY = 24 * HOUR
TWO_DAYS = 2 * DAY
WEEK = 7 * DAY
MONTH = 30 * DAY
THREE_MONTHS = 3 * MONTH

SEMAPHORE_JOBS = 16

HTTP_IMG_URL = "https://cbjpeg.stream.highwebmedia.com/stream?room="

EDGES = [81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 106, 108,
         109, 110, 111, 112, 113, 115, 116, 117, 118, 119, 120, 123, 124, 125, 126, 133, 134, 135, 136, 137, 138, 139,
         140, 141, 142, 143, 144, 145, 146, 147, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 164,
         165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186,
         187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208,
         209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230,
         231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 248, 249, 250, 251, 252, 253,
         254, 256, 257, 259, 260, 261, 264, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 278, 279, 280, 281, 282,
         283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304,
         305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326,
         327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348,
         349, 350, 351, 352]

random.seed(time.time())
alive_edges = set()
last_successful_edge = None

executor = ThreadPoolExecutor(max_workers=20)

root = Tk()


class MainWindow:

    def __init__(self):
        global root

        self.http_session = requests.Session()
        self.http_session.headers.update(HEADERS)

        self.menu_bar = Menu(root)
        self.menu_bar.add_command(label="Back", command=self.back_in_history)
        # self.menu_bar.add_command(label="Toggle image", command=self.toggle_image)

        hist_menu = Menu(self.menu_bar, tearoff=0)
        hist_menu.add_command(label="All time", command=lambda: self.show_full_history(ALL_TIME))
        hist_menu.add_command(label="Last hour", command=lambda: self.show_full_history(HOUR))
        hist_menu.add_command(label="Two hours", command=lambda: self.show_full_history(TWO_HOURS))
        hist_menu.add_command(label="Six hours", command=lambda: self.show_full_history(SIX_HOURS))
        hist_menu.add_command(label="Half day", command=lambda: self.show_full_history(HALF_DAY))
        hist_menu.add_command(label="Last day", command=lambda: self.show_full_history(DAY))
        hist_menu.add_command(label="Two days", command=lambda: self.show_full_history(TWO_DAYS))
        hist_menu.add_command(label="Week", command=lambda: self.show_full_history(WEEK))
        hist_menu.add_command(label="Month", command=lambda: self.show_full_history(MONTH))
        hist_menu.add_command(label="Three months", command=lambda: self.show_full_history(THREE_MONTHS))
        self.menu_bar.add_cascade(label="History", menu=hist_menu)

        root.config(menu=self.menu_bar)

        self.session = None
        self.show_image = False
        self.hist_window = None

        self.model_name = None
        self.resolution = None
        self.update_title()

        self.level = 0

        self.image_label = Label(root)

        self.level += 1
        self.cb_model = ttk.Combobox(root, width=60)
        self.cb_model.bind("<FocusIn>", self.focus_callback)
        self.cb_model.bind("<Button-1>", self.drop_down_callback)
        self.cb_model.bind('<Return>', self.enter_callback)
        self.cb_model.focus_set()
        self.cb_model.grid(row=self.level, column=0, columnspan=3, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_add = Button(root, text="+", command=self.add_to_favorites)
        self.btn_add.grid(row=self.level, column=3, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_remove = Button(root, text="-", command=self.remove_from_favorites)
        self.btn_remove.grid(row=self.level, column=4, sticky=W + E, padx=PAD, pady=PAD)

        self.level += 1
        self.btn_update = Button(root, text="Update info", command=lambda: self.update_model_info(True))
        self.btn_update.grid(row=self.level, column=0, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_prev = Button(root, text="<< Prev", command=lambda: self.next_favorite(False))
        self.btn_prev.grid(row=self.level, column=1, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_next = Button(root, text="Next >>", command=lambda: self.next_favorite(True))
        self.btn_next.grid(row=self.level, column=2, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_scan = Button(root, text="Scan On", command=self.toggle_scan)
        self.btn_scan.grid(row=self.level, column=3, columnspan=2, sticky=W + E, padx=PAD, pady=PAD)

        self.level += 1
        self.btn_show_recording = Button(root,
                                         text="Show recording model",
                                         command=self.show_recording_model,
                                         state=DISABLED)
        self.btn_show_recording.grid(row=self.level, column=0, sticky=W + E, padx=PAD, pady=PAD)

        self.copy_button = Button(root, text="Copy", command=self.copy_model_name)
        self.copy_button.grid(row=self.level, column=1, sticky=W + E, padx=PAD, pady=PAD)

        self.paste_button = Button(root, text="Paste", command=self.paste_model_name)
        self.paste_button.grid(row=self.level, column=2, sticky=W + E, padx=PAD, pady=PAD)

        img = Image.open('assets/rec_small.png')
        self.img_record = ImageTk.PhotoImage(img)
        self.btn_start = Button(root, image=self.img_record, command=self.on_btn_start)
        self.btn_start.grid(row=self.level, column=3, sticky=W + E, padx=PAD, pady=PAD)

        img = Image.open('assets/stop_small.png')
        self.img_stop = ImageTk.PhotoImage(img)
        self.btn_stop = Button(root, image=self.img_stop, command=self.on_btn_stop, state=DISABLED)
        self.btn_stop.grid(row=self.level, column=4, sticky=W + E, padx=PAD, pady=PAD)

        self.level += 1
        self.progress = ttk.Progressbar(root, orient=HORIZONTAL, length=120, mode='indeterminate')

        root.bind("<FocusIn>", self.focus_callback)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.play_list_url = None
        self.base_url = None
        self.model_image = None
        self.img_url = None
        self.scan_idx = -1
        self.repeat = N_REPEAT
        self.img_counter = 0

        self.hist_logger = logging.getLogger('history')
        self.hist_logger.setLevel(logging.INFO)

        self.fh_hist = logging.FileHandler(os.path.join(LOGS, f'hist_{int(time.time())}.log'))
        self.fh_hist.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s\t%(message)s')
        self.fh_hist.setFormatter(formatter)
        self.hist_logger.addHandler(self.fh_hist)

        if REMEMBER_PROXIES:
            self.proxy_logger = logging.getLogger('proxy')
            self.proxy_logger.setLevel(logging.INFO)

            self.fh_proxy = logging.FileHandler(os.path.join(LOGS, f'proxy_{int(time.time())}.log'))
            self.fh_proxy.setLevel(logging.INFO)
            self.proxy_logger.addHandler(self.fh_proxy)

            self.proxy_dict = {}
            self.load_proxy_dict()

        self.hist_stack = []

        self.toggle_image()
        self.load_image()

    def on_btn_start(self):
        self.btn_start.config(state=DISABLED)

        self.stop()

        success = self.update_model_info(True)
        if not success:
            self.set_default_state()
            return

        self.session = RecordSession(self, self.base_url, self.model_name, self.resolution)
        self.session.start()

        self.btn_stop.config(state=NORMAL)
        self.btn_show_recording.config(state=NORMAL)
        self.progress.grid(row=self.level, column=0, columnspan=5, sticky=W + E, padx=PAD, pady=PAD)
        self.progress.start()

        self.update_title()
        self.add_to_favorites()

        root.configure(background='green')

    def on_btn_stop(self):
        self.stop()
        self.set_default_state()

    def stop(self):
        if self.session is None:
            return

        self.session.stop()
        self.session = None

    def copy_model_name(self):
        clipboard.copy(self.cb_model.get())

    def paste_model_name(self):
        self.load_model(clipboard.paste(), True)

    def update_model_info(self, remember):
        if remember and (self.model_name is not None):
            if len(self.hist_stack) == 0 or (self.model_name != self.hist_stack[-1]):
                self.hist_stack.append(self.model_name)

        self.set_undefined_state()

        input_url = self.cb_model.get().strip()

        if len(input_url) == 0:
            self.set_undefined_state()
            return False

        self.base_url = None
        if input_url.startswith('https://edge'):
            slash_pos = input_url.rfind('/')
            self.base_url = input_url[: slash_pos + 1]
            colon_pos = self.base_url.rfind(':', 0, -1)

            sd_pos = self.base_url.find('-sd-', colon_pos)
            if sd_pos == -1:
                sd_pos = self.base_url.find('-ws-', colon_pos)

            self.model_name = self.base_url[colon_pos + 1: sd_pos]
        elif input_url.startswith('http'):
            slash_pos = input_url[: -1].rfind('/')
            self.model_name = input_url[slash_pos + 1: -1] if input_url.endswith('/') else input_url[slash_pos + 1:]
        else:
            self.model_name = input_url

        if self.base_url is None:
            success = self.get_resolutions()
            if not success:
                success = self.get_resolutions()

            if not success:
                self.set_undefined_state()
                return False

        self.img_url = HTTP_IMG_URL + self.model_name
        self.hist_logger.info(self.model_name)
        self.update_title()
        self.set_scan(False)

        return True

    def add_to_favorites(self):
        input_url = self.cb_model.get().strip()
        name = get_model_name(input_url)

        if (len(name) > 0) and (name not in self.cb_model['values']):
            self.cb_model['values'] = (name, *self.cb_model['values'])
            self.hist_logger.info(name)

    def remove_from_favorites(self):
        input_url = self.cb_model.get().strip()
        name = get_model_name(input_url)
        values = list(self.cb_model['values'])
        if name not in values:
            return

        idx = values.index(name)

        values.remove(name)
        self.cb_model['values'] = tuple(values)
        if len(values) == 0:
            self.cb_model.set('')
        elif idx == 0:
            self.cb_model.set(values[0])
        else:
            self.cb_model.set(values[idx - 1])

    def add_to_proxies(self, proxy):
        if len(self.cb_proxy['values']) == 0:
            self.cb_proxy['values'] = proxy
        elif proxy not in self.cb_proxy['values']:
            self.cb_proxy['values'] = (proxy, *self.cb_proxy['values'])

        self.proxy_logger.info(proxy)
        count = self.proxy_dict.get(proxy, 0)
        self.proxy_dict[proxy] = count + 1

    def focus_callback(self, event):
        self.cb_model.selection_range(0, END)
        if self.hist_window is not None:
            self.hist_window.lift()

    def drop_down_callback(self, event):
        self.cb_model.focus_set()
        self.cb_model.selection_range(0, END)
        self.cb_model.event_generate('<Down>')

    def enter_callback(self, event):
        self.update_model_info(True)

    def get_resolutions(self):
        global last_successful_edge

        edge = last_successful_edge
        if edge is None:
            edge = random.choice(EDGES)
        playlist_url = f"https://edge{edge}.stream.highwebmedia.com/live-hls/amlst:{self.model_name}/playlist.m3u8"
        try:
            r = self.http_session.get(playlist_url, timeout=TIMEOUT)
            if r.status_code == 302:
                redirect_url = r.headers['Location']
                r = self.http_session.get(redirect_url, timeout=TIMEOUT)
            lines = r.text.splitlines()

            resolutions = [line for line in lines if not line.startswith("#")]
            resolutions.reverse()

            if len(resolutions) == 0:
                return False

            self.resolution = resolutions[0]

            actual_url = r.url
            slash_pos = actual_url.rfind('/')
            self.base_url = actual_url[: slash_pos + 1]
            last_successful_edge = edge
            return True
        except RequestException as error:
            print("GetPlayList exception model: " + self.model_name)
            print(error)
            traceback.print_exc()
            if last_successful_edge == edge:
                last_successful_edge = None
            return False

    def load_image(self):
        global executor
        global root

        if self.scan_idx >= 0:
            values = list(self.cb_model['values'])
            max_idx = len(values)

            if max_idx > 0:
                if self.scan_idx >= max_idx:
                    self.scan_idx = max_idx - 1

                item = values[self.scan_idx]
                root.title("Scanning: " + item)
                self.img_url = HTTP_IMG_URL + item

                if self.repeat <= 0:
                    self.scan_idx = (self.scan_idx + 1) % max_idx
                    self.repeat = N_REPEAT

                self.repeat -= 1

        self.img_counter += 1
        if (self.img_url is not None) and self.show_image:
        # if (self.img_url is not None or self.img_counter % 30 == 0) and self.show_image and (self.model_name is not None):
            executor.submit(self.fetch_image)

        root.update_idletasks()
        root.after(DELAY, self.load_image)

    def fetch_image(self):
        global root

        try:
            # if self.img_counter % 30 == 0:
            #     self.img_url = HTTP_IMG_URL + self.model_name

            response = self.http_session.get(self.img_url, timeout=TIMEOUT)
            img = Image.open(io.BytesIO(response.content))
            w, h = img.size
            k = 450 / w
            img_resized = img.resize((450, int(h * k)), resample=Image.Resampling.NEAREST, reducing_gap=1.0)
            root.after_idle(self.update_image, img_resized)
        except BaseException as error:
            print("Exception URL: " + self.img_url)
            print(error)
            traceback.print_exc()
            self.img_url = None
            self.model_image = None
            self.repeat = 0
            self.img_counter = 0

    def update_image(self, img):
        self.model_image = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.model_image)

    def on_close(self):
        global root

        self.stop()
        root.update_idletasks()
        root.destroy()
        self.fh_hist.close()
        self.hist_logger.removeHandler(self.fh_hist)
        if REMEMBER_PROXIES:
            self.fh_proxy.close()
            self.proxy_logger.removeHandler(self.fh_proxy)
        self.http_session.close()

    def set_default_state(self):
        global root

        self.session = None
        self.btn_stop.config(state=DISABLED)
        self.btn_start.config(state=NORMAL)
        self.btn_show_recording.config(state=DISABLED)
        self.progress.stop()
        self.progress.grid_forget()
        self.update_title()
        root.configure(background='SystemButtonFace')

    def update_title(self):
        global root

        root.title(self.model_name or '<Undefined>')

        if self.resolution is not None:
            chunks = self.resolution.split('_')
            if len(chunks) >= 3:
                best_bandwidth = chunks[2][1:]
                root.title(str(last_successful_edge) + " : " + root.title() + " (" + best_bandwidth + ") ")

        if self.session is None:
            return

        if not self.session.is_alive():
            return

        if root.title().find(self.session.model_name) == -1:
            return

        root.title(root.title() + " - Recording")

    def set_undefined_state(self):
        self.model_image = None
        self.image_label.config(image=None)
        self.model_name = None
        self.img_url = None
        self.resolution = None
        self.update_title()

    def show_recording_model(self):
        if self.session is None:
            return

        self.load_model(self.session.model_name, True)

    def on_use_proxy_change(self, *args):
        if self.use_proxy.get():
            self.cb_proxy.config(state=NORMAL)
            self.cb_proxy.focus_set()
            self.cb_proxy.selection_range(0, END)
        else:
            self.cb_proxy.config(state=DISABLED)

    def toggle_image(self):
        global root

        if self.show_image:
            self.model_image = None
            self.image_label.config(image=None)
            self.img_url = None
            # self.image_label.grid_forget()
            self.image_label.place_forget()
            self.show_image = False
            self.set_scan(False)
        else:
            self.show_image = True
            # self.image_label.grid(row=0, column=0, columnspan=5, sticky=W + E, padx=PAD, pady=PAD)
            self.image_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.update_model_info(True)

    def show_full_history(self, period):
        if self.hist_window is not None:
            self.hist_window.on_close()

        self.hist_window = HistoryWindow(self, Toplevel(root), load_hist_dict(period))

    def back_in_history(self):
        if len(self.hist_stack) == 0:
            return

        self.load_model(self.hist_stack.pop(), False)

    def load_proxy_dict(self):
        for file in os.listdir(LOGS):
            if not file.startswith('proxy_'):
                continue

            full_path = os.path.join(LOGS, file)
            if os.path.getsize(full_path) == 0:
                continue

            with open(full_path) as f:
                for line in f.readlines():
                    name = line.strip()
                    count = self.proxy_dict.get(name, 0)
                    self.proxy_dict[name] = count + 1

        hist = sorted(self.proxy_dict.items(), key=lambda x: x[1], reverse=True)
        self.cb_proxy.configure(values=[x[0] for x in hist[:10]])

    def toggle_scan(self):
        self.set_scan(self.scan_idx < 0)

    def set_scan(self, active):
        if active:
            input_url = self.cb_model.get().strip()
            name = get_model_name(input_url)
            values = list(self.cb_model['values'])
            sz = len(values)
            if sz < 2:
                return
            if name not in values:
                self.scan_idx = 0
            else:
                self.scan_idx = (values.index(name) + 1) % sz
            self.repeat = N_REPEAT
            self.btn_scan.config(text="Scan Off")
            return

        self.scan_idx = -1
        self.btn_scan.config(text="Scan On")

    def next_favorite(self, forward):
        input_url = self.cb_model.get().strip()
        name = get_model_name(input_url)
        values = list(self.cb_model['values'])
        sz = len(values)
        if sz < 2:
            return
        if name not in values:
            return

        idx = values.index(name)
        step = 1 if forward else -1
        next_item = values[(idx + step) % sz]

        self.load_model(next_item, True)

    def load_model(self, model, remember):
        self.cb_model.set(model)
        self.cb_model.selection_range(0, END)
        self.update_model_info(remember)

    def on_shrink(self):
        pass


def load_hist_dict(period):
    now = time.time()

    res = {}
    for file in os.listdir(LOGS):
        if not file.startswith('hist_'):
            continue

        full_path = os.path.join(LOGS, file)
        if os.path.getsize(full_path) == 0:
            continue

        mtime = os.path.getmtime(full_path)
        diff = now - mtime

        if (period != ALL_TIME) and (diff > period):
            continue

        with open(full_path) as f:
            for line in f.readlines():
                parts = line.strip().split('\t')
                if len(parts) == 1:
                    name = parts[0]
                else:
                    stamp = datetime.datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S,%f').timestamp()
                    name = parts[1]
                    diff = now - stamp
                    if (period != ALL_TIME) and (diff > period):
                        continue

                count = res.get(name, 0)
                res[name] = count + 1

    return res


def get_model_name(input_url):
    if input_url.startswith('https://edge'):
        slash_pos = input_url.rfind('/')
        b_url = input_url[: slash_pos + 1]
        colon_pos = b_url.rfind(':', 0, -1)

        sd_pos = b_url.find('-sd-', colon_pos)
        if sd_pos == -1:
            sd_pos = b_url.find('-ws-', colon_pos)

        return b_url[colon_pos + 1: sd_pos]
    elif input_url.startswith('http'):
        slash_pos = input_url[: -1].rfind('/')
        return input_url[slash_pos + 1: -1] if input_url.endswith('/') else input_url[slash_pos + 1:]
    else:
        return input_url


class Model:
    def __init__(self, pos, name):
        self.model_name = name
        self.pos = pos
        self.is_online = False


async def fetch(url, session):
    try:
        async with session.get(url) as response:
            if response.status != 200:
                if response.status != 403:
                    print(response.status, url)

                if response.status == 503 or response.status == 502:
                    return 'Retry'

                return ''

            return await response.read()
    except (ClientConnectorError, ServerTimeoutError) as e:
        print(e, url)
        return 'Retry'
    except BaseException as error:
        print(error)
        traceback.print_exc()
        return ''


async def bound_fetch(sem, url, session):
    # Getter function with semaphore.
    async with sem:
        return await fetch(url, session)


async def fetch_playlists(model_list):
    # create instance of Semaphore
    sem = asyncio.Semaphore(SEMAPHORE_JOBS)
    tasks = []

    time_out = aiohttp.ClientTimeout(sock_connect=2.05, sock_read=3.05)
    async with ClientSession(timeout=time_out) as session:
        for rnd, model in model_list:
            playlist_url = f"https://edge{rnd}.stream.highwebmedia.com/live-hls/amlst:{model.model_name}/playlist.m3u8"
            task = asyncio.ensure_future(bound_fetch(sem, playlist_url, session))
            tasks.append(task)

        return await asyncio.gather(*tasks)


def update_models_bps(model_list, tries):
    global last_successful_edge

    if len(model_list) == 0:
        return

    print("try #", tries)

    if tries > 1:
        time.sleep(1)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError as e:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if len(alive_edges) < SEMAPHORE_JOBS // 4:
        rnd_sample = random.sample(EDGES, len(model_list))
    else:
        rnd_sample = random.choices(list(alive_edges), k=len(model_list))
    future = asyncio.ensure_future(fetch_playlists(zip(rnd_sample, model_list)))
    results = zip(model_list, rnd_sample, loop.run_until_complete(future))

    failed = []
    for model, edge, response in results:
        if len(response) == 0:
            model.is_online = False
            continue

        if response == 'Retry':
            failed.append(model)
            continue

        model.is_online = True

        if edge is not None:
            last_successful_edge = edge
            alive_edges.add(edge)

    update_models_bps(failed, tries + 1)


class HistoryWindow:
    MAX_QUERY_SIZE = 64

    def __init__(self, parent, win, hist_dict):
        self.window = win
        self.parent_window = parent
        self.hist_dict = hist_dict
        self.window.title("Full history")
        # self.window.resizable(False, False)

        frm_top = Frame(win)
        frm_bottom = Frame(win)

        self.btn_test = Button(frm_top, text="Test", command=self.on_test)
        self.btn_test.grid(row=1, column=1, sticky=W + E)

        self.progress = ttk.Progressbar(frm_top, orient=HORIZONTAL, length=30, mode='indeterminate')

        self.btn_test_next = Button(frm_top, text="Test Next", command=self.on_test_next)
        self.btn_test_next.grid(row=1, column=4, sticky=W + E)

        self.search = StringVar()
        self.search.trace("w", lambda name, index, mode, sv=self.search: self.on_search(sv))
        self.entry_search = Entry(frm_top, textvariable=self.search, width=52)
        self.entry_search.grid(row=2, column=1, columnspan=3, sticky=W + E)

        self.btn_clear = Button(frm_top, text="Clear", command=self.on_clear)
        self.btn_clear.grid(row=2, column=4, sticky=W + E)

        self.list_box = Listbox(frm_bottom, width=60, height=40, selectmode=SINGLE)
        self.list_box.pack(side=LEFT, fill=BOTH, expand=1)
        scroll = Scrollbar(frm_bottom, command=self.list_box.yview, orient=VERTICAL)
        scroll.pack(side=RIGHT, fill=Y)
        self.list_box.config(yscrollcommand=scroll.set)
        self.list_box.bind('<<ListboxSelect>>', self.on_listbox_select)

        frm_top.pack()
        frm_bottom.pack()

        self.window.bind("<FocusIn>", self.focus_callback)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.test_online_start = 0

        self.fill_list_box()

    def on_clear(self):
        self.search.set("")
        self.on_search(self.search)

    def on_search(self, search):
        query = search.get().strip().lower()
        if len(query) < 2:
            self.fill_list_box()
            return

        self.list_box.delete(0, END)
        search_results = []
        for key in self.hist_dict:
            pos = key.lower().find(query)
            if pos == -1:
                continue

            search_results.append((key, pos))

        search_results.sort(key=lambda x: x[1])
        self.list_box.insert(END, *[x[0] for x in search_results])

    def fill_list_box(self):
        self.list_box.delete(0, END)
        hist = sorted(self.hist_dict.items(), key=lambda x: x[1], reverse=True)
        self.list_box.insert(END, *[x[0] for x in hist])

    def on_listbox_select(self, event):
        w = event.widget
        selected = w.curselection()
        if len(selected) == 0:
            return

        index = selected[0]
        value = w.get(index)
        self.parent_window.load_model(value, True)

    def lift(self):
        self.window.lift()

    def on_close(self):
        self.parent_window.hist_window = None
        self.window.update_idletasks()
        self.window.destroy()

    def focus_callback(self, event):
        self.entry_search.selection_range(0, END)
        root.lift()

    def test_online(self, model_list):
        global root

        update_models_bps(model_list, 1)
        root.after_idle(self.update_listbox, model_list)

    def update_listbox(self, model_list):
        for model in model_list:
            self.list_box.itemconfig(model.pos, {'fg': 'red' if model.is_online else 'blue'})
        self.set_controls_state(NORMAL)

    def on_test(self):
        self.test_online_start = 0
        for i in range(self.list_box.size()):
            self.list_box.itemconfig(i, {'fg': 'black'})

        self.on_test_next()

    def on_test_next(self):
        items = self.list_box.get(self.test_online_start, self.test_online_start + HistoryWindow.MAX_QUERY_SIZE - 1)

        model_list = []
        for i, name in zip(range(self.test_online_start, self.test_online_start + len(items)), items):
            model_list.append(Model(i, name))

        self.test_online_start += HistoryWindow.MAX_QUERY_SIZE
        self.set_controls_state(DISABLED)

        executor.submit(self.test_online, model_list)

    def set_controls_state(self, state):
        self.btn_test.config(state=state)
        self.btn_test_next.config(state=state)
        self.btn_clear.config(state=state)
        self.entry_search.config(state=state)

        if state == DISABLED:
            self.progress.grid(row=1, column=2, columnspan=2, sticky=W + E)
            self.progress.start()
        else:
            self.progress.grid_forget()
            self.progress.stop()


class Chunks:
    IDX_CUR_POS = 3

    def __init__(self, lines):
        self.ts = [line for line in lines if not line.startswith("#")]
        self.cur_pos = int(lines[Chunks.IDX_CUR_POS].split(':')[1])


class SessionPool:

    def __init__(self, count):
        self.size = count
        self.data = []
        self.current = 0
        for i in range(self.size):
            s = requests.Session()
            s.headers.update(HEADERS)
            self.data.append(s)

    def get(self):
        s = self.data[self.current]
        self.current += 1
        self.current %= self.size
        return s


POOL = SessionPool(5)


class RecordSession(Thread):
    MIN_CHUNKS = 6

    def __init__(self, main_win, url_base, model, chunk_url):
        super(RecordSession, self).__init__()

        self.http_session = requests.Session()
        self.http_session.headers.update(HEADERS)

        self.main_win = main_win
        self.base_url = url_base
        self.model_name = model
        self.output_dir = os.path.join(OUTPUT, self.model_name + '_' + str(int(time.time())))
        os.mkdir(self.output_dir)

        self.chunks_url = urljoin(self.base_url, chunk_url)
        self.name = 'RecordSession'
        self.stopped = False
        self.daemon = True
        self.file_num = 1
        self.file_deq = deque(maxlen=4)

        self.logger = logging.getLogger('beeg_application')
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] %(threadName)s:%(funcName)s > %(message)s')

        self.fh = logging.FileHandler(os.path.join(self.output_dir, self.model_name + '.log'))
        self.fh.setLevel(logging.DEBUG)
        self.fh.setFormatter(formatter)
        self.logger.addHandler(self.fh)

    def get_chunks(self):
        self.logger.debug(self.chunks_url)
        try:
            r = self.http_session.get(self.chunks_url, timeout=TIMEOUT)
            if r.status_code != 200:
                self.logger.debug(f"Status {r.status_code}: {self.chunks_url}")
                return None

            lines = r.text.splitlines()

            if len(lines) < RecordSession.MIN_CHUNKS:
                return None

            return Chunks(lines)
        except RequestException as error:
            self.logger.exception(error)
            return None

    def save_to_file(self, remote_filename, local_filename):
        self.logger.debug(remote_filename)
        file_path = os.path.join(self.output_dir, local_filename)

        ts_url = urljoin(self.base_url, remote_filename)
        try:
            session = POOL.get()
            with session.get(ts_url, stream=True, timeout=TIMEOUT) as r, open(file_path, 'wb') as fd:
                if r.status_code != 200:
                    self.logger.debug(f"Status {r.status_code}: {remote_filename}")
                    return
                for chunk in r.iter_content(chunk_size=65536):
                    fd.write(chunk)
        except BaseException as error:
            self.logger.exception(error)

    def run(self):
        global executor
        global root

        self.logger.info("Started!")
        fails = 0
        last_pos = 0

        while not self.stopped:
            chunks = self.get_chunks()
            if chunks is None:
                self.logger.info("Offline : " + self.chunks_url)
                fails += 1

                if fails > MAX_FAILS:
                    break

                time.sleep(1)
                continue
            else:
                fails = 0

            if last_pos >= chunks.cur_pos:
                time.sleep(0.5)
                continue

            last_pos = chunks.cur_pos
            self.logger.debug(last_pos)

            try:
                for ts in chunks.ts:
                    if ts in self.file_deq:
                        self.logger.debug("Skipped: " + ts)
                        continue

                    self.file_deq.append(ts)
                    executor.submit(self.save_to_file, ts, f'{self.file_num:020}.ts')
                    self.file_num += 1
            except BaseException as e:
                self.logger.exception(e)

            time.sleep(0.5)

        try:
            root.after_idle(self.main_win.set_default_state)
        except RuntimeError as e:
            self.logger.exception(e)

        self.logger.info("Exited!")
        self.fh.close()
        self.logger.removeHandler(self.fh)
        self.http_session.close()

    def stop(self):
        self.stopped = True


if __name__ == "__main__":
    if not os.path.exists(LOGS):
        os.mkdir(LOGS)
    if not os.path.exists(OUTPUT):
        os.mkdir(OUTPUT)

    # root.resizable(False, False)
    my_gui = MainWindow()
    if len(sys.argv) > 4:
        w = sys.argv[1]
        h = sys.argv[2]
        x = sys.argv[3]
        y = sys.argv[4]
        root.geometry(f'{w}x{h}+{x}+{y}')

    root.mainloop()
