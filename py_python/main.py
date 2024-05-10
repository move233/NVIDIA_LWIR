import ctypes
import threading
import numpy as np
import cv2
import datetime
import serial
import serial.tools.list_ports
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget,QFileDialog
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer,pyqtSignal, QThread
from LWIR_NVIDIAui import Ui_LWIR
import sys
import time
import os

# ******初始定义******
# 启用高 DPI 支持
QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
# 加载 DLL
frame_size = 640 * 512 * 2
dll = ctypes.WinDLL('E:/vscode_c++_project/nvidia_LWIR/py_python/libudp_dll.dll', winmode=0)
# 定义返回类型
dll.UDP_INIT.argtypes = [ctypes.c_int]
dll.UDP_INIT.restype = None
dll.START_UPDATE_FRAME_THREAD.argtypes = []
dll.START_UPDATE_FRAME_THREAD.restype = None
dll.STOP_UPDATE_FRAME_THREAD.argtypes = []
dll.STOP_UPDATE_FRAME_THREAD.restype = None
dll.GET_CURRENT_FRAME.argtypes = []
dll.GET_CURRENT_FRAME.restype = ctypes.POINTER(ctypes.c_char)

# 定义目标检测函数
def RX(img0,img90):
    Data_re = np.stack((img0, img90), axis=2)
    nHeight_re, nWidth_re, _ = Data_re.shape
    Data_re1 = Data_re.reshape(nWidth_re*nHeight_re, 2).T
    X_mean = np.mean(Data_re1, axis=1, keepdims=True)
    X = Data_re1 - X_mean
    Sigma = np.dot(X, X.T) / X.shape[1]

    # 添加微小的扰动值以防止奇异矩阵错误
    epsilon = 1e-6
    Sigma += np.eye(Sigma.shape[0]) * epsilon

    Sigma_inv = np.linalg.inv(Sigma)

    D = np.zeros(X.shape[1])
    for m in range(X.shape[1]):
        D[m] = np.dot(np.dot(X[:, m].T, Sigma_inv), X[:, m])

    img_re = D.reshape(nHeight_re, nWidth_re)
    min_val = np.min(img_re)
    max_val = np.max(img_re)

    # 转换为8位来显示
    img_re1 = ((img_re - min_val) / (max_val - min_val) * 255).astype(np.uint8)
    return img_re1


# ******图像采集线程子类******
class DownloadThread(QThread):
    update_signal = pyqtSignal(str)
    done_signal = pyqtSignal()
    send_signal=pyqtSignal(str)
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.lock = threading.Lock()
        
    def run(self):
        if self.main_app.angle_flag == 1:
            send_data = '0sj00008C00\r'
            self.main_app.angle_N = 3
        elif self.main_app.angle_flag == 2:
            send_data = '0sj00005D55\r'
            self.main_app.angle_N = 4
        elif self.main_app.angle_flag == 3:
            send_data = '0sj00004600\r'
            self.main_app.angle_N = 5
        elif self.main_app.angle_flag == 4:
            send_data = '0sj00002EAB\r'
            self.main_app.angle_N = 7
        elif self.main_app.angle_flag == 5:
            send_data = '0sj000007C7\r'
            self.main_app.angle_N = 37

        # 创建文件夹
        current_time = datetime.datetime.now().strftime('%Y-%m-%d-%H_%M_%S')
        folder_name = f"{self.main_app.angle_flag}_{current_time}/"
        os.makedirs(self.main_app.folder_path + '/' + folder_name)
        text_folder = f"文件夹 {folder_name} 创建成功"
        self.update_signal.emit(text_folder)

        # 电机切换回到零位
        self.send_signal.emit(send_data)
        time.sleep(2)
        self.send_signal.emit('0ma00000000\r')
        time.sleep(1)
        self.main_app.capture_running=False
        with self.lock:
            if self.main_app.frame_base is not None:
                save_path = os.path.join(self.main_app.folder_path, folder_name, '1.bmp')
                cv2.imwrite(save_path, self.main_app.frame_base)

        n = 2
        while n <= self.main_app.angle_N:
            time.sleep(1)
            self.send_signal.emit('0fw\r')
            with self.lock:
                if self.main_app.frame_base is not None:
                    save_path = os.path.join(self.main_app.folder_path, folder_name, str(n) + '.bmp')
                    cv2.imwrite(save_path, self.main_app.frame_base)
            n += 1

        if n == self.main_app.angle_N + 1:
            self.send_signal.emit('0ma00000000\r')
            self.update_signal.emit("采集完成")


# ******目标检测程子类******
class DetectThread(QThread):
    update_signal = pyqtSignal(str)
    done_signal = pyqtSignal()
    send_signal=pyqtSignal(str)
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.lock = threading.Lock()
    
    def run(self):
        while self.main_app.detect_running:
            self.send_signal.emit('0ma00000000\r')
            time.sleep(0.5)
            I90 = self.main_app.frame_base
            self.send_signal.emit('0sj00008C00\r')

            while True:
                self.send_signal.emit('0fw\r')
                time.sleep(0.5)
                I0 = I90
                I90 = self.main_app.frame_base
                self.main_app.frame_function = RX(I0, I90)
                self.main_app.display()
                self.update_signal.emit("检测成功")
                time.sleep(1)

                self.send_signal.emit('0bw\r')
                time.sleep(0.5)
                I0 = I90
                I90 = self.main_app.frame_base
                self.main_app.frame_function = RX(I0, I90)
                self.main_app.display()
                self.update_signal.emit("检测成功")
                time.sleep(1)

                if not self.main_app.detect_running:
                    break
        self.update_signal.emit("检测已停止")

# ******主窗口类******
class MainWindow(QMainWindow,Ui_LWIR):
    # 初始化
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setupUi(self)
        # 视频显示区域
        self.detect_flag=0
        self.frame_base = None
        self.frame_function = None
        self.display()
        # 状态返回区域设置为只读不允许编辑
        self.feedback_information.setReadOnly(True)
        # 连接按钮等控件的信号与槽
        self.connect_button.clicked.connect(self.stream)
        self.detection_button.clicked.connect(self.detect)
        self.stopdet_button.clicked.connect(self.stopdetection)
        self.path_file.clicked.connect(self.pathfile)
        self.angle_display.currentIndexChanged.connect(self.angle_status)
        self.download_button.clicked.connect(self.download_capture)
        self.openserial_button.clicked.connect(self.port_open_recv)
        # 初始化串口实例
        self.ser=serial.Serial()
        # 初始化全局变量
        self.detect_running = False
        self.streaming = False
        self.capture_running = False
        self.stream_thread = None
        self.angle_flag=None
        self.angle_N=None
        self.folder_path = None
        # 计时器(相机视频流)
        self.timer_stream = QTimer(self)
        self.timer_stream.timeout.connect(self.stream_and_update)
    
    # 串口
    def showEvent(self, event):
        self.populate_ports()
        super().showEvent(event)

    def populate_ports(self):
        self.serial_display.clear()  # 清空现有选项
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.serial_display.addItem(port.device)

    def port_open_recv(self):
        selected_port = self.serial_display.currentText()
        if selected_port:
            try:
                self.ser.port = selected_port
                self.ser.baudrate = 9600  # 根据需要调整波特率
                self.ser.bytesize = 8
                self.ser.stopbits = 1
                self.ser.parity = 'N'
                self.ser.open()
                self.feedback_information.append(f"已连接到 {selected_port}。")
            except Exception as e:
                self.feedback_information.append(f"连接到 {selected_port} 时出错：{e}")
        else:
            self.feedback_information.append("未选择串口或无可用串口。")
    
    def send(self,send_data):
        if self.ser.isOpen():
            self.ser.write(send_data.encode('utf-8'))
            text_serial = send_data + "发送成功"
            self.feedback_information.append(text_serial)
        else:
            text_serial = "发送失败！串口未打开"
            self.feedback_information.append(text_serial)

    # 界面显示（相机视频+检测画）
    def display(self):
        if self.frame_base is not None:
            img_base = QImage(self.frame_base.data, 640, 512, 640, QImage.Format.Format_Grayscale8)
            pixmap_base = QPixmap.fromImage(img_base)
            self.video_base.setPixmap(pixmap_base)
            
        if self.frame_function is not None:
            img_function = QImage(self.frame_function.data, 640, 512, 640, QImage.Format.Format_Grayscale8)
            pixmap_function = QPixmap.fromImage(img_function)
            self.video_function.setPixmap(pixmap_function)
    
    # 相机视频流
    def stream(self):
        if self.connect_button.text() == '打开相机':
            if not self.streaming:
                self.streaming = True
                dll.UDP_INIT(32345)
                dll.START_UPDATE_FRAME_THREAD()
                self.timer_stream.start(3)
                text_start = "相机已连接"
                self.feedback_information.append(text_start)
                self.connect_button.setText('关闭相机')
        else:
            dll.STOP_UPDATE_FRAME_THREAD()
            self.streaming=False
            self.timer_stream.stop()
            text_start = "相机已关闭"
            self.feedback_information.append(text_start)
            self.connect_button.setText('打开相机')

    def stream_and_update(self):
        frame_ptr = dll.GET_CURRENT_FRAME()
        frame_data = ctypes.string_at(frame_ptr, frame_size)
        self.frame_base = np.frombuffer(frame_data, dtype=np.uint16).reshape((512, 640))
        normalized_frame = cv2.normalize(self.frame_base, None, 0, 255, cv2.NORM_MINMAX)
        # 将 8 位图像转换为 uint8 类型，以便显示
        self.frame_base = np.uint8(normalized_frame)
        self.display()
    # 检测
    def star_detection(self):
        if not self.detect_running:
            self.detect_running = True
            self.detect_thread = DetectThread(self)
            self.detect_thread.send_signal.connect(self.send)
            self.detect_thread.update_signal.connect(self.feedback_information.append)
            self.detect_thread.start()
    def detection_loop(self):
        while self.detect_flag:
            self.send('0ma00000000\r')
            time.sleep(0.5)
            I90 = self.frame_base
            self.send('0sj00008C00\r')

            while True:
                self.send('0fw\r')
                time.sleep(0.5)
                I0 = I90
                I90 = self.frame_base
                self.frame_function = RX(I0, I90)
                self.display()
                self.feedback_information.append("检测成功")
                time.sleep(1)

                self.send('0bw\r')
                time.sleep(0.5)
                I0 = I90
                I90 = self.frame_base
                self.frame_function = RX(I0, I90)
                self.display()
                self.feedback_information.append("检测成功")
                time.sleep(1)

                if not self.detect_flag:
                    break
        self.feedback_information.append("检测已停止")

    def stopdetection(self):
        self.detect_running = False
    
    def reset_detect_flag(self):
        self.detect_running_running = False

    def detect(self):
        if not self.detect_running:
            self.detect_running = True
            self.detect_thread = DetectThread(self)
            self.detect_thread.send_signal.connect(self.send)
            self.detect_thread.done_signal.connect(self.reset_detect_flag)
            self.detect_thread.update_signal.connect(self.feedback_information.append)
            self.detect_thread.start()

    # 保存
    def reset_capture_flag(self):
        self.capture_running = False

    def pathfile(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "/")
        if self.folder_path:
            self.path_display.setText(self.folder_path)

    def angle_status(self,index):
        self.angle_flag = index#记录下当前索引，以便于采集时驱动电机用
        text_download = "当前偏振通道："+ str(index)+"  "+self.angle_display.currentText()
        self.feedback_information.append(text_download)

    def download_capture(self):
        if not self.capture_running:
            self.capture_running = True
            self.download_thread = DownloadThread(self)
            self.download_thread.send_signal.connect(self.send)
            self.download_thread.done_signal.connect(self.reset_capture_flag)
            self.download_thread.update_signal.connect(self.feedback_information.append)
            self.download_thread.start()

if __name__=="__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())