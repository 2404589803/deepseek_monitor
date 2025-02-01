# -*- coding: utf-8 -*-
"""
配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('config/.env')

# API配置
API_CONFIG = {
    'base_url': 'https://api.deepseek.com/v1',  # DeepSeek API基础URL
    'api_key': os.getenv('DEEPSEEK_API_KEY'),  # API密钥
    'timeout': 30,  # 请求超时时间（秒）
    'max_retries': 3,  # 最大重试次数
    'model': 'deepseek-chat',  # 使用的模型名称
    'web_url': 'https://chat.deepseek.com'  # DeepSeek网页版URL
}

# 监控配置
MONITOR_CONFIG = {
    'check_interval': 300,  # 检查间隔（秒）
    'error_threshold': 3,  # 连续错误阈值
    'test_message': 'Hello, this is a test message.',  # 测试消息
    'log_file': 'logs/monitor.log'  # 日志文件路径
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
