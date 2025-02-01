# -*- coding: utf-8 -*-
"""
DeepSeek API 监控模块
"""

import os
import asyncio
import aiohttp
from loguru import logger
from datetime import datetime, timedelta
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(ROOT_DIR))

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
            os.path.join(ROOT_DIR, self.log_file),
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
        test_message = f"""DeepSeek 监控服务测试推送

测试时间: {current_time}
测试消息: {self.test_message}

此消息用于测试推送服务是否正常工作。如果您收到此消息，说明推送服务配置成功。

监控服务将会在以下情况发送通知：
1. 服务启动时（当前消息）
2. DeepSeek 服务出现异常时（连续{self.error_threshold}次检测失败）
3. DeepSeek 服务恢复正常时

监控间隔: {self.check_interval}秒"""
        
        success = await self.push_service.send_push(
            title="DeepSeek监控服务测试推送",
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
        logger.info("正在检查 API 状态...")
        
        if not self.api_key:
            logger.info("API密钥未配置，跳过API检查")
            return True, "API检查已跳过（未配置密钥）"
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": self.test_message}]
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                logger.info(f"正在连接API: {self.base_url}")
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    logger.info(f"API响应状态码: {response.status}")
                    if response.status == 200:
                        return True, "API 服务正常"
                    else:
                        error_msg = await response.text()
                        return False, f"API 请求失败: HTTP {response.status} - {error_msg}"
        except asyncio.TimeoutError:
            logger.error(f"API 请求超时（{self.timeout}秒）")
            return False, f"API 连接超时（{self.timeout}秒）"
        except Exception as e:
            logger.error(f"API 检查出错: {str(e)}")
            return False, f"API 连接错误: {str(e)}"

    async def check_web_status(self):
        """检查网页版状态"""
        logger.info("正在检查网页版状态...")
        
        from playwright.async_api import async_playwright, TimeoutError
        
        for attempt in range(self.max_retries):
            try:
                async with async_playwright() as p:
                    # 启动浏览器，添加更多参数
                    browser = await p.chromium.launch(
                        headless=True,
                        args=[
                            '--disable-gpu',
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-accelerated-2d-canvas',
                            '--disable-accelerated-jpeg-decoding',
                            '--disable-accelerated-mjpeg-decode',
                            '--disable-accelerated-video-decode',
                            '--disable-gpu-compositing',
                            '--disable-gpu-memory-buffer-video-frames',
                            '--disable-gpu-rasterization'
                        ]
                    )
                    
                    # 创建上下文，添加更多配置
                    context = await browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        locale='zh-CN',
                        timezone_id='Asia/Shanghai',
                        geolocation={'latitude': 39.9042, 'longitude': 116.4074},  # 北京坐标
                        ignore_https_errors=True
                    )
                    
                    # 创建新页面
                    page = await context.new_page()
                    
                    try:
                        logger.info(f"正在连接网页: {self.web_url} (第{attempt + 1}次尝试)")
                        
                        # 设置超时
                        page.set_default_timeout(self.timeout * 1000)  # 转换为毫秒
                        
                        # 等待网络空闲
                        await page.route("**/*", lambda route: route.continue_())
                        
                        # 监听response事件以获取状态码
                        response = await page.goto(
                            self.web_url,
                            wait_until='domcontentloaded',  # 改为更快的加载策略
                            timeout=self.timeout * 1000
                        )
                        
                        if not response:
                            raise Exception("未收到响应")
                        
                        status = response.status
                        logger.info(f"网页响应状态码: {status}")
                        logger.info(f"网页响应头: {response.headers if response else 'N/A'}")
                        
                        # 等待页面加载完成
                        try:
                            await page.wait_for_load_state('networkidle', timeout=5000)  # 等待5秒网络空闲
                        except TimeoutError:
                            logger.warning("等待网络空闲超时，但继续检查")
                        
                        # 检查页面内容
                        content = await page.content()
                        if "chat.deepseek.com" in content.lower() or status in [200, 301, 302]:
                            return True, "网页版服务正常"
                        else:
                            error_msg = f"网页版访问失败: HTTP {status}"
                            if attempt < self.max_retries - 1:
                                logger.warning(f"{error_msg}，将在3秒后重试...")
                                await asyncio.sleep(3)
                                continue
                            return False, error_msg
                    finally:
                        await context.close()
                        await browser.close()
                        
            except TimeoutError as e:
                error_msg = f"网页加载超时: {str(e)}"
                logger.error(error_msg)
                if attempt < self.max_retries - 1:
                    logger.warning(f"{error_msg}，将在3秒后重试...")
                    await asyncio.sleep(3)
                    continue
                return False, error_msg
                
            except Exception as e:
                error_msg = f"网页检查出错: {str(e)}"
                logger.error(error_msg)
                if attempt < self.max_retries - 1:
                    logger.warning(f"{error_msg}，将在3秒后重试...")
                    await asyncio.sleep(3)
                    continue
                return False, f"网页连接错误: {str(e)}"
        
        return False, "网页检查失败：已达到最大重试次数"

    async def monitor_once(self):
        """执行一次完整的监控检查"""
        logger.info("开始执行监控检查...")
        
        try:
            api_ok, api_msg = await asyncio.wait_for(
                self.check_api_status(),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.error("API 状态检查超时")
            api_ok, api_msg = False, f"API 检查超时（{self.timeout}秒）"
        
        try:
            web_ok, web_msg = await asyncio.wait_for(
                self.check_web_status(),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.error("网页状态检查超时")
            web_ok, web_msg = False, f"网页检查超时（{self.timeout}秒）"
        
        current_time = datetime.now()
        next_check_time = current_time + timedelta(seconds=self.check_interval)
        
        status_message = f"""DeepSeek 服务状态报告

📅 检测时间: {current_time.strftime("%Y-%m-%d %H:%M:%S")}

服务状态:
{'🟢' if api_ok else '🔴'} API: {api_msg}
{'🟢' if web_ok else '🔴'} 网页版: {web_msg}

📊 监控信息:
• 连续错误次数: {self.consecutive_errors}/{self.error_threshold}
• 检测间隔: {self.check_interval}秒
• 下次检测: {next_check_time.strftime("%H:%M:%S")}

🔗 快速访问:
{self.web_url}"""
        
        if not api_ok or not web_ok:
            self.consecutive_errors += 1
            if self.consecutive_errors >= self.error_threshold:
                logger.error(status_message)
                # 发送告警通知
                await self.push_service.send_push(
                    title="🚨 DeepSeek 服务异常告警",
                    message=status_message,
                    url=self.web_url
                )
        else:
            if self.consecutive_errors >= self.error_threshold:
                # 如果之前有错误，现在恢复了，发送恢复通知
                recovery_message = f"""DeepSeek 服务恢复通知

✅ 服务已恢复正常运行！

📅 恢复时间: {current_time.strftime("%Y-%m-%d %H:%M:%S")}

当前状态:
🟢 API: {api_msg}
🟢 网页版: {web_msg}

📊 监控信息:
• 检测间隔: {self.check_interval}秒
• 下次检测: {next_check_time.strftime("%H:%M:%S")}

🔗 立即访问:
{self.web_url}"""
                
                await self.push_service.send_push(
                    title="✅ DeepSeek 服务已恢复正常",
                    message=recovery_message,
                    url=self.web_url
                )
            
            self.consecutive_errors = 0
            logger.info(status_message)

    async def start_monitoring(self):
        """开始监控"""
        logger.info("开始监控 DeepSeek 服务状态")
        
        # 启动时立即执行一次监控检查
        logger.info("执行首次监控检查...")
        await self.monitor_once()
        
        # 然后开始定时监控
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                await self.monitor_once()
            except Exception as e:
                logger.error(f"监控过程出错: {str(e)}")

if __name__ == "__main__":
    monitor = DeepSeekAPIMonitor()
    asyncio.run(monitor.start_monitoring())
