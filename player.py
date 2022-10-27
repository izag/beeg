# importing vlc module
import os

os.add_dll_directory(r'C:\Program Files\VideoLAN\VLC')

import vlc
import time




def main():
    # creating vlc media player object
    media_player = vlc.MediaPlayer("C:\\Users\\Gregory\\tmp1\\abby_youyou_1665567238.ts")

    # start playing video
    media_player.play()

    # wait so the video can be played for 5 seconds
    # irrespective for length of video
    time.sleep(5)


if __name__ == "__main__":
    main()
