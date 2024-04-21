"""langchain_deepread."""

import logging
from logging.handlers import TimedRotatingFileHandler
from langchain_searxng.constants import PROJECT_ROOT_PATH

# Set to 'DEBUG' to have extensive logging turned on, even for libraries
ROOT_LOG_LEVEL = "INFO"

PRETTY_LOG_FORMAT = "%(asctime)s.%(msecs)03d [%(levelname)-5s] [%(filename)-12s][line:%(lineno)d] - %(message)s"
logging.basicConfig(level=ROOT_LOG_LEVEL, format=PRETTY_LOG_FORMAT, datefmt="%H:%M:%S")
logging.captureWarnings(True)


file_handler = TimedRotatingFileHandler(
    filename=PROJECT_ROOT_PATH / "log/app.log",
    when="midnight",
    interval=1,
    backupCount=7,
)
file_handler.suffix = "%Y-%m-%d.log"
file_handler.encoding = "utf-8"
file_handler.setLevel(ROOT_LOG_LEVEL)
# 创建格式化器并将其添加到处理器
file_formatter = logging.Formatter(PRETTY_LOG_FORMAT)
file_handler.setFormatter(file_formatter)

logging.getLogger().addHandler(file_handler)
