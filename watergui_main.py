import sys
import threading
import time
import socket
import numpy as np
import cv2
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt
from datetime import datetime

import camera_settings
from camera_settings import Ui_Window
import cam
from gui import Ui_MainWindow  # 导入从 .ui 文件生成的类
from cam import *
#这样可以直接调用cam.py中的函数并实体化类
class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self.setupUi(self)  # 设置UI
        self.rec_flag = False
        #实体化相机类
        #self.camera=cam.camera()
        self.frame1 = None
        self.frame2 = None
        self.frame3 = None
        self.frame4 = None
        self.frame5 = None
        # self.frame6=None
        # 连接按钮等控件的信号与槽

        self.connect_button.clicked.connect(self.start_stop_camera)
        self.capture_button.clicked.connect(self.capture)
        self.camera_setting_button.clicked.connect(self.camera_setting)
        self.recording_button.clicked.connect(self.recording)
        # ... 其他控件的信号槽连接 ...
        self.timer = QTimer(self)#计时器，用来控制update_frame的循环调用的频率，在start_camera函数中启动这个计时器，这里只做初始化
        self.timer.timeout.connect(self.update_frame)


    def camera_setting(self):
        # 判断对象是否有包含的属性，判断是否出现'camera_settings_window'
        if not hasattr(self, 'camera_settings_window'):
            self.camera_settings_window = Ui_Window()
            self.camera_settings_window.setupUi(self.camera_settings_window)
            self.camera_settings_window.pushButton.clicked.connect(self.setting)
        self.camera_settings_window.show()
    #停止计时器，即停止视频显示
    def setting(self):
        print("子菜单")
    #     添加相机设置的具体功能

    #更新帧的函数，真实情况这里需要调用相机函数获取当前帧，这个函数里现在六个图像都是一样的，实际需要处理
    def update_frame(self):
        #这里的frame可以设置为相机的原始数据，如果需要保存当前数据的功能，可以调用self.frame1/frame2...来访问
        ret, self.frame1 = self.cap.read()

        if self.frame1 is not None:
            self.frame1 = cv2.cvtColor(self.frame1, cv2.COLOR_BGR2GRAY)
            self.frame2 = self.frame1
            self.frame3 = self.frame1
            self.frame4 = self.frame1
            self.frame5 = self.frame1
            # self.frame6 = self.frame1
            #如果现在的状态是正在录像，就把当前更新的帧写入文件中去
            if self.rec_flag:
                self.video_writer.write(self.frame1)
            self.display()#更新完帧后调用显示函数

    #把帧转换成Qt能使用的格式并显示
    def display(self):
        h, w = self.frame1.shape
        bytes_per_line = w
        q_img1 = QImage(self.frame1.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        q_img2 = QImage(self.frame2.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        q_img3 = QImage(self.frame3.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        q_img4 = QImage(self.frame4.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        q_img5 = QImage(self.frame5.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        # q_img6 = QImage(self.frame6.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        pixmap1 = QPixmap.fromImage(q_img1)
        scaled_pixmap1 = pixmap1.scaled(self.visible.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.visible.setPixmap(scaled_pixmap1)
        pixmap2 = QPixmap.fromImage(q_img2)
        scaled_pixmap2 = pixmap2.scaled(self.function1.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.function1.setPixmap(scaled_pixmap2)
        pixmap3 = QPixmap.fromImage(q_img3)
        scaled_pixmap3 = pixmap3.scaled(self.function2.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.function2.setPixmap(scaled_pixmap3)
        pixmap4 = QPixmap.fromImage(q_img4)
        scaled_pixmap4 = pixmap4.scaled(self.function3.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.function3.setPixmap(scaled_pixmap4)
        pixmap5 = QPixmap.fromImage(q_img5)
        scaled_pixmap5 = pixmap5.scaled(self.function4.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.function4.setPixmap(scaled_pixmap5)
        # pixmap6 = QPixmap.fromImage(q_img6)
        # scaled_pixmap6 = pixmap6.scaled(self.l6.size(), Qt.AspectRatioMode.KeepAspectRatio)
        # self.l6.setPixmap(scaled_pixmap6)
    #如果录像flag为False，则开始录像，初始化输出的

    def start_stop_camera(self):
        if self.connect_button.text() == '连接相机':
            self.start_camera()
        else:
            self.stop_camera()
    def start_camera(self):
        self.cap = cv2.VideoCapture(1)#连接到摄像头1
        #self.cap = cv2.VideoCapture("1.1.mp4")#测试用视频
        self.timer.start(30)
        print("start cam.py")
        text_start = "相机已连接"
        self.feedback_information.append(text_start)
        self.connect_button.setText('停止相机')
        # 启动相机的逻辑
        #self.cam.py.start_camera()
        # 更新UI或其他操作
    def stop_camera(self):
        self.timer.stop()
        text_start = "相机已停止"
        self.feedback_information.append(text_start)
        self.connect_button.setText('连接相机')
    # 定义其他方法，例如更新UI显示视频流等

    def capture(self):
        #只演示了frame1

        if self.frame1 is not None:
            current_time = datetime.now()
            file_name = current_time.strftime("%H%M%S") + ".jpg"
            cv2.imwrite(file_name, self.frame1)
        print("capture")
        text_start = "图片已保存"
        self.feedback_information.append(text_start)
    #启动计时器，开始显示

    def recording(self):
        if self.recording_button.text() == '开始录制':
            self.recording_start()
        else:
            self.recording_stop()
    def recording_start(self):
        if not self.rec_flag:
            self.rec_flag = True
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            fps = 20.0
            frame_size = (self.frame1.shape[1], self.frame1.shape[0])
            self.video_writer = cv2.VideoWriter('output.avi', fourcc, fps, frame_size, False)
            print("Started Recording")
            text_start = "开始录制"
            self.feedback_information.append(text_start)
            self.recording_button.setText('停止录制')
    def recording_stop(self):
        self.rec_flag = False
        if self.video_writer:
            self.video_writer.release()
        print("Stopped Recording")
        text_start = "结束录制"
        self.feedback_information.append(text_start)
        self.recording_button.setText('开始录制')



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())
