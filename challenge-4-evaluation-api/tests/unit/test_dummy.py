# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import importlib
import os
import sys


def _load_agent_module(prompt_style: str | None = None):
    """Reload the agent module so env-driven prompt selection is deterministic."""
    module_name = "cymbal_support_agent.agent"

    if prompt_style is None:
        os.environ.pop("CYMBAL_PROMPT_STYLE", None)
    else:
        os.environ["CYMBAL_PROMPT_STYLE"] = prompt_style

    if module_name in sys.modules:
        return importlib.reload(sys.modules[module_name])
    return importlib.import_module(module_name)


def test_prompt_style_defaults_to_simple() -> None:
    agent_module = _load_agent_module(None)

    assert agent_module.PROMPT_STYLE == "simple"
    assert agent_module.ACTIVE_INSTRUCTIONS == agent_module.SIMPLE_INSTRUCTIONS


def test_prompt_style_detailed_selected() -> None:
    agent_module = _load_agent_module("detailed")

    assert agent_module.PROMPT_STYLE == "detailed"
    assert agent_module.ACTIVE_INSTRUCTIONS == agent_module.DETAILED_INSTRUCTIONS


def test_detailed_instructions_contain_negative_rules() -> None:
    agent_module = _load_agent_module("detailed")

    assert "What not to do:" in agent_module.ACTIVE_INSTRUCTIONS
    assert "Do not claim to escalate to a human team." in agent_module.ACTIVE_INSTRUCTIONS
    assert "Do not ask for full payment card numbers" in agent_module.ACTIVE_INSTRUCTIONS
