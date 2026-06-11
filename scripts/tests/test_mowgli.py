"""Tests for mowgli package."""
import json
import subprocess
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from mowgli.config import (
    MowgliConfig,
    ModelSpec,
    load_config,
    _DEFAULT_MODELS,
    MODELS_FILE,
)
from mowgli.providers import get_provider
from mowgli.providers.base import StreamState, StreamEvent, ProviderResult
from mowgli.providers.claude import ClaudeProvider
from mowgli.providers.gemini import GeminiProvider
from mowgli.repl import MowgliREPL, _tool_icon, _format_tool_input
from mowgli.branding import _get_project_name


# ═══════════════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════════════

class TestModelSpec:
    def test_create(self):
        spec = ModelSpec(alias="opus", provider="claude", model_id="claude-opus-4-6", cli_binary="/usr/bin/claude")
        assert spec.alias == "opus"
        assert spec.provider == "claude"

    def test_missing_field_raises(self):
        with pytest.raises(TypeError):
            ModelSpec(alias="opus", provider="claude")


class TestMowgliConfig:
    def test_resolve_known_model(self):
        config = load_config()
        spec = config.resolve_model("sonnet")
        assert spec.alias == "sonnet"
        assert spec.provider == "claude"

    def test_resolve_unknown_raises(self):
        config = load_config()
        with pytest.raises(ValueError, match="Unknown model"):
            config.resolve_model("nonexistent")

    def test_all_defaults_present(self):
        config = load_config()
        for alias in ("opus", "sonnet", "haiku", "gemini-pro", "gemini-lite"):
            spec = config.resolve_model(alias)
            assert spec.provider in ("claude", "gemini")

    def test_default_model_is_sonnet(self):
        config = load_config()
        assert config.default_model == "sonnet"

    def test_user_overrides(self, tmp_path):
        override = {
            "default_model": "custom",
            "models": {
                "custom": {
                    "alias": "custom",
                    "provider": "claude",
                    "model_id": "custom-model",
                    "cli_binary": "/usr/bin/claude",
                }
            },
        }
        override_file = tmp_path / "models.json"
        override_file.write_text(json.dumps(override))

        with patch("mowgli.config.MODELS_FILE", override_file):
            config = load_config()
            assert config.default_model == "custom"
            spec = config.resolve_model("custom")
            assert spec.model_id == "custom-model"
            # Defaults still available
            assert "sonnet" in config.models


# ═══════════════════════════════════════════════════════════════════════════════
# Providers
# ═══════════════════════════════════════════════════════════════════════════════

class TestProviderFactory:
    def test_get_claude(self):
        p = get_provider("claude")
        assert p.name == "claude"

    def test_get_gemini(self):
        p = get_provider("gemini")
        assert p.name == "gemini"

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("openai")


class TestStreamState:
    def test_initial_state(self):
        state = StreamState()
        assert state.printed_text_len == 0
        assert len(state.seen_tool_ids) == 0
        assert state.last_char_newline is True

    def test_reset(self):
        state = StreamState()
        state.printed_text_len = 100
        state.seen_tool_ids.add("t1")
        state.reset()
        assert state.printed_text_len == 0
        assert len(state.seen_tool_ids) == 0


class TestClaudeProvider:
    @pytest.fixture
    def provider(self):
        return ClaudeProvider()

    @pytest.fixture
    def state(self):
        return StreamState()

    # ── Args building ──

    def test_new_session_args(self, provider):
        args = provider.build_headless_args("hello", "claude-sonnet-4-6", "sess-1", resume=False)
        assert "--session-id" in args
        assert "sess-1" in args
        assert "--resume" not in args
        assert "--verbose" in args

    def test_resume_args(self, provider):
        args = provider.build_headless_args("hello", "claude-sonnet-4-6", "sess-1", resume=True)
        assert "--resume" in args
        assert "--session-id" not in args

    def test_include_partial(self, provider):
        args = provider.build_headless_args("hello", "claude-sonnet-4-6", "sess-1", include_partial=True)
        assert "--include-partial-messages" in args

    def test_no_partial(self, provider):
        args = provider.build_headless_args("hello", "claude-sonnet-4-6", "sess-1", include_partial=False)
        assert "--include-partial-messages" not in args

    # ── Event parsing ──

    def test_parse_init_captures_session(self, provider, state):
        line = json.dumps({"type": "system", "subtype": "init", "session_id": "abc"})
        ev = provider.parse_stream_line(line, state)
        assert ev is None
        assert state.session_id == "abc"

    def test_parse_text_delta(self, provider, state):
        line = json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello"}]}})
        ev = provider.parse_stream_line(line, state)
        assert ev is not None
        assert ev.type == "text_delta"
        assert ev.content == "Hello"
        assert state.printed_text_len == 5

    def test_parse_text_incremental(self, provider, state):
        line1 = json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello"}]}})
        line2 = json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello World"}]}})
        provider.parse_stream_line(line1, state)
        ev = provider.parse_stream_line(line2, state)
        assert ev.content == " World"
        assert state.printed_text_len == 11

    def test_parse_no_new_text_returns_none(self, provider, state):
        line = json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello"}]}})
        provider.parse_stream_line(line, state)
        ev = provider.parse_stream_line(line, state)
        assert ev is None

    def test_parse_tool_use(self, provider, state):
        line = json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "x.py"}}
        ]}})
        ev = provider.parse_stream_line(line, state)
        assert ev.type == "tool_use"
        assert ev.tool_name == "Read"

    def test_parse_duplicate_tool_ignored(self, provider, state):
        line = json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Read", "input": {}}
        ]}})
        provider.parse_stream_line(line, state)
        ev = provider.parse_stream_line(line, state)
        assert ev is None

    def test_parse_thinking_ignored(self, provider, state):
        line = json.dumps({"type": "assistant", "message": {"content": [{"type": "thinking", "thinking": "hmm"}]}})
        ev = provider.parse_stream_line(line, state)
        assert ev is None

    def test_parse_result_cost(self, provider, state):
        line = json.dumps({"type": "result", "total_cost_usd": 0.01})
        ev = provider.parse_stream_line(line, state)
        assert ev.type == "cost"
        assert ev.cost_usd == 0.01

    def test_parse_invalid_json(self, provider, state):
        ev = provider.parse_stream_line("not json {", state)
        assert ev is None

    def test_parse_unknown_type(self, provider, state):
        line = json.dumps({"type": "rate_limit_event"})
        ev = provider.parse_stream_line(line, state)
        assert ev is None

    def test_parse_tool_result(self, provider, state):
        line = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": [{"type": "text", "text": "file contents"}]}
        ]}})
        ev = provider.parse_stream_line(line, state)
        assert ev.type == "tool_result"
        assert "file contents" in ev.content

    def test_parse_tool_result_string_content(self, provider, state):
        line = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "raw string result"}
        ]}})
        ev = provider.parse_stream_line(line, state)
        assert ev.content == "raw string result"


class TestGeminiProvider:
    @pytest.fixture
    def provider(self):
        return GeminiProvider()

    @pytest.fixture
    def state(self):
        return StreamState()

    def test_new_session_args(self, provider):
        args = provider.build_headless_args("hello", "gemini-2.5-pro", "sess-1", resume=False)
        assert "--session-id" in args
        assert "-o" in args

    def test_resume_uses_latest(self, provider):
        args = provider.build_headless_args("hello", "gemini-2.5-pro", "sess-1", resume=True)
        idx = args.index("--resume")
        assert args[idx + 1] == "latest"

    def test_parse_text(self, provider, state):
        line = json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Hi"}]}})
        ev = provider.parse_stream_line(line, state)
        assert ev.type == "text_delta"
        assert ev.content == "Hi"

    def test_parse_top_level_text(self, provider, state):
        line = json.dumps({"type": "text", "text": "Top level"})
        ev = provider.parse_stream_line(line, state)
        assert ev.type == "text_delta"

    def test_parse_result(self, provider, state):
        line = json.dumps({"type": "result", "total_cost_usd": 0.003})
        ev = provider.parse_stream_line(line, state)
        assert ev.type == "cost"


# ═══════════════════════════════════════════════════════════════════════════════
# REPL utilities
# ═══════════════════════════════════════════════════════════════════════════════

class TestToolDisplay:
    def test_known_icon(self):
        assert _tool_icon("Read") == "📄"
        assert _tool_icon("Bash") == "⚡"

    def test_unknown_icon(self):
        assert _tool_icon("CustomTool") == "⚙"

    def test_format_read(self):
        assert _format_tool_input("Read", {"file_path": "/a/b.py"}) == "/a/b.py"

    def test_format_bash(self):
        assert _format_tool_input("Bash", {"command": "echo hi"}) == "echo hi"

    def test_format_bash_truncated(self):
        long_cmd = "x" * 100
        result = _format_tool_input("Bash", {"command": long_cmd})
        assert len(result) <= 81  # 80 + ellipsis

    def test_format_grep(self):
        result = _format_tool_input("Grep", {"pattern": "TODO", "path": "src/"})
        assert "TODO" in result

    def test_format_empty(self):
        assert _format_tool_input("Read", {}) == ""


class TestREPLSlashCommands:
    @pytest.fixture
    def repl(self):
        return MowgliREPL(model_alias="haiku")

    def test_exit(self, repl):
        assert repl._handle_slash("/exit") is False

    def test_quit(self, repl):
        assert repl._handle_slash("/quit") is False

    def test_help(self, repl):
        assert repl._handle_slash("/help") is True

    def test_models(self, repl):
        assert repl._handle_slash("/models") is True

    def test_cost(self, repl):
        assert repl._handle_slash("/cost") is True

    def test_clear_resets_session(self, repl):
        old_id = repl.session_id
        repl.turn = 5
        repl._handle_slash("/clear")
        assert repl.session_id != old_id
        assert repl.turn == 0

    def test_model_switch(self, repl):
        repl._handle_slash("/model opus")
        assert repl.model_spec.alias == "opus"
        assert repl.provider.name == "claude"
        assert repl.turn == 0

    def test_model_switch_gemini(self, repl):
        repl._handle_slash("/model gemini-pro")
        assert repl.model_spec.alias == "gemini-pro"
        assert repl.provider.name == "gemini"

    def test_model_switch_invalid(self, repl):
        old_alias = repl.model_spec.alias
        repl._handle_slash("/model doesnotexist")
        assert repl.model_spec.alias == old_alias  # unchanged

    def test_model_no_arg(self, repl):
        assert repl._handle_slash("/model") is True

    def test_unknown_command(self, repl):
        assert repl._handle_slash("/foobar") is True


# ═══════════════════════════════════════════════════════════════════════════════
# Branding
# ═══════════════════════════════════════════════════════════════════════════════

class TestBranding:
    def test_get_project_name_returns_string(self):
        name = _get_project_name()
        assert isinstance(name, str)
        assert len(name) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic models
# ═══════════════════════════════════════════════════════════════════════════════

class TestPydanticModels:
    def test_provider_result(self):
        r = ProviderResult(text="hello", cost_usd=0.01)
        assert r.text == "hello"

    def test_stream_event(self):
        ev = StreamEvent(type="text_delta", content="hi")
        assert ev.type == "text_delta"
        assert ev.tool_name is None

    def test_stream_event_tool(self):
        ev = StreamEvent(type="tool_use", tool_name="Read", tool_input={"path": "x"})
        assert ev.tool_name == "Read"


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Manager
# ═══════════════════════════════════════════════════════════════════════════════

class TestMCPManager:
    @pytest.fixture
    def global_json(self, tmp_path):
        """A temp global.json with two servers, one disabled."""
        data = {
            "plugins": {"higgsfield@claude-plugins-official": True},
            "servers": {
                "graphify": {"command": "graphify", "args": ["serve", "--transport", "stdio"]},
            },
            "_disabled_servers": {
                "notebooklm": {"command": "npx", "args": ["notebooklm-mcp@latest"]},
            },
        }
        f = tmp_path / "global.json"
        f.write_text(json.dumps(data))
        return f

    def _patch(self, global_json):
        """Context manager that patches GLOBAL_JSON and ACTIVATE_PY."""
        import mowgli.mcp_manager as mm
        from unittest.mock import patch as _patch, MagicMock
        return _patch.multiple(
            mm,
            GLOBAL_JSON=global_json,
            _sync=MagicMock(),  # don't actually call activate.py in tests
        )

    def test_list_servers(self, global_json):
        import mowgli.mcp_manager as mm
        with patch.object(mm, "GLOBAL_JSON", global_json), \
             patch.object(mm, "_sync", lambda: None):
            servers = mm.list_servers()
        names = {s.name: s.enabled for s in servers}
        assert names["graphify"] is True
        assert names["notebooklm"] is False

    def test_enable_server(self, global_json):
        import mowgli.mcp_manager as mm
        with patch.object(mm, "GLOBAL_JSON", global_json), \
             patch.object(mm, "_sync", lambda: None):
            msg = mm.enable_server("notebooklm")
            servers = mm.list_servers()
        assert "enabled" in msg
        names = {s.name: s.enabled for s in servers}
        assert names["notebooklm"] is True

    def test_enable_already_enabled(self, global_json):
        import mowgli.mcp_manager as mm
        with patch.object(mm, "GLOBAL_JSON", global_json), \
             patch.object(mm, "_sync", lambda: None):
            msg = mm.enable_server("graphify")
        assert "already enabled" in msg

    def test_disable_server(self, global_json):
        import mowgli.mcp_manager as mm
        with patch.object(mm, "GLOBAL_JSON", global_json), \
             patch.object(mm, "_sync", lambda: None):
            msg = mm.disable_server("graphify")
            servers = mm.list_servers()
        assert "disabled" in msg
        names = {s.name: s.enabled for s in servers}
        assert names["graphify"] is False

    def test_disable_already_disabled(self, global_json):
        import mowgli.mcp_manager as mm
        with patch.object(mm, "GLOBAL_JSON", global_json), \
             patch.object(mm, "_sync", lambda: None):
            msg = mm.disable_server("notebooklm")
        assert "already disabled" in msg

    def test_unknown_server(self, global_json):
        import mowgli.mcp_manager as mm
        with patch.object(mm, "GLOBAL_JSON", global_json), \
             patch.object(mm, "_sync", lambda: None):
            msg = mm.enable_server("nonexistent")
        assert "Unknown" in msg

    def test_enable_persists_to_json(self, global_json):
        import mowgli.mcp_manager as mm
        with patch.object(mm, "GLOBAL_JSON", global_json), \
             patch.object(mm, "_sync", lambda: None):
            mm.enable_server("notebooklm")
        data = json.loads(global_json.read_text())
        assert "notebooklm" in data["servers"]
        assert "notebooklm" not in data.get("_disabled_servers", {})

    def test_disable_persists_to_json(self, global_json):
        import mowgli.mcp_manager as mm
        with patch.object(mm, "GLOBAL_JSON", global_json), \
             patch.object(mm, "_sync", lambda: None):
            mm.disable_server("graphify")
        data = json.loads(global_json.read_text())
        assert "graphify" not in data["servers"]
        assert "graphify" in data["_disabled_servers"]


# ═══════════════════════════════════════════════════════════════════════════════
# REPL /mcp command
# ═══════════════════════════════════════════════════════════════════════════════

class TestREPLMcpCommand:
    @pytest.fixture
    def repl(self):
        return MowgliREPL(model_alias="haiku")

    def test_mcp_slash_returns_true(self, repl):
        import mowgli.mcp_manager as mm
        from unittest.mock import patch as _patch, MagicMock
        mock_servers = [mm.MCPServer("graphify", "graphify", [], True)]
        with _patch.object(mm, "list_servers", return_value=mock_servers):
            result = repl._handle_slash("/mcp")
        assert result is True

    def test_mcp_on_slash(self, repl):
        import mowgli.mcp_manager as mm
        from unittest.mock import patch as _patch
        with _patch.object(mm, "enable_server", return_value="✓ 'x' enabled.") as mock_enable:
            repl._handle_slash("/mcp on x")
            mock_enable.assert_called_once_with("x")

    def test_mcp_off_slash(self, repl):
        import mowgli.mcp_manager as mm
        from unittest.mock import patch as _patch
        with _patch.object(mm, "disable_server", return_value="✓ 'x' disabled.") as mock_disable:
            repl._handle_slash("/mcp off x")
            mock_disable.assert_called_once_with("x")


# ═══════════════════════════════════════════════════════════════════════════════
# Spinner callback
# ═══════════════════════════════════════════════════════════════════════════════

class TestSpinner:
    def test_on_first_output_called_on_text_delta(self):
        """on_first_output callback fires on first text_delta event."""
        import json as _json
        from mowgli.providers.base import StreamState
        from mowgli.providers.claude import ClaudeProvider
        from unittest.mock import MagicMock, patch
        import subprocess
        import io

        provider = ClaudeProvider()
        state = StreamState()

        events = [
            _json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Hi"}]}}),
            _json.dumps({"type": "result", "total_cost_usd": 0.001}),
        ]
        fake_stdout = io.StringIO("\n".join(events) + "\n")

        callback = MagicMock()

        repl = MowgliREPL(model_alias="haiku")

        class FakeProc:
            stdout = fake_stdout
            stderr = io.StringIO("")
            returncode = 0
            def wait(self): pass

        cost = repl._stream_response(FakeProc(), state, on_first_output=callback)
        callback.assert_called_once()
        assert cost == 0.001

    def test_on_first_output_not_called_if_no_output(self):
        """on_first_output not called if subprocess emits no meaningful events."""
        import json as _json
        from mowgli.providers.base import StreamState
        from unittest.mock import MagicMock
        import io

        state = StreamState()
        fake_stdout = io.StringIO(_json.dumps({"type": "system", "subtype": "init", "session_id": "x"}) + "\n")

        repl = MowgliREPL(model_alias="haiku")

        class FakeProc:
            stdout = fake_stdout
            stderr = io.StringIO("")
            returncode = 0
            def wait(self): pass

        callback = MagicMock()
        repl._stream_response(FakeProc(), state, on_first_output=callback)
        callback.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════════════════

class TestCLI:
    def test_help(self):
        result = subprocess.run(["mowgli", "--help"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "Mowgli Studio" in result.stdout

    def test_models_command(self):
        result = subprocess.run(["mowgli", "models"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "sonnet" in result.stdout
        assert "opus" in result.stdout

    def test_mcp_help(self):
        result = subprocess.run(["mowgli", "mcp", "--help"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "on" in result.stdout
        assert "off" in result.stdout

    def test_mcp_list(self):
        result = subprocess.run(["mowgli", "mcp"], capture_output=True, text=True)
        assert result.returncode == 0
