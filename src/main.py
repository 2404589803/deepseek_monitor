# -*- coding: utf-8 -*-
"""
DeepSeek 监控服务主程序
"""

from loguru import logger
from api_monitor.monitor import DeepSeekAPIMonitor

async def main():
    logger.info("Starting DeepSeek Monitor")
    monitor = DeepSeekAPIMonitor()
    await monitor.monitor_once()  # 只运行一次监控检查

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 