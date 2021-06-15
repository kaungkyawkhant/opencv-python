import sys

import cv2
import numpy as np
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QDir, QUrl
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtMultimedia import QMediaContent
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QAction, QFileDialog, QMainWindow, QSlider, \
    QSizePolicy, QHBoxLayout, QPushButton, QStyle, QGridLayout

from FaceDetectionModule import FaceDetector
from HandTrackingModules import HandDetector


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img)
        # shut down capture system
        cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Video Client")
        self.thread = VideoThread()
        self.faceDetector = FaceDetector()
        self.handDetector = HandDetector()
        # self.setWindowTitle("Qt live label demo")
        self.disply_width = 1400
        self.display_height = 800

        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(self.disply_width, self.display_height)

        # create open webcam button
        self.openWebCamBtn = QPushButton()
        self.openWebCamBtn.setEnabled(True)
        self.openWebCamBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.openWebCamBtn.clicked.connect(self.openWebCam)

        # create detect face button
        self.detectFaceBtn = QPushButton()
        self.detectFaceBtn.setEnabled(False)
        self.detectFaceBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.detectFaceBtn.clicked.connect(self.detectFace)
        # create detect hand button
        self.detectHandBtn = QPushButton()
        self.detectHandBtn.setEnabled(False)
        self.detectHandBtn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        self.detectHandBtn.clicked.connect(self.detectHands)

        self.btnLayouts = QHBoxLayout()
        self.btnLayouts.setContentsMargins(0, 0, 0, 0)
        self.btnLayouts.addWidget(self.openWebCamBtn, alignment=Qt.AlignLeft | Qt.AlignBottom)
        self.btnLayouts.addWidget(self.detectFaceBtn, alignment=Qt.AlignLeft | Qt.AlignBottom)
        self.btnLayouts.addWidget(self.detectHandBtn, alignment=Qt.AlignLeft | Qt.AlignBottom)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.image_label)
        self.mainLayout.addLayout(self.btnLayouts)

        self.central_Widget = QWidget()
        self.central_Widget.setLayout(self.mainLayout)
        self.setCentralWidget(self.central_Widget)

        # create Open Action
        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open Video')
        openAction.triggered.connect(self.openFile)
        # create Open Webcam Action
        webCamAction = QAction(QIcon('open.png'), '&WebCam', self)
        webCamAction.setShortcut('Ctrl+W')
        webCamAction.setStatusTip('Open WebCam')
        webCamAction.triggered.connect(self.openWebCam)
        # create Exit Action
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit Application')
        exitAction.triggered.connect(self.exitCall)

        # create menu bar and add actions
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(webCamAction)
        fileMenu.addAction(exitAction)

        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        # set the vbox layout as the widgets layout
        self.setLayout(vbox)

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""

        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    @pyqtSlot(np.ndarray)
    def update_faceimage(self, cv_img):
        """Updates the image_label with a new opencv image"""
        cv_faceimg, bbox = self.faceDetector.findFaces(cv_img)
        qt_img = self.convert_cv_qt(cv_faceimg)
        self.image_label.setPixmap(qt_img)

    @pyqtSlot(np.ndarray)
    def update_handimage(self, cv_img):
        """Updates the image_label with a new opencv image"""
        cv_hangimg = self.handDetector.findHands(cv_img)
        qt_img = self.convert_cv_qt(cv_hangimg)
        self.image_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb_image.shape

        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def openWebCam(self):
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()
        self.detectFaceBtn.setEnabled(True)
        self.detectHandBtn.setEnabled(True)

    def detectFace(self):
        self.thread.change_pixmap_signal.disconnect(self.update_image)
        self.thread.change_pixmap_signal.connect(self.update_faceimage)
        # start the thread
        self.thread.start()
        self.detectFaceBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

    def detectHands(self):
        if self.detectHandBtn.setEnabled(True):
            self.thread.change_pixmap_signal.disconnect(self.update_faceimage)
        # self.thread.change_pixmap_signal.disconnect(self.update_image)

        self.thread.change_pixmap_signal.connect(self.update_handimage)
        # start the thread
        self.thread.start()

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open Video', QDir.homePath())
        if fileName != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
            self.detectFaceBtn.setEnabled(True)

    def exitCall(self):
        sys.exit(app.exec_())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = MainWindow()
    a.resize(1500, 900)
    a.show()
    sys.exit(app.exec_())

# =================================#
# import sys
#
# from PyQt5.QtCore import QDir, Qt, QUrl
# from PyQt5.QtGui import QIcon
# from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
# from PyQt5.QtMultimediaWidgets import QVideoWidget
# from PyQt5.QtWidgets import QMainWindow, QPushButton, QStyle, QApplication, QSlider, QLabel, QSizePolicy, QAction, \
#     QFileDialog, QWidget, QHBoxLayout, QVBoxLayout
#
#
# class VideoWindow(QMainWindow):
#
#     def __init__(self, parent=None):
#         super(VideoWindow, self).__init__(parent)
#         self.setWindowTitle("Video Client")
#         self.mediaPlayer = QMediaPlayer(None,QMediaPlayer.VideoSurface)
#         videoWidget = QVideoWidget()
#         self.playButton = QPushButton()
#         self.playButton.setEnabled(False)
#         self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
#         self.playButton.clicked.connect(self.play)
#
#         self.positionSlider = QSlider(Qt.Horizontal)
#         self.positionSlider.setRange(0,0)
#         self.positionSlider.sliderMoved.connect(self.setPosition)
#
#         self.errorLabel = QLabel()
#         self.errorLabel.setSizePolicy(QSizePolicy.Preferred,
#                                       QSizePolicy.Maximum)
#
#         #create Open Action
#         openAction = QAction(QIcon('open.png'), '&Open', self)
#         openAction.setShortcut('Ctrl+O')
#         openAction.setStatusTip('Open Video')
#         openAction.triggered.connect(self.openFile)
#
#         #create Exit Action
#         exitAction = QAction(QIcon('exit.png'), '&Exit', self)
#         exitAction.setShortcut('Ctrl+Q')
#         exitAction.setStatusTip('Exit Application')
#         exitAction.triggered.connect(self.exitCall)
#
#         #create menu bar and add actions
#         menuBar = self.menuBar()
#         fileMenu = menuBar.addMenu('&File')
#         fileMenu.addAction(openAction)
#         fileMenu.addAction(exitAction)
#
#         #create a widget for window contents
#         widcontent = QWidget(self)
#         self.setCentralWidget(widcontent)
#
#         #create layout and add to widget
#         controlLayout = QHBoxLayout()
#         controlLayout.setContentsMargins(0,0,0,0)
#         controlLayout.addWidget(self.playButton)
#         controlLayout.addWidget(self.positionSlider)
#
#         layout = QVBoxLayout()
#         layout.addWidget(videoWidget)
#         layout.addLayout(controlLayout)
#         layout.addWidget(self.errorLabel)
#
#         #set widget to contain window contents
#         widcontent.setLayout(layout)
#
#         self.mediaPlayer.setVideoOutput(videoWidget)
#         self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
#         self.mediaPlayer.positionChanged.connect(self.positionChanged)
#         self.mediaPlayer.durationChanged.connect(self.durationChanged)
#         self.mediaPlayer.error.connect(self.handleError)
#
#     def mediaStateChanged(self, state):
#         if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
#             self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
#         else:
#             self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
#
#     def positionChanged(self, position):
#         self.positionSlider.setValue(position)
#
#     def durationChanged(self, duration):
#         self.positionSlider.setRange(0, duration)
#
#     def handleError(self):
#         self.playButton.setEnabled(False)
#         self.errorLabel.setText("Error : " + self.mediaPlayer.errorString())
#
#     def openFile(self):
#         fileName, _ = QFileDialog.getOpenFileName(self, 'Open Video', QDir.homePath())
#
#         if fileName != '':
#             self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
#             self.playButton.setEnabled(True)
#
#     def exitCall(self):
#         sys.exit(app.exec_())
#
#     def play(self):
#         if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
#             self.mediaPlayer.pause()
#         else:
#             self.mediaPlayer.play()
#
#     def setPosition(self, position):
#         self.mediaPlayer.setPosition(position)
#
#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     player = VideoWindow()
#     player.resize(1500, 1500)
#     player.show()
#     sys.exit(app.exec_())
