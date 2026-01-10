"""Test CLI entry point."""

from src import cli


def test_cli_module_imports() -> None:
    """Verify CLI module can be imported."""
    assert hasattr(cli, "main")


def test_cli_main_is_callable() -> None:
    """Verify main function is callable."""
    assert callable(cli.main)
