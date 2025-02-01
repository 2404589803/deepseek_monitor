# -*- coding: utf-8 -*-
"""
DeepSeek 监控系统入口
"""

import asyncio
from loguru import logger
from api_monitor.monitor import DeepSeekAPIMonitor

async def main():
    try:
        logger.info("启动 DeepSeek 监控系统")
        monitor = DeepSeekAPIMonitor()
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("监控系统已停止")
    except Exception as e:
        logger.error(f"监控系统发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 