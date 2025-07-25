# tabtab/main.py
"""TabTab输入法应用程序的主入口点。

该文件负责初始化PyQt应用程序，设置环境（如DPI），
创建并连接输入法核心组件，并启动事件循环。
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, Qt

from input_manager import InputManager
from candidate_window import CandidateWindow

# 解决Windows上的DPI感知问题
if sys.platform == "win32":
    # 设置DPI感知级别为系统感知，以避免在高分屏下的权限问题
    os.environ["QT_WINDOWS_DPI_AWARENESS"] = "1" # System Aware

def main():
    """应用程序的主函数。

    执行以下操作:
    1. 创建QApplication实例。
    2. 创建候选词窗口(CandidateWindow)和输入管理器(InputManager)。
    3. 将InputManager的父对象设置为app，以进行自动内存管理。
    4. 启动应用程序事件循环。
    5. 在程序退出时，确保所有资源被正确释放。
    """
    app = QApplication(sys.argv)
    
    candidate_window = CandidateWindow()
    input_manager = InputManager(candidate_window, parent=app)
    
    exit_code = app.exec()
    
    input_manager.stop()
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
