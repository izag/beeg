import socket
import socketserver
import sys, ctypes, vlc, clipboard
import threading
import os
import time
from PyQt5 import QtCore, QtWidgets, QtNetwork, QtGui


HOST = 'localhost'
PORT = 8686
SERVER_ADDRESS = (HOST, PORT)


class StreamProviderDir(object):
    def __init__(self, rootpath, file_ext):
        self._media_files = []
        self._rootpath = rootpath
        self._file_ext = file_ext
        self._start_file_count = 0
        self._index = 0
        self._data = None
        self._pos = 0


    def update_file_list(self):
        print("read file list")
        NFILES = 3
        files = []
        try_count = 10
        while try_count > 0 and len(files) == 0:
            for entry in os.listdir(self._rootpath):
                if os.path.splitext(entry)[1] == f".{self._file_ext}":
                    files.append(os.path.join(self._rootpath, entry))
            try_count -= 1

        if len(files) == 0:
            return

        files.sort()

        # first run
        if self._start_file_count == 0:
            if len(files) <= NFILES:
                self._media_files = files
            else:
                self._start_file_count = len(files) - NFILES
            
            wait_download(files[-1])

        self._media_files = files[self._start_file_count:]

        # print("playlist:")
        # for index, media_file in enumerate(self._media_files):
        #     print(f"[{index}] {media_file}")

    def open(self):
        """
        this function is responsible of opening the media.
        it could have been done in the __init__, but it is just an example

        in this case it scan the specified folder, but it could also scan a
        remote url or whatever you prefer.
        """

        self.update_file_list()

    def release_resources(self):
        """
        In this example this function is just a placeholder,
        in a more complex example this may release resources after the usage,
        e.g. closing the socket from where we retrieved media data
        """
        print("releasing stream provider")
        # self._data = None

    def seek(self, offset):
        """
        Again, a placeholder, not useful for the example
        """
        print(f"requested seek with offset={offset}")

    def get_data(self, length):
        """
        It reads the current file in the list and returns the binary data
        In this example it reads from file, but it could have downloaded data from an url
        """

        try_count = 10
        while self._index == len(self._media_files) and try_count > 0:
            print("the end of file list is reached")
            self.update_file_list()
            try_count -= 1
            time.sleep(0.5)

        if self._index == len(self._media_files):
            print("file list is over")
            return b''
        
        data = b''
        if self._data is None:
            print(f"reading file [{self._index}] {self._media_files[self._index]}")
            self.update_file_list()
            with open(self._media_files[self._index], 'rb') as stream:
                self._data = stream.read()
                self._pos = 0

        if self._pos < len(self._data):
            # print(f"pos={self._pos} len={len(self._data)}")
            remains = len(self._data) - self._pos
            # print(f"remains={remains} length={length}")
            len_to_read = min(length, remains)
            # print(f"len_to_read={len_to_read} interval=[{self._pos}, {self._pos + len_to_read}]")
            data = self._data[self._pos:self._pos + len_to_read]
            self._pos = self._pos + len_to_read
            # print(f"new_pos={self._pos}")

        if self._pos >= len(self._data):
            self._index = self._index + 1
            # print(f"go to index={self._index}")
            self._data = None

        return data


def get_size(filepath):
    if os.path.isfile(filepath): 
        st = os.stat(filepath)
        return st.st_size
    else:
        return -1
    

def wait_download(file_path):
    current_size = get_size(file_path)
    time.sleep(0.5)
    new_size = get_size(file_path)
    try_count = 10
    while try_count > 0 and (current_size != new_size or new_size == 0):
        print(f'waiting for file to be downloded {file_path}')
        current_size = new_size
        time.sleep(0.5)
        try_count -= 1
        new_size = get_size(file_path)


@vlc.CallbackDecorators.MediaOpenCb
def media_open_cb(opaque, data_pointer, size_pointer):
    print("OPEN", opaque, data_pointer, size_pointer)

    stream_provider = ctypes.cast(opaque, ctypes.POINTER(ctypes.py_object)).contents.value
    stream_provider.open()

    data_pointer.contents.value = opaque
    size_pointer.value = sys.maxsize

    print("OPEN", opaque, data_pointer, size_pointer)

    return 0


@vlc.CallbackDecorators.MediaReadCb
def media_read_cb(opaque, buffer, length):
    # print("READ", opaque, buffer, length)

    stream_provider = ctypes.cast(opaque, ctypes.POINTER(ctypes.py_object)).contents.value

    data = stream_provider.get_data(length)
    bytes_read = len(data)

    new_data = data
    if bytes_read > length:
        new_data = data[:length]
        bytes_read = length

    if bytes_read > 0:
        for index, char in enumerate(new_data):
            buffer[index] = char

    # print(f"just read {bytes_read} bytes")
    return bytes_read


@vlc.CallbackDecorators.MediaSeekCb
def media_seek_cb(opaque, offset):
    print("SEEK", opaque, offset)

    stream_provider = ctypes.cast(opaque, ctypes.POINTER(ctypes.py_object)).contents.value
    stream_provider.seek(offset)

    return 0


@vlc.CallbackDecorators.MediaCloseCb
def media_close_cb(opaque):
    print("CLOSE", opaque)

    stream_provider = ctypes.cast(opaque, ctypes.POINTER(ctypes.py_object)).contents.value
    stream_provider.release_resources()


class VLCPlayer(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__()
        self._vlc = vlc.Instance()
        self._player = self._vlc.media_player_new()
        self._player.event_manager().event_attach(
            vlc.EventType.MediaPlayerEndReached, self._handle_finished
        )
        self._player.video_set_key_input(0)
        self._player.video_set_mouse_input(0)
        self._provider = StreamProviderDir('.', 'ts')
    
    def play(self):
        self._player.audio_set_volume(100)
        self._player.play()
        # print(self._player.get_hwnd())

    def stop(self):
        self._player.stop()

    def set_rate(self, rate):
        self._player.set_rate(rate)

    def load(self, path):
        self._provider = StreamProviderDir(path.strip(), 'ts')
        stream_provider_ptr = ctypes.cast(ctypes.pointer(ctypes.py_object(self._provider)), ctypes.c_void_p)
        self._player.set_media(
            self._vlc.media_new_callbacks(
                media_open_cb,
                media_read_cb,
                media_seek_cb,
                media_close_cb,
                stream_provider_ptr
            )
        )

    def set_hwnd(self, wnd):
        self._player.set_hwnd(wnd)

    def get_hwnd(self):
        self._player.get_hwnd()

    def _handle_finished(self, event):
        if event.type == vlc.EventType.MediaPlayerEndReached:
            self.player.stop()

    def toggle_fullscreen(self):
        self._player.toggle_fullscreen()


class StopSignalEmitter(QtCore.QObject):
    stop_signal = QtCore.pyqtSignal(str, name='stop')


emitter = StopSignalEmitter()


class VideoFrame(QtWidgets.QFrame):
    def __init__(self, mainWin):
        super().__init__()
        self.frm = mainWin
    
    def mousePressEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.RightButton:
            self.frm.setWindowState(self.frm.windowState() & ~QtCore.Qt.WindowFullScreen)
            self.frm.buttonsFrame.show()
            self.frm.handleStop()
            self.frm.setWindowState(self.frm.windowState() | QtCore.Qt.WindowMinimized)


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        self.buttonPlay = QtWidgets.QPushButton('Play')
        self.buttonPlay.clicked.connect(self.handlePlay)
        self.buttonStop = QtWidgets.QPushButton('Stop')
        self.buttonStop.clicked.connect(self.handleStop)
        # self.buttonRate = QtWidgets.QPushButton('Rate')
        # self.buttonRate.clicked.connect(self.handleRate)
        emitter.stop_signal.connect(self.handlePlayAnother)

        self.hbuttonbox = QtWidgets.QHBoxLayout()
        self.hbuttonbox.addWidget(self.buttonPlay)
        self.hbuttonbox.addWidget(self.buttonStop)
        # layout.addWidget(self.buttonRate)

        self.buttonsFrame = QtWidgets.QFrame()
        self.buttonsFrame.setLayout(self.hbuttonbox)
        self.buttonsFrame.setMinimumSize(QtCore.QSize(200, 40))
        self.buttonsFrame.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        self.videoframe = VideoFrame(self)
        # self.palette = self.videoframe.palette()
        # self.palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        # self.videoframe.setPalette(self.palette)
        # self.videoframe.setAutoFillBackground(True)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.setContentsMargins(0, 0, 0, 0)
        self.vboxlayout.addWidget(self.buttonsFrame)
        self.vboxlayout.addWidget(self.videoframe)
        self.widget.setLayout(self.vboxlayout)

        self.player = VLCPlayer()
        self.player.set_hwnd(self.videoframe.winId())

        self.shortcutFull = QtWidgets.QShortcut(self)
        self.shortcutFull.setKey(QtGui.QKeySequence('F'))
        self.shortcutFull.setContext(QtCore.Qt.ApplicationShortcut)
        self.shortcutFull.activated.connect(self.handleFullScreen)

    def handlePlay(self):
        path = clipboard.paste()
        if not os.path.exists(path):
            return
        
        self.player.load(path)
        self.player.play()

    def handleStop(self):
        self.player.stop()

    def handlePlayAnother(self, path):
        self.player.stop()

        self.setWindowTitle(path)

        self.buttonsFrame.hide()
        # this will remove minimized status 
        # and restore window with keeping maximized/normal state
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)

        # this will activate the window
        self.activateWindow()

        self.player.load(path)
        self.player.play()
        self.setWindowState(self.windowState() | QtCore.Qt.WindowFullScreen)

    def handleRate(self):
        # Server().startServer()
        # Messenger().slotSendMessage()
        self.rate = self.rate / 2
        self.player.set_rate(self.rate)

    def handleOpen(self):
        path, ok = QtWidgets.QFileDialog.getOpenFileName(self, filter='All Files (*.*)')
        if ok:
            self.player.load(path)

    def handleFullScreen(self):
        if self.isFullScreen():
            self.setWindowState(self.windowState() & ~QtCore.Qt.WindowFullScreen)
            self.buttonsFrame.show()
        else:
            self.buttonsFrame.hide()
            self.setWindowState(self.windowState() | QtCore.Qt.WindowFullScreen)
            
    # def mousePressEvent(self, QMouseEvent):
    #     if QMouseEvent.button() == QtCore.Qt.RightButton:
    #         self.setWindowState(self.windowState() & ~QtCore.Qt.WindowFullScreen)
    #         self.buttonsFrame.show()
    #         self.handleStop()

class Messenger(object):
    def __init__(self):
        super(Messenger, self).__init__()
        self.pSocket = None
        self.listenServer = None
        self.pSocket = QtNetwork.QTcpSocket()
        self.pSocket.readyRead.connect(self.slotReadData)
        self.pSocket.connected.connect(self.on_connected)
        self.pSocket.error.connect(self.on_error)

    def slotSendMessage(self):
        self.pSocket.connectToHost(QtNetwork.QHostAddress.LocalHost, PORT)

    def on_error(self, error):
        if error == QtNetwork.QAbstractSocket.ConnectionRefusedError:
            print(f'Unable to send data to port: {PORT}')
            print("trying to reconnect")
            QtCore.QTimer.singleShot(1000, self.slotSendMessage)

    def on_connected(self):
        cmd = "Hi there!"
        print("Command Sent:", cmd)
        ucmd = unicode(cmd, "utf-8")
        self.pSocket.write(ucmd)
        self.pSocket.flush()
        self.pSocket.disconnectFromHost()

    def slotReadData(self):
        print("Reading data:", self.pSocket.readAll())


# class Server(threading.Thread):

#     def run():
#         # Настраиваем сокет
#         server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         server_socket.bind(SERVER_ADDRESS)
#         server_socket.listen(10)
#         print(f'server is running {SERVER_ADDRESS}')

#         while True:
#             connection, address = server_socket.accept()
#             print(f"new connection from {address}")

#             data = connection.recv(1024)
#             print(str(data))

#             connection.send(bytes('Hello from server!', encoding='UTF-8'))

#             connection.close()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        path = str(self.rfile.readline(), 'ascii').strip()
        print('received: ' + path)
        # player.stop()
        # player.load(path)
        # player.play()
        emitter.stop_signal.emit(path)


class Client(QtCore.QObject):
    def SetSocket(self, socket):
        self.socket = socket
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_connected)
        self.socket.readyRead.connect(self.on_readyRead)
        print("Client Connected from IP %s" % self.socket.peerAddress().toString())

    def on_connected(self):
        print("Client Connected Event")

    def on_disconnected(self):
        print("Client Disconnected")

    def on_readyRead(self):
        msg = self.socket.readAll()
        print(type(msg), msg.count())
        print("Client Message:", msg)


# class Server(QtCore.QObject):
#     def __init__(self, parent=None):
#         QtCore.QObject.__init__(self)
#         self.server = QtNetwork.QTcpServer()
#         self.server.newConnection.connect(self.on_newConnection)

#     def on_newConnection(self):
#         while self.server.hasPendingConnections():
#             print("Incoming Connection...")
#             self.client = Client(self)
#             self.client.SetSocket(self.server.nextPendingConnection())

#     def startServer(self):
#         if self.server.listen(QtNetwork.QHostAddress.LocalHost, PORT):
#             print(f"Server is listening on port: {PORT}")
#             self.server.newConnection.connect(self.on_newConnection)
#         else:
#             print("Server couldn't wake up")


if __name__ == '__main__':
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    with server:
        ip, port = server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

        app = QtWidgets.QApplication(sys.argv)  
        window = Window()
        window.setWindowTitle('VLC Player')
        window.setGeometry(600, 100, 200, 80)
        window.show()
        exit_code = app.exec_()
        server.shutdown()
        sys.exit(exit_code)