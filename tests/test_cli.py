"""CLI tests — --help, theme in all flag combinations, version (Phase 0 acceptance)."""
from typer.testing import CliRunner

from fieldshift import __version__
from fieldshift.cli import app

runner = CliRunner()


def test_help_exits_zero_and_lists_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "theme" in result.output
    assert "version" in result.output


def test_theme_prints_badges_words_and_symbols():
    for args in ([], ["--plain"], ["--ascii"], ["--plain", "--ascii"]):
        result = runner.invoke(app, [*args, "theme"])
        assert result.exit_code == 0, (args, result.output)
        out = result.output
        # badge words (DATA.md §0.2)
        for word in ("verified", "extracted", "general", "placeholder", "missing", "farmer"):
            assert word in out, (args, word)
        # palette roles and symbol names listed
        for role in ("brand", "muted", "nasa", "fao", "farmer", "estimate", "unknown"):
            assert role in out, (args, role)
        for sym in ("ok", "error", "warning", "extracted", "general", "farmer", "pointer", "back", "other", "progress"):
            assert sym in out, (args, sym)


def test_theme_ascii_shows_fallback_glyph_column():
    result = runner.invoke(app, ["--ascii", "theme"])
    assert result.exit_code == 0
    assert "ascii fallback" in result.output


def test_theme_respects_no_color_env(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    result = runner.invoke(app, ["theme"])
    assert result.exit_code == 0
    assert "NO_COLOR=set" in result.output


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output
