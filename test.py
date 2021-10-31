import asyncio
import random
import time
import traceback
from tkinter import CENTER, N, Tk, Canvas, HIDDEN, NORMAL
from tkinter.ttk import Label

from PIL import ImageTk, Image
from aiohttp import ClientSession

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
    listbox = tk.Listbox(master)
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


if __name__ == "__main__":
    # root = tk.Tk()
    # demo(root)
    # root.mainloop()
    # test_online(TEST_DATA)
    test_transparancy()
