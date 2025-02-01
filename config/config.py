from pathlib import Path
from dotenv import load_dotenv
import os

# 加载环境变量
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# API配置
API_CONFIG = {
    'base_url': 'https://api.deepseek.com',
    'api_key': os.getenv('DEEPSEEK_API_KEY'),
    'timeout': 30,  # 请求超时时间（秒）
    'max_retries': 3,  # 最大重试次数
    'model': 'deepseek-chat',  # 默认模型
    'web_url': 'https://chat.deepseek.com/'  # 网页版地址
}

# 监测配置
MONITOR_CONFIG = {
    'check_interval': 600,  # 检查间隔（秒）
    'error_threshold': 3,   # 连续错误阈值
    'log_file': 'logs/api_monitor.log',
    'test_message': "Hello",  # 用于测试的消息
}

# 告警配置
ALERT_CONFIG = {
    'enable_email': bool(os.getenv('ENABLE_EMAIL', False)),
    'smtp_server': os.getenv('SMTP_SERVER'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'smtp_username': os.getenv('SMTP_USERNAME'),
    'smtp_password': os.getenv('SMTP_PASSWORD'),
    'alert_recipients': os.getenv('ALERT_RECIPIENTS', '').split(','),
}

# 推送配置
PUSH_CONFIG = {
    'enable_push': bool(os.getenv('ENABLE_PUSH', True)),
    'host': os.getenv('PUSH_HOST', '0.0.0.0'),     # 推送服务器主机
    'port': int(os.getenv('PUSH_PORT', 8080)),     # 推送服务器端口
    'vapid_public_key': os.getenv('VAPID_PUBLIC_KEY'),   # VAPID 公钥
    'vapid_private_key': os.getenv('VAPID_PRIVATE_KEY'), # VAPID 私钥
    'vapid_sub': os.getenv('VAPID_SUB', 'mailto:admin@example.com'), # VAPID 订阅邮箱
    'qrcode_file': 'config/webpush_qr.png',        # 二维码保存路径
    'enable_serverchan': bool(os.getenv('ENABLE_SERVERCHAN', True)),
    'serverchan_key': os.getenv('SERVERCHAN_KEY'),
    'enable_telegram': bool(os.getenv('ENABLE_TELEGRAM', False)),
    'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
    'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
} 