# importing vlc module
# import os
#
# os.add_dll_directory(r'C:\Program Files\VideoLAN\VLC')
import os

import vlc
import time


def main():
    # # creating vlc media player object
    # media_player = vlc.MediaPlayer("C:\\Users\\Gregory\\Downloads\\01-01.avi")
    #
    # # start playing video
    # media_player.play()
    #
    # # wait so the video can be played for 5 seconds
    # # irrespective for length of video
    # time.sleep(15)

    # creating a media player object
    media_list_player = vlc.MediaListPlayer()

    # creating Instance class object
    player = vlc.Instance()

    # creating a media list object
    media_list = vlc.MediaList()

    # # creating a new media
    # media = player.media_new("C:\\Users\\Gregory\\tmp2\\lolliis_1701902034689184\\00000000000000000001.ts")
    #
    # # adding media to media list
    # media_list.add_media(media)
    #
    # # creating a new media
    # media = player.media_new("C:\\Users\\Gregory\\tmp2\\lolliis_1701902034689184\\00000000000000000002.ts")
    #
    # # adding media to media list
    # media_list.add_media(media)
    #
    # # creating a new media
    # media = player.media_new("C:\\Users\\Gregory\\tmp2\\lolliis_1701902034689184\\00000000000000000003.ts")
    #
    # # adding media to media list
    # media_list.add_media(media)
    #
    # # creating a new media
    # media = player.media_new("C:\\Users\\Gregory\\tmp2\\lolliis_1701902034689184\\00000000000000000004.ts")
    #
    # # adding media to media list
    # media_list.add_media(media)

    # folder = "C:\\Users\\Gregory\\tmp2\\lolliis_1701902034689184"
    folder = "C:\\Users\\Gregory\\tmp2\\vixenp_1701908303862079"
    for file in os.listdir(folder):
        media = player.media_new(os.path.join(folder, file))
        media_list.add_media(media)

    # setting media list to the media player
    media_list_player.set_media_list(media_list)
    media_list_player.play()

    #
    # https://voj95lu22w.a.trbcdn.net/sch/a18074ac2e5c51f67ec7a84de64ad072/63bf7b12dc8143a92526bc294d85af98/720/32.ts?host=vh-61&version=2&uid=346589176&aid=552159&j=eyJ2byI6LTEsImNwIjoxLCJncyI6ZmFsc2UsImNwcyI6MCwiY2MiOjE4MTQsInBsIjoiIn0%3D&s=b7fa62751136e7ab0b9b1e9b942df5cd
    # https://voj95lu22w.a.trbcdn.net/sch/a18074ac2e5c51f67ec7a84de64ad072/63bf7b12dc8143a92526bc294d85af98/720/33.ts?host=vh-61&version=2&uid=346589176&aid=552159&j=eyJ2byI6LTEsImNwIjoxLCJncyI6ZmFsc2UsImNwcyI6MCwiY2MiOjE4MTQsInBsIjoiIn0%3D&s=7e7dd528954c7ea29baea7fdb23f8f64

    # instance = vlc.Instance('--input-repeat=0', '--fullscreen')
    # player = instance.media_player_new()
    # media = instance.media_new("C:/Users/Gregory/tmp/Vishenka7777_1700127344/00000000000000000029.ts")
    # # media.get_mrl()
    # player.set_media(media)
    # player.play()

    media_player = media_list_player.get_media_player()

    # wait so the video can be played for 5 seconds
    # irrespective for length of video
    # time.sleep(15)
    # media_player.set_rate(0.75)
    #
    # time.sleep(15)
    # media_player.set_rate(0.50)
    #
    # time.sleep(15)
    # media_player.set_rate(0.25)
    #
    # time.sleep(15)
    # media_player.set_rate(0.1)
    #
    # time.sleep(15)
    # media_player.set_rate(0.25)
    #
    # time.sleep(15)
    # media_player.set_rate(0.50)
    #
    # time.sleep(15)
    # media_player.set_rate(0.75)
    #
    # time.sleep(15)
    # media_player.set_rate(1)

    time.sleep(60)


if __name__ == "__main__":
    main()
