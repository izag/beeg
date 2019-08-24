import io
import logging
import os
import subprocess
import time
import traceback
from _tkinter import TclError
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Thread
from tkinter import Tk, Button, Entry, ttk, W, E, Image, Label, DISABLED, NORMAL, Menu, StringVar, END, HORIZONTAL

import requests
from PIL import Image, ImageTk
from requests import RequestException
from requests.compat import urljoin

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0'

# TODO: change referer
REFERER = 'https://cbjpeg.stream.highwebmedia.com'

PROXIES = None

HEADERS = {
    'User-agent': USER_AGENT,
    'Referer': REFERER
}

DELAY = 2000
PAD = 5
MAX_FAILS = 6
OUTPUT = "C:/tmp/"

HTTP_IMG_URL = "https://cbjpeg.stream.highwebmedia.com/stream?room="
PLAYLIST_URL = "https://booloo.com/live/"

executor = ThreadPoolExecutor(max_workers=20)

root = Tk()


class MainWindow:

    def __init__(self):
        menubar = Menu(root)
        self.history = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="History", menu=self.history)
        root.config(menu=menubar)

        self.session = None

        self.model_name = None
        self.update_title()

        self.level = 0

        self.image_label = Label(root)
        self.image_label.grid(row=self.level, column=0, columnspan=3, sticky=W + E, padx=PAD, pady=PAD)

        self.level += 1
        self.input_text = StringVar()
        self.entry = Entry(root, textvariable=self.input_text, width=80)
        self.entry.bind("<FocusIn>", self.focus_callback)
        self.entry.bind('<Return>', self.enter_callback)
        self.entry.focus_set()
        self.entry.grid(row=self.level, column=0, columnspan=3, sticky=W + E, padx=PAD, pady=PAD)

        self.level += 1
        self.btn_update = Button(root, text="Update info", command=self.update_model_info)
        self.btn_update.grid(row=self.level, column=0, sticky=W + E, padx=PAD, pady=PAD)

        self.cb_resolutions = ttk.Combobox(root, state="readonly", values=[])
        self.cb_resolutions.grid(row=self.level, column=1, columnspan=2, sticky=W + E, padx=PAD, pady=PAD)

        self.level += 1
        self.btn_show_recording = Button(root,
                                         text="Show recording model",
                                         command=self.show_recording_model,
                                         state=DISABLED)
        self.btn_show_recording.grid(row=self.level, column=0, sticky=W + E, padx=PAD, pady=PAD)

        self.level += 1
        self.btn_start = Button(root, text="Start", command=self.on_btn_start)
        self.btn_start.grid(row=self.level, column=0, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_stop = Button(root, text="Stop", command=self.on_btn_stop, state=DISABLED)
        self.btn_stop.grid(row=self.level, column=1, sticky=W + E, padx=PAD, pady=PAD)

        self.copy_button = Button(root, text="Copy model name", command=self.copy_model_name)
        self.copy_button.grid(row=self.level, column=2, sticky=W + E, padx=PAD, pady=PAD)

        self.level += 1
        self.progress = ttk.Progressbar(root, orient=HORIZONTAL, length=120, mode='indeterminate')

        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.play_list_url = None
        self.base_url = None
        self.model_image = None
        self.img_url = None

        self.load_image()

    def on_btn_start(self):
        self.btn_start.config(state=DISABLED)

        self.stop()

        idx = self.cb_resolutions.current()

        success = self.update_model_info()
        if not success:
            self.set_default_state()
            return

        items_count = len(self.cb_resolutions['value'])
        if items_count == 0:
            self.set_default_state()
            return

        if items_count <= idx or idx < 0:
            idx = 0

        self.cb_resolutions.current(idx)

        self.update_title()

        self.session = RecordSession(self, self.base_url, self.model_name, self.cb_resolutions.get())
        self.session.start()

        self.btn_stop.config(state=NORMAL)
        self.btn_show_recording.config(state=NORMAL)
        self.progress.grid(row=self.level, column=0, columnspan=3, sticky=W + E, padx=PAD, pady=PAD)
        self.progress.start()

        self.update_title()

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
        root.clipboard_clear()
        root.clipboard_append(root.title())
        root.update()

    def update_model_info(self):
        self.set_undefined_state()
        input_url = self.input_text.get().strip()

        if len(input_url) == 0:
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
                self.set_undefined_state()
                return False

        self.img_url = HTTP_IMG_URL + self.model_name
        self.add_to_history()
        self.update_title()

        return True

    def add_to_history(self):
        try:
            self.history.index(self.model_name)
        except TclError:
            arg = f'{self.model_name}'
            self.history.insert_command(0,
                                        label=self.model_name,
                                        command=lambda: self.load_from_history(arg))

    def load_from_history(self, model):
        self.input_text.set(model)
        self.entry.selection_range(0, END)
        self.update_model_info()

    def focus_callback(self, event):
        self.entry.selection_range(0, END)

    def enter_callback(self, event):
        self.update_model_info()

    def get_resolutions(self):
        playlist_url = urljoin(PLAYLIST_URL, self.model_name)
        try:
            r = requests.get(playlist_url, headers=HEADERS, proxies=PROXIES)
            lines = r.text.splitlines()

            resolutions = [line for line in lines if not line.startswith("#")]
            resolutions.reverse()

            self.cb_resolutions.configure(values=resolutions)
            if len(resolutions) == 0:
                return False

            self.cb_resolutions.current(0)

            actual_url = r.url
            slash_pos = actual_url.rfind('/')
            self.base_url = actual_url[: slash_pos + 1]
            return True
        except RequestException as error:
            print("GetPlayList exception model: " + self.model_name)
            print(error)
            traceback.print_exc()
            return False

    def load_image(self):
        if self.img_url is not None:
            executor.submit(self.fetch_image)

        root.update_idletasks()
        root.after(DELAY, self.load_image)

    def fetch_image(self):
        try:
            response = requests.get(self.img_url, headers=HEADERS, proxies=PROXIES)
            img = Image.open(io.BytesIO(response.content))
            root.after_idle(self.update_image, img)
        except BaseException as error:
            root.after_idle(self.set_undefined_state)
            print("Exception URL: " + self.img_url)
            print(error)
            traceback.print_exc()

    def update_image(self, img):
        self.model_image = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.model_image)

    def on_close(self):
        self.stop()
        root.update_idletasks()
        root.destroy()

    def set_default_state(self):
        self.session = None
        self.btn_stop.config(state=DISABLED)
        self.btn_start.config(state=NORMAL)
        self.btn_show_recording.config(state=DISABLED)
        self.progress.stop()
        self.progress.grid_forget()
        self.update_title()
        root.configure(background='SystemButtonFace')

    def update_title(self):
        root.title(self.model_name or '<Undefined>')

        if self.session is None:
            return

        if not self.session.is_alive():
            return

        if self.session.model_name != root.title():
            return

        root.title(root.title() + " - Recording")

    def set_undefined_state(self):
        self.model_image = None
        self.image_label.config(image=None)
        self.model_name = None
        self.img_url = None
        self.update_title()

    def show_recording_model(self):
        if self.session is None:
            return

        self.input_text.set(self.session.model_name)
        self.entry.selection_range(0, END)
        self.update_model_info()


class Chunks:
    IDX_CUR_POS = 3

    def __init__(self, lines):
        self.ts = [line for line in lines if not line.startswith("#")]
        self.cur_pos = int(lines[Chunks.IDX_CUR_POS].split(':')[1])


class RecordSession(Thread):
    MIN_CHUNKS = 6

    def __init__(self, main_win, url_base, model, chunk_url):
        super(RecordSession, self).__init__()

        self.main_win = main_win
        self.base_url = url_base
        self.model_name = model
        self.output_dir = os.path.join(OUTPUT, self.model_name + '_' + str(int(time.time())))
        os.mkdir(self.output_dir)

        self.chunks_url = urljoin(self.base_url, chunk_url)
        self.name = 'RecordSession'
        self.stopped = False
        self.daemon = True

        self.logger = logging.getLogger('bonga_application')
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] %(threadName)s:%(funcName)s > %(message)s')

        self.fh = logging.FileHandler(os.path.join(self.output_dir, self.model_name + '.log'))
        self.fh.setLevel(logging.DEBUG)
        self.fh.setFormatter(formatter)
        self.logger.addHandler(self.fh)

    def get_chunks(self):
        self.logger.debug(self.chunks_url)
        try:
            r = requests.get(self.chunks_url, headers=HEADERS, proxies=PROXIES)
            lines = r.text.splitlines()

            if len(lines) < RecordSession.MIN_CHUNKS:
                return None

            return Chunks(lines)
        except RequestException as error:
            self.logger.exception(error)
            return None

    def save_to_file(self, filename):
        self.logger.debug(filename)
        fpath = os.path.join(self.output_dir, filename)
        if os.path.exists(fpath):
            self.logger.debug("Skipped: " + filename)
            return

        ts_url = urljoin(self.base_url, filename)
        subprocess.run(["c:\\progs\\wget\\wget.exe", "-q", "--no-check-certificate",
                        "-O", fpath,
                        ts_url])

    def run(self):
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
                    executor.submit(self.save_to_file, ts)
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

    def stop(self):
        self.stopped = True


if __name__ == "__main__":
    root.resizable(False, False)
    my_gui = MainWindow()
    root.mainloop()
