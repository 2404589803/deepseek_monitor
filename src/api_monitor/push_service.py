# -*- coding: utf-8 -*-
"""
推送服务模块，支持Server酱和Telegram推送
"""

import os
import aiohttp
from loguru import logger
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('config/.env')

def parse_bool(value):
    """解析布尔值"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.lower().strip()
        if value in ('true', '1', 'yes', 'on', 't'):
            return True
        if value in ('false', '0', 'no', 'off', 'f'):
            return False
    return False

class PushService:
    def __init__(self):
        # 强制设置环境变量
        os.environ['ENABLE_SERVERCHAN'] = 'true'
        os.environ['SERVERCHAN_KEY'] = 'SCT268620T8SsHNSfDkAYxbiinkUSB9v23'
        
        # Server酱配置
        enable_serverchan = os.getenv('ENABLE_SERVERCHAN', 'false')
        self.enable_serverchan = parse_bool(enable_serverchan)
        self.serverchan_key = os.getenv('SERVERCHAN_KEY')
        
        # Telegram配置
        enable_telegram = os.getenv('ENABLE_TELEGRAM', 'false')
        self.enable_telegram = parse_bool(enable_telegram)
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # 输出配置信息
        logger.info(f"Server酱配置: enable={self.enable_serverchan}, key={'已配置' if self.serverchan_key else '未配置'}")
        logger.info(f"Telegram配置: enable={self.enable_telegram}, token={'已配置' if self.telegram_bot_token else '未配置'}, chat_id={'已配置' if self.telegram_chat_id else '未配置'}")
        
        if not any([
            self.enable_serverchan and self.serverchan_key,
            self.enable_telegram and self.telegram_bot_token and self.telegram_chat_id
        ]):
            logger.warning("未配置任何推送通道")
        else:
            if self.enable_serverchan and self.serverchan_key:
                logger.info("Server酱推送已启用")
            if self.enable_telegram and self.telegram_bot_token and self.telegram_chat_id:
                logger.info("Telegram推送已启用")
    
    async def send_serverchan(self, title: str, message: str) -> bool:
        """通过Server酱发送通知"""
        if not self.enable_serverchan or not self.serverchan_key:
            logger.warning("Server酱未启用或未配置密钥")
            return False
            
        url = f"https://sctapi.ftqq.com/{self.serverchan_key}.send"
        data = {
            "title": title,
            "desp": message
        }
        
        try:
            logger.info(f"正在发送Server酱推送: {url}")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    response_text = await response.text()
                    logger.info(f"Server酱响应: {response_text}")
                    
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 0:
                            logger.info("Server酱推送成功")
                            return True
                        else:
                            logger.error(f"Server酱推送失败: {result.get('message')}")
                    else:
                        logger.error(f"Server酱推送失败，状态码: {response.status}")
        except Exception as e:
            logger.error(f"Server酱推送出错: {str(e)}")
        
        return False
    
    async def send_telegram(self, title: str, message: str, url: Optional[str] = None) -> bool:
        """通过Telegram发送通知"""
        if not self.enable_telegram or not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("Telegram未启用或配置不完整")
            return False
            
        api_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        text = f"*{title}*\n\n{message}"
        if url:
            text += f"\n\n[详情]({url})"
        
        data = {
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        
        try:
            logger.info(f"正在发送Telegram推送")
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=data) as response:
                    response_text = await response.text()
                    logger.info(f"Telegram响应: {response_text}")
                    
                    if response.status == 200:
                        result = await response.json()
                        if result.get('ok'):
                            logger.info("Telegram推送成功")
                            return True
                        else:
                            logger.error(f"Telegram推送失败: {result.get('description')}")
                    else:
                        logger.error(f"Telegram推送失败，状态码: {response.status}")
        except Exception as e:
            logger.error(f"Telegram推送出错: {str(e)}")
        
        return False
    
    async def send_push(self, title: str, message: str, url: Optional[str] = None) -> bool:
        """向所有已配置的通道发送通知"""
        success = False
        
        if self.enable_serverchan and self.serverchan_key:
            logger.info("尝试发送Server酱推送")
            if await self.send_serverchan(title, message):
                success = True
        
        if self.enable_telegram and self.telegram_bot_token and self.telegram_chat_id:
            logger.info("尝试发送Telegram推送")
            if await self.send_telegram(title, message, url):
                success = True
        
        return success
