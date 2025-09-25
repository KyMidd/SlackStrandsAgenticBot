"""Common test fixtures for MCP tool call evaluation."""

from abc import ABC, abstractmethod
from typing import Any

from deepdiff import DeepDiff

from .mcp_tool_tracer import MockedMCPServer


class CompetencyTest(ABC):
    """A base class for competency tests that helps define and verify expected tool calls."""

    def __init__(
        self,
        query: str,
        expected_tools: list[dict[str, Any]],
        allowed_helper_tools: list[str] | None = None,
        description: str | None = None,
        max_conversation_turns: int = 5,
        model: str = "gpt-4.1",
    ):
        """Initialize a competency test case.

        Args:
            query: The user query to test
            expected_tools: List of expected tool calls with parameters
            allowed_helper_tools: List of tool names that are allowed to be called
            description: Optional description of the test case
            max_conversation_turns: Maximum number of conversation turns allowed
            model: The model to use for the test (default: "gpt-4.1")
        """
        self.query = query
        self.expected_tools = expected_tools
        self.allowed_helper_tools = allowed_helper_tools
        self.description = description or query
        self.max_conversation_turns = max_conversation_turns
        self.model = model

    @abstractmethod
    def register_mock_responses(self, mcp: MockedMCPServer) -> None:
        """Register mock responses for the expected tool calls.

        This is a placeholder method - implementations should
        override this with domain-specific mock responses.

        Args:
            mcp: The tool tracer to register responses with
        """

    def verify_tool_calls(self, mcp: MockedMCPServer) -> bool:
        """Verify that the expected incident tools were called correctly."""
        # Check that all expected incident tools were called
        for expected in self.expected_tools:
            tool_name = expected["tool_name"]
            expected_params = expected.get("parameters", {})

            if not self._verify_tool_called(mcp, tool_name, expected_params):
                print(f"Expected tool {tool_name} was not called correctly")
                return False

        # Check that no disallowed tools were called
        if self.allowed_helper_tools:
            all_called_tools = mcp.get_called_tool_names()
            expected_tool_names = {tool["tool_name"] for tool in self.expected_tools}
            allowed_tools = set(self.allowed_helper_tools) | expected_tool_names

            for tool_name in all_called_tools:
                if tool_name not in allowed_tools:
                    print(f"Disallowed tool {tool_name} was called")
                    return False
        return True

    def _verify_tool_called(self, mcp: MockedMCPServer, tool_name: str, expected_params: dict[str, Any]) -> bool:
        """Verify a tool was called with expected parameters."""
        actual_calls = mcp.get_calls_for_tool(tool_name)
        if not actual_calls:
            return False

        return any(self._params_are_compatible(expected_params, call["parameters"]) for call in actual_calls)

    def _params_are_compatible(self, expected: dict[str, Any], actual: dict[str, Any]) -> bool:
        """Check if actual parameters are compatible with expected ones.

        Compatible means:
        1. All expected fields are present with correct values
        2. Additional fields in actual are allowed (flexible)
        3. Nested objects are checked

        Args:
            expected: Expected parameter structure
            actual: Actual parameters from LLM call

        Returns:
            True if parameters are compatible
        """
        diff = DeepDiff(expected, actual, ignore_order=True)

        compatibility_issues = []

        # Missing keys/values (these break compatibility)
        # Storing the details in case we want to log them
        if "dictionary_item_removed" in diff:
            compatibility_issues.extend(diff["dictionary_item_removed"])
        if "iterable_item_removed" in diff:
            compatibility_issues.extend(diff["iterable_item_removed"])
        if "values_changed" in diff:
            compatibility_issues.extend(
                [f"{k}: {v['old_value']} -> {v['new_value']}" for k, v in diff["values_changed"].items()]
            )
        if "type_changes" in diff:
            compatibility_issues.extend(
                [f"{k}: {v['old_type']} -> {v['new_type']}" for k, v in diff["type_changes"].items()]
            )

        return len(compatibility_issues) == 0
