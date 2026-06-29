"""The CONSUMER half of the pattern. Run this in a SEPARATE terminal from the
API. It pulls 'todo_created' events off the queue and processes them (here,
just prints them) — decoupled from the API that produced them.

Run:  python consumer.py
"""

import asyncio
import json

from app.config import SERVICE_BUS_CONNECTION_STRING, SERVICE_BUS_QUEUE_NAME


async def main() -> None:
    if not SERVICE_BUS_CONNECTION_STRING:
        print("SERVICE_BUS_CONNECTION_STRING is not set. Add it to .env first.")
        return

    from azure.servicebus.aio import ServiceBusClient

    async with ServiceBusClient.from_connection_string(
        SERVICE_BUS_CONNECTION_STRING
    ) as client:
        receiver = client.get_queue_receiver(queue_name=SERVICE_BUS_QUEUE_NAME)
        async with receiver:
            print(f"Listening on queue '{SERVICE_BUS_QUEUE_NAME}'. Ctrl+C to stop.")
            while True:
                messages = await receiver.receive_messages(
                    max_message_count=10, max_wait_time=5
                )
                for msg in messages:
                    try:
                        event = json.loads(str(msg))
                        print("Consumed event:", event)
                        # ... real processing would go here ...
                        await receiver.complete_message(msg)  # remove from queue
                    except Exception as e:
                        print("Failed to process message:", e)
                        await receiver.abandon_message(msg)  # put it back


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
