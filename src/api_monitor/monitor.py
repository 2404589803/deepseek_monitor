# -*- coding: utf-8 -*-
"""
DeepSeek API 监控模块的核心实现
"""

import time
import aiohttp
import asyncio
from loguru import logger
from datetime import datetime
from typing import Dict, Any
from openai import OpenAI

from config.config import API_CONFIG, MONITOR_CONFIG
from .push_service import PushService

class DeepSeekAPIMonitor:
    def __init__(self):
        self.base_url = API_CONFIG['base_url']
        self.api_key = API_CONFIG['api_key']
        self.timeout = API_CONFIG['timeout']
        self.max_retries = API_CONFIG['max_retries']
        self.model = API_CONFIG['model']
        self.web_url = API_CONFIG['web_url']
        self.check_interval = MONITOR_CONFIG['check_interval']
        self.error_threshold = MONITOR_CONFIG['error_threshold']
        self.test_message = MONITOR_CONFIG['test_message']
        
        self.consecutive_errors = 0
        self.push_service = PushService()
        
        # 只在有 API key 时初始化 OpenAI 客户端
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info("API 监控已启用")
        else:
            self.client = None
            logger.info("API 监控未启用（未配置 API key）")
        
        # 设置日志
        logger.add(
            MONITOR_CONFIG['log_file'],
            rotation="500 MB",
            retention="10 days",
            level="INFO"
        )

    async def check_api_health(self) -> Dict[str, Any]:
        """检查API的健康状态"""
        # 如果没有配置 API key，直接返回跳过状态
        if not self.api_key:
            return {
                'status': None,
                'response_time': 0,
                'is_healthy': True,  # 返回 True 这样不会触发告警
                'timestamp': datetime.now().isoformat(),
                'skipped': True
            }

        start_time = time.time()
        try:
            # 使用实际的 API 调用进行测试
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": self.test_message},
                ],
                stream=False
            )
            
            response_time = time.time() - start_time
            
            # 检查响应是否包含预期的字段
            if hasattr(response, 'choices') and len(response.choices) > 0:
                return {
                    'status': 200,
                    'response_time': response_time,
                    'is_healthy': True,
                    'timestamp': datetime.now().isoformat(),
                    'response_content': response.choices[0].message.content
                }
            else:
                return {
                    'status': 500,
                    'response_time': response_time,
                    'is_healthy': False,
                    'error': "API响应格式异常",
                    'timestamp': datetime.now().isoformat()
                }
            
        except Exception as e:
            return {
                'status': None,
                'response_time': time.time() - start_time,
                'is_healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def check_web_health(self) -> Dict[str, Any]:
        """检查网页版的可访问性"""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.web_url, timeout=self.timeout) as response:
                    response_time = time.time() - start_time
                    return {
                        'status': response.status,
                        'response_time': response_time,
                        'is_healthy': response.status == 200,
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                'status': None,
                'response_time': time.time() - start_time,
                'is_healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def send_notification(self, title: str, message: str):
        """发送通知"""
        await self.push_service.send_push(
            title=title,
            message=message,
            url=self.web_url
        )

    async def monitor_once(self):
        """执行一次完整的状态检查"""
        api_result = await self.check_api_health()
        web_result = await self.check_web_health()
        
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建状态消息
        status_message = f"检测时间: {current_time}\n"
        if not api_result.get('skipped'):
            status_message += f"API 状态: {'✅ 正常' if api_result['is_healthy'] else '❌ 异常'}\n"
        status_message += f"网页版状态: {'✅ 正常' if web_result['is_healthy'] else '❌ 异常'}"
        
        # 判断是否需要发送告警
        is_healthy = (api_result.get('skipped') or api_result['is_healthy']) and web_result['is_healthy']
        
        if not is_healthy:
            self.consecutive_errors += 1
            if self.consecutive_errors >= self.error_threshold:
                await self.send_notification(
                    "🚨 DeepSeek 服务异常告警",
                    status_message
                )
        else:
            if self.consecutive_errors >= self.error_threshold:
                await self.send_notification(
                    "✅ DeepSeek 服务已恢复",
                    f"服务已恢复正常运行\n{status_message}"
                )
            self.consecutive_errors = 0
            logger.info(status_message)

    async def start_monitoring(self):
        """开始监控"""
        logger.info("开始监控 DeepSeek 服务状态")
        while True:
            try:
                await self.monitor_once()
            except Exception as e:
                logger.error(f"监控过程出错: {str(e)}")
            
            await asyncio.sleep(self.check_interval)

if __name__ == "__main__":
    monitor = DeepSeekAPIMonitor()
    asyncio.run(monitor.start_monitoring())
