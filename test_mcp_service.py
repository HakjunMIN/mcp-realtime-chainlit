#!/usr/bin/env python3
"""
Unit tests for mcp_service.py
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from mcp_service import MCPServerClient, MCPService, MCPTool


class TestMCPTool:
    """Test MCPTool dataclass"""
    
    def test_mcp_tool_creation(self):
        """Test creating an MCPTool instance"""
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object", "properties": {}}
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert isinstance(tool.parameters, dict)


class TestMCPServerClient:
    """Test MCPServerClient class"""
    
    @pytest.fixture
    def client(self):
        """Create a fresh MCPServerClient instance"""
        return MCPServerClient()
    
    def test_initialization(self, client):
        """Test MCPServerClient initialization"""
        assert client.servers == {}
        assert client.tools == {}
        assert client.processes == {}
    
    @pytest.mark.asyncio
    async def test_start_server_invalid_config(self, client):
        """Test starting server with invalid config"""
        config = {}  # Missing command
        
        with pytest.raises(Exception):
            await client.start_server("test_server", config)
    
    @pytest.mark.asyncio
    async def test_send_request(self, client):
        """Test sending JSON-RPC request"""
        # Create a mock process
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdin.write = Mock()
        mock_process.stdin.drain = AsyncMock()
        
        request = {"jsonrpc": "2.0", "id": 1, "method": "test"}
        
        await client._send_request(mock_process, request)
        
        # Verify write was called with JSON + newline
        expected_data = (json.dumps(request) + "\n").encode()
        mock_process.stdin.write.assert_called_once_with(expected_data)
        mock_process.stdin.drain.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_read_response_valid(self, client):
        """Test reading valid JSON-RPC response"""
        mock_process = Mock()
        response_data = {"jsonrpc": "2.0", "id": 1, "result": "success"}
        response_line = (json.dumps(response_data) + "\n").encode()
        
        mock_process.stdout = Mock()
        mock_process.stdout.readline = AsyncMock(return_value=response_line)
        
        result = await client._read_response(mock_process)
        
        assert result == response_data
    
    @pytest.mark.asyncio
    async def test_read_response_empty(self, client):
        """Test reading empty response"""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stdout.readline = AsyncMock(return_value=b"")
        
        result = await client._read_response(mock_process)
        
        assert result is None
    
    def test_get_tools_for_openai_empty(self, client):
        """Test getting OpenAI format tools when no tools exist"""
        result = client.get_tools_for_openai()
        
        assert result == []
    
    def test_get_tools_for_openai_with_tools(self, client):
        """Test getting OpenAI format tools with existing tools"""
        client.tools = {
            "tool1": {
                "server": "server1",
                "name": "tool1",
                "description": "Test tool 1",
                "parameters": {"type": "object"}
            },
            "tool2": {
                "server": "server1",
                "name": "tool2",
                "description": "Test tool 2",
                "parameters": {"type": "object"}
            }
        }
        
        result = client.get_tools_for_openai()
        
        assert len(result) == 2
        assert all("name" in tool for tool in result)
        assert all("description" in tool for tool in result)
        assert all("parameters" in tool for tool in result)
    
    @pytest.mark.asyncio
    async def test_call_tool_not_found(self, client):
        """Test calling a tool that doesn't exist"""
        with pytest.raises(Exception, match="Tool .* not found"):
            await client.call_tool("nonexistent_tool", {}, "call_1")
    
    @pytest.mark.asyncio
    async def test_call_tool_server_not_running(self, client):
        """Test calling a tool when server is not running"""
        client.tools["test_tool"] = {
            "server": "test_server",
            "name": "test_tool",
            "description": "Test",
            "parameters": {}
        }
        
        with pytest.raises(Exception, match="Server .* not running"):
            await client.call_tool("test_tool", {}, "call_1")
    
    @pytest.mark.asyncio
    async def test_shutdown_no_servers(self, client):
        """Test shutdown with no active servers"""
        await client.shutdown()
        
        assert len(client.processes) == 0
        assert len(client.tools) == 0
    
    @pytest.mark.asyncio
    async def test_shutdown_with_servers(self, client):
        """Test shutdown with active servers"""
        # Add mock processes
        mock_process1 = Mock()
        mock_process1.terminate = Mock()
        mock_process1.wait = AsyncMock()
        
        mock_process2 = Mock()
        mock_process2.terminate = Mock()
        mock_process2.wait = AsyncMock()
        
        client.processes = {
            "server1": mock_process1,
            "server2": mock_process2
        }
        client.tools = {"tool1": {}, "tool2": {}}
        
        await client.shutdown()
        
        mock_process1.terminate.assert_called_once()
        mock_process2.terminate.assert_called_once()
        mock_process1.wait.assert_awaited_once()
        mock_process2.wait.assert_awaited_once()
        
        assert len(client.processes) == 0
        assert len(client.tools) == 0


class TestMCPService:
    """Test MCPService class"""
    
    @pytest.fixture
    def service(self):
        """Create a fresh MCPService instance"""
        return MCPService()
    
    def test_initialization(self, service):
        """Test MCPService initialization"""
        assert service.initialized is False
        assert isinstance(service.client, MCPServerClient)
    
    @pytest.mark.asyncio
    async def test_initialize_once(self, service):
        """Test that initialize can be called and sets initialized flag"""
        # Mock the client's start_server method
        service.client.start_server = AsyncMock()
        
        await service.initialize()
        
        assert service.initialized is True
    
    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, service):
        """Test that initialize is idempotent (can be called multiple times)"""
        service.client.start_server = AsyncMock()
        
        # First call
        await service.initialize()
        first_call_count = service.client.start_server.call_count
        
        # Second call should not start servers again
        await service.initialize()
        second_call_count = service.client.start_server.call_count
        
        assert first_call_count == second_call_count
    
    @pytest.mark.asyncio
    async def test_get_tool_response_auto_initialize(self, service):
        """Test that get_tool_response auto-initializes if needed"""
        service.client.start_server = AsyncMock()
        service.client.call_tool = AsyncMock(return_value={"result": "success"})
        
        result = await service.get_tool_response("test_tool", {}, "call_1")
        
        assert service.initialized is True
        service.client.call_tool.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_get_tool_response_error_handling(self, service):
        """Test error handling in get_tool_response"""
        service.initialized = True
        service.client.call_tool = AsyncMock(side_effect=Exception("Tool call failed"))
        
        result = await service.get_tool_response("test_tool", {}, "call_1")
        
        assert "error" in result
        assert "Tool call failed" in result["error"]
    
    def test_get_tools_for_openai_not_initialized(self, service):
        """Test getting tools when service is not initialized"""
        result = service.get_tools_for_openai()
        
        assert result == []
    
    def test_get_tools_for_openai_initialized(self, service):
        """Test getting tools when service is initialized"""
        service.initialized = True
        service.client.get_tools_for_openai = Mock(return_value=[
            {"name": "tool1", "description": "Test tool"}
        ])
        
        result = service.get_tools_for_openai()
        
        assert len(result) == 1
        service.client.get_tools_for_openai.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown(self, service):
        """Test shutdown method"""
        service.initialized = True
        service.client.shutdown = AsyncMock()
        
        await service.shutdown()
        
        assert service.initialized is False
        service.client.shutdown.assert_awaited_once()
