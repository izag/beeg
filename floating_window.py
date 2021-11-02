import tkinter as tk
from tkinter import HIDDEN, NORMAL
from ctypes import windll
from PIL import Image, ImageTk

INIT_WIDTH = 200
INIT_HEIGHT = 120

GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        # self.overrideredirect(True)
        # self.set_appwindow()
        self.x = None
        self.y = None

        self.img_orig = Image.open("assets/girl.jpg")
        img = fit_image(self.img_orig, INIT_WIDTH, INIT_HEIGHT)
        width, height = img.size

        self.geometry('{}x{}'.format(width, height))

        self.canvas = tk.Canvas(self, width=width, height=height, bd=0, highlightthickness=0)

        x_center = width // 2
        y_center = height // 2
        self.photo_img = ImageTk.PhotoImage(img)
        self.bg_img = self.canvas.create_image(x_center, y_center, image=self.photo_img)

        self.id_rect = self.canvas.create_rectangle(5, 5, width - 5, height - 5,
                                                    outline='red',
                                                    width=10,
                                                    fill='')
        self.canvas.pack()
        self.canvas.addtag_all("all")

        self.after(333, self.blink, self.canvas, self.id_rect)

        w_orig, h_orig = self.img_orig.size
        self.maxsize(w_orig, h_orig)

        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.do_move)
        self.bind("<Configure>", self.on_resize)
        # self.bind('<Enter>', self.on_enter)
        # self.bind('<Leave>', self.on_leave)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def blink(self, canvas, id_figure):
        state = canvas.itemcget(id_figure, 'state')
        if state != HIDDEN:
            canvas.itemconfigure(id_figure, state=HIDDEN)
        else:
            canvas.itemconfigure(id_figure, state=NORMAL)
        self.after(333, self.blink, canvas, id_figure)

    def on_enter(self, event):
        self.overrideredirect(False)

    def on_leave(self, event):
        self.overrideredirect(True)
        self.set_appwindow()

    def on_resize(self, event):
        self.canvas.config(width=event.width, height=event.height)
        img = fit_image(self.img_orig, event.width, event.height)
        self.photo_img = ImageTk.PhotoImage(img)
        self.canvas.itemconfigure(self.bg_img, image=self.photo_img)
        self.canvas.moveto(self.bg_img, 0, 0)
        self.canvas.coords(self.id_rect, 5, 5, event.width - 5, event.height - 5)

    def set_appwindow(self):
        hwnd = windll.user32.GetParent(self.winfo_id())
        style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
        res = windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
        # re-assert the new window style
        self.withdraw()
        self.after(10, self.deiconify)


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


if __name__ == "__main__":
    app = App()
    app.mainloop()
