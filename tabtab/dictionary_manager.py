# tabtab/dictionary_manager.py
"""词库管理器，负责加载和查询rime词库文件。

该模块实现了对8105.dict.yaml文件的解析和加载，
提供高效的拼音到汉字转换查询功能。
"""

import yaml
import os
from typing import Dict, Optional, List


class DictionaryManager:
    """词库管理器，负责加载和查询词库数据。
    
    支持rime格式的yaml词库文件，提供拼音到汉字的快速查询功能。
    """
    
    def __init__(self, dict_path: str = None):
        """初始化词库管理器。
        
        Args:
            dict_path: 词库文件路径，默认为assets/8105.dict.yaml
        """
        self.word_dict: Dict[str, List[str]] = {}
        self.load_dictionary(dict_path)
    
    def load_dictionary(self, dict_path: str = None):
        """加载词库文件。
        
        Args:
            dict_path: 词库文件路径
        """
        if dict_path is None:
            # 默认使用项目中的8105词库
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dict_path = os.path.join(current_dir, '..', 'assets', '8105.dict.yaml')
        
        try:
            with open(dict_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 分离YAML头部和词条数据
            parts = content.split('...\n', 1)
            if len(parts) < 2:
                print("Warning: Invalid dictionary format")
                return
                
            # 解析词条数据
            word_lines = parts[1].strip().split('\n')
            for line in word_lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                parts = line.split('\t')
                if len(parts) >= 2:
                    hanzi = parts[0]
                    pinyin_with_spaces = parts[1]
                    pinyin = pinyin_with_spaces.replace(" ", "")
                    
                    if pinyin not in self.word_dict:
                        self.word_dict[pinyin] = []
                    
                    if hanzi not in self.word_dict[pinyin]:
                        self.word_dict[pinyin].append(hanzi)
                    
        except FileNotFoundError:
            print(f"Dictionary file not found: {dict_path}")
        except Exception as e:
            print(f"Error loading dictionary: {e}")
    
    def lookup(self, pinyin_str: str) -> Optional[List[str]]:
        """查询拼音对应的汉字列表。
        
        Args:
            pinyin_str: 拼音字符串
            
        Returns:
            对应的汉字列表，如果未找到则返回None
        """
        return self.word_dict.get(pinyin_str)
    
    def get_candidates(self, pinyin_str: str, max_count: int = 10) -> list:
        """获取拼音的候选词列表。
        
        Args:
            pinyin_str: 拼音字符串
            max_count: 最大返回数量
            
        Returns:
            候选词列表
        """
        candidates = []
        
        # 精确匹配
        exact_matches = self.lookup(pinyin_str)
        if exact_matches:
            candidates.extend(exact_matches)
        
        # 前缀匹配
        for pinyin, hanzi_list in self.word_dict.items():
            if pinyin.startswith(pinyin_str):
                for hanzi in hanzi_list:
                    if hanzi not in candidates:
                        candidates.append(hanzi)
                        if len(candidates) >= max_count:
                            return candidates
        
        return candidates


if __name__ == '__main__':
    # 测试词库管理器
    dm = DictionaryManager()
    print(f"Total words loaded: {len(dm.word_dict)}")
    
    # 测试查询
    test_pinyins = ['ni', 'hao', 'nihao', 'zhongguo']
    for pinyin in test_pinyins:
        result = dm.lookup(pinyin)
        candidates = dm.get_candidates(pinyin, 5)
        print(f"'{pinyin}': {result}, candidates: {candidates}")
