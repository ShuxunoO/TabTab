# tabtab/ai_client.py
import ollama
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class AIWorker(QObject):
    """在独立线程中运行的AI工作类，用于处理耗时的AI模型调用。

    该类继承自QObject，以便可以移动到QThread中。它负责与Ollama服务通信，
    获取文本补全建议，并通过信号将结果发送回主线程，避免阻塞GUI。
    """
    response_ready = pyqtSignal(str)

    def __init__(self, model='qwen2.5:0.5b', parent=None):
        """AIWorker的构造函数。

        Args:
            model (str, optional): 要使用的AI模型名称。默认为'qwen2.5:0.5b'。
            parent (QObject, optional): 父对象。默认为None。
        """
        super().__init__(parent)
        self.client = ollama.Client()
        self.model = model

    def get_completion(self, text):
        """获取AI文本补全。

        调用Ollama API，发送当前文本作为上下文，并请求补全。
        请求完成后，通过response_ready信号发出结果。

        Args:
            text (str): 需要补全的上下文文本。
        """
        print(f"用户输入: {text}")
        try:
            # 使用用户提供的示例作为基础，构建一个通用的补全请求
            response = self.client.chat(model=self.model, messages=[
                {
                    'role': 'user',
                    'content': f"直接继续下面的文本，不要提供任何解释或多余的文字，只返回补全的内容，要求少于50字：{text}",
                },
            ])
            completion = response.get("message", {}).get("content", "")
            print(f"Ai 补全: {completion}")
            self.response_ready.emit(completion.strip())
        except Exception as e:
            print(f"Error calling AI service: {e}")
            self.response_ready.emit("")

class AIClient(QObject):
    """AI服务客户端，负责管理AIWorker和线程。

    这个类封装了与AI服务交互的逻辑，包括线程管理和信号连接。
    它提供了一个简单的接口来异步请求文本补全。
    """
    completion_requested = pyqtSignal(str)
    
    def __init__(self, model='qwen2.5:0.5b', parent=None):
        """AIClient的构造函数。

        Args:
            model (str, optional): 要使用的AI模型名称。默认为'qwen2.5:0.5b'。
            parent (QObject, optional): 父对象。默认为None。
        """
        super().__init__(parent)
        self.thread = QThread(self)
        self.worker = AIWorker(model)
        self.worker.moveToThread(self.thread)

        self.completion_requested.connect(self.worker.get_completion)
        
        self.thread.start()
        print("AIClient initialized and thread started.")

    def request_completion(self, text):
        """异步请求文本补全。

        发出completion_requested信号，由连接到该信号的AIWorker在子线程中处理。

        Args:
            text (str): 需要补全的上下文文本。
        """
        self.completion_requested.emit(text)

    def stop(self):
        """停止AI客户端和其工作线程。
        
        安全地退出并等待线程结束。
        """
        self.thread.quit()
        self.thread.wait()
        print("AIClient stopped.")

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    
    client = AIClient()
    
    def handle_response(response):
        print(f"Test response: {response}")
        client.stop()
        app.quit()

    client.worker.response_ready.connect(handle_response)
    client.request_completion("你好，")
    
    sys.exit(app.exec())
