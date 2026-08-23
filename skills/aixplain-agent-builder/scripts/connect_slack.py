#!/usr/bin/env python3
"""Create a least-privilege Slack OAuth tool and return its authorization URL."""

from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone

from aixplain import Aixplain


SLACK_INTEGRATION_ID = "686432941223092cb4294d3f"
ALLOWED_ACTIONS = [
    "SLACK_FIND_CHANNELS",
    "SLACK_FETCH_CONVERSATION_HISTORY",
    "SLACK_FETCH_MESSAGE_THREAD_FROM_A_CONVERSATION",
    "SLACK_CHAT_POST_MESSAGE",
]


def main() -> None:
    aix = Aixplain()
    integration = aix.Integration.get(SLACK_INTEGRATION_ID)
    available_actions = {action.name for action in integration.list_actions()}
    missing = set(ALLOWED_ACTIONS) - available_actions
    if missing:
        raise RuntimeError(f"Slack integration is missing required actions: {sorted(missing)}")

    suffix = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S-UTC")
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        tool = aix.Tool(
            name=f"Renewal Risk Slack {suffix}",
            description=(
                "Finds Slack channels, reads channel history and threads, and posts "
                "renewal-risk messages. It cannot delete messages or administer Slack."
            ),
            integration=integration,
            allowed_actions=ALLOWED_ACTIONS,
        ).save()

    connect_url = next(
        (str(item.message) for item in captured if "http" in str(item.message)),
        None,
    )
    print(
        json.dumps(
            {
                "status": "AUTHORIZATION_REQUIRED" if connect_url else "CREATED",
                "tool_id": tool.id,
                "tool_name": tool.name,
                "allowed_actions": list(tool.allowed_actions or []),
                "connect_url": connect_url,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
