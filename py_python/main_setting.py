from capture_setting import Ui_capture_setting
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog
import sys

class MainApp(QMainWindow, Ui_capture_setting):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 设置UI
        self.pathfile.clicked.connect(self.capture_pathfile)
        self.angle.currentIndexChanged.connect(self.angle_status)
        self.capture.clicked.connect(self.captur)

    def capture_pathfile(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹", "/")
        if folder_path:
            self.filedisplay.setText(folder_path)

    def angle_status(self,index):
        print("当前选中项的索引:", index)#所引述徐是按照界面设计从0开始编号的
        print("当前选中项的文本:", self.angle.currentText())
    
    def capture(self):

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())