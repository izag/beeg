import tkinter as tk
import vlc
from tkinter import filedialog, W, E, ttk, HORIZONTAL, BOTTOM, X, BOTH, TOP, LEFT
from datetime import timedelta


class MediaPlayerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Media Player")
        self.geometry("800x600")

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self.current_file = None
        self.playing_video = False
        self.video_paused = False

        frm_top = tk.Frame(self)
        frm_bottom = tk.Frame(self)

        self.search = tk.StringVar()
        self.entry_play = tk.Entry(frm_top, textvariable=self.search)
        self.entry_play.pack(side=LEFT, fill=X, padx=5, expand=True)

        self.btn_play = tk.Button(frm_top, text="PLay", command=self.on_play)
        self.btn_play.pack(side=LEFT)

        self.btn_stop = tk.Button(frm_top, text="Stop", command=self.on_stop)
        self.btn_stop.pack(side=LEFT)

        self.media_canvas = tk.Canvas(frm_bottom, bg="black")
        self.media_player.set_hwnd(self.media_canvas.winfo_id())
        self.media_canvas.pack(fill=BOTH, expand=True)

        self.progress = ttk.Progressbar(frm_bottom, orient=HORIZONTAL, length=30, mode='indeterminate')
        self.progress.pack(side=BOTTOM, fill=X)

        frm_top.pack(side=TOP, fill=X)
        frm_bottom.pack(fill=BOTH, expand=True)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Media Files", "*.mp4 *.avi"), ("All Files", "*.*")]
        )
        if file_path:
            self.current_file = file_path
            self.time_label.config(text="00:00:00 / " + self.get_duration_str())
            self.play_video()

    def get_duration_str(self):
        if self.playing_video:
            total_duration = self.media_player.get_length()
            total_duration_str = str(timedelta(milliseconds=total_duration))[:-3]
            return total_duration_str
        return "00:00:00"

    def play_video(self):
        if not self.playing_video:
            media = self.instance.media_new(self.current_file)
            self.media_player.set_media(media)
            self.media_player.play()
            self.playing_video = True

    def fast_forward(self):
        if self.playing_video:
            current_time = self.media_player.get_time() + 10000
            self.media_player.set_time(current_time)

    def rewind(self):
        if self.playing_video:
            current_time = self.media_player.get_time() - 10000
            self.media_player.set_time(current_time)

    def pause_video(self):
        if self.playing_video:
            if self.video_paused:
                self.media_player.play()
                self.video_paused = False
                self.pause_button.config(text="Pause")
            else:
                self.media_player.pause()
                self.video_paused = True
                self.pause_button.config(text="Resume")

    def stop(self):
        if self.playing_video:
            self.media_player.stop()
            self.playing_video = False
        self.time_label.config(text="00:00:00 / " + self.get_duration_str())

    def set_video_position(self, value):
        if self.playing_video:
            total_duration = self.media_player.get_length()
            position = int((float(value) / 100) * total_duration)
            self.media_player.set_time(position)

    def update_video_progress(self):
        if self.playing_video:
            total_duration = self.media_player.get_length()
            current_time = self.media_player.get_time()
            # if total_duration != 0:
            #     progress_percentage = (current_time / total_duration) * 100
            #     self.progress_bar.set(progress_percentage)
            current_time_str = str(timedelta(milliseconds=current_time))[:-3]
            total_duration_str = str(timedelta(milliseconds=total_duration))[:-3]
            self.time_label.config(text=f"{current_time_str}/{total_duration_str}")
        self.after(1000, self.update_video_progress)
        
    def on_play(self):
        pass

    def on_stop(self):
        pass


if __name__ == "__main__":
    app = MediaPlayerApp()
    app.update_video_progress()
    app.mainloop()
