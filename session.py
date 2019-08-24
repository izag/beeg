import io
import logging
import os
import subprocess
import sys
import time
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Thread
from tkinter import Tk, Image, Label
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import build_opener

from PIL import Image, ImageTk

opener = build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

MAX_FAILS = 6
PAD = 5
DELAY = 2000
OUTPUT = "C:/tmp/"

logger = logging.getLogger('beeg_application')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(threadName)s:%(funcName)s > %(message)s')

executor = ThreadPoolExecutor(max_workers=10)


class Chunks:
    IDX_CUR_POS = 3

    def __init__(self, lines):
        self.ts = [line for line in lines if not line.startswith("#")]
        self.cur_pos = int(lines[Chunks.IDX_CUR_POS].split(':')[1])


class RecordSession(Thread):
    MIN_CHUNKS = 6

    def __init__(self, master, url_base, model, chunk_url, dir_output):
        super(RecordSession, self).__init__()

        self.master = master
        self.base_url = url_base
        self.model_name = model
        self.output_dir = dir_output
        self.chunks_url = urljoin(self.base_url, chunk_url)
        self.name = 'RecordSession'
        self.stopped = False
        self.daemon = True

    def get_model_name(self):
        return self.model_name

    def get_best_quality(self):
        plst_url = urljoin(self.base_url, "playlist.m3u8")
        with opener.open(plst_url) as f:
            content = f.read().decode('utf-8')
            lines = content.splitlines()

            return lines[-1]

    def get_chunks(self):
        logger.debug(self.chunks_url)
        try:
            with opener.open(self.chunks_url) as f:
                content = f.read().decode('utf-8')
                lines = content.splitlines()

                if len(lines) < RecordSession.MIN_CHUNKS:
                    return None

                return Chunks(lines)
        except HTTPError as error:
            logger.exception(error)
            return None

    def save_to_file(self, filename):
        logger.debug(filename)
        fpath = os.path.join(self.output_dir, filename)
        if os.path.exists(fpath):
            logger.debug("Skipped: " + filename)
            return

        ts_url = urljoin(self.base_url, filename)
        subprocess.run(["c:\\progs\\wget\\wget.exe", "-q", "--no-check-certificate",
                        "-O", fpath,
                        ts_url])

    def run(self):
        fails = 0
        last_pos = 0

        while not self.stopped:
            chunks = self.get_chunks()
            if chunks is None:
                logger.info("Offline : " + self.chunks_url)
                fails += 1

                if fails > MAX_FAILS:
                    self.master.quit()
                    self.master.update_idletasks()
                    return

                time.sleep(1)
                continue
            else:
                fails = 0

            if last_pos >= chunks.cur_pos:
                time.sleep(0.5)
                continue

            last_pos = chunks.cur_pos
            logger.debug(last_pos)

            try:
                for ts in chunks.ts:
                    executor.submit(self.save_to_file, ts)
            except BaseException as e:
                logger.exception(e)

            time.sleep(0.5)

    def stop(self):
        self.stopped = True


class ImageWindow:

    def __init__(self, master, img_url):
        self.master = master
        self.img_url = img_url
        self.name = "ImageWindow"
        self.model_image = None

        self.image_label = Label(master)
        self.image_label.pack()

        self.load_image()

    def load_image(self):
        try:
            with opener.open(self.img_url) as f:
                raw_data = f.read()
                content = io.BytesIO(raw_data)
                img = Image.open(content)
                self.model_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.model_image)
        except BaseException as e:
            logger.exception(e)

        self.master.update_idletasks()
        self.master.after(DELAY, self.load_image)


class Control(Thread):

    def __init__(self, master, session):
        super(Control, self).__init__()
        self.master = master
        self.session = session
        self.daemon = True

    def run(self):
        while True:
            try:
                cmd = input()
                if cmd != 'exit':
                    print('pong')
                    continue
            except EOFError as e:
                logger.exception(e)

            print('bye')
            self.session.stop()
            self.master.quit()
            self.master.update_idletasks()
            return


if __name__ == "__main__":
    if len(sys.argv) < 5:
        sys.exit(1)

    base_url = sys.argv[1]
    model_name = sys.argv[2]
    chunks_url = sys.argv[3]
    image_url = sys.argv[4]

    output_dir = OUTPUT + model_name + '_' + str(int(time.time()))
    os.mkdir(output_dir)

    fh = logging.FileHandler(output_dir + '/' + model_name + '.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info("Started!")

    root = Tk()
    root.resizable(False, False)
    root.title(model_name + ' - Recording')
    record_session = RecordSession(root, base_url, model_name, chunks_url, output_dir)
    record_session.start()
    control = Control(root, record_session)
    control.start()
    my_gui = ImageWindow(root, image_url)
    root.mainloop()
    logger.info("Exited!")
    print('bye')
    sys.exit(0)
