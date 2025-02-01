﻿# -*- coding: utf-8 -*-
"""
DeepSeek API 监控模块
"""

import asyncio
import aiohttp
from loguru import logger
from datetime import datetime
from config.config import API_CONFIG, MONITOR_CONFIG
from api_monitor.push_service import PushService

class DeepSeekAPIMonitor:
    def __init__(self):
        self.base_url = API_CONFIG['base_url']
        self.api_key = API_CONFIG['api_key']
        self.web_url = API_CONFIG['web_url']
        self.timeout = API_CONFIG['timeout']
        self.max_retries = API_CONFIG['max_retries']
        self.model = API_CONFIG['model']
        
        self.check_interval = MONITOR_CONFIG['check_interval']
        self.error_threshold = MONITOR_CONFIG['error_threshold']
        self.test_message = MONITOR_CONFIG['test_message']
        self.log_file = MONITOR_CONFIG['log_file']
        
        self.consecutive_errors = 0
        self.push_service = PushService()
        
        # 配置日志
        logger.add(
            self.log_file,
            rotation="500 MB",
            encoding="utf-8",
            enqueue=True,
            compression="zip",
            retention="10 days"
        )

    async def test_push(self):
        """测试推送功能"""
        logger.info("正在测试推送功能...")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_message = f"这是一条测试消息\n发送时间: {current_time}"
        
        success = await self.push_service.send_push(
            title="DeepSeek监控测试推送",
            message=test_message,
            url=self.web_url
        )
        
        if success:
            logger.info("测试推送发送成功")
        else:
            logger.error("测试推送发送失败")
        
        return success

    async def check_api_status(self):
        """检查 API 状态"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": self.test_message}]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return True, "API 服务正常"
                    else:
                        error_msg = await response.text()
                        return False, f"API 请求失败: HTTP {response.status} - {error_msg}"
        except Exception as e:
            return False, f"API 连接错误: {str(e)}"

    async def check_web_status(self):
        """检查网页版状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.web_url,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return True, "网页版服务正常"
                    else:
                        return False, f"网页版访问失败: HTTP {response.status}"
        except Exception as e:
            return False, f"网页版连接错误: {str(e)}"

    async def monitor_once(self):
        """执行一次完整的监控检查"""
        api_ok, api_msg = await self.check_api_status()
        web_ok, web_msg = await self.check_web_status()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_message = f"[{current_time}] DeepSeek 服务状态:\n"
        status_message += f"API: {api_msg}\n"
        status_message += f"网页版: {web_msg}"
        
        if not api_ok or not web_ok:
            self.consecutive_errors += 1
            if self.consecutive_errors >= self.error_threshold:
                logger.error(status_message)
                # 发送告警通知
                await self.push_service.send_push(
                    title="DeepSeek 服务异常告警",
                    message=status_message,
                    url=self.web_url
                )
        else:
            self.consecutive_errors = 0
            logger.info(status_message)

    async def start_monitoring(self):
        """开始监控"""
        logger.info("开始监控 DeepSeek 服务状态")
        # 启动时先进行一次推送测试
        await self.test_push()
        
        while True:
            try:
                await self.monitor_once()
            except Exception as e:
                logger.error(f"监控过程出错: {str(e)}")
            
            await asyncio.sleep(self.check_interval)

if __name__ == "__main__":
    monitor = DeepSeekAPIMonitor()
    asyncio.run(monitor.start_monitoring())
