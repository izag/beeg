import tkinter as tk
from tkinter import HIDDEN, NORMAL, Button, LEFT, TOP, NW, NSEW, CENTER
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
        self.x = None
        self.y = None
        self.is_original = False

        self.img_orig = Image.open("assets/girl.jpg")
        self.w_orig, self.h_orig = self.img_orig.size
        img = fit_image(self.img_orig, INIT_WIDTH, INIT_HEIGHT)
        self.w_resized, self.h_resized = img.size

        self.geometry(f'{self.w_resized}x{self.h_resized}')
        self.eval('tk::PlaceWindow . center')

        self.canvas = tk.Canvas(self, width=self.w_resized, height=self.h_resized, bd=0, highlightthickness=0)

        x_center = self.w_resized // 2
        y_center = self.h_resized // 2
        self.photo_img = ImageTk.PhotoImage(img)
        self.bg_img = self.canvas.create_image(x_center, y_center, image=self.photo_img)

        self.id_rect = self.canvas.create_rectangle(4, 4, self.w_resized - 4, self.h_resized - 4,
                                                    outline='red',
                                                    width=8,
                                                    fill='')

        img = Image.open('assets/rec_small.png')
        self.img_record = ImageTk.PhotoImage(img)
        self.btn_start = Button(self, image=self.img_record)
        # self.btn_start.pack(side=TOP, anchor=NW)

        self.canvas.place(x=x_center, y=y_center, anchor=CENTER, relwidth=1, relheight=1)

        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.do_move)
        self.bind("<Configure>", self.on_resize)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Double-Button-1>', self.on_double_click)

        self.after(333, self.blink, self.canvas, self.id_rect)
        # self.after(100, self.set_appwindow)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        if self.x is None or self.y is None:
            return

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
        # self.overrideredirect(False)
        # width = self.winfo_width()
        # height = self.winfo_height()
        self.btn_start.pack(side=TOP, anchor=NW)
        self.geometry(f"+{self.winfo_x()}+{self.winfo_y()}")

    def on_leave(self, event):
        # self.overrideredirect(True)
        # self.set_appwindow()
        self.btn_start.pack_forget()

    def on_resize(self, event):
        self.resize_canvas(event.width, event.height)

    def on_double_click(self, event):
        width = self.w_resized
        height = self.h_resized
        if not self.is_original:
            width = self.w_orig
            height = self.h_orig

        self.geometry(f'{width}x{height}')
        self.resize_canvas(width, height)

        if not self.is_original:
            self.center()

        self.is_original = not self.is_original

    def resize_canvas(self, width, height):
        self.canvas.config(width=width, height=height)
        img = fit_image(self.img_orig, width, height)
        self.photo_img = ImageTk.PhotoImage(img)
        self.canvas.itemconfigure(self.bg_img, image=self.photo_img)
        x_center = width // 2
        y_center = height // 2
        self.canvas.coords(self.bg_img, x_center, y_center)
        self.canvas.coords(self.id_rect, 4, 4, width - 4, height - 4)
        self.canvas.place_configure(x=x_center, y=y_center, anchor=CENTER, relwidth=1, relheight=1)

    def set_appwindow(self):
        hwnd = windll.user32.GetParent(self.winfo_id())
        style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
        res = windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
        # re-assert the new window style
        self.withdraw()
        self.after(10, self.deiconify)

    def center(self):
        self.update_idletasks()
        width = self.winfo_width()
        frm_width = self.winfo_rootx() - self.winfo_x()
        win_width = width + 2 * frm_width
        height = self.winfo_height()
        titlebar_height = self.winfo_rooty() - self.winfo_y()
        win_height = height + titlebar_height + frm_width
        x = self.winfo_screenwidth() // 2 - win_width // 2
        y = self.winfo_screenheight() // 2 - win_height // 2
        self.geometry(f'+{x}+{y}')
        self.deiconify()


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
