# -*- coding: utf-8 -*-

API_CONFIG = {
    'base_url': 'https://api.deepseek.com/v1',
    'api_key': None,
    'timeout': 30,  # 增加超时时间到30秒
    'max_retries': 3,
    'model': 'deepseek-chat',
    'web_url': 'https://chat.deepseek.com'
}

MONITOR_CONFIG = {
    'check_interval': 3600,  # 设置检查间隔为1小时
    'error_threshold': 3,   # 连续错误阈值
    'test_message': '这是一条来自 DeepSeek 监控服务的测试消息',  # 测试消息
    'log_file': 'logs/monitor.log'  # 日志文件路径
}
