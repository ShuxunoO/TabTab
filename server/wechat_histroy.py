import requests
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeChatHistoryExporter:
    """微信聊天记录导出器"""
    
    def __init__(self, api_base: str = "http://localhost:5030/api/v1/chatlog"):
        self.api_base = api_base
        
    def fetch_chat_history(self, 
                          talker: str,
                          start_date: str = "2022-01-01",
                          end_date: Optional[str] = None,
                          limit: int = 1000000,
                          offset: int = 0) -> Optional[Dict[Any, Any]]:
        """
        获取聊天记录
        
        Args:
            talker: 聊天对象（wxid、remark或nickName）
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD，默认为今天
            limit: 每次请求的记录数量限制
            offset: 偏移量
            
        Returns:
            聊天记录数据或None（如果失败）
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            
        params = {
            "time": f"{start_date}~{end_date}",
            "talker": talker,
            "format": "json",
            "limit": limit,
            "offset": offset
        }
        
        try:
            logger.info(f"正在获取 {talker} 的聊天记录...")
            response = requests.get(self.api_base, params=params, timeout=30)
            response.raise_for_status()  # 抛出HTTP错误异常
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return None
    
    def save_to_file(self, data: Dict[Any, Any], filename: str, output_dir: str = "data") -> bool:
        """
        保存数据到文件
        
        Args:
            data: 要保存的数据
            filename: 文件名
            output_dir: 输出目录
            
        Returns:
            保存是否成功
        """
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 聊天记录已保存至 {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存文件失败: {e}")
            return False
    
    def export_chat_history(self, 
                           talker: str,
                           start_date: str = "2022-01-01",
                           end_date: Optional[str] = None,
                           output_dir: str = "output") -> bool:
        """
        导出聊天记录的完整流程
        
        Args:
            talker: 聊天对象
            start_date: 开始日期
            end_date: 结束日期
            output_dir: 输出目录
            
        Returns:
            导出是否成功
        """
        # 获取聊天记录
        chat_data = self.fetch_chat_history(talker, start_date, end_date)
        
        if chat_data is None:
            return False
        
        # 生成文件名
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            
        safe_talker = "".join(c for c in talker if c.isalnum() or c in "._-")
        filename = f"chatlog_{safe_talker}_{start_date.replace('-', '')}_{end_date.replace('-', '')}.json"
        
        # 保存文件
        return self.save_to_file(chat_data, filename, output_dir)

def main():
    """主函数"""
    exporter = WeChatHistoryExporter()
    
    # 配置参数
    talker = "陈泽文"
    start_date = "2024-01-01"
    end_date = "2025-08-01"
    # start_date = "2022-01-01"
    # end_date = "2025-08-01"
    
    # 导出聊天记录
    success = exporter.export_chat_history(
        talker=talker,
        start_date=start_date,
        end_date=end_date
    )
    
    if not success:
        logger.error("导出失败")
        exit(1)

if __name__ == "__main__":
    main()