import ctypes
import io
import subprocess
import threading
import time
import traceback
from _tkinter import TclError
from threading import Thread
from tkinter import Tk, Button, Entry, ttk, W, E, Image, Label, DISABLED, NORMAL, Menu, StringVar, END
from urllib.parse import urljoin
from urllib.request import build_opener

from PIL import Image, ImageTk

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0'

opener = build_opener()
opener.addheaders = [('User-agent', USER_AGENT)]

PAD = 5
HTTP_IMG_URL = "https://cbjpeg.stream.highwebmedia.com/stream?room="
PLAYLIST_URL = "https://booloo.com/live/"


class MainWindow:

    def __init__(self, master):
        self.master = master
        menubar = Menu(self.master)
        self.history = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="History", menu=self.history)
        self.master.config(menu=menubar)

        self.session = None
        self.started = False
        self.death_listener = None

        self.model_name = "----------------"
        self.master.title(self.model_name)

        level = 0

        self.image_label = Label(master)
        self.image_label.grid(row=level, column=0, columnspan=3, sticky=W + E, padx=PAD, pady=PAD)

        level += 1
        self.input_text = StringVar()
        self.entry = Entry(master, textvariable=self.input_text, width=80)
        self.entry.bind("<FocusIn>", self.entry_callback)
        self.entry.focus_set()
        self.entry.grid(row=level, column=0, columnspan=3, sticky=W + E, padx=PAD, pady=PAD)

        level += 1
        self.btn_resolutions = Button(master, text="Update info", command=self.update_model_info)
        self.btn_resolutions.grid(row=level, column=0, sticky=W + E, padx=PAD, pady=PAD)

        self.cb_resolutions = ttk.Combobox(master, state="readonly", values=[])
        self.cb_resolutions.grid(row=level, column=1, columnspan=2, sticky=W + E, padx=PAD, pady=PAD)

        level += 1
        self.btn_start = Button(master, text="Start", command=self.on_btn_start)
        self.btn_start.grid(row=level, column=0, sticky=W + E, padx=PAD, pady=PAD)

        self.btn_stop = Button(master, text="Stop", command=self.on_btn_stop, state=DISABLED)
        self.btn_stop.grid(row=level, column=1, sticky=W + E, padx=PAD, pady=PAD)

        self.copy_button = Button(master, text="Copy model name", command=self.copy_model_name)
        self.copy_button.grid(row=level, column=2, sticky=W + E, padx=PAD, pady=PAD)

        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        self.play_list_url = None
        self.base_url = None
        self.model_image = None
        self.img_url = None

    def on_btn_start(self):
        self.btn_stop.config(state=NORMAL)
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

        self.master.title(self.model_name)
        self.session = subprocess.Popen(['python', 'session.py',
                                         self.base_url, self.model_name, self.cb_resolutions.get(), self.img_url],
                                        stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT)

        self.master.configure(background='green')

        if self.death_listener is not None:
            if self.death_listener.is_alive():
                self.death_listener.raise_exception()

        self.death_listener = SessionDeathListener(self, self.session)
        self.death_listener.start()

    def on_btn_stop(self):
        self.stop()
        self.set_default_state()

    def stop(self):
        if self.session is None:
            return

        if self.death_listener is not None:
            self.death_listener.stop()
            self.death_listener = None

        try:
            self.session.communicate(b'exit', timeout=1)
        except (subprocess.TimeoutExpired, ValueError) as e:
            print(e)

        self.session = None

    def copy_model_name(self):
        self.master.clipboard_clear()
        self.master.clipboard_append(self.master.title())
        self.master.update()

    def update_model_info(self):
        input_url = self.input_text.get().strip()

        if len(input_url) == 0:
            self.model_image = None
            self.image_label.config(image=None)
            return False

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
            self.model_name = input_url[slash_pos + 1: -1]
        else:
            self.model_name = input_url

        self.img_url = HTTP_IMG_URL + self.model_name

        self.load_image()
        success = self.get_resolutions()
        if not success:
            self.model_image = None
            self.image_label.config(image=None)
            return False

        self.master.title(self.model_name)
        self.add_to_history()

        return True

    def add_to_history(self):
        try:
            idx = self.history.index(self.model_name)
        except TclError:
            arg = f'{self.model_name}'
            self.history.insert_command(0,
                                        label=self.model_name,
                                        command=lambda: self.load_from_history(arg))

    def load_from_history(self, model):
        self.input_text.set(model)
        self.update_model_info()

    def entry_callback(self, event):
        self.entry.selection_range(0, END)

    def get_resolutions(self):
        playlist_url = urljoin(PLAYLIST_URL, self.model_name)
        with opener.open(playlist_url) as f:
            content = f.read().decode('utf-8')
            lines = content.splitlines()

            resolutions = [line for line in lines if not line.startswith("#")]
            resolutions.reverse()

            self.cb_resolutions.configure(values=resolutions)
            if len(resolutions) == 0:
                return False

            self.cb_resolutions.current(0)

            actual_url = f.geturl()
            slash_pos = actual_url.rfind('/')
            self.base_url = actual_url[: slash_pos + 1]

        return True

    def load_image(self):
        try:
            with opener.open(self.img_url) as f:
                raw_data = f.read()
                content = io.BytesIO(raw_data)
                img = Image.open(content)
                self.model_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.model_image)
        except BaseException as error:
            self.model_image = None
            self.image_label.config(image=None)
            print(error)
            traceback.print_exc()

    def on_close(self):
        self.stop()
        self.master.destroy()

    def set_default_state(self):
        self.session = None
        self.btn_stop.config(state=DISABLED)
        self.btn_start.config(state=NORMAL)
        self.master.configure(background='SystemButtonFace')


class SessionDeathListener(Thread):

    def __init__(self, window, session):
        super(SessionDeathListener, self).__init__()
        self.daemon = True
        self.session = session
        self.window = window
        self.stopped = False
        self.name = 'SessionDeathListener'

    def run(self):
        if self.session is None:
            self.window.set_default_state()
            return

        try:
            while not self.stopped:
                self.session.stdin.write(b'ping\n')
                self.session.stdin.flush()
                answer = self.session.stdout.readline()

                if answer == 'bye':
                    self.window.set_default_state()
                    return

                time.sleep(1)
        except BaseException as e:
            print(e)
            traceback.print_exc()
            self.window.set_default_state()

    def raise_exception(self):
        thread_id = threading.get_ident()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print(self.name + '> Exception raise failure')

    def stop(self):
        self.stopped = True


if __name__ == "__main__":
    root = Tk()
    root.resizable(False, False)
    my_gui = MainWindow(root)
    root.mainloop()
