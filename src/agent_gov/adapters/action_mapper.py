"""Pure mapping functions that convert framework-specific action parameters
into the generic action dictionaries expected by PolicyEvaluator.

Each function is a pure, stateless transformation — no side effects, no I/O.
"""
from __future__ import annotations


def map_langchain_prompt(prompt: str) -> dict[str, object]:
    """Map a LangChain prompt string to a policy action dictionary.

    Parameters
    ----------
    prompt:
        Raw prompt text to evaluate.

    Returns
    -------
    dict[str, object]
        Contains ``action_type``, ``content``, and ``content_length``.
    """
    return {
        "action_type": "langchain_prompt",
        "content": prompt,
        "content_length": len(prompt),
    }


def map_langchain_tool_call(
    tool_name: str,
    args: dict[str, object],
) -> dict[str, object]:
    """Map a LangChain tool call to a policy action dictionary.

    Parameters
    ----------
    tool_name:
        Name of the tool being invoked.
    args:
        Keyword arguments passed to the tool.

    Returns
    -------
    dict[str, object]
        Contains ``action_type``, ``tool_name``, ``args``, and ``arg_count``.
    """
    return {
        "action_type": "langchain_tool_call",
        "tool_name": tool_name,
        "args": args,
        "arg_count": len(args),
    }


def map_crewai_task(
    task_description: str,
    agent_role: str,
) -> dict[str, object]:
    """Map a CrewAI task to a policy action dictionary.

    Parameters
    ----------
    task_description:
        Human-readable description of the task to execute.
    agent_role:
        The role label of the agent executing the task.

    Returns
    -------
    dict[str, object]
        Contains ``action_type``, ``task_description``, ``agent_role``,
        and ``content_length``.
    """
    return {
        "action_type": "crewai_task",
        "task_description": task_description,
        "agent_role": agent_role,
        "content_length": len(task_description),
    }


def map_crewai_delegation(
    from_agent: str,
    to_agent: str,
) -> dict[str, object]:
    """Map a CrewAI agent-to-agent delegation to a policy action dictionary.

    Parameters
    ----------
    from_agent:
        Role or name of the delegating agent.
    to_agent:
        Role or name of the receiving agent.

    Returns
    -------
    dict[str, object]
        Contains ``action_type``, ``from_agent``, and ``to_agent``.
    """
    return {
        "action_type": "crewai_delegation",
        "from_agent": from_agent,
        "to_agent": to_agent,
    }


def map_openai_message(role: str, content: str) -> dict[str, object]:
    """Map an OpenAI Agents SDK message to a policy action dictionary.

    Parameters
    ----------
    role:
        Message role (e.g. ``"user"``, ``"assistant"``, ``"system"``).
    content:
        Message text content.

    Returns
    -------
    dict[str, object]
        Contains ``action_type``, ``role``, ``content``, and
        ``content_length``.
    """
    return {
        "action_type": "openai_message",
        "role": role,
        "content": content,
        "content_length": len(content),
    }


def map_anthropic_message(role: str, content: str) -> dict[str, object]:
    """Map an Anthropic SDK message to a policy action dictionary.

    Parameters
    ----------
    role:
        Message role (e.g. ``"user"``, ``"assistant"``).
    content:
        Message text content.

    Returns
    -------
    dict[str, object]
        Contains ``action_type``, ``role``, ``content``, and
        ``content_length``.
    """
    return {
        "action_type": "anthropic_message",
        "role": role,
        "content": content,
        "content_length": len(content),
    }


def map_microsoft_activity(activity_type: str, text: str) -> dict[str, object]:
    """Map a Microsoft Bot Framework activity to a policy action dictionary.

    Parameters
    ----------
    activity_type:
        Bot Framework activity type (e.g. ``"message"``, ``"event"``).
    text:
        Text payload of the activity.

    Returns
    -------
    dict[str, object]
        Contains ``action_type``, ``activity_type``, ``text``, and
        ``content_length``.
    """
    return {
        "action_type": "microsoft_activity",
        "activity_type": activity_type,
        "text": text,
        "content_length": len(text),
    }
