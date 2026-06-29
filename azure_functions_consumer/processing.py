"""Event-handling logic, kept separate from the trigger so it can be unit
tested without the Azure Functions runtime or a real Service Bus."""

import json
import logging

logger = logging.getLogger("todo_consumer")


def process_message(body: str) -> dict:
    """Parse a raw message body and route it to the right handler."""
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        logger.error("Message was not valid JSON: %s", body)
        return {"status": "error", "reason": "invalid_json"}
    return process_event(event)


def process_event(event: dict) -> dict:
    event_type = event.get("event")
    data = event.get("data", {})

    if event_type == "todo_created":
        logger.info("New todo: id=%s title=%r", data.get("id"), data.get("title"))
        # ... real side effects go here: send an email, update a search
        # index, write to analytics, etc. ...
        return {"status": "processed", "todo_id": data.get("id")}

    logger.warning("Unhandled event type: %s", event_type)
    return {"status": "ignored", "event": event_type}
