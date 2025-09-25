"""MCP Tool Tracer - For testing LLM tool calls without execution."""

from collections.abc import Callable
from typing import Any


class MockedMCPServer:
    """A utility class that mocks tool calls for MCP tools.

    It records which tools are called, with what parameters,
    and can verify expectations about tool usage.
    """

    def __init__(self):
        """Initialize the tool tracer with empty call history."""
        self.tool_calls = []
        self.current_call_index = 0
        self.mock_responses = {}

    def invoke_tool(self, tool_name: str, **parameters) -> Any:
        """Mock invoking a tool by recording the call and returning a mock response.

        Args:
            tool_name: The name of the tool to invoke
            **parameters: Parameters to pass to the tool

        Returns:
            A mock response for the tool
        """
        return self.get_mock_response(tool_name, parameters)

    def record_tool_call(self, tool_name: str, parameters: dict[str, Any]) -> None:
        """Record a tool call with its parameters.

        Args:
            tool_name: Name of the tool being called
            parameters: Parameters passed to the tool
        """
        self.tool_calls.append(
            {"tool_name": tool_name, "parameters": parameters, "call_index": self.current_call_index}
        )
        self.current_call_index += 1

    def register_mock_response(
        self, tool_name: str, parameters_matcher: dict[str, Any] | Callable, response: Any
    ) -> None:
        """Register a mock response for a specific tool and parameter pattern.

        Args:
            tool_name: Name of the tool
            parameters_matcher: Either a dictionary of expected parameters or
                               a callable that takes parameters and returns bool
            response: The mock response to return
        """
        if tool_name not in self.mock_responses:
            self.mock_responses[tool_name] = []

        self.mock_responses[tool_name].append({"matcher": parameters_matcher, "response": response})

    def get_mock_response(self, tool_name: str, parameters: dict[str, Any]) -> Any:
        """Get a mock response for a tool call based on registered responses.

        Args:
            tool_name: Name of the tool
            parameters: Parameters passed to the tool

        Returns:
            The mock response if one matches, otherwise a default response
        """
        # Record the call
        self.record_tool_call(tool_name, parameters)

        # Find a matching response
        if tool_name in self.mock_responses:
            for mock in self.mock_responses[tool_name]:
                matcher = mock["matcher"]
                if callable(matcher):
                    if matcher(parameters):
                        return mock["response"]
                else:
                    # Direct dictionary comparison
                    if all(key in parameters and parameters[key] == value for key, value in matcher.items()):
                        return mock["response"]

        # Default response if no match
        return {"status": "success", "message": f"Default mock response for {tool_name}"}

    def get_called_tool_names(self) -> list[str]:
        """Get a list of all tool names that were called.

        Returns:
            List of unique tool names that were called
        """
        return list({call["tool_name"] for call in self.tool_calls})

    def get_calls_for_tool(self, tool_name: str) -> list[dict[str, Any]]:
        """Get all calls for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            List of calls to the specified tool
        """
        return [call for call in self.tool_calls if call["tool_name"] == tool_name]
