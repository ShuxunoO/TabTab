# tabtab/keyboard_listener.py
"""全局键盘监听器，负责捕获键盘事件。

该模块使用pynput库实现全局键盘事件监听，
将键盘事件转换为Qt信号传递给主线程处理。
"""

from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from typing import Callable, Optional


class KeyboardListener(QObject):
    """全局键盘监听器，在独立线程中监听键盘事件。
    
    为了避免pynput阻塞主GUI线程，该监听器在一个单独的QThread中运行。
    它通过发出keyPressed信号，将键盘事件安全地传递给主线程进行处理。
    """
    
    # 信号：键盘按下事件
    key_pressed = pyqtSignal(object)
    # 信号：键盘释放事件
    key_released = pyqtSignal(object)
    # 信号：请求阻止键盘事件
    suppress_key = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        """初始化键盘监听器。
        
        Args:
            parent: 父对象
        """
        super().__init__(parent)
        self.listener: Optional[keyboard.Listener] = None
        self.is_listening = False
        self.should_suppress = False
    
    def start_listening(self):
        """启动键盘监听。"""
        if self.is_listening:
            return
            
        try:
            self.listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.listener.start()
            self.is_listening = True
            print("Keyboard listener started")
        except Exception as e:
            print(f"Failed to start keyboard listener: {e}")
    
    def stop_listening(self):
        """停止键盘监听。"""
        if self.listener and self.is_listening:
            self.listener.stop()
            self.is_listening = False
            print("Keyboard listener stopped")
    def on_key_press(self, key):
        """键盘按下事件回调。
        
        此方法在pynput的监听线程中被调用，它通过信号将事件传递给主线程。
        
        Args:
            key: 按下的键
            
        Returns:
            如果应该阻止事件传播则返回False，否则返回None
        """
        try:
            self.key_pressed.emit(key)
            # 检查是否需要阻止事件传播
            if self.should_suppress:
                self.should_suppress = False  # 重置标志
                return False  # 阻止事件传播
            return None  # 允许事件传播
        except Exception as e:
            print(f"Error in key press handler: {e}")
            return None
    
    def set_suppress_next_key(self, suppress: bool):
        """设置是否阻止下一个键盘事件的传播。
        
        Args:
            suppress: 是否阻止
        """
        self.should_suppress = suppress
    
    def on_key_release(self, key):
        """键盘释放事件回调。
        
        Args:
            key: 释放的键
        """
        try:
            self.key_released.emit(key)
        except Exception as e:
            print(f"Error in key release handler: {e}")


class KeyboardListenerThread(QThread):
    """键盘监听器线程，管理KeyboardListener的生命周期。"""
    
    # 信号
    key_pressed = pyqtSignal(object)
    key_released = pyqtSignal(object)
    
    def __init__(self, parent=None):
        """初始化监听器线程。"""
        super().__init__(parent)
        self.listener = KeyboardListener()
        
        # 连接信号
        self.listener.key_pressed.connect(self.key_pressed.emit)
        self.listener.key_released.connect(self.key_released.emit)
        
        # 将监听器移动到当前线程
        self.listener.moveToThread(self)
    def run(self):
        """线程运行方法。"""
        self.listener.start_listening()
        self.exec()  # 启动事件循环
    
    def stop_listening(self):
        """停止监听并退出线程。"""
        self.listener.stop_listening()
        self.quit()
        self.wait()
    
    def set_key_handler(self, handler: Callable):
        """设置按键处理函数。
        
        Args:
            handler: 按键处理函数，返回True表示阻止按键，False表示允许传播
        """
        self.listener.set_key_handler(handler)


def is_printable_char(key) -> bool:
    """判断按键是否为可打印字符。
    
    Args:
        key: 按键对象
        
    Returns:
        如果是可打印字符则返回True
    """
    try:
        return hasattr(key, 'char') and key.char and key.char.isprintable()
    except:
        return False


def is_alpha_char(key) -> bool:
    """判断按键是否为字母字符。
    
    Args:
        key: 按键对象
        
    Returns:
        如果是字母字符则返回True
    """
    try:
        return hasattr(key, 'char') and key.char and key.char.isalpha()
    except:
        return False


def is_digit_char(key) -> bool:
    """判断按键是否为数字字符。
    
    Args:
        key: 按键对象
        
    Returns:
        如果是数字字符则返回True
    """
    try:
        # 处理 pynput.keyboard.KeyCode
        if hasattr(key, 'char') and key.char and key.char.isdigit():
            return True
        # 处理 pynput.keyboard.Key (例如 numpad 数字)
        if hasattr(key, 'name') and key.name and key.name.startswith('num_'):
            return key.name.split('_')[1].isdigit()
        # 兼容 vk
        if hasattr(key, 'vk') and 48 <= key.vk <= 57: # 主键盘数字 0-9
            return True
        if hasattr(key, 'vk') and 96 <= key.vk <= 105: # 小键盘数字 0-9
            return True
        return False
    except:
        return False


def get_key_char(key) -> str:
    """获取按键对应的字符。
    
    Args:
        key: 按键对象
        
    Returns:
        按键对应的字符，如果无法获取则返回空字符串
    """
    try:
        if hasattr(key, 'char') and key.char:
            return key.char
        # 兼容 vk for numpad
        if hasattr(key, 'vk') and 96 <= key.vk <= 105:
            return str(key.vk - 96)
        # 兼容 vk for main keyboard
        if hasattr(key, 'vk') and 48 <= key.vk <= 57:
            return str(key.vk - 48)
    except:
        pass
    return ""


if __name__ == '__main__':
    # 测试键盘监听器
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    def on_key_press(key):
        print(f"Key pressed: {key}")
        if hasattr(key, 'char'):
            print(f"Character: {key.char}")
    
    def on_key_release(key):
        print(f"Key released: {key}")
    
    # 创建监听器线程
    listener_thread = KeyboardListenerThread()
    listener_thread.key_pressed.connect(on_key_press)
    listener_thread.key_released.connect(on_key_release)
    
    # 启动监听
    listener_thread.start()
    
    try:
        app.exec()
    finally:
        listener_thread.stop_listening()
