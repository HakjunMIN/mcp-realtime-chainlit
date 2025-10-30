#!/usr/bin/env python3
"""
Unit tests for realtime.py classes
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from collections import defaultdict
from realtime import RealtimeEventHandler, RealtimeConversation, RealtimeClient
import numpy as np


class TestRealtimeEventHandler:
    """Test RealtimeEventHandler class"""
    
    @pytest.fixture
    def handler(self):
        """Create a fresh RealtimeEventHandler instance"""
        return RealtimeEventHandler()
    
    def test_initialization(self, handler):
        """Test RealtimeEventHandler initialization"""
        assert isinstance(handler.event_handlers, defaultdict)
        assert len(handler.event_handlers) == 0
    
    def test_on_register_handler(self, handler):
        """Test registering event handlers"""
        mock_callback = Mock()
        
        handler.on("test_event", mock_callback)
        
        assert "test_event" in handler.event_handlers
        assert mock_callback in handler.event_handlers["test_event"]
    
    def test_on_register_multiple_handlers(self, handler):
        """Test registering multiple handlers for the same event"""
        callback1 = Mock()
        callback2 = Mock()
        
        handler.on("test_event", callback1)
        handler.on("test_event", callback2)
        
        assert len(handler.event_handlers["test_event"]) == 2
    
    def test_clear_event_handlers(self, handler):
        """Test clearing all event handlers"""
        handler.on("event1", Mock())
        handler.on("event2", Mock())
        
        handler.clear_event_handlers()
        
        assert len(handler.event_handlers) == 0
    
    def test_dispatch_sync_handler(self, handler):
        """Test dispatching to synchronous handlers"""
        mock_callback = Mock()
        event_data = {"type": "test", "data": "value"}
        
        handler.on("test_event", mock_callback)
        handler.dispatch("test_event", event_data)
        
        mock_callback.assert_called_once_with(event_data)
    
    def test_dispatch_multiple_handlers(self, handler):
        """Test dispatching to multiple handlers"""
        callback1 = Mock()
        callback2 = Mock()
        event_data = {"type": "test"}
        
        handler.on("test_event", callback1)
        handler.on("test_event", callback2)
        handler.dispatch("test_event", event_data)
        
        callback1.assert_called_once_with(event_data)
        callback2.assert_called_once_with(event_data)
    
    def test_dispatch_no_handlers(self, handler):
        """Test dispatching event with no registered handlers"""
        # Should not raise an error
        handler.dispatch("nonexistent_event", {})
    
    @pytest.mark.asyncio
    async def test_wait_for_next(self, handler):
        """Test wait_for_next method"""
        event_data = {"type": "test", "value": 42}
        
        # Start waiting in background
        wait_task = asyncio.create_task(handler.wait_for_next("test_event"))
        
        # Give it time to set up
        await asyncio.sleep(0.01)
        
        # Dispatch the event
        handler.dispatch("test_event", event_data)
        
        # Wait for the result
        result = await wait_task
        
        assert result == event_data


class TestRealtimeConversation:
    """Test RealtimeConversation class"""
    
    @pytest.fixture
    def conversation(self):
        """Create a fresh RealtimeConversation instance"""
        return RealtimeConversation()
    
    def test_initialization(self, conversation):
        """Test RealtimeConversation initialization"""
        assert conversation.item_lookup == {}
        assert conversation.items == []
        assert conversation.response_lookup == {}
        assert conversation.responses == []
        assert conversation.queued_speech_items == {}
        assert conversation.queued_transcript_items == {}
        assert conversation.queued_input_audio is None
    
    def test_clear(self, conversation):
        """Test clearing conversation state"""
        # Add some data
        conversation.items = [{"id": "1"}]
        conversation.item_lookup = {"1": {"id": "1"}}
        conversation.queued_input_audio = b"audio"
        
        conversation.clear()
        
        assert conversation.items == []
        assert conversation.item_lookup == {}
        assert conversation.queued_input_audio is None
    
    def test_queue_input_audio(self, conversation):
        """Test queuing input audio"""
        audio_data = b"test_audio_data"
        
        conversation.queue_input_audio(audio_data)
        
        assert conversation.queued_input_audio == audio_data
    
    def test_get_item_exists(self, conversation):
        """Test getting an item that exists"""
        item = {"id": "item_1", "type": "message"}
        conversation.item_lookup["item_1"] = item
        
        result = conversation.get_item("item_1")
        
        assert result == item
    
    def test_get_item_not_exists(self, conversation):
        """Test getting an item that doesn't exist"""
        result = conversation.get_item("nonexistent")
        
        assert result is None
    
    def test_get_items(self, conversation):
        """Test getting all items"""
        items = [{"id": "1"}, {"id": "2"}]
        conversation.items = items
        
        result = conversation.get_items()
        
        assert result == items
        # Ensure it returns a copy
        assert result is not conversation.items
    
    def test_process_item_created_basic(self, conversation):
        """Test processing item.created event"""
        event = {
            "type": "conversation.item.created",
            "item": {
                "id": "item_1",
                "type": "message",
                "role": "user",
                "content": []
            }
        }
        
        item, delta = conversation.process_event(event)
        
        assert item is not None
        assert item["id"] == "item_1"
        assert "formatted" in item
        assert item["status"] == "completed"
        assert "item_1" in conversation.item_lookup
        assert item in conversation.items
    
    def test_process_item_created_with_text_content(self, conversation):
        """Test processing item.created with text content"""
        event = {
            "type": "conversation.item.created",
            "item": {
                "id": "item_1",
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hello"},
                    {"type": "text", "text": " World"}
                ]
            }
        }
        
        item, delta = conversation.process_event(event)
        
        assert item["formatted"]["text"] == "Hello World"
    
    def test_process_item_created_function_call(self, conversation):
        """Test processing item.created for function call"""
        event = {
            "type": "conversation.item.created",
            "item": {
                "id": "item_1",
                "type": "function_call",
                "name": "test_function",
                "call_id": "call_123"
            }
        }
        
        item, delta = conversation.process_event(event)
        
        assert item is not None
        assert item["status"] == "in_progress"
        assert "tool" in item["formatted"]
        assert item["formatted"]["tool"]["name"] == "test_function"
        assert item["formatted"]["tool"]["call_id"] == "call_123"
    
    def test_process_item_deleted(self, conversation):
        """Test processing item.deleted event"""
        # First create an item
        item = {"id": "item_1", "type": "message"}
        conversation.item_lookup["item_1"] = item
        conversation.items.append(item)
        
        event = {
            "type": "conversation.item.deleted",
            "item_id": "item_1"
        }
        
        deleted_item, delta = conversation.process_event(event)
        
        assert deleted_item == item
        assert "item_1" not in conversation.item_lookup
        assert item not in conversation.items
    
    def test_process_response_created(self, conversation):
        """Test processing response.created event"""
        event = {
            "type": "response.created",
            "response": {
                "id": "response_1",
                "status": "in_progress",
                "output": []
            }
        }
        
        item, delta = conversation.process_event(event)
        
        assert "response_1" in conversation.response_lookup
        assert conversation.response_lookup["response_1"] in conversation.responses
    
    def test_process_text_delta(self, conversation):
        """Test processing response.text.delta event"""
        # First create an item
        item = {
            "id": "item_1",
            "content": [{"type": "text", "text": "Hello"}],
            "formatted": {"text": "Hello"}
        }
        conversation.item_lookup["item_1"] = item
        
        event = {
            "type": "response.text.delta",
            "item_id": "item_1",
            "content_index": 0,
            "delta": " World"
        }
        
        result_item, delta = conversation.process_event(event)
        
        assert result_item["content"][0]["text"] == "Hello World"
        assert result_item["formatted"]["text"] == "Hello World"
        assert delta == {"text": " World"}
    
    def test_process_audio_transcript_delta(self, conversation):
        """Test processing response.audio_transcript.delta event"""
        # First create an item
        item = {
            "id": "item_1",
            "content": [{"type": "audio", "transcript": "Hello"}],
            "formatted": {"transcript": "Hello"}
        }
        conversation.item_lookup["item_1"] = item
        
        event = {
            "type": "response.audio_transcript.delta",
            "item_id": "item_1",
            "content_index": 0,
            "delta": " there"
        }
        
        result_item, delta = conversation.process_event(event)
        
        assert result_item["content"][0]["transcript"] == "Hello there"
        assert result_item["formatted"]["transcript"] == "Hello there"
        assert delta == {"transcript": " there"}
    
    def test_process_speech_started(self, conversation):
        """Test processing input_audio_buffer.speech_started event"""
        event = {
            "type": "input_audio_buffer.speech_started",
            "item_id": "item_1",
            "audio_start_ms": 1000
        }
        
        item, delta = conversation.process_event(event)
        
        assert "item_1" in conversation.queued_speech_items
        assert conversation.queued_speech_items["item_1"]["audio_start_ms"] == 1000
    
    def test_process_speech_stopped(self, conversation):
        """Test processing input_audio_buffer.speech_stopped event"""
        # First start speech
        conversation.queued_speech_items["item_1"] = {"audio_start_ms": 1000}
        
        # Create mock input audio buffer - use bytearray instead of numpy array
        # to match expected input format
        input_audio = bytearray([1, 2, 3, 4, 5, 6, 7, 8])
        
        event = {
            "type": "input_audio_buffer.speech_stopped",
            "item_id": "item_1",
            "audio_end_ms": 2000
        }
        
        item, delta = conversation.process_event(event, input_audio)
        
        assert "audio_end_ms" in conversation.queued_speech_items["item_1"]
        assert "audio" in conversation.queued_speech_items["item_1"]


class TestRealtimeClient:
    """Test RealtimeClient class"""
    
    @pytest.fixture
    def client(self):
        """Create a fresh RealtimeClient instance"""
        with patch.dict('os.environ', {
            'AZURE_OPENAI_ENDPOINT': 'wss://test.openai.azure.com',
            'AZURE_OPENAI_API_KEY': 'test_key',
            'AZURE_OPENAI_DEPLOYMENT': 'test_deployment'
        }):
            return RealtimeClient(system_prompt="Test prompt", max_tokens=2048)
    
    def test_initialization(self, client):
        """Test RealtimeClient initialization"""
        assert client.system_prompt == "Test prompt"
        assert client.max_tokens == 2048
        assert client.session_created is False
        assert client.tools == {}
    
    def test_default_session_config(self, client):
        """Test default session configuration"""
        assert "modalities" in client.session_config
        assert "instructions" in client.session_config
        assert "voice" in client.session_config
        assert client.session_config["instructions"] == "Test prompt"
        assert client.session_config["max_response_output_tokens"] == 2048
    
    def test_reset_config(self, client):
        """Test resetting configuration"""
        # Add some data
        client.session_created = True
        client.tools = {"tool1": {}}
        
        result = client._reset_config()
        
        assert result is True
        assert client.session_created is False
        assert client.tools == {}
    
    def test_is_connected_false(self, client):
        """Test is_connected when not connected"""
        assert client.is_connected() is False
    
    def test_get_turn_detection_type(self, client):
        """Test getting turn detection type"""
        client.session_config["turn_detection"] = {"type": "server_vad"}
        
        result = client.get_turn_detection_type()
        
        assert result == "server_vad"
    
    @pytest.mark.asyncio
    async def test_update_system_prompt(self, client):
        """Test updating system prompt"""
        client.update_session = AsyncMock()
        
        await client.update_system_prompt("New prompt")
        
        assert client.system_prompt == "New prompt"
        client.update_session.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_update_max_tokens(self, client):
        """Test updating max tokens"""
        client.update_session = AsyncMock()
        
        await client.update_max_tokens(8192)
        
        assert client.max_tokens == 8192
        client.update_session.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_update_config(self, client):
        """Test updating both system prompt and max tokens"""
        client.update_session = AsyncMock()
        
        await client.update_config(system_prompt="New prompt", max_tokens=4096)
        
        assert client.system_prompt == "New prompt"
        assert client.max_tokens == 4096
        client.update_session.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_add_tool_success(self, client):
        """Test adding a tool successfully"""
        client.update_session = AsyncMock()
        
        definition = {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {"type": "object"}
        }
        handler = Mock()
        
        result = await client.add_tool(definition, handler)
        
        assert "test_tool" in client.tools
        assert result["definition"] == definition
        assert result["handler"] == handler
        client.update_session.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_add_tool_missing_name(self, client):
        """Test adding a tool without name raises error"""
        definition = {"description": "No name"}
        handler = Mock()
        
        with pytest.raises(Exception, match="Missing tool name"):
            await client.add_tool(definition, handler)
    
    @pytest.mark.asyncio
    async def test_add_tool_duplicate(self, client):
        """Test adding duplicate tool raises error"""
        client.update_session = AsyncMock()
        
        definition = {"name": "test_tool", "description": "Test"}
        handler = Mock()
        
        await client.add_tool(definition, handler)
        
        # Try to add again
        with pytest.raises(Exception, match="already added"):
            await client.add_tool(definition, handler)
    
    @pytest.mark.asyncio
    async def test_add_tool_invalid_handler(self, client):
        """Test adding a tool with non-callable handler"""
        definition = {"name": "test_tool"}
        handler = "not_a_function"
        
        with pytest.raises(Exception, match="must be a function"):
            await client.add_tool(definition, handler)
    
    def test_remove_tool_success(self, client):
        """Test removing a tool successfully"""
        client.tools["test_tool"] = {"definition": {}, "handler": Mock()}
        
        result = client.remove_tool("test_tool")
        
        assert result is True
        assert "test_tool" not in client.tools
    
    def test_remove_tool_not_exists(self, client):
        """Test removing non-existent tool raises error"""
        with pytest.raises(Exception, match="does not exist"):
            client.remove_tool("nonexistent_tool")
    
    @pytest.mark.asyncio
    async def test_delete_item(self, client):
        """Test deleting a conversation item"""
        client.realtime.send = AsyncMock()
        
        await client.delete_item("item_123")
        
        client.realtime.send.assert_awaited_once()
        call_args = client.realtime.send.call_args
        assert call_args[0][0] == "conversation.item.delete"
        assert call_args[0][1]["item_id"] == "item_123"
