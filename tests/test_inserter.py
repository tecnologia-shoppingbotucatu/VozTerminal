"""Testes para o inserter multiplataforma."""

import sys
import pytest
from unittest.mock import patch, MagicMock

from vozterminal.inserter import (
    LinuxInserter,
    WindowsInserter,
    TextInserter,
)


class TestLinuxInserter:
    """Testes para o LinuxInserter (xdotool)."""

    def test_empty_text_returns_true(self):
        inserter = LinuxInserter(typing_delay_ms=12)
        assert inserter.insert("") is True

    @patch("vozterminal.inserter.subprocess.run")
    def test_insert_calls_xdotool(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        inserter = LinuxInserter(typing_delay_ms=12)
        assert inserter.insert("hello") is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "xdotool" in args[0]
        assert "type" in args
        assert "hello" in args

    @patch("vozterminal.inserter.subprocess.run")
    def test_insert_failure_returns_false(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        inserter = LinuxInserter(typing_delay_ms=12)
        assert inserter.insert("hello") is False

    @patch("vozterminal.inserter.subprocess.run")
    def test_insert_with_newline(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        inserter = LinuxInserter(typing_delay_ms=12)
        assert inserter.insert_with_newline("hello") is True
        assert mock_run.call_count == 2  # type + key Return


class TestTextInserterSelection:
    """Testa seleção automática de plataforma."""

    def test_linux_selects_linux_inserter(self):
        with patch.object(sys, "platform", "linux"):
            inserter = TextInserter(typing_delay_ms=12)
            assert isinstance(inserter._impl, LinuxInserter)

    def test_win32_selects_windows_inserter(self):
        with patch.object(sys, "platform", "win32"):
            inserter = TextInserter(typing_delay_ms=12)
            assert isinstance(inserter._impl, WindowsInserter)

    def test_darwin_selects_linux_inserter(self):
        """macOS usa LinuxInserter como fallback (xdotool não existe mas é o default não-Windows)."""
        with patch.object(sys, "platform", "darwin"):
            inserter = TextInserter(typing_delay_ms=12)
            assert isinstance(inserter._impl, LinuxInserter)

    def test_facade_delegates_insert(self):
        """Verifica que TextInserter delega para a implementação."""
        with patch.object(sys, "platform", "linux"):
            inserter = TextInserter(typing_delay_ms=12)
            inserter._impl = MagicMock()
            inserter._impl.insert.return_value = True
            assert inserter.insert("test") is True
            inserter._impl.insert.assert_called_once_with("test")

    def test_facade_delegates_insert_with_newline(self):
        with patch.object(sys, "platform", "linux"):
            inserter = TextInserter(typing_delay_ms=12)
            inserter._impl = MagicMock()
            inserter._impl.insert_with_newline.return_value = True
            assert inserter.insert_with_newline("test") is True
            inserter._impl.insert_with_newline.assert_called_once_with("test")


class TestWindowsInserter:
    """Testes para o WindowsInserter (sem precisar de Windows real)."""

    def test_empty_text_returns_true(self):
        inserter = WindowsInserter(typing_delay_ms=12)
        assert inserter.insert("") is True
