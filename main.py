# 界面显示与各个功能调用
# version：功能调用
import ctypes
import threading
import numpy as np
import cv2
import time
import serial


# 定义串口
ser = serial.Serial()
def port_open_recv():#对串口的参数进行配置
    ser.port = 'COM8'
    ser.baudrate=9600
    ser.bytesize=8
    ser.stopbits=1
    ser.parity="N"#奇偶校验位
    ser.open()
    if(ser.isOpen()):
        print("串口打开成功！")
    else:
        print("串口打开失败！")

# 加载 DLL
dll = ctypes.CDLL('E:/vscode_c++_project/dll_new/source/dll_c/build/camera.dll', winmode=0)

# 定义返回类型
dll.getImageBufferAddress.argtypes = []  # 无参数
dll.getImageBufferAddress.restype = ctypes.POINTER(ctypes.c_ubyte) 

# 启动视频流线程
dll.start_stream()
time.sleep(3)
buffer_size = 640*512
# 获取图像缓冲区地址
buffer_address = dll.getImageBufferAddress()
buffer = (ctypes.c_uint16 * buffer_size).from_address(ctypes.addressof(buffer_address.contents))
image = np.frombuffer(buffer, dtype=np.uint16).reshape((512, 640)) 
# 使用 NumPy 创建数组视图
while True:
    min_val = np.min(image)
    max_val = np.max(image)
    image_normalized = ((image - min_val) / (max_val - min_val) * 255).astype(np.uint8)
    cv2.imshow('Normalized Image', image_normalized)


# 串口电机驱动
def port_close():
    ser.close()
    if(ser.isOpen()):
        print("串口关闭失败！")
    else:
        print("串口关闭成功！")

def send(send_data):
    if(ser.isOpen()):
        ser.write(send_data.encode('utf-8'))#编码
        print("发送成功",send_data)
    else:
        print("发送失败！")

while True:
    send('0ma00000000\r\n')
    sleep(0.3)
    # 此处为图像返回至图像处理dll
    print("0°图像已采集")

    sleep(0.7)

    send('0mr00008C00\r\n')
    sleep(0.3)
    # 此处为图像返回至图像处理dll
    print("90°图像已采集")
    sleep(0.7)

cv2.destroyAllWindows()
dll.stop_stream()
print("关闭相机")