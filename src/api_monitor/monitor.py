import time
import requests
from loguru import logger
import schedule
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from openai import OpenAI
import aiohttp
import asyncio

from config.config import API_CONFIG, MONITOR_CONFIG, ALERT_CONFIG
from .push_service import PushService

class DeepSeekAPIMonitor:
    def __init__(self):
        self.base_url = API_CONFIG['base_url']
        self.api_key = API_CONFIG['api_key']
        self.timeout = API_CONFIG['timeout']
        self.max_retries = API_CONFIG['max_retries']
        self.model = API_CONFIG['model']
        self.web_url = API_CONFIG['web_url']
        self.error_count = 0
        self.last_success = None
        
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # 初始化推送服务
        self.push_service = PushService()
        
        # 设置日志
        logger.add(
            MONITOR_CONFIG['log_file'],
            rotation="500 MB",
            retention="10 days",
            level="INFO"
        )

    def check_api_health(self) -> Dict[str, Any]:
        """检查API的健康状态"""
        start_time = time.time()
        try:
            # 使用实际的 API 调用进行测试
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": MONITOR_CONFIG['test_message']},
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

    def send_alert(self, message: str):
        """发送告警邮件"""
        if not ALERT_CONFIG['enable_email']:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = ALERT_CONFIG['smtp_username']
            msg['To'] = ', '.join(ALERT_CONFIG['alert_recipients'])
            msg['Subject'] = 'DeepSeek 监控告警'
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(ALERT_CONFIG['smtp_server'], ALERT_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(ALERT_CONFIG['smtp_username'], ALERT_CONFIG['smtp_password'])
                server.send_message(msg)
                
            logger.info("告警邮件发送成功")
        except Exception as e:
            logger.error(f"发送告警邮件失败: {str(e)}")

    async def send_notification(self, title: str, message: str):
        """发送通知（邮件和推送）"""
        # 发送邮件通知
        self.send_alert(message)
        
        # 发送手机推送
        await self.push_service.send_push(
            title=title,
            message=message,
            url=self.web_url
        )

    async def monitor_step(self):
        """执行一次监控检查"""
        # 检查 API
        api_result = self.check_api_health()
        # 检查网页版
        web_result = await self.check_web_health()
        
        # 综合检查结果
        is_healthy = api_result['is_healthy'] and web_result['is_healthy']
        
        if is_healthy:
            self.error_count = 0
            self.last_success = datetime.now()
            status_message = (
                f"检查正常 - API响应时间: {api_result['response_time']:.2f}秒, "
                f"网页响应时间: {web_result['response_time']:.2f}秒"
            )
            logger.info(status_message)
            
            # 如果之前有错误，现在恢复了，发送恢复通知
            if self.error_count > 0:
                await self.send_notification(
                    "DeepSeek 服务已恢复",
                    f"服务已恢复正常运行\n{status_message}"
                )
        else:
            self.error_count += 1
            api_msg = api_result.get('error', f"HTTP状态码: {api_result['status']}")
            web_msg = web_result.get('error', f"HTTP状态码: {web_result['status']}")
            error_message = f"检查失败 - API: {api_msg}, 网页: {web_msg}"
            logger.error(error_message)
            
            if self.error_count >= MONITOR_CONFIG['error_threshold']:
                alert_message = (
                    f"DeepSeek 服务连续 {self.error_count} 次检查失败\n"
                    f"API状态: {'正常' if api_result['is_healthy'] else '异常'}\n"
                    f"API错误: {api_msg if not api_result['is_healthy'] else '无'}\n"
                    f"网页状态: {'正常' if web_result['is_healthy'] else '异常'}\n"
                    f"网页错误: {web_msg if not web_result['is_healthy'] else '无'}\n"
                    f"最后成功时间: {self.last_success or '无'}\n"
                    f"当前时间: {datetime.now()}"
                )
                await self.send_notification(
                    "DeepSeek 服务异常",
                    alert_message
                )

    async def start_monitoring(self):
        """启动监控"""
        logger.info("开始 DeepSeek 监控")
        
        # 输出推送服务状态
        push_status = self.push_service.get_qr_status()
        if push_status['enabled'] and push_status['qr_generated']:
            logger.info(f"推送服务已启用，请扫描二维码完成设置：{push_status['qr_path']}")
        
        # 立即执行一次检查
        await self.monitor_step()
        
        while True:
            await self.monitor_step()
            await asyncio.sleep(MONITOR_CONFIG['check_interval'])

if __name__ == "__main__":
    monitor = DeepSeekAPIMonitor()
    asyncio.run(monitor.start_monitoring())
