import datetime
import io
import json
import os
import random
import time
from tkinter import TOP, Entry, Menu, StringVar, Toplevel, ttk
from tkinter.ttk import Style
import traceback
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from idlelib.tooltip import Hovertip
from tkinter import E, W, Label, Tk, Frame, NSEW, BOTH, Button, Scrollbar, Canvas, VERTICAL, HORIZONTAL, RIGHT, Y, BOTTOM, X, LEFT, \
    NW, EW, DISABLED, NORMAL
from tkinter.font import Font, nametofont

import clipboard
import cloudscraper
import requests
from queue import Queue
from PIL import Image, ImageTk
from urllib3 import Retry
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from threading import Event
from tbselenium.tbdriver import TorBrowserDriver


random.seed()

PAD = 0
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
TIMEOUT = (3.05, 23.05)
IMG_WIDTH = 180
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
ROWS = 24
COLS = 4

IMG_HEADERS = {
    'User-Agent': USER_AGENT,
    'Referer': 'https://chaturbate.com',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

STREAM_HEADERS = {
    'User-Agent': USER_AGENT,
    'Referer': 'https://chaturbate.com',
    'Accept': 'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Sec-GPC': '1',
    'Sec-Fetch-Dest': 'image',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'cross-site',
    'Priority': 'u=5, i'
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

class ThreadPoolExecutorWithQueueSizeLimit(ThreadPoolExecutor):
    def __init__(self, maxsize=1, *args, **kwargs):
        super(ThreadPoolExecutorWithQueueSizeLimit, self).__init__(*args, **kwargs)
        self._work_queue = Queue(maxsize=maxsize)

# selenium supports only 1 thread
executor = ThreadPoolExecutor(max_workers=1)
root = Tk()

# selenium driver spoils cwd 
working_dir = os.getcwd()

# firefox_profile = webdriver.FirefoxProfile('C:\\Users\\Gregory\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\zlk8ndod.default-release\\')
# firefox_profile.set_preference('browser.privatebrowsing.autostart', True)
# options = Options()
# options.profile = firefox_profile
# driver = webdriver.Firefox(options=options)

driver = TorBrowserDriver(tbb_fx_binary_path="C:\\Users\\Gregory\\Desktop\\TorBrowser\\Browser\\firefox.exe", tbb_profile_path="C:\\Users\\Gregory\\Desktop\\TorBrowser\\Browser\\TorBrowser\\Data\\Browser\\profile.default\\")

os.chdir(working_dir)

image_loader_session = requests.Session()
image_loader_session.headers.update(STREAM_HEADERS)
HTTP_IMG_URL = "https://jpeg.live.mmcdn.com/stream?room="


class MainWindow:

    def __init__(self):
        global root

        root.bind("<FocusIn>", self.focus_in_callback)

        self.menu_bar = Menu(root)
        root.config(menu=self.menu_bar)

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

        frm_top = Frame(root)

        self.btn_back = Button(frm_top, text="Back", command=self.go_back)
        self.btn_back.grid(row=0, column=0, sticky=EW)

        self.btn_home = Button(frm_top, text="Home", command=self.show_home_page)
        self.btn_home.grid(row=0, column=1, sticky=EW)

        self.btn_couples = Button(frm_top, text="Couples", command=lambda: self.show_home_page('c'))
        self.btn_couples.grid(row=0, column=2, sticky=EW)

        self.btn_trans = Button(frm_top, text="Trans", command=lambda: self.show_home_page('t'))
        self.btn_trans.grid(row=0, column=3, sticky=EW)

        self.btn_refresh = Button(frm_top, text="Refresh", command=self.refresh_in_thread)
        self.btn_refresh.grid(row=0, column=4, sticky=EW)

        self.sv_model = StringVar()
        self.entry_model = Entry(frm_top, textvariable=self.sv_model, width=40)
        self.entry_model.bind('<Return>', self.load_more_like)
        self.entry_model.grid(row=0, column=5, sticky=EW)

        self.btn_load = Button(frm_top, text="Load", command=self.load_more_like)
        self.btn_load.grid(row=0, column=6, sticky=EW)

        self.btn_prev = Button(frm_top, text="Prev", command=self.show_prev_page)
        self.btn_prev.grid(row=0, column=7, sticky=EW)

        self.btn_next = Button(frm_top, text="Next", command=self.show_next_page)
        self.btn_next.grid(row=0, column=8, sticky=EW)

        self.btn_last = Button(frm_top, text="Last", command=self.show_last_page)
        self.btn_last.grid(row=0, column=9, sticky=EW)

        self.frm_main = ScrollFrame(root)
        self.image_buttons = self.fill_panel(self.frm_main.view_port)

        # self.canvas = Canvas(root, width=200, height=100, bg="black", bd=0, highlightthickness=0)

        frm_top.pack(side=TOP, fill=X)
        # self.canvas.pack(pady=10)
        self.frm_main.pack(fill=BOTH, expand=True)

        self.hist_stack = []
        self.page = 0
        self.gender = None
        self.view_history = False
        self.hist_models = []
        self.hist_period = 0

        self.loading_task = None
        self.stop_event = Event()
        
        self.image_loader = ThreadPoolExecutor(max_workers=1)
        self.image_loader_future = None
        self.image_loader_stop_event = Event()

        self.preview_window = PreviewWindow(self, root)
        self.preview_window.withdraw()

    def show_next_page(self):
        self.page += 1

        if self.view_history:
            success = self.show_history_in_thread()
            if not success:
                self.page -= 1
        else:
            self.show_page_in_thread()

    def show_prev_page(self):
        if self.page <= 0:
            return
        
        self.page -= 1

        if self.view_history:
            success = self.show_history_in_thread()
            if not success:
                self.page += 1
        else:
            self.show_page_in_thread()

    def show_last_page(self):
        if not self.view_history:
            return
        
        if len(self.hist_models) == 0:
            return

        num_buttons = COLS * ROWS
        previous_value = self.page
        self.page = (len(self.hist_models) - 1) // num_buttons
        success = self.show_history_in_thread()
        if not success:
            self.page = previous_value

    def show_home_page(self, gender=None):
        self.page = 0
        self.gender = gender
        self.view_history = False
        self.show_page_in_thread()

    def show_page_in_thread(self):
        global root

        if self.loading_task is not None and not self.loading_task.done():
            if not self.loading_task.cancel():
                self.stop_event.set()

        root.title(f'Gender {self.gender} Page {self.page}')
        self.set_controls_state(DISABLED)
        self.frm_main.scroll_top_left()
        for btn in self.image_buttons:
            btn.reset()
        
        self.loading_task = executor.submit(self.show_page, self.gender, self.page)
        self.loading_task.add_done_callback(lambda f: self.set_controls_state(NORMAL))

    def show_page(self, gender, page):
        result = get_all(gender, page)
        models = [(model['username'], model['img'], f"{model['country']} {model['location']}") for model in result['rooms']]
        self.reconfigure_buttons(models)

    def load_more_like(self):
        model = self.sv_model.get().strip()
        if len(model) == 0:
            return

        self.show_page_more_like_in_thread(model, None, True)

    def show_page_more_like_in_thread(self, model, location, remember):
        global root

        if self.loading_task is not None and not self.loading_task.done():
            if not self.loading_task.cancel():
                self.stop_event.set()

        root.title(model or '<Undefined>')
        self.set_controls_state(DISABLED)

        if remember and (model is not None) and (len(self.hist_stack) == 0 or (model != self.hist_stack[-1])):
            self.hist_stack.append(model)

        self.frm_main.scroll_top_left()
        for btn in self.image_buttons:
            btn.reset()

        self.loading_task = executor.submit(self.show_page_more_like, model)
        self.loading_task.add_done_callback(lambda f: self.set_controls_state(NORMAL))

        self.load_main_image_in_thread(model, location)

    def show_page_more_like(self, model):
        result = get_more_like(model)
        models = [(model['room'], model['img'], f"{model['country']} {model['location']}") for model in result['rooms']]
        self.reconfigure_buttons(models)

    def refresh_in_thread(self):
        if self.loading_task is not None and not self.loading_task.done():
            if not self.loading_task.cancel():
                self.stop_event.set()

        self.set_controls_state(DISABLED)
        # self.frm_main.scroll_top_left()
        
        self.loading_task = executor.submit(self.refresh)
        self.loading_task.add_done_callback(lambda f: self.set_controls_state(NORMAL))

    def show_full_history(self, period):
        global root

        if self.loading_task is not None and not self.loading_task.done():
            if not self.loading_task.cancel():
                self.stop_event.set()

        self.page = 0
        self.view_history = True
        self.hist_period = period
        root.title(f'History for period {self.hist_period} page {self.page}')
        self.set_controls_state(DISABLED)
        self.frm_main.scroll_top_left()
        for btn in self.image_buttons:
            btn.reset()

        self.loading_task = executor.submit(self.test_online, period)
        self.loading_task.add_done_callback(lambda f: self.set_controls_state(NORMAL))

    def test_online(self, period):
        history = load_hist_dict(period)
        hist = sorted(history.items(), key=lambda x: x[1], reverse=True)
        online_models = get_all_online()

        if online_models is None:
            return

        self.hist_models = []
        for model_name, weight in hist:
            model = online_models.get(model_name, None)
            if model is None:
                continue
            self.hist_models.append((model['username'], model['image_url'], model['country']))

        self.show_history(self.page)

    def show_history_in_thread(self):
        global root

        if len(self.hist_models) == 0:
            return False

        if self.page * ROWS * COLS > len(self.hist_models):
            return False

        if self.loading_task is not None and not self.loading_task.done():
            if not self.loading_task.cancel():
                self.stop_event.set()

        root.title(f'History for period {self.hist_period} page {self.page}')
        self.set_controls_state(DISABLED)
        self.frm_main.scroll_top_left()
        for btn in self.image_buttons:
            btn.reset()

        self.loading_task = executor.submit(self.show_history, self.page)
        self.loading_task.add_done_callback(lambda f: self.set_controls_state(NORMAL))

        return True

    def show_history(self, page):
        num_buttons = ROWS * COLS
        self.reconfigure_buttons(self.hist_models[page * num_buttons : (page + 1) * num_buttons])

    def set_controls_state(self, status):
        self.btn_back.config(state=status)
        self.btn_home.config(state=status)
        self.btn_couples.config(state=status)
        self.btn_trans.config(state=status)
        self.btn_refresh.config(state=status)
        self.btn_load.config(state=status)
        self.btn_next.config(state=status)
        self.btn_prev.config(state=status)
        self.btn_last.config(state=status)
        self.menu_bar.entryconfig("History", state=status)

        # for btn in self.image_buttons:
        #     btn.config(state=status)

    def reconfigure_buttons(self, models):
        http_session = requests.Session()
        http_session.headers.update(IMG_HEADERS)

        try:
            i = 0
            for cell in self.image_buttons:
                if self.stop_event.is_set():
                    break

                if i >= len(models):
                    break

                username, img_url, location = models[i]
                self.reconfigure_button(http_session, cell, username, img_url, location)
                i += 1
        except BaseException as error:
            print(error)
            traceback.print_exc()
        finally:
            self.stop_event.clear()
            http_session.close()


    def refresh(self):
        http_session = requests.Session()
        http_session.headers.update(IMG_HEADERS)

        try:
            for cell in self.image_buttons:
                if self.stop_event.is_set():
                    break

                button = cell.img_button
                self.reconfigure_button(http_session, cell, button.link, button.img_url, button.location)
        except BaseException as error:
            print(error)
            traceback.print_exc()
        finally:
            self.stop_event.clear()
            http_session.close()

    def reconfigure_button(self, http_session, cell, url, img_url, location):
        global root

        if (img_url is None) or (len(img_url) == 0):
            return

        # image = download_image(http_session, img_url.replace('/ri/', '/riw/'))
        image = download_image(http_session, HTTP_IMG_URL + url)

        photo_image = None
        if (image is not None) and (len(image) != 0):
            img = Image.open(io.BytesIO(image))
            img_resized = resize_image(img, IMG_WIDTH)
            photo_image = ImageTk.PhotoImage(img_resized)

        root.after_idle(cell.set_values, url, photo_image, img_url, location)

    def go_back(self):
        if len(self.hist_stack) == 0:
            self.show_page_in_thread()
            return
        
        model = self.hist_stack.pop()
        if model == root.title():
            self.go_back()
            return
        
        self.show_page_more_like_in_thread(model, None, False)

    def fill_panel(self, panel):
        buttons = []
        for i in range(ROWS):
            for j in range(COLS):
                btn = ModelFrame(self, panel)
                btn.grid(row=i, column=j, sticky=NSEW, padx=PAD, pady=PAD)
                buttons.append(btn)

        return buttons
    
    def on_enter(self, event):
        if event.widget.link is None:
            return
        
        # print(f"entered {event.widget.link}")
        
        if self.image_loader_future is not None and not self.image_loader_future.done():
            if not self.image_loader_future.cancel():
                self.image_loader_stop_event.set()

        self.image_loader_future = self.image_loader.submit(self.fetch_image, event.widget)
        # print(f"submited {event.widget.link}")
        # self.image_loader_future.add_done_callback(lambda f: event.widgetself.set_controls_state(NORMAL))

    def on_leave(self, event):
        if self.image_loader_future is not None and not self.image_loader_future.done():
            # print(f"leaved {event.widget.link}")
            if not self.image_loader_future.cancel():
                self.image_loader_stop_event.set()
                # print(f"set {event.widget.link}")
            # else:
            #     print(f"canceled {event.widget.link}")

    def fetch_image(self, button):
        global root
        time.sleep(0.5)

        try:
            while not self.image_loader_stop_event.is_set():
                img_url = HTTP_IMG_URL + button.link + f"&f={random.random()}"
                # print(img_url)
                
                response = image_loader_session.get(img_url, timeout=TIMEOUT)
                if response.status_code != 200:
                    return
                
                img = Image.open(io.BytesIO(response.content))
                img_resized = resize_image(img, IMG_WIDTH)
                photo_image = ImageTk.PhotoImage(img_resized)
                root.after_idle(button.set_image, photo_image)

                time.sleep(0.1)
        except BaseException as error:
            print("Exception URL: " + HTTP_IMG_URL + button.link)
            print(error)
            traceback.print_exc()
        finally:
            self.image_loader_stop_event.clear()

    def load_main_image_in_thread(self, model, location):
        # self.menu_bar.entryconfig("Preview", state=DISABLED)
        self.preview_window.deiconify()
        self.preview_window.set_values(model, location)
        self.preview_window.load_main_image_in_thread()
        self.preview_window.load_hls_source_in_thread()

    def focus_in_callback(self, event):
        if event.widget != root:
            return

        self.preview_window.lift()


def get_all_online():
    # driver.get(f'view-source:https://chaturbat.net.ru/get-models/all')

    # content = driver.find_element(By.TAG_NAME, 'pre').text
    # result = json.loads(content)

    # online_models = {}
    # for model in result:
        # if model['current_show'] != 'public':
            # continue
        # online_models[model['username']] = model

    # return online_models

    try:
        with requests.Session() as http_session:
            http_session.headers.update(CHATUBAT_NET_RU_HEADERS)
            http_session.adapters['https://'].max_retries = Retry.DEFAULT
            scraper = cloudscraper.create_scraper(http_session)
            online_models = {}
            for page in range(1, 100):
                r = scraper.get(f"https://chaturbat.net.ru/more-models?page={page}", timeout=TIMEOUT)
                # r = http_session.get("https://chaturbat.net.ru/get-models/all", timeout=TIMEOUT)
                if r.status_code != 200:
                    return None
            
                result = r.json()
                for model in result['models']:
                    if model['current_show'] != 'public':
                        continue
                    online_models[model['username']] = model

            return online_models
    except BaseException as error:
        print(error)
        traceback.print_exc()


def get_all(gender, page):
    src = f'view-source:https://chaturbate.com/api/ts/roomlist/room-list/?limit={ROWS * COLS}&offset={page * ROWS * COLS}'

    if gender is not None:
        src += f'&genders={gender}'

    driver.get(src)

    content = driver.find_element(By.TAG_NAME, 'pre').text
    return json.loads(content)


def get_more_like(model):
    driver.get(f'view-source:https://chaturbate.com/api/more_like/{model}/')

    content = driver.find_element(By.TAG_NAME, 'pre').text
    return json.loads(content)


def get_hls_source(model):
    driver.get(f'view-source:https://chaturbate.com/api/chatvideocontext/{model}/')

    content = driver.find_element(By.TAG_NAME, 'pre').text
    info = json.loads(content)
    return info['hls_source']


def download_image(http_session, url):
    # qpos = url.rfind('?')
    # if qpos > 0:
        # url = url[:qpos]
    
    try:
        response = http_session.get(url, timeout=TIMEOUT, allow_redirects=False)
        if response.status_code == 404:
            return None
        
        if response.status_code != 200:
            print(url)
            return None

        return response.content
    except BaseException as error:
        print(error)
        traceback.print_exc()


def resize_image(img, width):
    w, h = img.size
    k = width / w
    return img.resize((width, int(h * k)), resample=Image.Resampling.NEAREST, reducing_gap=1.0)


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
                if len(name) == 0 or '\x00' == name[0]:
                    continue

                count = res.get(name, 0)
                res[name] = count + 1

    return res


class ModelFrame(Frame):
    def __init__(self, win, parent, cnf={}, **kw):
        super().__init__(parent, cnf, **kw)  # create a frame (self)

        self.img_button = LinkButton(win, self, text="None")
        self.img_button.link = None
        self.model = None
        self.name = HyperLinkButton(self)
        self.main_win = win

        self.img_button.grid(row=0, column=0)
        self.name.grid(row=1, column=0)

    def reset(self):
        self.img_button.reset()
        self.name.config(text=None, command=None)
        self.model = None

    def set_values(self, model, img, img_url, location):
        self.img_button.set_values(model, img, img_url, location)
        self.model = model
        self.name.config(text=model[:15], command=lambda: self.main_win.show_page_more_like_in_thread(model, location, True))


class LinkButton(Button):
    def __init__(self, win, parent=None, *args, **kw):
        super().__init__(parent, *args, **kw)
        super().bind("<Enter>", win.on_enter)
        super().bind("<Leave>", win.on_leave)
        super().bind("<Button-3>", self.copy_link)
        self.link = None
        self.image = None
        self.img_url = None
        self.location = None
        self.main_win = win
        # self.tip = Hovertip(self, text=None, hover_delay=100)

    def copy_link(self, event):
        clipboard.copy(self.link)

    def reset(self):
        self.config(image='', command=None, background="SystemButtonFace")
        self.link = None
        self.img_url = None
        self.image = None
        self.location = None
        # self.tip.text = None

    def set_values(self, url, img, img_url, location):
        self.config(image=img, command=lambda: self.main_win.load_main_image_in_thread(url, location))
        self.image = img
        self.img_url = img_url
        self.link = url
        self.location = location
        # self.tip.text = url

    def set_image(self, img):
        self.config(image=img)
        self.image = img


class HyperLinkButton(ttk.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use the default font.
        label_font = nametofont("TkDefaultFont").cget("family")
        self.font = Font(family=label_font, size=12, weight='bold')
        # Label-like styling.
        self.link_style = Style()
        self.link_style.configure("Link.TLabel", foreground="#357fde", font=self.font)
        self.configure(style="Link.TLabel", cursor="hand2")
        self.bind("<Enter>", self.on_mouse_enter)
        self.bind("<Leave>", self.on_mouse_leave)

    def on_mouse_enter(self, event):
        self.font.configure(underline=True)

    def on_mouse_leave(self, event):
        self.font.configure(underline=False)



class ScrollFrame(Frame):
    """Copyright: https://gist.github.com/mp035/9f2027c3ef9172264532fcd6262f3b01"""

    def __init__(self, parent, cnf={}, **kw):
        super().__init__(parent, cnf, **kw)  # create a frame (self)

        self.canvas = Canvas(self, borderwidth=0, background="#ffffff")  # place canvas on self

        # place a frame on the canvas, this frame will hold the child widgets
        self.view_port = Frame(self.canvas, background="#ffffff")

        self.vsb = Scrollbar(self, orient=VERTICAL, command=self.canvas.yview)  # place a scrollbar on self
        self.hsb = Scrollbar(self, orient=HORIZONTAL, command=self.canvas.xview)  # place a scrollbar on self
        # attach scrollbar action to scroll of canvas
        self.canvas.configure(xscrollcommand=self.hsb.set, yscrollcommand=self.vsb.set)

        self.vsb.pack(side=RIGHT, fill=Y)  # pack scrollbar to right of self
        self.hsb.pack(side=BOTTOM, fill=X)  # pack scrollbar to right of self
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)  # pack canvas to left of self and expand to fil
        self.canvas_window = self.canvas.create_window((4, 4), window=self.view_port, anchor=NW,
                                                       # add view port frame to canvas
                                                       tags="self.view_port")

        # bind an event whenever the size of the viewPort frame changes.
        self.view_port.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind('<Enter>', self.bound_to_mousewheel)
        self.canvas.bind('<Leave>', self.unbound_to_mousewheel)

        # perform an initial stretch on render, otherwise the scroll region has a tiny border until the first resize
        self.on_frame_configure(None)

    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame"""
        # whenever the size of the frame changes, alter the scroll region respectively.
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel_x(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_y(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel_y)
        self.canvas.bind_all("<Control-MouseWheel>", self.on_mousewheel_x)
        self.canvas.bind_all("<Up>", lambda event: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Down>", lambda event: self.canvas.yview_scroll(1, "units"))
        self.canvas.bind_all("<Left>", lambda event: self.canvas.xview_scroll(-1, "units"))
        self.canvas.bind_all("<Right>", lambda event: self.canvas.xview_scroll(1, "units"))

    def unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Control-MouseWheel>")
        self.canvas.unbind_all("<Up>")
        self.canvas.unbind_all("<Down>")
        self.canvas.unbind_all("<Left>")
        self.canvas.unbind_all("<Right>")

    def scroll_top_left(self):
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)


class PreviewWindow(Toplevel):
    SMALL_WIDTH = 360

    def __init__(self, parent, master, cnf={}, **kw):
        super().__init__(master, cnf={}, **kw)
        
        self.parent_window = parent
        self.canvas = Canvas(self, width=200, height=100, bg="black", bd=0, highlightthickness=0)
        self.canvas.pack(fill=BOTH)

        self.sv_stats = StringVar()
        self.lbl_stats = Label(self, textvariable=self.sv_stats)
        self.lbl_stats.pack(pady=10)

        self.sv_link = StringVar()
        self.lbl_link = Label(self, textvariable=self.sv_link)
        self.lbl_link.pack(side="left", fill="x")

        self.btn_link = Button(self, text="Link", command=self.copy_link)
        self.btn_link.pack(pady=10)
        
        self.geometry(f"+{root.winfo_screenwidth() - 854}+0")
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Configure>", self.update_wraplength)

        self.main_image_loader = ThreadPoolExecutor(max_workers=1)
        self.main_image_loader_future = None
        self.main_image_loader_stop_event = Event()
        self.main_image = None

        self.model = None
        self.resize = True

        self.hls_task = None

    def on_close(self):
        self.stop()
        self.withdraw()
        # self.parent_window.menu_bar.entryconfig("Preview", state=NORMAL)

    def stop(self):
        if self.main_image_loader_future is not None and not self.main_image_loader_future.done():
            if not self.main_image_loader_future.cancel():
                self.main_image_loader_stop_event.set()

    def load_main_image_in_thread(self):
        self.stop()
        self.main_image_loader_future = self.main_image_loader.submit(self.fetch_image_main)

    def fetch_image_main(self):
        global root

        try:
            while not self.main_image_loader_stop_event.is_set():
                if self.model is None:
                    break

                img_url = HTTP_IMG_URL + self.model + f"&f={random.random()}"
                # print(img_url)

                response = image_loader_session.get(img_url, timeout=TIMEOUT)
                if response.status_code != 200:
                    return

                img = Image.open(io.BytesIO(response.content))
                # if self.resize:
                #     img = resize_image(img, PreviewWindow.SMALL_WIDTH)
                photo_image = ImageTk.PhotoImage(img)
                root.after_idle(self.update_main_image, photo_image)

                time.sleep(0.5)
        except BaseException as error:
            print("Exception URL: " + HTTP_IMG_URL + self.model)
            print(error)
            traceback.print_exc()
        finally:
            self.main_image_loader_stop_event.clear()

    def update_main_image(self, photo_image):
        w = photo_image.width()
        h = photo_image.height()
        # self.geometry(f"{w}x{h}")
        x_center = w // 2
        y_center = h // 2
        self.canvas.config(width=w, height=h)
        # print(f"window = {self.winfo_geometry()} image = {w}x{h}")
        if self.main_image is None:
            self.main_image = self.canvas.create_image(x_center, y_center, image=photo_image)
        else:
            self.canvas.itemconfigure(self.main_image, image=photo_image)
            self.canvas.coords(self.main_image, x_center, y_center)

    def load_hls_source_in_thread(self):
        if self.hls_task is not None and not self.hls_task.done():
            self.hls_task.cancel()

        self.sv_link.set('')
        self.btn_link.config(state=DISABLED)
        self.hls_task = executor.submit(get_hls_source, self.model)
        self.hls_task.add_done_callback(lambda f: root.after_idle(self.after_get_hls_source, f))

    def after_get_hls_source(self, future):
        hls_source = future.result()
        if hls_source is None:
            return
        
        self.sv_link.set(hls_source)
        self.btn_link.config(state=NORMAL)

    def copy_link(self):
        clipboard.copy(self.sv_link.get())

    def set_values(self, model, location):
        self.model = model
        self.title(model or '<Undefined>')
        self.sv_stats.set(location)

    def on_enter(self, event):
        self.resize = False

    def on_leave(self, event):
        self.resize = True

    def update_wraplength(self, _event):
        self.lbl_link.configure(wraplength=self.lbl_link.winfo_width())


if __name__ == "__main__":
    root.geometry(f"760x{root.winfo_screenheight()}+-7+0")
    root.title("<Undefined>")
    # root.state('zoomed')
    main_win = MainWindow()
    root.mainloop()
    driver.quit()
    image_loader_session.close()