"""Service Bus settings, read from environment / .env.

If SERVICE_BUS_CONNECTION_STRING is empty, the publisher runs in a graceful
'log-only' fallback so the API still works locally without Azure.
"""

import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_BUS_CONNECTION_STRING = os.getenv("SERVICE_BUS_CONNECTION_STRING", "")
SERVICE_BUS_QUEUE_NAME = os.getenv("SERVICE_BUS_QUEUE_NAME", "todo-events")
