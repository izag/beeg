import sys
import vlc
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
# from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtPrintSupport import *

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.sizeHint = lambda: QSize(1280, 900)
        self.move(100, 10)
        self.mainFrame = QFrame()
        self.setCentralWidget(self.mainFrame)
        t_lay_parent = QHBoxLayout()
        t_lay_parent.setContentsMargins(0, 0, 0, 0)

        self.videoFrame = QFrame()
        self.videoFrame.mouseDoubleClickEvent = self.mouseDoubleClickEvent
        t_lay_parent.addWidget(self.videoFrame)
        self.vlcInstance = vlc.Instance(['--video-on-top'])
        self.videoPlayer = self.vlcInstance.media_player_new()
        self.videoPlayer = self.vlcInstance.media_player_new()
        self.videoPlayer.video_set_mouse_input(False)
        self.videoPlayer.video_set_key_input(False)
        self.videoPlayer.set_mrl("C:\\Users\\Gregory\\Documents\\Study\\JVA-076\\JVA-076 08.07\\day14.mp4")
        self.videoPlayer.audio_set_mute(True)
        if sys.platform.startswith('linux'): # for Linux using the X Server
            self.videoPlayer.set_xwindow(self.videoFrame.winId())
        elif sys.platform == "win32": # for Windows
            self.videoPlayer.set_hwnd(self.videoFrame.winId())
        elif sys.platform == "darwin": # for MacOS
            self.videoPlayer.set_nsobject(int(self.videoFrame.winId()))

        self.videoPlayer.play()


        self.videoFrame1 = QFrame()
        t_lay_parent.addWidget(self.videoFrame1)
        self.videoFrame1.mouseDoubleClickEvent = self.mouseDoubleClickEvent1
        self.vlcInstance1 = vlc.Instance(['--video-on-top'])
        self.videoPlayer1 = self.vlcInstance1.media_player_new()
        self.videoPlayer1 = self.vlcInstance1.media_player_new()
        self.videoPlayer1.video_set_mouse_input(False)
        self.videoPlayer1.video_set_key_input(False)
        self.videoPlayer1.set_mrl("C:\\Users\Gregory\\Documents\\Study\\JVA-076\\JVA-076 08.07\\day13.mp4")
        self.videoPlayer1.audio_set_mute(True)
        if sys.platform.startswith('linux'): # for Linux using the X Server
            self.videoPlayer1.set_xwindow(self.videoFrame1.winId())
        elif sys.platform == "win32": # for Windows
            self.videoPlayer1.set_hwnd(self.videoFrame1.winId())
        elif sys.platform == "darwin": # for MacOS
            self.videoPlayer1.set_nsobject(int(self.videoFrame1.winId()))

        self.videoPlayer1.play()

        self.mainFrame.setLayout(t_lay_parent)
        self.show()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.windowState() == Qt.WindowNoState:
                self.videoFrame1.hide()
                self.videoFrame.show()
                self.setWindowState(Qt.WindowFullScreen)
            else:
                self.videoFrame1.show()
                self.setWindowState(Qt.WindowNoState)

    def mouseDoubleClickEvent1(self, event):
        if event.button() == Qt.LeftButton:
            if self.windowState() == Qt.WindowNoState:
                self.videoFrame.hide()
                self.videoFrame1.show()
                self.setWindowState(Qt.WindowFullScreen)
            else:
                self.videoFrame.show()
                self.setWindowState(Qt.WindowNoState)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("VLC Test")

    window = MainWindow()
    app.exec_()