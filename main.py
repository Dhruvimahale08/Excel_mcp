import asyncio
from utils.logger import setup_logger
from utils.config_loader import load_config
from agent.employee_agent import run_agent

if __name__ == "__main__":
    config = load_config()
    logger = setup_logger(
        "excel_mcp.main",
        log_file=config.get("logging", {}).get("file"),
        level=config.get("logging", {}).get("level", "INFO")
    )
    
    logger.info("Starting MCP Agent...")
    try:
        asyncio.run(run_agent())
        logger.info("MCP Agent finished successfully")
    except KeyboardInterrupt:
        logger.info("Agent interrupted by user")
    except Exception as e:
        logger.error(f"Agent failed: {e}", exc_info=True)
        raise
