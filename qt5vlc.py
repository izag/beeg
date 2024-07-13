import sys, ctypes, vlc
from PyQt5 import QtCore, QtWidgets

class VLCPlayer(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__()
        self._vlc = vlc.Instance()
        self._player = self._vlc.media_player_new()

    @staticmethod
    @vlc.CallbackDecorators.MediaOpenCb
    def _open_cb(voidptr, data, size):
        data.contents.value = voidptr
        size.value = sys.maxsize
        print("OPEN", voidptr, data, size)
        return 0

    @staticmethod
    @vlc.CallbackDecorators.MediaReadCb
    def _read_cb(voidptr, buffer, length):
        print("READ", voidptr, buffer, length)
        stream = ctypes.cast(voidptr, ctypes.POINTER(ctypes.py_object)).contents.value
        data = stream.read(length)
        for index, char in enumerate(data):
            buffer[index] = char
        return len(data)

    @staticmethod
    @vlc.CallbackDecorators.MediaSeekCb
    def _seek_cb(voidptr, offset):
        stream = ctypes.cast(voidptr, ctypes.POINTER(ctypes.py_object)).contents.value
        stream.seek(offset)
        return 0

    @staticmethod
    @vlc.CallbackDecorators.MediaCloseCb
    def _close_cb(voidptr):
        stream = ctypes.cast(voidptr, ctypes.POINTER(ctypes.py_object)).contents.value
        stream.close()

    def play(self):
        self._player.play()

    def stop(self):
        self._player.stop()

    def load(self, path):
        file = QtCore.QFile(path)
        file.open(QtCore.QIODevice.ReadOnly)
        voidptr = ctypes.cast(ctypes.pointer(ctypes.py_object(file)), ctypes.c_void_p)
        self._player.set_media(
            self._vlc.media_new_callbacks(
                self._open_cb,
                self._read_cb,
                self._seek_cb,
                self._close_cb,
                voidptr
            )
        )


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.buttonPlay = QtWidgets.QPushButton('Play')
        self.buttonPlay.clicked.connect(self.handlePlay)
        self.buttonStop = QtWidgets.QPushButton('Stop')
        self.buttonStop.clicked.connect(self.handleStop)
        self.buttonOpen = QtWidgets.QPushButton('Open')
        self.buttonOpen.clicked.connect(self.handleOpen)
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.buttonOpen)
        layout.addWidget(self.buttonPlay)
        layout.addWidget(self.buttonStop)
        self.player = VLCPlayer(self)

    def handlePlay(self):
        self.player.play()

    def handleStop(self):
        self.player.stop()

    def handleOpen(self):
        path, ok = QtWidgets.QFileDialog.getOpenFileName(self, filter='All Files (*.*)')
        if ok:
            self.player.load(path)

if __name__ == '__main__':
    print(sys.maxsize)
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.setWindowTitle('VLC Player')
    window.setGeometry(600, 100, 200, 80)
    window.show()
    sys.exit(app.exec_())