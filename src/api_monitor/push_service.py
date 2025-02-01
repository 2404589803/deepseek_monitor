import json
import qrcode
from pathlib import Path
from loguru import logger
from typing import Optional, List, Dict
from aiohttp import web
import aiohttp_jinja2
import jinja2
from pywebpush import webpush, WebPushException
from config.config import PUSH_CONFIG
import aiohttp

class PushService:
    def __init__(self):
        self.enabled = PUSH_CONFIG['enable_push']
        self.host = PUSH_CONFIG['host']
        self.port = PUSH_CONFIG['port']
        self.vapid_public_key = PUSH_CONFIG['vapid_public_key']
        self.vapid_private_key = PUSH_CONFIG['vapid_private_key']
        self.vapid_sub = PUSH_CONFIG['vapid_sub']
        self.qr_path = Path(PUSH_CONFIG['qrcode_file'])
        self.subscriptions: List[Dict] = []
        self.enable_serverchan = PUSH_CONFIG['enable_serverchan']
        self.serverchan_key = PUSH_CONFIG['serverchan_key']
        self.enable_telegram = PUSH_CONFIG['enable_telegram']
        self.telegram_bot_token = PUSH_CONFIG['telegram_bot_token']
        self.telegram_chat_id = PUSH_CONFIG['telegram_chat_id']
        
        # 确保二维码保存目录存在
        self.qr_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.enabled:
            if not all([self.vapid_public_key, self.vapid_private_key]):
                logger.warning("VAPID 密钥未配置，请先配置 VAPID_PUBLIC_KEY 和 VAPID_PRIVATE_KEY")
            else:
                self._setup_web_server()
                self._generate_qr_code()

        if self.enable_serverchan and not self.serverchan_key:
            logger.warning("Server酱 未配置 SERVERCHAN_KEY")
        if self.enable_telegram and (not self.telegram_bot_token or not self.telegram_chat_id):
            logger.warning("Telegram Bot 未配置 token 或 chat_id")

    def _setup_web_server(self):
        """设置 Web 服务器"""
        app = web.Application()
        template_path = str(Path(__file__).parent / 'templates')
        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(template_path))
        
        app.router.add_get('/', self.handle_index)
        app.router.add_post('/subscribe', self.handle_subscribe)
        app.router.add_post('/unsubscribe', self.handle_unsubscribe)
        app.router.add_static('/static', str(Path(__file__).parent / 'static'))
        app.router.add_get('/sw.js', self.handle_service_worker)
        
        runner = web.AppRunner(app)
        self.runner = runner

    async def start(self):
        """启动推送服务"""
        if self.enabled and all([self.vapid_public_key, self.vapid_private_key]):
            await self.runner.setup()
            site = web.TCPSite(self.runner, self.host, self.port)
            await site.start()
            logger.info(f"推送服务已启动: http://{self.host}:{self.port}")

    async def stop(self):
        """停止推送服务"""
        if hasattr(self, 'runner'):
            await self.runner.cleanup()

    def _generate_qr_code(self):
        """生成订阅页面的二维码"""
        try:
            subscribe_url = f"http://{self.host}:{self.port}"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(subscribe_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(self.qr_path)
            logger.info("推送服务二维码已生成，请使用手机扫描二维码：{}".format(self.qr_path))
            logger.info
        except Exception as e:
            logger.error(f"生成二维码失败: {str(e)}")


    @aiohttp_jinja2.template('subscribe.html')
    async def handle_index(self, request):
        """处理首页请求"""
        return {'vapid_public_key': self.vapid_public_key}

    async def handle_service_worker(self, request):
        """提供 Service Worker 文件"""
        return web.FileResponse(Path(__file__).parent / 'static' / 'sw.js')

    async def handle_subscribe(self, request):
        """处理订阅请求"""
        try:
            data = await request.json()
            if data not in self.subscriptions:
                self.subscriptions.append(data)
            return web.Response(status=200)
        except Exception as e:
            logger.error(f"处理订阅请求失败: {str(e)}")
            return web.Response(status=500)

    async def handle_unsubscribe(self, request):
        """处理取消订阅请求"""
        try:
            data = await request.json()
            if data in self.subscriptions:
                self.subscriptions.remove(data)
            return web.Response(status=200)
        except Exception as e:
            logger.error(f"处理取消订阅请求失败: {str(e)}")
            return web.Response(status=500)

    async def send_serverchan(self, title: str, message: str, url: Optional[str] = None) -> bool:
        """发送 Server酱 推送"""
        try:
            if not self.enable_serverchan or not self.serverchan_key:
                return False
                
            api_url = f'https://sctapi.ftqq.com/{self.serverchan_key}.send'
            content = f"{message}\n\n"
            if url:
                content += f"详情链接：{url}"
                
            data = {
                'title': title,
                'desp': content
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 0:
                            logger.info("Server酱推送成功")
                            return True
                        else:
                            logger.error(f"Server酱推送失败: {result.get('message')}")
                    else:
                        logger.error(f"Server酱推送失败: HTTP {response.status}")
            return False
        except Exception as e:
            logger.error(f"Server酱推送出错: {str(e)}")
            return False

    async def send_telegram(self, title: str, message: str, url: Optional[str] = None) -> bool:
        """发送 Telegram 推送"""
        try:
            if not self.enable_telegram or not self.telegram_bot_token or not self.telegram_chat_id:
                return False
                
            api_url = f'https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage'
            message_text = f"*{title}*\n\n{message}"
            if url:
                message_text += f"\n\n[详情链接]({url})"
                
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message_text,
                'parse_mode': 'Markdown'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=data) as response:
                    if response.status == 200:
                        logger.info("Telegram推送成功")
                        return True
                    else:
                        logger.error(f"Telegram推送失败: HTTP {response.status}")
            return False
        except Exception as e:
            logger.error(f"Telegram推送出错: {str(e)}")
            return False

    async def send_push(self, title: str, message: str, url: Optional[str] = None) -> bool:
        """发送推送消息（同时尝试所有已启用的推送方式）"""
        success = False
        
        # 尝试 Server酱 推送
        if self.enable_serverchan:
            if await self.send_serverchan(title, message, url):
                success = True
                
        # 尝试 Telegram 推送
        if self.enable_telegram:
            if await self.send_telegram(title, message, url):
                success = True
                
        return success

    def get_qr_status(self) -> dict:
        """获取二维码状态信息"""
        return {
            'enabled': self.enabled and all([self.vapid_public_key, self.vapid_private_key]),
            'qr_generated': self.qr_path.exists(),
            'qr_path': str(self.qr_path) if self.qr_path.exists() else None,
            'subscribers_count': len(self.subscriptions)
        }