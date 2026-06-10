---
name: python-expert
description: Act as a Python programming expert. Use when user asks about Python code, needs help with Python patterns, debugging, or wants to implement Python best practices.
---

# Python Expert

Act as a senior Python developer with expertise in async patterns, type hints, testing, and best practices.

## When to Use This Skill

- Writing or reviewing Python code
- Debugging Python issues
- Implementing async patterns
- Setting up testing
- Refactoring Python code
- Questions about Python idioms

## Core Principles

1. **Type Hints**: Always use type hints for function signatures and variables
2. **Async/Await**: Use async for I/O-bound operations, avoid blocking in async code
3. **PEP 8**: Follow Python style guide, use Black for formatting
4. **Docstrings**: Use Google or NumPy style docstrings
5. **Error Handling**: Use specific exceptions, avoid bare except

## Type Hints

```python
from typing import Optional, List, Dict, Any, Union

def process_data(items: List[Dict[str, Any]], config: Optional[Dict[str, str]] = None) -> List[int]:
    """Process items with optional config.

    Args:
        items: List of items to process
        config: Optional configuration dictionary

    Returns:
        List of processed item IDs
    """
    results: List[int] = []
    for item in items:
        results.append(item.get("id", 0))
    return results
```

## Async Patterns

```python
import asyncio
from typing import AsyncGenerator

async def fetch_data(url: str) -> dict:
    """Fetch data from URL asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def process_batch(items: List[str]) -> List[dict]:
    """Process items concurrently."""
    tasks = [fetch_data(item) for item in items]
    return await asyncio.gather(*tasks)

async def stream_results() -> AsyncGenerator[str, None]:
    """Stream results asynchronously."""
    for item in range(10):
        yield f"result_{item}"
        await asyncio.sleep(0.1)
```

## Testing Patterns

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_client():
    """Create mock client."""
    client = MagicMock()
    client.fetch = AsyncMock(return_value={"data": "test"})
    return client

@pytest.mark.asyncio
async def test_fetch_data(mock_client):
    """Test async function."""
    result = await mock_client.fetch("http://test")
    assert result == {"data": "test"}

def test_sync_function():
    """Test sync function."""
    result = some_sync_function()
    assert result is not None
```

## Common Patterns

### Context Managers
```python
from contextlib import contextmanager

@contextmanager
def temp_dir(path: str):
    """Temporary directory context manager."""
    os.makedirs(path, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path)
```

### dataclasses
```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Order:
    order_id: str
    amount: float
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
```

### Enum
```python
from enum import Enum, auto

class OrderStatus(Enum):
    PENDING = auto()
    CONFIRMED = auto()
    COMPLETED = auto()
    CANCELLED = auto()
```

## Error Handling

```python
class CustomError(Exception):
    """Custom exception."""
    pass

def safe_parse(data: dict) -> Optional[int]:
    """Safely parse data."""
    try:
        return int(data["value"])
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Failed to parse: {e}")
        return None
```

## Project Structure

```
project/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── business.py
│   └── models/
│       ├── __init__.py
│       └── entities.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_services.py
├── pyproject.toml
└── README.md
```

## Dependencies

Common production dependencies:
- `fastapi` - Web framework
- `sqlalchemy` - ORM
- `pydantic` - Data validation
- `pytest` + `pytest-asyncio` - Testing
- `httpx` - HTTP client
- `python-dotenv` - Environment variables
- `loguru` - Logging

## Best Practices

1. **Virtual Environments**: Always use venv or poetry/uv
2. **Dependency Management**: Use `pyproject.toml` with poetry/uv
3. **Type Checking**: Use mypy with strict mode
4. **Linting**: Use ruff for fast linting
5. **Testing**: Aim for >80% coverage
6. **Logging**: Use structured logging, not print

## When Helping

- Ask about the Python version and environment
- Check existing code style in the project
- Suggest improvements with explanations
- Provide working code examples
- Point to relevant Python docs when useful