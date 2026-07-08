import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.clients.claude_client import ClaudeClient
from app.exceptions.claude_exceptions import *

@pytest.mark.asyncio
async def test_claude_client_retry_on_overload():
    """Verify retry behavior on overloaded_error."""
    mock_client = AsyncMock()
    mock_client.messages.stream.side_effect = [
        Exception("overloaded_error"),  # First call fails
        MagicMock(),  # Second call succeeds
    ]
    
    client = ClaudeClient(mock_client, settings=MockSettings())
    
    events = []
    async for event in client.stream("system", "user"):
        events.append(event)
    
    assert len(events) > 0
    assert mock_client.messages.stream.call_count == 2

@pytest.mark.asyncio
async def test_claude_client_no_retry_on_auth_error():
    """Verify no retry on authentication_error."""
    mock_client = AsyncMock()
    mock_client.messages.stream.side_effect = Exception("authentication_error")
    
    client = ClaudeClient(mock_client, settings=MockSettings())
    
    with pytest.raises(ClaudeAuthError):
        async for _ in client.stream("system", "user"):
            pass
    
    assert mock_client.messages.stream.call_count == 1

@pytest.mark.asyncio
async def test_claude_client_section_detection():
    """Verify section detection works correctly."""
    mock_stream = AsyncMock()
    mock_stream.__aenter__.return_value = mock_stream
    mock_stream.__aiter__.return_value = [
        MagicMock(type="content_block_delta", delta=MagicMock(type="text_delta", text="## Roadmap\n")),
        MagicMock(type="content_block_delta", delta=MagicMock(type="text_delta", text="Content...")),
        MagicMock(type="message_stop"),
    ]
    
    mock_client = AsyncMock()
    mock_client.messages.stream.return_value = mock_stream
    
    client = ClaudeClient(mock_client, settings=MockSettings())
    
    events = []
    async for event in client.stream("system", "user"):
        events.append(event)
    
    assert events[0].type == "section"
    assert events[0].section == "roadmap"
    assert events[1].type == "chunk"