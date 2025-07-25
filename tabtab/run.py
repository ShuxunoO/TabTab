# tabtab/run.py
"""简化的TabTab输入法启动脚本。

用于快速启动和测试输入法功能。
"""

import sys
from PyQt6.QtWidgets import QApplication
from input_manager import InputManager


def main():
    """主函数。"""
    print("=== TabTab输入法 ===")
    print("启动中...")
    
    app = QApplication(sys.argv)
    app.setApplicationName("TabTab输入法")
    
    # 创建输入管理器
    input_manager = InputManager()
    
    try:
        # 启动输入法
        input_manager.start()
        
        print("\n输入法已启动！")
        print("使用说明：")
        print("1. 输入拼音字母，会显示候选词窗口")
        print("2. 按数字键1-9选择候选词")
        print("3. 按Tab键或空格键选择第一个候选词")
        print("4. 按ESC键取消输入")
        print("5. 按Ctrl+C退出程序")
        print("\n开始输入拼音试试吧！")
        
        # 运行应用程序
        app.exec()
        
    except KeyboardInterrupt:
        print("\n收到退出信号...")
    except Exception as e:
        print(f"运行出错: {e}")
    finally:
        input_manager.stop()
        print("输入法已停止。")


if __name__ == '__main__':
    main()
