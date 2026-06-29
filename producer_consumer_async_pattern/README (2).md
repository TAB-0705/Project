# To-Do API + Azure Service Bus (Producer-Consumer)

Extends the CRUD To-Do API so that creating a todo **publishes a
`todo_created` event** to an Azure Service Bus queue. A separate **consumer**
worker reads those events. This decouples the API (producer) from downstream
work (consumer) via an async queue.

## Architecture

```
app/
  router.py            create_todo is async -> awaits the service
  service.py           create(): persist, then publish event
  event_publisher.py   PRODUCER: async send to Service Bus (only Azure-aware file)
  config.py            connection string + queue name from .env
  repository.py        in-memory store (unchanged)
  schemas.py           Pydantic models (unchanged)
consumer.py            CONSUMER: separate worker that reads the queue
```

The Service Bus access is isolated in `event_publisher.py`, just like DB
access is isolated in the repository.

## Run WITHOUT Azure (fallback mode, for quick local testing)

Leave `SERVICE_BUS_CONNECTION_STRING` empty in `.env`. Creating a todo logs the
event instead of sending it, and the API still returns 201.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
POST a todo at http://127.0.0.1:8000/docs — you'll see a log line:
`Service Bus not configured; event NOT sent: {...}`.

## Run WITH Azure (the real producer-consumer demo)

### 1. Create the queue (Azure Portal)
- Create a **Service Bus namespace** (Basic tier is enough).
- Inside it, create a **queue** named `todo-events`.
- Under **Shared access policies**, copy the **connection string** (needs
  Send + Listen).

### 2. Configure
Rename `.env.example` to `.env` and paste the connection string:
```
SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://...;SharedAccessKeyName=...;SharedAccessKey=...
SERVICE_BUS_QUEUE_NAME=todo-events
```

### 3. Run both halves (two terminals)
```powershell
# Terminal 1 - the API (producer)
python -m uvicorn app.main:app --reload

# Terminal 2 - the worker (consumer)
python consumer.py
```

### 4. Demo
Create a todo via http://127.0.0.1:8000/docs. Terminal 2 prints:
```
Consumed event: {'event': 'todo_created', 'data': {'id': 1, 'title': '...'}}
```

## Talking points

- **Why a queue at all:** the API can respond immediately after storing the
  todo; slow downstream work (emails, indexing, analytics) happens in the
  consumer, independently. That's the decoupling the producer-consumer pattern
  buys you.
- **Why async:** the publish uses the async Service Bus client and an async
  endpoint, so sending the event doesn't block the request thread.
- **Why publish AFTER persisting:** you don't want to announce a todo that
  failed to save.
- **The fallback's trade-off (be honest):** it 'fails open' — if the bus is
  unconfigured/down, the todo is still created and the event is only logged.
  Simple and demo-friendly, but in production you might use the transactional
  outbox pattern so an event is never silently lost.
