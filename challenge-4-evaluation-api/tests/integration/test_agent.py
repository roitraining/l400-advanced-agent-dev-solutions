import importlib
import sys


def _load_agent_module(prompt_style: str):
    """Reload the agent module so env-based prompt style is applied fresh."""
    import os

    os.environ["CYMBAL_PROMPT_STYLE"] = prompt_style

    module_name = "cymbal_support_agent.agent"
    if module_name in sys.modules:
        return importlib.reload(sys.modules[module_name])
    return importlib.import_module(module_name)


def test_simple_prompt_style_uses_simple_instructions() -> None:
    agent_module = _load_agent_module("simple")

    assert "friendly, practical, and customer-focused" in agent_module.ACTIVE_INSTRUCTIONS
    assert "What not to do:" not in agent_module.ACTIVE_INSTRUCTIONS


def test_detailed_prompt_style_uses_detailed_instructions() -> None:
    agent_module = _load_agent_module("detailed")

    assert "What to do:" in agent_module.ACTIVE_INSTRUCTIONS
    assert "What not to do:" in agent_module.ACTIVE_INSTRUCTIONS
    assert "Do not claim to escalate to a human team." in agent_module.ACTIVE_INSTRUCTIONS


def test_policy_reference_is_embedded_in_active_instructions() -> None:
    agent_module = _load_agent_module("detailed")

    assert "Policy 6. Electronics" in agent_module.ACTIVE_INSTRUCTIONS
    assert "Policy 14. Cancellation" in agent_module.ACTIVE_INSTRUCTIONS
    assert agent_module.root_agent.name == "cymbal_customer_service_agent"
