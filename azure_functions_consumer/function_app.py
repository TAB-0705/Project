"""Azure Function (Python v2 programming model).

A Service Bus queue trigger: this function runs automatically every time a
message lands on the 'todo-events' queue — no polling loop, the platform
invokes it for you. The trigger stays thin: decode the message and hand it to
the processing module.
"""

import logging
import azure.functions as func

from processing import process_message

app = func.FunctionApp()


@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="todo-events",
    connection="ServiceBusConnection",  # name of the app setting holding the conn string
)
def todo_event_consumer(msg: func.ServiceBusMessage) -> None:
    body = msg.get_body().decode("utf-8")
    logging.info("Service Bus message received: %s", body)

    result = process_message(body)
    logging.info("Processing result: %s", result)
    # If this function returns without raising, the message is auto-completed
    # (removed from the queue). Raising an exception lets it retry / dead-letter.
