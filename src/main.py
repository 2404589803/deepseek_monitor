# -*- coding: utf-8 -*-
import asyncio
from loguru import logger
from api_monitor.monitor import DeepSeekAPIMonitor

async def main():
    try:
        logger.info("Starting DeepSeek Monitor")
        monitor = DeepSeekAPIMonitor()
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Monitor stopped")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 