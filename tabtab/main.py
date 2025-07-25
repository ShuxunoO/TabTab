# tabtab/main.py
"""TabTab输入法应用程序的主入口点。

该文件负责初始化PyQt应用程序，设置环境，
创建并启动输入法核心组件。
"""

import sys
import os
import signal
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QAction

from input_manager import InputManager


class TabTabApplication:
    """TabTab输入法应用程序类。"""
    
    def __init__(self):
        """初始化应用程序。"""
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # 防止关闭窗口时退出应用
        
        # 设置应用程序信息
        self.app.setApplicationName("TabTab输入法")
        self.app.setApplicationVersion("1.0.0")
        
        # 输入管理器
        self.input_manager = InputManager()
        
        # 系统托盘
        self.setup_system_tray()
        
        # 设置信号处理
        self.setup_signal_handlers()
    
    def setup_system_tray(self):
        """设置系统托盘图标和菜单。"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available on this system.")
            return
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self.app)
        
        # 设置托盘图标（使用默认图标）
        self.tray_icon.setIcon(self.app.style().standardIcon(
            self.app.style().StandardPixmap.SP_ComputerIcon
        ))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 启动/停止动作
        self.start_action = QAction("启动输入法", self.app)
        self.start_action.triggered.connect(self.start_input_method)
        tray_menu.addAction(self.start_action)
        
        self.stop_action = QAction("停止输入法", self.app)
        self.stop_action.triggered.connect(self.stop_input_method)
        self.stop_action.setEnabled(False)
        tray_menu.addAction(self.stop_action)
        
        tray_menu.addSeparator()
        
        # 退出动作
        quit_action = QAction("退出", self.app)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 设置托盘提示
        self.tray_icon.setToolTip("TabTab输入法")
        
        # 显示托盘图标
        self.tray_icon.show()
        
        # 连接托盘图标点击事件
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
    
    def setup_signal_handlers(self):
        """设置信号处理器。"""
        # 处理Ctrl+C信号
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # 定期检查信号的定时器
        self.signal_timer = QTimer()
        self.signal_timer.timeout.connect(lambda: None)  # 允许处理信号
        self.signal_timer.start(100)  # 每100ms检查一次
    
    def signal_handler(self, signum, frame):
        """处理系统信号。"""
        print(f"\nReceived signal {signum}, quitting...")
        self.quit_application()
    
    def start_input_method(self):
        """启动输入法。"""
        try:
            self.input_manager.start()
            self.start_action.setEnabled(False)
            self.stop_action.setEnabled(True)
            self.tray_icon.showMessage(
                "TabTab输入法",
                "输入法已启动",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            print("TabTab输入法已启动")
        except Exception as e:
            print(f"启动输入法失败: {e}")
            self.tray_icon.showMessage(
                "TabTab输入法",
                f"启动失败: {e}",
                QSystemTrayIcon.MessageIcon.Critical,
                3000
            )
    
    def stop_input_method(self):
        """停止输入法。"""
        try:
            self.input_manager.stop()
            self.start_action.setEnabled(True)
            self.stop_action.setEnabled(False)
            self.tray_icon.showMessage(
                "TabTab输入法",
                "输入法已停止",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            print("TabTab输入法已停止")
        except Exception as e:
            print(f"停止输入法失败: {e}")
    
    def on_tray_icon_activated(self, reason):
        """处理托盘图标激活事件。"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # 双击切换输入法状态
            if self.start_action.isEnabled():
                self.start_input_method()
            else:
                self.stop_input_method()
    
    def quit_application(self):
        """退出应用程序。"""
        try:
            self.stop_input_method()
        except:
            pass
        
        self.tray_icon.hide()
        self.app.quit()
    
    def run(self):
        """运行应用程序。"""
        print("TabTab输入法启动中...")
        print("双击系统托盘图标可以启动/停止输入法")
        print("按Ctrl+C退出程序")
        
        # 自动启动输入法
        QTimer.singleShot(1000, self.start_input_method)
        
        return self.app.exec()


def main():
    """主函数。"""
    # 设置Windows DPI感知（如果是Windows系统）
    if sys.platform == "win32":
        try:
            # 尝试设置DPI感知
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    # 创建并运行应用程序
    app = TabTabApplication()
    return app.run()


if __name__ == '__main__':
    sys.exit(main())
