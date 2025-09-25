from pydantic import BaseModel

from pagerduty_mcp.models.users import User


class MCPContext(BaseModel):
    user: User | None
