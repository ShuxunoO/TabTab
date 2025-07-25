# tabtab/dictionary_manager.py
import yaml

class DictionaryManager:
    """负责加载和管理输入法词库。

    该类提供了从Rime格式的.dict.yaml文件中加载词典的功能，
    并提供一个简单的接口来查询拼音对应的词汇。
    """
    def __init__(self):
        """DictionaryManager的构造函数。

        初始化一个空的词典。
        """
        self.word_dict = {}

    def load_rime_dict(self, file_path):
        """加载Rime词库文件。

        解析.dict.yaml文件，提取词语和对应的拼音，并存入word_dict。
        这是一个简化的解析器，主要处理---之后的数据行。
        Rime词典格式通常为：<汉字词>\\t<拼音序列>\\t<频率>

        Args:
            file_path (str): 词库文件的路径。
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                try:
                    start_index = lines.index("---\n") + 1
                except ValueError:
                    start_index = 0
                
                for line in lines[start_index:]:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        word = parts[0]
                        pinyin_seq = parts[1].split(' ')
                        self.word_dict[''.join(pinyin_seq)] = word
            print(f"Loaded {len(self.word_dict)} words from {file_path}")
        except Exception as e:
            print(f"Error loading dictionary {file_path}: {e}")

    def lookup(self, pinyin_str):
        """查询拼音字符串对应的词语。

        Args:
            pinyin_str (str): 要查询的无空格拼音字符串。

        Returns:
            str or None: 如果找到，返回对应的词语；否则返回None。
        """
        return self.word_dict.get(pinyin_str)

if __name__ == '__main__':
    dummy_dict_content = """
# Rime dictionary
# ... metadata ...
---
你好	ni hao
世界	shi jie
"""
    dummy_file = "dummy.dict.yaml"
    with open(dummy_file, "w", encoding="utf-8") as f:
        f.write(dummy_dict_content)

    dict_manager = DictionaryManager()
    dict_manager.load_rime_dict(dummy_file)
    print(f"Lookup 'nihao': {dict_manager.lookup('nihao')}")
    print(f"Lookup 'shijie': {dict_manager.lookup('shijie')}")
    
    import os
    os.remove(dummy_file)
