# tabtab/dictionary_manager.py
"""词库管理器，负责加载和查询rime词库文件。

该模块实现了对8105.dict.yaml文件的解析和加载，
提供高效的拼音到汉字转换查询功能。
"""

import yaml
import os
from typing import Dict, Optional, List, Tuple


class DictionaryManager:
    """词库管理器，负责加载和查询词库数据。
    
    支持rime格式的yaml词库文件，提供拼音到汉字的快速查询功能。
    """
    
    def __init__(self, dict_paths: List[str] = None):
        """初始化词库管理器。
        
        Args:
            dict_paths: 词库文件路径列表，默认为assets/8105.dict.yaml和assets/41448.dict.yaml
        """
        # word_dict 存储拼音到汉字列表的映射
        self.word_dict: Dict[str, List[str]] = {}
        # word_freq_dict 存储(汉字, 拼音)到词频的映射
        self.word_freq_dict: Dict[Tuple[str, str], int] = {}
        self.load_dictionaries(dict_paths)
    
    def load_dictionaries(self, dict_paths: List[str] = None):
        """加载多个词库文件。
        
        Args:
            dict_paths: 词库文件路径列表
        """
        if dict_paths is None:
            # 默认使用项目中的词库文件，按优先级排序
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dict_paths = [
                os.path.join(current_dir, '..', 'assets', 'base.dict.yaml'),
                os.path.join(current_dir, '..', 'assets', '8105.dict.yaml'),
                os.path.join(current_dir, '..', 'assets', '41448.dict.yaml')
            ]
        
        # 按顺序加载词库文件，后面的词库不会覆盖前面已存在的词条
        for dict_path in dict_paths:
            if os.path.exists(dict_path):
                self.load_dictionary(dict_path)
    
    def load_dictionary(self, dict_path: str):
        """加载单个词库文件。
        
        Args:
            dict_path: 词库文件路径
        """
        try:
            with open(dict_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 分离YAML头部和词条数据
            parts = content.split('...\n', 1)
            if len(parts) < 2:
                print(f"Warning: Invalid dictionary format in {dict_path}")
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
                    
                    # 如果有词频信息
                    freq = 1
                    if len(parts) >= 3:
                        try:
                            freq = int(parts[2])
                        except ValueError:
                            pass
                    
                    if pinyin not in self.word_dict:
                        self.word_dict[pinyin] = []
                    
                    # 避免重复添加相同的汉字
                    if hanzi not in self.word_dict[pinyin]:
                        self.word_dict[pinyin].append(hanzi)
                        self.word_freq_dict[(hanzi, pinyin)] = freq
                    
        except FileNotFoundError:
            print(f"Dictionary file not found: {dict_path}")
        except Exception as e:
            print(f"Error loading dictionary {dict_path}: {e}")
    
    def lookup(self, pinyin_str: str) -> Optional[List[str]]:
        """查询拼音对应的汉字列表。
        
        Args:
            pinyin_str: 拼音字符串
            
        Returns:
            对应的汉字列表，如果未找到则返回None
        """
        return self.word_dict.get(pinyin_str)
    
    def get_word_frequency(self, hanzi: str, pinyin: str) -> int:
        """获取词语的词频。
        
        Args:
            hanzi: 汉字
            pinyin: 拼音
            
        Returns:
            词频，如果没有则返回1
        """
        return self.word_freq_dict.get((hanzi, pinyin), 1)
    
    def get_candidates(self, pinyin_str: str, max_count: int = 10) -> list:
        """获取拼音的候选词列表，按词频排序。
        
        Args:
            pinyin_str: 拼音字符串
            max_count: 最大返回数量
            
        Returns:
            候选词列表，按词频从高到低排序
        """
        candidates = []
        
        # 精确匹配
        exact_matches = self.lookup(pinyin_str)
        if exact_matches:
            # 按词频排序
            exact_matches.sort(key=lambda x: self.get_word_frequency(x, pinyin_str), reverse=True)
            candidates.extend(exact_matches)
        
        # 前缀匹配
        prefix_matches = []
        for pinyin, hanzi_list in self.word_dict.items():
            if pinyin.startswith(pinyin_str):
                for hanzi in hanzi_list:
                    if hanzi not in candidates:  # 避免重复
                        prefix_matches.append((hanzi, self.get_word_frequency(hanzi, pinyin)))
        
        # 按词频排序前缀匹配结果
        prefix_matches.sort(key=lambda x: x[1], reverse=True)
        candidates.extend([hanzi for hanzi, freq in prefix_matches])
        
        return candidates[:max_count] if max_count > 0 else candidates


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