# start a fastapi server with uvicorn

import uvicorn

from langchain_searxng.main import app
from langchain_searxng.settings.settings import settings

# Set log_config=None to do not use the uvicorn logging configuration, and
# use ours instead. For reference, see below:
# https://github.com/tiangolo/fastapi/discussions/7457#discussioncomment-5141108
try:
    uvicorn.run(app, host="0.0.0.0", port=settings().server.port, log_config=None)
except KeyboardInterrupt:
    ...
