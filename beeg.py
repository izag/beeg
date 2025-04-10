import asyncio
import datetime
import io
import logging
import os
import random
import re
import socket
import sys
import time
import traceback
from collections import deque
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue
from threading import Thread
from tkinter import Tk, Button, ttk, W, E, Label, DISABLED, NORMAL, Menu, END, HORIZONTAL, \
    Toplevel, Listbox, Scrollbar, LEFT, Y, SINGLE, BOTH, RIGHT, VERTICAL, Frame, Entry, \
    StringVar, BOTTOM, X, Canvas
from urllib.parse import urljoin

import aiohttp
import clipboard
import cloudscraper
import requests
import vlc
from PIL import Image, ImageTk
from aiohttp import ClientSession, ClientConnectorError, ServerTimeoutError
from requests import RequestException
from urllib3 import Retry

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0'

REFERER = 'https://jpeg.live.mmcdn.com'

proxies = None

REMEMBER_PROXIES = False

HEADERS = {
    'User-Agent': USER_AGENT,
    'Referer': REFERER
}

CHATUBAT_NET_RU_HEADERS = {
    'User-Agent': USER_AGENT,
    'Referer': 'https://chaturbat.net.ru',
    'Host': 'chaturbat.net.ru',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'X-Requested-With': 'XMLHttpRequest',
    'DNT': '1',
    'Sec-GPC': '1',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'TE': 'trailers',
}

TIMEOUT = (3.05, 9.05)
SHORT_IMG_DELAY = 2000
LONG_IMG_DELAY = 30000
SHORT_REC_DURATION = 120
PAD = 5
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

HTTP_IMG_URL = "https://jpeg.live.mmcdn.com/stream?room="

PLAYER_HOST = 'localhost'
PLAYER_PORT = 8686

random.seed(time.time())
alive_edges = set()
last_successful_edge = None

executor = ThreadPoolExecutor(max_workers=5)


class ThreadPoolExecutorWithQueueSizeLimit(ThreadPoolExecutor):
    def __init__(self, maxsize=1, *args, **kwargs):
        super(ThreadPoolExecutorWithQueueSizeLimit, self).__init__(*args, **kwargs)
        self._work_queue = Queue(maxsize=maxsize)


image_loader = ThreadPoolExecutor(max_workers=1)
image_loader_future = None

root = Tk()


class MainWindow:

    def __init__(self):
        global root

        self.http_session = requests.Session()
        self.http_session.headers.update(HEADERS)
        self.http_session.adapters['https://'].max_retries = Retry.DEFAULT

        self.menu_bar = Menu(root)
        self.menu_bar.add_command(label="Back", command=self.back_in_history)
        self.menu_bar.add_command(label="Toggle image", command=self.toggle_image)

        self.hist_menu = Menu(self.menu_bar, tearoff=0)
        self.hist_menu.add_command(label="All time", command=lambda: self.show_full_history(ALL_TIME))
        self.hist_menu.add_command(label="Last hour", command=lambda: self.show_full_history(HOUR))
        self.hist_menu.add_command(label="Two hours", command=lambda: self.show_full_history(TWO_HOURS))
        self.hist_menu.add_command(label="Six hours", command=lambda: self.show_full_history(SIX_HOURS))
        self.hist_menu.add_command(label="Half day", command=lambda: self.show_full_history(HALF_DAY))
        self.hist_menu.add_command(label="Last day", command=lambda: self.show_full_history(DAY))
        self.hist_menu.add_command(label="Two days", command=lambda: self.show_full_history(TWO_DAYS))
        self.hist_menu.add_command(label="Week", command=lambda: self.show_full_history(WEEK))
        self.hist_menu.add_command(label="Month", command=lambda: self.show_full_history(MONTH))
        self.hist_menu.add_command(label="Three months", command=lambda: self.show_full_history(THREE_MONTHS))
        self.menu_bar.add_cascade(label="History", menu=self.hist_menu)

        self.menu_bar.add_command(label="Link", command=self.copy_model_link)
        # self.menu_bar.add_command(label="Play", command=self.copy_recording_path)
        # self.menu_bar.add_command(label="View", command=self.show_player_window)

        root.config(menu=self.menu_bar)

        self.record_sessions = {}
        self.show_image = False
        self.record_started = False
        self.hist_window = None

        self.model_name = None
        self.resolution = None

        self.level = 0

        self.image_label = Label(root)
        # self.image_label = Canvas(root, bd=0, highlightthickness=0)
        # self.bg_img = None

        self.level += 1
        self.cb_model = ttk.Combobox(root, width=60)
        self.cb_model.bind("<FocusIn>", self.focus_in_callback)
        self.cb_model.bind("<Button-1>", self.drop_down_callback)
        self.cb_model.bind('<Return>', self.enter_callback)
        self.cb_model.focus_set()
        self.cb_model.grid(row=self.level, column=0, columnspan=3, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_add = Button(root, text="+", command=self.add_to_combobox)
        self.btn_add.grid(row=self.level, column=3, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_remove = Button(root, text=" - ", command=self.remove_from_favorites)
        self.btn_remove.grid(row=self.level, column=4, sticky=W + E, padx=PAD, pady=PAD)

        self.level += 1
        self.btn_update = Button(root, text="Update info", command=lambda: self.update_model_info_async(True))
        self.btn_update.grid(row=self.level, column=0, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_prev = Button(root, text="<< Prev", command=lambda: self.next_favorite(False))
        self.btn_prev.grid(row=self.level, column=1, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_next = Button(root, text="Next >>", command=lambda: self.next_favorite(True))
        self.btn_next.grid(row=self.level, column=2, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_play = Button(root, text="Play", command=self.play_recording)
        self.btn_play.grid(row=self.level, column=3, columnspan=2, sticky=W + E, padx=PAD, pady=PAD)

        self.level += 1
        self.btn_record_short = Button(root, text="Record short", command=lambda: self.on_record(SHORT_REC_DURATION))
        self.btn_record_short.grid(row=self.level, column=0, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_copy = Button(root, text="Copy", command=self.copy_model_name)
        self.btn_copy.grid(row=self.level, column=1, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_paste = Button(root, text="Paste", command=self.paste_model_name)
        self.btn_paste.grid(row=self.level, column=2, sticky=W + E, padx=PAD, pady=PAD)

        img = Image.open('assets/rec_small.png')
        self.img_record = ImageTk.PhotoImage(img)
        self.btn_start = Button(root, image=self.img_record, command=self.on_btn_start)
        self.btn_start.grid(row=self.level, column=3, sticky=W + E, padx=PAD, pady=PAD)

        img = Image.open('assets/stop_small.png')
        self.img_stop = ImageTk.PhotoImage(img)

        img = Image.open('assets/rec1_small.png')
        self.img_paste_record = ImageTk.PhotoImage(img)
        self.btn_paste_record = Button(root, image=self.img_paste_record, command=lambda: self.on_paste_and_record(SHORT_REC_DURATION))
        self.btn_paste_record.grid(row=self.level, column=4, sticky=W + E, padx=PAD, pady=PAD)

        self.level += 1
        self.progress = ttk.Progressbar(root, orient=HORIZONTAL, length=120, mode='indeterminate')
        
        self.sv_stats = StringVar()
        self.lbl_stats = Label(root, textvariable=self.sv_stats)
        self.lbl_stats.grid(row=self.level, column=0, columnspan=4, sticky=W + E, padx=PAD, pady=PAD)

        root.bind("<FocusIn>", self.focus_in_callback)
        root.bind("<FocusOut>", self.focus_out_callback)
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

        self.fh_hist = logging.FileHandler(os.path.join(LOGS, f'hist_{int(time.time() * 1000000)}.log'))
        self.fh_hist.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s\t%(message)s')
        self.fh_hist.setFormatter(formatter)
        self.hist_logger.addHandler(self.fh_hist)

        if REMEMBER_PROXIES:
            self.proxy_logger = logging.getLogger('proxy')
            self.proxy_logger.setLevel(logging.INFO)

            self.fh_proxy = logging.FileHandler(os.path.join(LOGS, f'proxy_{int(time.time() * 1000000)}.log'))
            self.fh_proxy.setLevel(logging.INFO)
            self.proxy_logger.addHandler(self.fh_proxy)

            self.proxy_dict = {}
            self.load_proxy_dict()

        self.hist_stack = []

        self.update_title()
        self.toggle_image()

        self.load_image_task_id = None
        self.load_image_delay = LONG_IMG_DELAY

        # self.vlc_instance = vlc.Instance()
        # self.media_player = self.vlc_instance.media_player_new()

        # edge for browsing
        self.edges = {}

    def on_btn_start(self):
        if self.record_started:
            self.on_btn_stop()
            self.record_started = False
            self.btn_start.config(image=self.img_record)
            return
        
        self.on_record(0)

    def on_paste_and_record(self, duration):
        model = clipboard.paste()
        self.cb_model.set(model)

        success = self.update_base_url(True)
        if not success:
            return
        
        model = self.model_name
        session = self.record_sessions.get(model, None)
        if session is not None and session.is_alive():
            self.process_online_model()
            self.disable_for_update(NORMAL)
            return
        
        if self.base_url is None or self.resolution is None:
            get_resolutions_future = executor.submit(self.get_resolutions_retry, model, True)
            get_resolutions_future.add_done_callback(lambda f: root.after_idle(self.after_successful_start, f, model, duration))
            return

        # in case of edge url input
        self.start_recording(model, duration)

    def on_record(self, duration):
        session = self.record_sessions.get(self.model_name, None)
        if session is not None and session.is_alive():
            return
        
        success = self.update_base_url(True)
        if not success:
            return
        
        model = self.model_name
        if self.base_url is None or self.resolution is None:
            get_resolutions_future = executor.submit(self.get_resolutions_retry, model, True)
            get_resolutions_future.add_done_callback(lambda f: root.after_idle(self.after_successful_start, f, model, duration))
            return

        # in case of edge url input
        self.start_recording(model, duration)

    def after_successful_start(self, future, model, duration):
        success = future.result()
        if not success:
            self.set_undefined_state()
            self.disable_for_update(NORMAL)
            return

        self.start_recording(model, duration)

    def start_recording(self, model, duration):
        session = RecordSession(self, self.base_url, model, self.resolution, self.hist_logger, duration)
        self.record_sessions[model] = session
        session.start()

        self.record_started = True
        self.btn_start.config(image=self.img_stop)
        self.add_model_to_combobox(model)
        self.process_online_model()
        self.disable_for_update(NORMAL)

    def on_btn_stop(self):
        self.stop()
        self.update_title()

    def stop(self):
        session = self.record_sessions.get(self.model_name, None)
        if session is None:
            return

        session.stop()
        del self.record_sessions[self.model_name]

    def copy_model_name(self):
        clipboard.copy(self.cb_model.get())

    def paste_model_name(self):
        self.load_model(clipboard.paste(), True)

    def copy_model_link(self):
        clipboard.copy(urljoin(self.base_url, 'playlist.m3u8'))

    def play_recording(self):
        session = self.record_sessions.get(self.model_name, None)
        if session is None or not session.is_alive():
            return

        clipboard.copy(session.output_dir)
        executor.submit(send_to_player, session.output_dir) 

    def update_base_url(self, remember):
        if remember and (self.model_name is not None):
            if len(self.hist_stack) == 0 or (self.model_name != self.hist_stack[-1]):
                self.hist_stack.append(self.model_name)

        self.set_undefined_state()
        self.disable_for_update(DISABLED)

        self.record_sessions = { model: thread for model, thread in self.record_sessions.items() if thread is not None and thread.is_alive() }

        input_url = self.cb_model.get().strip()

        if len(input_url) == 0:
            self.set_undefined_state()
            self.disable_for_update(NORMAL)
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
            chunk_pos = input_url.rfind('chunklist')
            if chunk_pos >= 0:
                self.resolution = input_url[chunk_pos:]
            # found = re.search(r"https://(.*?)/", input_url, re.DOTALL)
            # if (found is not None) and (found.group(0) is not None):
            #     self.edge = found.group(1)
        elif input_url.startswith('http'):
            slash_pos = input_url[: -1].rfind('/')
            self.model_name = input_url[slash_pos + 1: -1] if input_url.endswith('/') else input_url[slash_pos + 1:]
        else:
            self.model_name = input_url

        return True

    def update_model_info_async(self, remember):
        success = self.update_base_url(remember)
        if not success:
            return

        if self.base_url is None:
            get_resolutions_future = executor.submit(self.test_online)
            get_resolutions_future.add_done_callback(lambda f: root.after_idle(self.after_test_online, f))
            return

        self.process_online_model()
        self.disable_for_update(NORMAL)

    def test_online(self):
        img_url = HTTP_IMG_URL + self.model_name + f"&f={random.random()}"
        try:
            response = self.http_session.get(img_url, timeout=TIMEOUT)
            if response.status_code != 200:
                return False
            
            img = Image.open(io.BytesIO(response.content))
            return True
        except BaseException as error:
            print("Exception URL: " + img_url)
            print(error)
            traceback.print_exc()
            return False

    def after_test_online(self, future):
        success = future.result()
        self.disable_for_update(NORMAL)
        if not success:
            self.set_undefined_state()
            return
        
        self.process_online_model()

    def process_online_model(self):
        self.img_url = HTTP_IMG_URL + self.model_name
        self.update_title()
        # self.set_scan(False)
        self.start_load_image()

    def disable_for_update(self, new_state):
        self.btn_update.config(state=new_state)
        # self.btn_prev.config(state=new_state)
        # self.btn_next.config(state=new_state)
        # self.btn_play.config(state=new_state)
        # self.btn_copy.config(state=new_state)
        # self.btn_paste.config(state=new_state)
        self.btn_start.config(state=new_state)
        self.btn_paste_record.config(state=new_state)
        self.btn_record_short.config(state=new_state)
        # if self.hist_window is not None:
        #     self.hist_window.list_box.config(state=new_state)

    def add_to_combobox(self):
        input_url = self.cb_model.get().strip()
        name = get_model_name(input_url)
        self.add_model_to_combobox(name)

    def add_model_to_combobox(self, model):
        if (len(model) > 0) and (model not in self.cb_model['values']):
            self.cb_model['values'] = (model, *self.cb_model['values'])
            self.hist_logger.info(model)

        if len(self.cb_model['values']) > 1:
            self.btn_next.config(state=NORMAL)
            self.btn_prev.config(state=NORMAL)

        self.update_title()

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

        if len(values) < 2:
            self.btn_next.config(state=DISABLED)
            self.btn_prev.config(state=DISABLED)

        self.update_title()

    def add_to_proxies(self, proxy):
        if len(self.cb_proxy['values']) == 0:
            self.cb_proxy['values'] = proxy
        elif proxy not in self.cb_proxy['values']:
            self.cb_proxy['values'] = (proxy, *self.cb_proxy['values'])

        self.proxy_logger.info(proxy)
        count = self.proxy_dict.get(proxy, 0)
        self.proxy_dict[proxy] = count + 1

    def focus_in_callback(self, event):
        if event.widget != root:
            return

        self.start_load_image()
        # self.cb_model.selection_range(0, END)
        if self.hist_window is not None:
            self.hist_window.lift()

    def focus_out_callback(self, event):
        self.load_image_delay = LONG_IMG_DELAY

    def start_load_image(self):
        try:
            root.after_cancel(self.load_image_task_id)
        except ValueError:
            pass
        self.load_image_delay = SHORT_IMG_DELAY
        self.load_image_task_id = root.after_idle(self.load_image)

    def drop_down_callback(self, event):
        self.cb_model.focus_set()
        # self.cb_model.selection_range(0, END)
        self.cb_model.event_generate('<Down>')

    def enter_callback(self, event):
        self.update_model_info_async(True)

    def get_hls_source(self):
        try:
            self.http_session.headers.update(CHATUBAT_NET_RU_HEADERS)
            self.http_session.adapters['https://'].max_retries = Retry.DEFAULT
            scraper = cloudscraper.create_scraper(self.http_session)
            # r = scraper.get(f"https://chaturbat.net.ru/{self.model_name}", timeout=(3.05, 9.05))
            # if r.status_code != 200:
            #     return None
            r = scraper.get(f"https://chaturbat.net.ru/chat-model/{self.model_name}/none.json", timeout=(3.05, 9.05))
            if r.status_code != 200:
                return None
            result = r.json()

            if result['room_status'] != 'public':
                return None

            return result['hls_source']
        except BaseException as error:
            print(error)
            traceback.print_exc()

    def get_resolutions(self, model, for_record):
        playlist_url = self.edges.get(model, None)
        # if self.edge is None or for_record:
        if playlist_url is None:
            playlist_url = self.get_hls_source()
            if playlist_url is None or len(playlist_url) < 1:
                return False

            # found = re.search(r"https://(.*?)/live-hls/amlst:(.*?)-sd-(.*?)/playlist.m3u8", playlist_url, re.DOTALL)
            # if (found is not None) and (found.group(0) is not None):
            #     self.edge = found.group(1)
            #     if for_record:
            #         self.edges[model] = found.group(1)
            #         self.suffix = found.group(3)
            # else:
            #     print("Url", playlist_url, "doesn't match the template!")
        # else:
        #     playlist_url = f"https://{model_edge}/live-hls/amlst:{model}-sd-{self.suffix}/playlist.m3u8"
        #     self.edge = model_edge
        # else:
        #     playlist_url = f"https://{self.edge}/live-hls/amlst:{model}-sd-{self.suffix}/playlist.m3u8"

        try:
            self.http_session.headers.update(HEADERS)
            r = self.http_session.get(playlist_url, timeout=TIMEOUT)
            if r.status_code == 302:
                redirect_url = r.headers['Location']
                r = self.http_session.get(redirect_url, timeout=TIMEOUT)

            if r.status_code == 404:
                print("get_resolutions status code 404 for url:", playlist_url)
                del self.edges[model]
                return False

            print("Url is OK:", playlist_url)
            self.edges[model] = playlist_url

            lines = r.text.splitlines()

            resolutions = [line for line in lines if not line.startswith("#")]
            resolutions.reverse()

            if len(resolutions) == 0:
                return False

            self.resolution = resolutions[0]

            actual_url = r.url
            slash_pos = actual_url.rfind('/')
            self.base_url = actual_url[: slash_pos + 1]
            return True
        except RequestException as error:
            print("GetPlayList exception model: " + model)
            print(error)
            traceback.print_exc()

            del self.edges[model]
            
            return False
        
    def get_resolutions_retry(self, model, for_record):
        success = self.get_resolutions(model, for_record)
        if not success:
            success = self.get_resolutions(model, for_record)
        if not success:
            success = self.get_resolutions(model, for_record)
        if not success:
            success = self.get_resolutions(model, for_record)

        return success

    def load_image(self):
        global image_loader
        global image_loader_future
        global root

        if self.img_url is None or not self.show_image:
            return

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
        if image_loader_future is None or image_loader_future.done():
            # if (self.img_url is not None or self.img_counter % 30 == 0) and self.show_image and (self.model_name is not None):
            image_loader_future = image_loader.submit(self.fetch_image)

        root.update_idletasks()
        self.load_image_task_id = root.after(self.load_image_delay, self.load_image)

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
            self.model_image = ImageTk.PhotoImage(img_resized)
            root.after_idle(self.update_image)
        except BaseException as error:
            print("Exception URL: " + self.img_url)
            print(error)
            traceback.print_exc()
            self.img_url = None
            self.model_image = None
            self.repeat = 0
            self.img_counter = 0

    def update_image(self):
        # self.model_image = ImageTk.PhotoImage(img)
        # width, height = img.size
        # self.image_label.config(width=width, height=height)
        # x_center = width // 2
        # y_center = height // 2
        # if self.bg_img is None:
        #     self.bg_img = self.image_label.create_image(x_center, y_center, image=self.model_image)
        # else:
        #     self.image_label.itemconfigure(self.bg_img, image=self.model_image)
        #     self.image_label.coords(self.bg_img, x_center, y_center)
        session = self.record_sessions.get(self.model_name, None)
        if session is not None and session.is_alive():
            remains = session.get_remaining()
            if remains > 0:
                self.btn_record_short.config(text=f"Remains {remains}")
            empty = session.get_empty()
            missed = session.get_missed()
            self.sv_stats.set(f"Empty: {empty}\nMissed: {missed}")
        else:
            self.sv_stats.set("")

        self.image_label.config(image=self.model_image)

    def on_close(self):
        global root

        for model, session in self.record_sessions.items():
            if session is None:
                continue

            session.stop()

        root.update_idletasks()
        root.destroy()
        # executor.shutdown(False, cancel_futures=True)
        # image_loader.shutdown(False, cancel_futures=True)
        self.fh_hist.close()
        self.hist_logger.removeHandler(self.fh_hist)
        if REMEMBER_PROXIES:
            self.fh_proxy.close()
            self.proxy_logger.removeHandler(self.fh_proxy)
        self.http_session.close()

    def set_default_state(self):
        global root

        # self.session = None
        self.btn_paste_record.config(state=NORMAL)
        self.btn_start.config(state=NORMAL)
        self.btn_record_short.config(state=NORMAL)
        self.progress.stop()
        self.progress.grid_forget()
        self.update_title()
        root.configure(background='SystemButtonFace')

    def update_title(self):
        global root

        self.btn_update.configure(background='SystemButtonFace')
        self.btn_record_short.config(text='Record short')

        infinite = 0
        for m, s in self.record_sessions.items():
            if s.is_alive() and s.get_remaining() == -1:
                infinite += 1

        stats = f'({len(self.record_sessions)}/{infinite}/{len(self.cb_model['values'])})'

        if self.model_name is None:
            self.record_started = False
            self.btn_start.config(image=self.img_record, state=DISABLED)
            root.title(f'{stats} <Undefined>')
            return
        
        root.title(f'{stats} {self.model_name}')

        if self.resolution is not None:
            chunks = self.resolution.split('_')
            if len(chunks) >= 3:
                best_bandwidth = chunks[2][1:]
                edge_addr = '' # self.edges.get(self.model_name, self.edge)
                root.title(f'{stats} {edge_addr} : {self.model_name} ({best_bandwidth}) ')

        session = self.record_sessions.get(self.model_name, None)

        self.record_started = session is not None and session.is_alive()
        self.btn_start.config(state=NORMAL, image=self.img_stop if self.record_started else self.img_record)

        if not self.record_started:
            return

        root.title(root.title() + " - Recording")
        self.btn_update.configure(background='green' if session.duration > 0 else 'red')
        

    def update_active_records(self, model_name):
        self.record_sessions = { model: thread for model, thread in self.record_sessions.items() if thread is not None and thread.is_alive() }
        self.update_title()

    def set_undefined_state(self):
        self.model_image = None
        self.image_label.config(image=None)
        # self.model_name = None
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
            # self.set_scan(False)
            try:
                root.after_cancel(self.load_image_task_id)
            except ValueError:
                pass
        else:
            self.show_image = True
            # self.image_label.grid(row=0, column=0, columnspan=5, sticky=W + E, padx=PAD, pady=PAD)
            self.image_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.update_model_info_async(True)

    def show_full_history(self, period):
        if self.hist_window is not None:
            self.hist_window.on_close()

        self.menu_bar.entryconfig("History", state=DISABLED)
        hist_future = executor.submit(load_hist_dict, period)
        hist_future.add_done_callback(lambda f: root.after_idle(self.show_hist_window, f))

    def show_hist_window(self, future):
        history = future.result()
        self.hist_window = HistoryWindow(self, Toplevel(root), history)
        self.menu_bar.entryconfig("History", state=NORMAL)

    def show_player_window(self):
        player_window = PlayerWindow(self, Toplevel(root))

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
            self.btn_play.config(text="Scan Off")
            return

        self.scan_idx = -1
        self.btn_play.config(text="Scan On")

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
        # self.cb_model.selection_range(0, END)
        self.update_model_info_async(remember)

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

                # broken line
                if '\x00' == name[0]:
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
            playlist_url = f"https://edge{rnd}-hel.live.mmcdn.com/live-hls/amlst:{model.model_name}/playlist.m3u8"
            task = asyncio.ensure_future(bound_fetch(sem, playlist_url, session))
            tasks.append(task)

        return await asyncio.gather(*tasks)


def send_to_player(path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((PLAYER_HOST, PLAYER_PORT))
        sock.sendall(bytes(path + "\n", 'ascii'))


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
        self.list_box.bind('<<ListboxSelect>>', self.on_listbox_select)
        v_scroll = Scrollbar(frm_bottom, command=self.list_box.yview, orient=VERTICAL)
        h_scroll = Scrollbar(frm_bottom, command=self.list_box.xview, orient=HORIZONTAL)

        self.list_box.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        v_scroll.pack(side=RIGHT, fill=Y)
        h_scroll.pack(side=BOTTOM, fill=X)
        self.list_box.pack(side=LEFT, fill=BOTH, expand=True)

        frm_top.pack()
        frm_bottom.pack()

        self.window.bind("<FocusIn>", self.focus_in_callback)
        self.window.bind("<FocusOut>", self.focus_out_callback)
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

    def focus_in_callback(self, event):
        if event.widget != self.window:
            return
        # self.entry_search.selection_range(0, END)
        root.lift()

    def focus_out_callback(self, event):
        # self.parent_window.show_image = False
        pass

    def test_online(self, model_list):
        global root

        update_models_bps(model_list, 1)
        root.after_idle(self.update_listbox, model_list)

    def update_listbox(self, model_list):
        for model in model_list:
            self.list_box.itemconfig(model.pos, {'fg': 'red' if model.is_online else 'blue'})
        self.set_controls_state(NORMAL)

    def on_test(self):
        for i in range(self.list_box.size()):
            self.list_box.itemconfig(i, {'fg': 'black'})

        self.set_controls_state(DISABLED)

        test_future = executor.submit(self.get_models)
        test_future.add_done_callback(lambda f: root.after_idle(self.after_get_models, f))


    def on_test_next(self):
        items = self.list_box.get(self.test_online_start, self.test_online_start + HistoryWindow.MAX_QUERY_SIZE - 1)

        # model_list = []
        # for i, name in zip(range(self.test_online_start, self.test_online_start + len(items)), items):
        #     model_list.append(Model(i, name))

        # self.test_online_start += HistoryWindow.MAX_QUERY_SIZE
        # self.set_controls_state(DISABLED)

        # executor.submit(self.test_online, model_list)

    def get_models(self):
        try:
            self.parent_window.http_session.headers.update(CHATUBAT_NET_RU_HEADERS)
            self.parent_window.http_session.adapters['https://'].max_retries = Retry.DEFAULT
            scraper = cloudscraper.create_scraper(self.parent_window.http_session)
            r = scraper.get(f"https://chaturbat.net.ru/get-models/all", timeout=(3.05, 9.05))
            if r.status_code != 200:
                return None
            
            result = r.json()

            online_models = set([model['username'] for model in result if model['current_show'] == 'public'])

            return online_models
        except BaseException as error:
            print(error)
            traceback.print_exc()

    def after_get_models(self, future):
        online_models = future.result()
        if online_models is None:
            return
        
        print(len(online_models))

        for i, item in enumerate(self.list_box.get(0, END)):
            self.list_box.itemconfig(i, {'fg': 'red' if item in online_models else 'blue'})

        self.set_controls_state(NORMAL)

    def set_controls_state(self, state):
        self.btn_test.config(state=state)
        self.btn_test_next.config(state=state)
        self.btn_clear.config(state=state)
        self.entry_search.config(state=state)

        if state == DISABLED:
            self.progress.grid(row=1, column=2, columnspan=2, sticky=W + E)
            self.progress.start(interval=1000)
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


POOL = SessionPool(1)


class RecordSession(Thread):
    MIN_CHUNKS = 6
    MAX_FAILS = 6
    MAX_EMPTY = 5
    SINGLE_THREAD = True
    STAT_INTERVAL = 120
    MAX_SIZE = 500_000_000

    def __init__(self, main_win, url_base, model, chunk_url, rating_logger, duration = 0):
        super(RecordSession, self).__init__()

        self.http_session = requests.Session()
        self.http_session.headers.update(HEADERS)

        self.main_win = main_win
        self.base_url = url_base
        self.model_name = model
        self.output_dir = os.path.join(OUTPUT, self.model_name + '_' + str(int(time.time() * 1000000)))
        os.mkdir(self.output_dir)

        self.chunks_url = urljoin(self.base_url, chunk_url)
        self.name = 'RecordSession'
        self.stopped = False
        self.daemon = True
        self.file_num = 1
        self.file_deq = deque(maxlen=4)
        self.duration = duration

        self.logger = logging.getLogger(f'record_{self.model_name}')
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] %(threadName)s:%(funcName)s > %(message)s')

        fh = logging.FileHandler(os.path.join(self.output_dir, self.model_name + '.log'))
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.hist_logger = rating_logger

        self.record_executor = ThreadPoolExecutor(max_workers=1)
        self.end_time = 0
        self.empty_count = 0
        self.missed = 0

    def get_chunks(self):
        self.logger.debug(self.chunks_url)
        try:
            r = self.http_session.get(self.chunks_url, timeout=TIMEOUT)
            if r.status_code != 200:
                self.logger.info(f"Status {r.status_code}: {self.chunks_url}")
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
        chunk_size = 0
        try:
            session = POOL.get()
            with session.get(ts_url, stream=True, timeout=TIMEOUT) as r, open(file_path, 'wb') as fd:
                if r.status_code != 200:
                    self.logger.info(f"Status {r.status_code}: {remote_filename}")
                    return 0
                
                for chunk in r.iter_content(chunk_size=65536):
                    chunk_size += fd.write(chunk)
        except BaseException as error:
            self.logger.exception(error)
        finally:
            st = os.stat(file_path)
            if st.st_size == 0:
                self.empty_count += 1

        return chunk_size

    def run(self):
        global root

        self.logger.info(f"Started {self.model_name}!")
        fails = 0
        last_pos = 0
        last_ts = 0
        start_time = time.time()
        self.end_time = start_time + self.duration
        downloaded_bytes = 0

        while not self.stopped and (self.duration <= 0 or time.time() < self.end_time):
            chunks = self.get_chunks()
            if chunks is None:
                self.logger.info("Offline : " + self.chunks_url)
                fails += 1

                if fails > RecordSession.MAX_FAILS:
                    break

                time.sleep(1)
                continue
            else:
                fails = 0

            if last_pos >= chunks.cur_pos:
                time.sleep(1)
                continue

            last_pos = chunks.cur_pos
            self.logger.debug(last_pos)

            try:
                for ts in chunks.ts:
                    if ts in self.file_deq:
                        self.logger.debug("Skipped: " + ts)
                        continue

                    dot_pos = ts.rfind('.')
                    under_pos = ts[:dot_pos].rfind('_')
                    ts_num = int(ts[under_pos + 1:dot_pos])
                    diff = ts_num - last_ts
                    if last_ts != 0 and diff > 1:
                        self.missed += diff - 1
                        for i in range(last_ts + 1, ts_num):
                            self.logger.info(f"Missed: {i}")
                    last_ts = ts_num

                    self.file_deq.append(ts)
                    filename = f'{self.file_num:020}.ts'
                    if RecordSession.SINGLE_THREAD:
                        downloaded_bytes += self.save_to_file(ts, filename)
                    else:
                        self.record_executor.submit(self.save_to_file, ts, f'{self.file_num:020}.ts')

                    self.file_num += 1

                    if (self.file_num - 2) % 30 == 0:
                        self.hist_logger.info(self.model_name)
            except BaseException as e:
                self.logger.exception(e)

            if time.time() - start_time > RecordSession.STAT_INTERVAL:
                self.empty_count = 0
                self.missed = 0

            if downloaded_bytes >= RecordSession.MAX_SIZE:
                self.output_dir = os.path.join(OUTPUT, self.model_name + '_' + str(int(time.time() * 1000000)))
                os.mkdir(self.output_dir)
                downloaded_bytes = 0

            time.sleep(0.5)

        self.logger.info(f"Exited {self.model_name}!")
        self.record_executor.shutdown(wait=False, cancel_futures=True)
        handlers = self.logger.handlers[:]
        for handler in handlers:
            self.logger.removeHandler(handler)
            handler.close()
        self.http_session.close()
        if not self.stopped:
            root.after(1000, self.main_win.update_active_records, self.model_name)

    def stop(self):
        self.stopped = True

    def get_remaining(self):
        if self.duration == 0:
            return -1

        return int(self.end_time - time.time())
    
    def get_empty(self):
        return self.empty_count

    def get_missed(self):
        return self.missed


class PlayerWindow:
    def __init__(self, parent, win):
        self.window = win
        self.parent_window = parent
        self.window.title("Media Player")
        self.window.geometry("800x600")

        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.media_canvas = Canvas(win, bg="black", width=800, height=400)
        parent.media_player.set_hwnd(self.media_canvas.winfo_id())
        self.media_canvas.pack(pady=10, fill=BOTH, expand=True)
        if parent.base_url is not None:
            media = parent.vlc_instance.media_new(urljoin(parent.base_url, 'playlist.m3u8'))
            parent.media_player.set_media(media)
            parent.media_player.play()

    def on_close(self):
        self.parent_window.hist_window = None
        self.media_player.stop()
        self.window.update_idletasks()
        self.window.destroy()


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
