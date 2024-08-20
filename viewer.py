import io
import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from idlelib.tooltip import Hovertip
from tkinter import Tk, Frame, NSEW, BOTH, Button, Scrollbar, Canvas, VERTICAL, HORIZONTAL, RIGHT, Y, BOTTOM, X, LEFT, \
    NW, EW, DISABLED, NORMAL

import clipboard
import cloudscraper
import requests
from PIL import Image, ImageTk
from urllib3 import Retry
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options


PAD = 5
TIMEOUT = (3.05, 9.05)
IMG_WIDTH = 300
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'

HEADERS = {
    'User-agent': USER_AGENT,
}

executor = ThreadPoolExecutor(max_workers=20)
root = Tk()

firefox_profile = webdriver.FirefoxProfile('C:\\Users\\Gregory\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\zlk8ndod.default-release\\')
firefox_profile.set_preference('browser.privatebrowsing.autostart', True)
options = Options()
options.profile = firefox_profile
driver = webdriver.Firefox(options=options)


class MainWindow:

    def __init__(self):
        global root

        frm_top = Frame(root)

        self.btn_back = Button(frm_top, text="Back", command=self.go_back)
        self.btn_back.grid(row=0, column=0, sticky=EW)

        self.btn_reload = Button(frm_top, text="Reload", command=self.show_page_in_thread)
        self.btn_reload.grid(row=0, column=1, sticky=EW)    

        self.frm_main = ScrollFrame(root)
        self.image_buttons = fill_panel(self.frm_main.view_port)

        frm_top.pack(fill=X)
        self.frm_main.pack(fill=BOTH, expand=1)

        self.hist_stack = []

    def show_page_in_thread(self):
        self.set_controls_state(DISABLED)
        future = executor.submit(self.show_page)
        future.add_done_callback(lambda f: self.set_controls_state(NORMAL))

    def show_page(self):
        global root

        root.after_idle(self.frm_main.scroll_top_left)

        result = get_all()

        self.reconfigure_buttons(self.image_buttons, list(result['models'].values()))


    def show_page_more_like_in_thread(self, model, remember):
        global root

        root.title(model or '<Undefined>')
        self.set_controls_state(DISABLED)

        if remember and (model is not None) and (len(self.hist_stack) == 0 or (model != self.hist_stack[-1])):
            self.hist_stack.append(model)
        
        future = executor.submit(self.show_page_more_like, model)
        future.add_done_callback(lambda f: self.set_controls_state(NORMAL))

    def show_page_more_like(self, model):
        global root

        root.after_idle(self.frm_main.scroll_top_left)

        result = get_more_like(model)

        self.reconfigure_buttons_more_like(self.image_buttons, result['rooms'])

    def set_controls_state(self, status):
        self.btn_reload.config(state=status)

        # for btn in self.image_buttons:
        #     btn.config(state=status)

    def reconfigure_buttons(self, buttons, models):
        headers = {
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

        http_session = requests.Session()
        http_session.headers.update(headers)

        try:
            # for btn in buttons:
                # btn.reset()

            i = 0
            for button in buttons:
                model_info = models[i]
                self.reconfigure_button(http_session, button, model_info['username'], model_info['image_url'])
                i += 1
        except BaseException as error:
            print(error)
            traceback.print_exc()
        finally:
            http_session.close()

    def reconfigure_buttons_more_like(self, buttons, models):
        headers = {
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

        http_session = requests.Session()
        http_session.headers.update(headers)

        try:
            for btn in buttons:
                btn.reset()

            i = 0
            for button in buttons:
                if i >= len(models):
                    break

                model_info = models[i]
                self.reconfigure_button(http_session, button, model_info['room'], model_info['img'])
                i += 1
        except BaseException as error:
            print(error)
            traceback.print_exc()
        finally:
            http_session.close()

    def reconfigure_button(self, http_session, btn, url, img_url):
        global root

        image = download_image(http_session, img_url.replace('/ri/', '/riw/'))

        if (image is None) or (len(image) == 0):
            return

        img = Image.open(io.BytesIO(image))
        w, h = img.size
        k = IMG_WIDTH / w
        img_resized = img.resize((IMG_WIDTH, int(h * k)))
        photo_image = ImageTk.PhotoImage(img_resized)
        if photo_image is None:
            return

        root.after_idle(btn.set_values, url, partial(self.show_page_more_like_in_thread, url, True), photo_image)

    def go_back(self):
        if len(self.hist_stack) == 0:
            self.show_page_in_thread()
            return
        
        model = self.hist_stack.pop()
        if model == root.title():
            self.go_back()
            return
        
        self.show_page_more_like_in_thread(self.hist_stack.pop(), False)


def fill_panel(panel):
    buttons = []
    for i in range(20):
        for j in range(5):
            btn = LinkButton(panel, text=f"({i}, {j})")
            btn.link = None
            btn.grid(row=i, column=j, sticky=NSEW, padx=PAD, pady=PAD)
            buttons.append(btn)

    return buttons


def get_all():
    headers = {
        'User-Agent': USER_AGENT,
        'Referer': 'https://chaturbat.net.ru',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    try:
        with requests.Session() as http_session:
            http_session.headers.update(headers)
            http_session.adapters['https://'].max_retries = Retry.DEFAULT
            scraper = cloudscraper.create_scraper(http_session)
            r = scraper.get("https://chaturbat.net.ru/get-models/all", timeout=(3.05, 9.05))
            if r.status_code != 200:
                return
            return r.json()
    except BaseException as error:
        print(error)
        traceback.print_exc()


def get_more_like(model):
    driver.get(f'view-source:https://chaturbate.com/api/more_like/{model}/')

    content = driver.page_source
    content = driver.find_element(By.TAG_NAME, 'pre').text
    return json.loads(content)


def download_image(http_session, url):
    response = http_session.get(url, timeout=TIMEOUT)
    if response.status_code == 404:
        return None

    image = response.content

    # if DEBUG:
    #     with open(get_filename(url), 'wb') as f:
    #         f.write(image)

    return image


class LinkButton(Button):
    def __init__(self, parent=None, *args, **kw):
        super().__init__(parent, *args, **kw)
        # super().bind("<Enter>", win.on_enter)
        # super().bind("<Leave>", win.on_leave)
        super().bind("<Button-3>", self.copy_link)
        self.link = None
        self.image = None
        self.tip = Hovertip(self, text=None, hover_delay=100)

    def copy_link(self, event):
        clipboard.copy(self.link)

    def reset(self):
        self.config(image='', command=None, background="SystemButtonFace")
        self.link = None

    def set_values(self, url, cmd, img):
        self.config(image=img, command=cmd)
        self.image = img
        self.link = url
        self.tip.text = url


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


if __name__ == "__main__":
    root.geometry("1044x720+0+0")
    root.title("Lalala")
    main_win = MainWindow()
    root.mainloop()
    driver.quit()