import asyncio
from api_monitor.monitor import DeepSeekAPIMonitor
from loguru import logger

async def main():
    try:
        logger.info("启动 DeepSeek 监控系统")
        api_monitor = DeepSeekAPIMonitor()
        await api_monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("监控系统已停止")
    except Exception as e:
        logger.error(f"监控系统发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 