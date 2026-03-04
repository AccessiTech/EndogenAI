# endogenai-a2a

Python client for A2A (Agent-to-Agent) task delegation between EndogenAI cognitive modules.

Implements the JSON-RPC 2.0 task protocol over HTTP. `send_task()` maps to `tasks/send` and is
fully wired end-to-end for all Phase 5 modules. `get_task()` maps to `tasks/get` and is
implemented in the client, but Phase 5 module servers do not yet handle `tasks/get` requests —
server-side support is scheduled for Phase 6. All Python Group II modules use this package
instead of raw `httpx` calls.

## Usage

```python
from endogenai_a2a import A2AClient

client = A2AClient(url="http://localhost:8202", timeout=10.0)
result = await client.send_task("consolidate_item", {"item": item.model_dump()})
```

## Interface

### `A2AClient`

| Method | Description |
|--------|-------------|
| `send_task(task_type, payload)` | Send a JSON-RPC 2.0 `tasks/send` request |
| `get_task(task_id)` | Fetch a task by ID via `tasks/get` |

### Exceptions

| Exception | When raised |
|-----------|-------------|
| `A2AError` | Base class for all A2A errors |
| `A2AProtocolError` | Invalid JSON-RPC response from server |
| `A2ATaskNotFound` | `tasks/get` returns null result |

## Development

```bash
cd shared/a2a/python
uv sync
uv run ruff check .
uv run mypy src/
uv run pytest
```

## Testing

Framework: **pytest**. Coverage threshold: **80%** (enforce with `pytest-cov` once installed — see
[docs/test-upgrade-workplan.md](../../../docs/test-upgrade-workplan.md) P05).

```bash
cd shared/a2a/python
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

All tests in `tests/test_client.py` use a mock transport — no live services required. Estimated coverage: ~75%
(target: 80%). No integration-test skip guards required for this package (unit-only test suite).
