from pathlib import Path

import pytest

from agents.agentv3 import system_prompt_utils
from agents.agentv3.system_prompt_utils import render_system_prompt


def test_render_system_prompt_defaults_missing_enable_flags_to_false(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    template_path = tmp_path / "system_prompt.md"
    config_path.write_text(
        """
tools:
  web_search:
    enabled: true
""",
        encoding="utf-8",
    )
    template_path.write_text(
        """
{%- if enable_web_search %}web enabled{% endif %}
{%- if enable_audio_asr %}audio enabled{% endif %}
""",
        encoding="utf-8",
    )

    rendered = render_system_prompt(
        config_path=str(config_path),
        template_path=str(template_path),
    )

    assert "web enabled" in rendered
    assert "audio enabled" not in rendered


def test_render_system_prompt_keeps_unknown_non_enable_variables_strict(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    template_path = tmp_path / "system_prompt.md"
    config_path.write_text("tools: {}\n", encoding="utf-8")
    template_path.write_text("{{ missing_variable }}", encoding="utf-8")

    with pytest.raises(ValueError, match="'missing_variable' is undefined"):
        render_system_prompt(
            config_path=str(config_path),
            template_path=str(template_path),
        )


def test_render_system_prompt_clips_oversized_user_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class CharacterTokenCounter:
        def count_tokens(self, text: str) -> int:
            return len(text)

    monkeypatch.setattr(
        system_prompt_utils,
        "LocalTokenCounter",
        lambda: CharacterTokenCounter(),
        raising=False,
    )

    config_path = tmp_path / "conf.yaml"
    template_path = tmp_path / "system_prompt.md"
    user_profile_path = tmp_path / "user_profile.md"
    config_path.write_text("tools: {}\n", encoding="utf-8")
    template_path.write_text("{{ USER_PROFILE }}", encoding="utf-8")
    user_profile_path.write_text("a" * 2005 + "TAIL_SHOULD_BE_REMOVED", encoding="utf-8")

    rendered = render_system_prompt(
        config_path=str(config_path),
        template_path=str(template_path),
        user_profile_path=str(user_profile_path),
    )

    assert "TAIL_SHOULD_BE_REMOVED" not in rendered
    assert f"...[内容已截断] 完整内容查看: {user_profile_path}" in rendered
