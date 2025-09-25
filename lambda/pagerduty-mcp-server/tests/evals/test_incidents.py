"""Tests for incident-related competency questions."""

from .competency_test import CompetencyTest, MockedMCPServer


class IncidentCompetencyTest(CompetencyTest):
    """Specialization of CompetencyTest for incident-related queries."""

    def register_mock_responses(self, mcp: MockedMCPServer) -> None:
        """Register minimal realistic responses to enable multi-turn conversations."""
        mcp.register_mock_response(
            "list_teams", lambda params: True, {"response": [{"id": "TEAM123", "name": "Dev Team"}]}
        )
        mcp.register_mock_response(
            "list_services", lambda params: True, {"response": [{"id": "SVC123", "name": "Web Service"}]}
        )


# Define the competency test cases
INCIDENT_COMPETENCY_TESTS = [
    IncidentCompetencyTest(
        query="Show me all incidents",
        expected_tools=[{"tool_name": "list_incidents", "parameters": {}}],
        description="Basic incident listing",
    ),
    IncidentCompetencyTest(
        query="Show me all triggered incidents",
        expected_tools=[{"tool_name": "list_incidents", "parameters": {"query_model": {"status": ["triggered"]}}}],
        description="List incidents filtered by status",
    ),
    IncidentCompetencyTest(
        query="Tell me about incident 123",
        expected_tools=[{"tool_name": "get_incident", "parameters": {"incident_id": "123"}}],
        description="Get specific incident by number",
    ),
    IncidentCompetencyTest(
        query="Create an incident with title 'Testing MCP' for service with ID 1234 with high urgency",
        expected_tools=[
            {
                "tool_name": "create_incident",
                "parameters": {
                    "create_model": {
                        "incident": {
                            "title": "Testing MCP",
                            "service": {"id": "1234"},
                        }
                    }
                },
            }
        ],
        description="Create incident for team (allows team lookup)",
    ),
    IncidentCompetencyTest(
        query="Create a high urgency incident titled 'Server down' for the Website service",
        expected_tools=[
            {
                "tool_name": "create_incident",
                "parameters": {"create_model": {"incident": {"title": "Server down", "urgency": "high"}}},
            }
        ],
        description="Create incident for service (allows service lookup)",
    ),
    IncidentCompetencyTest(
        query="Acknowledge incident 456",
        expected_tools=[
            {
                "tool_name": "manage_incidents",
                "parameters": {"manage_request": {"incident_ids": ["456"], "status": "acknowledged"}},
            }
        ],
        description="Acknowledge specific incident",
    ),
]
