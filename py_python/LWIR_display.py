# function:调用dll来显示相机画面
import ctypes
import threading
import numpy as np
import cv2
import time
def start_stream():
    dll.start_stream()

# 加载 DLL
dll = ctypes.CDLL('E:/vscode_c++_project/dll_new/libudp_dll.dll', winmode=0)

# 定义返回类型
dll.getImageBufferAddress.argtypes = []  # 无参数
dll.getImageBufferAddress.restype = ctypes.POINTER(ctypes.c_ubyte) 

# 启动视频流线程
t = threading.Thread(target=start_stream)
t.start()
time.sleep(1)
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
    cv2.waitKey(3)  # 等待按键然后关闭窗口
cv2.destroyAllWindows()