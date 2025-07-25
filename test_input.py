#!/usr/bin/env python3
"""测试输入法功能的脚本"""

import sys
import os

# 添加tabtab模块到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tabtab'))

from PyQt6.QtWidgets import QApplication
from tabtab.input_manager import InputManager

def main():
    """主函数"""
    print("=" * 50)
    print("TabTab 输入法测试")
    print("=" * 50)
    print("测试说明：")
    print("1. 输入字母进行拼音输入")
    print("2. 按数字键(1-9)选择候选词")
    print("3. 按Tab键确认第一个候选词")
    print("4. 按空格键确认第一个候选词")
    print("5. 按ESC键取消输入")
    print("6. 按Ctrl+C退出程序")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    input_manager = InputManager()
    
    try:
        input_manager.start()
        print("输入法已启动，请在任意文本框中测试...")
        app.exec()
    except KeyboardInterrupt:
        print("\n收到退出信号，正在停止...")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        input_manager.stop()
        print("输入法已停止")

if __name__ == '__main__':
    main()
