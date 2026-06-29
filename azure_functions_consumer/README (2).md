# Azure Function: Service Bus Consumer (Python v2)

A serverless consumer for the To-Do events. This Azure Function triggers
automatically whenever a message hits the `todo-events` Service Bus queue —
the event-driven replacement for the polling `consumer.py`.

## Files

```
function_app.py       the trigger (Python v2 decorator model) — stays thin
processing.py         event-handling logic (isolated, unit-testable)
host.json             runtime config + extension bundle (Service Bus binding)
local.settings.json   local app settings (put your connection string here)
requirements.txt      azure-functions
```

## ⚠️ Python version

**Azure Functions does NOT support Python 3.14.** Use **Python 3.11** (install
alongside 3.14). This is the Functions runtime's own limit, separate from any
torch issue.

## Prerequisites

- **Azure Functions Core Tools v4** (the `func` CLI):
  https://learn.microsoft.com/azure/azure-functions/functions-run-local
- **Azurite** (local storage emulator) for `AzureWebJobsStorage`, or a real
  storage account connection string. Azurite installs via:
  `npm install -g azurite` (then run `azurite` in a terminal).
- A Service Bus namespace + the `todo-events` queue (from the producer task).

## Setup & run (local)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Put your Service Bus connection string in `local.settings.json`:
```json
"ServiceBusConnection": "Endpoint=sb://...;SharedAccessKeyName=...;SharedAccessKey=..."
```

Start Azurite in one terminal (`azurite`), then start the function:
```powershell
func start
```

## Demo

1. Keep this function running (`func start`).
2. In the producer project, create a todo (POST /todos) pointed at the same
   queue.
3. This function fires automatically and logs:
   `New todo: id=1 title='Buy milk'`.

No producer handy? Send a test message to the queue from the Azure Portal
(Service Bus > queue > Service Bus Explorer > Send), using a body like:
`{"event": "todo_created", "data": {"id": 99, "title": "Test"}}`.

## Deploy (optional)

```powershell
func azure functionapp publish <your-function-app-name>
```
Then set `ServiceBusConnection` in the Function App's Application Settings.

## Talking points

- **Trigger vs polling.** `consumer.py` ran a loop asking the queue for
  messages. An Azure Function is **event-driven**: the platform watches the
  queue and invokes the function only when a message arrives, scaling to zero
  when idle. That's the serverless advantage.
- **The `connection` binding.** `connection="ServiceBusConnection"` is not the
  connection string itself — it's the NAME of an app setting that holds it.
  Locally that's `local.settings.json`; in Azure it's the Function App's
  Application Settings. This keeps secrets out of code.
- **Auto-complete and retries.** If the function returns normally, the message
  is completed (removed). If it raises, Service Bus retries and eventually
  dead-letters — built-in reliability you'd otherwise hand-code.
- **Thin trigger.** The trigger just decodes and delegates to `processing.py`,
  so the real logic is isolated and testable without the Functions runtime.
