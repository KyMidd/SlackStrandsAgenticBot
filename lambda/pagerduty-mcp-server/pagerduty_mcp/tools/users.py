from pagerduty_mcp.client import get_client
from pagerduty_mcp.models import ListResponseModel, User, UserQuery


def get_user_data() -> User:
    """Get the current user's data.

    Returns:
        User: User name, role, id, and summary and teams
    """
    response = get_client().rget("/users/me")
    return User.model_validate(response)


def list_users(
    query: str | None = None, teams_ids: list[str] | None = None, limit: int | None = None
) -> ListResponseModel[User]:
    """List users, optionally filtering by name (query) and team IDs.

    Args:
        query (str, optional): Filter users by name.
        teams_ids (list[str], optional): Filter users by team IDs.
        limit (int, optional): Pagination limit.

    Returns:
        List[User]: List of users matching the criteria.
    """
    user_query = UserQuery(query=query, teams_ids=teams_ids, limit=limit)
    response = get_client().rget("/users", params=user_query.to_params())
    users = [User(**user) for user in response]
    return ListResponseModel[User](response=users)
