import asyncio
import json
import random
import time
import traceback
from tkinter import CENTER, N, Tk, Canvas, HIDDEN, NORMAL, Listbox
from tkinter.ttk import Label

import cloudscraper as cloudscraper
import requests
from PIL import ImageTk, Image
from aiohttp import ClientSession
from requests_tor import RequestsTor, TOR_HEADERS
from urllib3 import Retry
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options


EDGES = [81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99,
         100, 101, 102, 103, 104, 106, 108, 110, 111, 112, 113, 115, 116, 117, 118, 119, 120, 123, 124, 125, 126,
         133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 145, 146, 150, 151, 152, 153, 155, 156,
         157, 158, 159, 160, 161, 162, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179,
         180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201,
         202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223,
         224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244,
         248, 249, 250, 251, 252, 254, 256, 259, 260, 261, 266, 267, 270, 271, 272, 273,
         275, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297,
         298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319,
         320, 321, 322, 323, 324, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341,
         342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352]

random.seed()


class Model:
    def __init__(self, pos, name):
        self.model_name = name
        self.pos = pos
        self.is_online = False


TEST_DATA = [
    Model(1, 'softrose'),
    Model(2, 'penelopa77'),
    Model(3, 'ronandalice'),
    Model(4, 'lana_sky'),
    Model(5, '_northern_girl_'),
    Model(6, '_k_______'),
    Model(7, 'deborah_melo'),
    Model(8, 'samay_amat'),
    Model(9, 'cutiepiealice'),
    Model(10, 'yaneller'),
    Model(11, 'blondiekayy')]


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


async def fetch_playlists(model_list):
    # create instance of Semaphore
    sem = asyncio.Semaphore(16)
    tasks = []
    rnd_sample = random.sample(EDGES, len(model_list))
    async with ClientSession() as session:
        for rnd, model in zip(rnd_sample, model_list):
            playlist_url = f"https://edge{rnd}.stream.highwebmedia.com/live-hls/amlst:{model.model_name}/playlist.m3u8"
            task = asyncio.ensure_future(bound_fetch(sem, playlist_url, session))
            tasks.append(task)

        return await asyncio.gather(*tasks)


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
            model.is_online = False
            continue

        if response == '503':
            failed.append(model)
            continue

        model.is_online = True

    update_models_bps(failed, tries + 1)


def test_online(model_list):
    update_models_bps(model_list, 1)


def demo(master):
    listbox = Listbox(master)
    listbox.pack(expand=1, fill="both")

    # inserting some items
    listbox.insert("end", "A list item")

    for item in ["one", "two", "three", "four"]:
        listbox.insert("end", item)

    # this changes the background colour of the 2nd item
    listbox.itemconfig(1, {'bg': 'red'})

    # this changes the font color of the 4th item
    listbox.itemconfig(3, {'fg': 'blue'})

    # another way to pass the colour
    listbox.itemconfig(2, bg='green')
    listbox.itemconfig(0, foreground="purple")


root = Tk()


def test_transparancy():
    global root

    img_background = ImageTk.PhotoImage(file="assets/rec1.png")
    img_record = ImageTk.PhotoImage(file="assets/rec2.png")
    img_bee = Image.open("assets/girl.jpg")
    # img_rec = Image.open("assets/rec3.gif")
    # img_canbe = Image.open("assets/canbebought.jpg")

    maxwidth = 200
    maxheight = 120
    img = fit_image(img_bee, maxwidth, maxheight)
    # img_rec = fit_image(img_rec, maxwidth, maxheight)

    width, height = img.size
    root.geometry('{}x{}'.format(width, height))
    root.overrideredirect(True)

    # Label(root, compound=N, image=background_img).place(x=0, y=0, relwidth=1, relheight=1)
    #
    # # background.image = background_img  # keep a reference!
    # Label(root, image=scanbtn_img).pack()

    canvas = Canvas(root, width=width, height=height, bd=0, highlightthickness=0)

    x_center = width // 2
    y_center = height // 2
    photo_img = ImageTk.PhotoImage(img)
    canvas.create_image(x_center, y_center, image=photo_img)
    # image_id = canvas.create_image(50, 50, image=img_record)

    # id_red_circle = canvas.create_oval(width - 30, 10, width - 10, 30, fill='red')
    id_red_frame = canvas.create_polygon(5, 5, width - 5, 5, width - 5, height - 5, 5, height - 5,
                                         outline='red',
                                         width=10,
                                         fill='')

    # photo_img_rec = ImageTk.PhotoImage(img_rec, format="gif -index 3")
    # canvas.create_image(x_center, y_center, image=photo_img_rec)

    # canvas.move(image_id, 245, 100)

    canvas.pack()

    root.after(333, blink, canvas, id_red_frame)
    root.mainloop()


def blink(canvas, id_figure):
    state = canvas.itemcget(id_figure, 'state')
    if state != HIDDEN:
        canvas.itemconfigure(id_figure, state=HIDDEN)
    else:
        canvas.itemconfigure(id_figure, state=NORMAL)
    root.after(333, blink, canvas, id_figure)


def fit_image(img, maxwidth, maxheight):
    width, height = img.size

    if width > height:
        scalingfactor = maxwidth / width
        width = maxwidth
        height = int(height * scalingfactor)
    else:
        scalingfactor = maxheight / height
        height = maxheight
        width = int(width * scalingfactor)

    return img.resize((width, height), Image.ANTIALIAS)


def quit_app():
    root.destroy()


def test_request_chaturbat_net_ru():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
        'Referer': 'https://chaturbat.net.ru',
        'Host': 'chaturbat.net.ru',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'X-Requested-With': 'XMLHttpRequest',
        'DNT': '1',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        # 'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'TE': 'trailers',
        # 'Priority': 'u=1',
    }

    try:
        with requests.Session() as http_session:
            http_session.headers.update(headers)
            http_session.adapters['https://'].max_retries = Retry.DEFAULT
            scraper = cloudscraper.create_scraper(http_session)
            # r = scraper.get("https://sex-videochat.club/feed/get-models/bonga/all/", timeout=(3.05, 9.05))
            # r = http_session.get("https://sex-videochat.club/feed/get-models/bonga/all/", timeout=(3.05, 9.05))

            r = scraper.get("https://chaturbat.net.ru/sigmasian", timeout=(3.05, 9.05))
            if r.status_code != 200:
                with open("404.txt", "wb") as fout:
                    fout.write(r.content)
                return
            r = scraper.get("https://chaturbat.net.ru/chat-model/sigmasian/none.json", timeout=(3.05, 9.05))
            # r = scraper.get("https://sex-videochat.club/chaturbate/chat/breeding_material/", timeout=(3.05, 9.05))
            if r.status_code != 200:
                with open("404.txt", "wb") as fout:
                    fout.write(r.content)
                return
            r.json()
    except BaseException as error:
        print(error)
        traceback.print_exc()


def test_request_all_chaturbat_net_ru():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
        'Referer': 'https://chaturbat.net.ru',
        # 'Host': 'chaturbat.net.ru',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-Requested-With': 'XMLHttpRequest',
        # 'DNT': '1',
        # 'Sec-GPC': '1',
        'Connection': 'keep-alive',
        # 'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        # 'TE': 'trailers',
        # 'Priority': 'u=1',
    }

    try:
        with requests.Session() as http_session:
            http_session.headers.update(headers)
            http_session.adapters['https://'].max_retries = Retry.DEFAULT
            scraper = cloudscraper.create_scraper(http_session)
            # r = scraper.get("https://sex-videochat.club/feed/get-models/bonga/all/", timeout=(3.05, 9.05))
            # r = http_session.get("https://sex-videochat.club/feed/get-models/bonga/all/", timeout=(3.05, 9.05))

            r = scraper.get("https://chaturbat.net.ru/get-models/all", timeout=(3.05, 9.05))
            if r.status_code != 200:
                with open("404.txt", "wb") as fout:
                    fout.write(r.content)
                return
            # r = http_session.get("https://chaturbat.net.ru/chat-model/adalyn_glow/none.json",
            #                      timeout=(3.05, 9.05))
            # r = scraper.get("https://sex-videochat.club/chaturbate/chat/breeding_material/", timeout=(3.05, 9.05))
            # if r.status_code != 200:
            #     with open("404.txt", "wb") as fout:
            #         fout.write(r.content)
            #     return
            r.json()
    except BaseException as error:
        print(error)
        traceback.print_exc()


def test_request_chaturbate_ajax():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
        'Referer': 'https://chaturbate.com',
        'Host': 'chaturbate.com',
        'origin': 'https://chaturbate.com',
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-Requested-With': 'XMLHttpRequest',
        'Referrer Policy': 'strict-origin-when-cross-origin',
        'cookie': 'csrftoken=PRvAZPwTXIBpnssDsmtfNzV7TwpSqtKt1Dj008KWQGxxei9gYl6U0k9Vo4ENrrp5; affkey=eJyrVipSslJQUtJRUEoBMYwMjEx0Dcx0DU2VagFVGwXN; sbr=sec:sbr95d263fd-4ef7-441e-8a00-0539509b680a:1sIhUi:AY04A4oDiUnoQ5dx6Gdc_9UQjam7sUzS8TcAiQ4342E; _sp_ses.825f=*; cf_clearance=btM3BscNRJ5UmA0kIwdDj5eSwRraUQRwiZ_p_ErEhsc-1718512112-1.0.1.1-Pzk6zkmIjaOYCTq56iHM2W352MZDznCZDwgR01YzId0y27c04lf6kkWL4OL08UNggE4M28NHlC.HFoz83SRIvA; __utfpp=f:trnxa5725b05405f095e735ed03661947dfa:1sIhVZ:kFAd60t_mNjAGqDYeesFIDKrNLhujoSTLzp99BQht_U; agreeterms=1; _sp_id.825f=6461f02b-9646-4e20-9063-1da59b7a816b.1718512103.1.1718512327..54f0e30a-afd8-481b-8ad1-da21c57aba39..a651bcde-7ac4-440a-bfce-aa877fca3031.1718512103070.10; __cf_bm=y.CR_mgvrSGZp3WNvld4ZbeQj4FbBlq7z6WhNTlfspA-1718512981-1.0.1.1-b.7ciLJhP3E_GdrRPNRVd5P.zX0JxN1TrZcg9M8w22fB50Whs8eqn3sfE6Cofl.ra4NzQ5J6xxwwITpAFJb6hg; ag={"teen-cams":16,"18to21-cams":17,"20to30-cams":1}',
        'x-newrelic-id': 'VQIGWV9aDxACUFNVDgMEUw==',
        'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'content-length': '625',
        'content-type': 'multipart/form-data;'
        # 'TE': 'trailers',
        # 'Priority': 'u=1',
    }

    data = {
        'room_slug': 'peek_in_my_window',
        'bandwidth': 'high',
        'csrfmiddlewaretoken': 'PRvAZPwTXIBpnssDsmtfNzV7TwpSqtKt1Dj008KWQGxxei9gYl6U0k9Vo4ENrrp5'
    }

    try:
        with requests.Session() as http_session:
            http_session.headers.update(headers)
            http_session.adapters['https://'].max_retries = Retry.DEFAULT
            scraper = cloudscraper.create_scraper(http_session)
            # r = scraper.get("https://sex-videochat.club/feed/get-models/bonga/all/", timeout=(3.05, 9.05))
            # r = http_session.get("https://sex-videochat.club/feed/get-models/bonga/all/", timeout=(3.05, 9.05))

            r = scraper.post("https://chaturbate.com/get_edge_hls_url_ajax/", data=data, timeout=(10.05, 9.05))
            if r.status_code != 200:
                with open("404.txt", "wb") as fout:
                    fout.write(r.content)
                return
            # r = http_session.get("https://chaturbat.net.ru/chat-model/adalyn_glow/none.json", timeout=(3.05, 9.05))
            # r = scraper.get("https://sex-videochat.club/chaturbate/chat/breeding_material/", timeout=(3.05, 9.05))
            # if r.status_code != 200:
            #     with open("404.txt", "wb") as fout:
            #         fout.write(r.content)
            #     return
            r.json()
    except BaseException as error:
        print(error)
        traceback.print_exc()


def test_tor():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
        'Referer': 'https://chaturbate.com',
        'Host': 'chaturbate.com',
        'origin': 'https://chaturbate.com',
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-Requested-With': 'XMLHttpRequest',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    headers1 = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
        'Referer': 'https://chaturbate.com',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'X-Requested-With': 'XMLHttpRequest',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'TE': 'trailers',
        'DNT': '1',
        'Sec-GPC': '1',
    }

    data = {
        'room_slug': 'peek_in_my_window',
        'bandwidth': 'high',
    }

    proxies = {
        "http": f"socks5h://localhost:9150",
        "https": f"socks5h://localhost:9150",
    }

    browser = {
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True,
        'mobile': False,
    }

    try:
        with requests.Session() as http_session:
            http_session.headers.update(headers1)
            http_session.adapters['https://'].max_retries = Retry.DEFAULT
            scraper = cloudscraper.create_scraper(sess=http_session, interpreter="nodejs", delay=100, browser=browser)
            # rt = RequestsTor()
            r = scraper.get('https://chaturbate.com/api/more_like/ohvivian/', proxies=proxies, timeout=(3.05, 9.05))
            # r = rt.get('https://chaturbate.com/', timeout=(3.05, 9.05))
            i = 0
            while r.status_code != 200 or i < 10:
                with open("404.txt", "wb") as fout:
                    fout.write(r.content)
                r = scraper.get('https://chaturbate.com/api/more_like/ohvivian/', proxies=proxies, timeout=(3.05, 9.05))
                i += 1

            if r.status_code != 200:
                return

            print(r.text)
    except BaseException as error:
        print(error)
        traceback.print_exc()


def test_selenium_firefox():
    firefox_profile = webdriver.FirefoxProfile('C:\\Users\\Gregory\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\zlk8ndod.default-release\\')
    firefox_profile.set_preference('browser.privatebrowsing.autostart', True)
    options = Options()
    options.profile = firefox_profile

    driver = webdriver.Firefox(options=options)
    driver.get('view-source:https://chaturbate.com/api/more_like/ohvivian/')

    content = driver.page_source
    content = driver.find_element(By.TAG_NAME, 'pre').text
    parsed_json = json.loads(content)
    print(parsed_json)

    # driver.quit()


if __name__ == "__main__":
    # root = tk.Tk()
    # demo(root)
    # root.mainloop()
    # test_online(TEST_DATA)
    # test_transparancy()
    # test_request_chaturbat_net_ru()
    # test_request_all_chaturbat_net_ru()
    # test_request_chaturbate_ajax()
    # test_tor()
    test_selenium_firefox()
