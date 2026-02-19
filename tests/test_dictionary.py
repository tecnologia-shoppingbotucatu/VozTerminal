"""Testes para o Dictionary."""

import json
import pytest
from vozterminal.dictionary import Dictionary


@pytest.fixture
def tmp_dict(tmp_path):
    """Cria dicionário vazio temporário."""
    dict_file = tmp_path / "dictionary.json"
    snippets_file = tmp_path / "snippets.json"
    return Dictionary(dict_file, snippets_file)


@pytest.fixture
def populated_dict(tmp_path):
    """Cria dicionário com dados pré-existentes."""
    dict_file = tmp_path / "dictionary.json"
    snippets_file = tmp_path / "snippets.json"

    dict_file.write_text(json.dumps({"pitom": "Python", "jsson": "JSON"}))
    snippets_file.write_text(json.dumps({"git commit": "git commit -m \"\""}))

    return Dictionary(dict_file, snippets_file)


class TestReplacements:
    def test_add_replacement(self, tmp_dict):
        tmp_dict.add_replacement("pitom", "Python")
        replacements = tmp_dict.get_replacements()
        assert ("pitom", "Python") in replacements

    def test_remove_replacement(self, tmp_dict):
        tmp_dict.add_replacement("pitom", "Python")
        assert tmp_dict.remove_replacement("pitom") is True
        assert tmp_dict.get_replacements() == []

    def test_remove_nonexistent(self, tmp_dict):
        assert tmp_dict.remove_replacement("nao_existe") is False

    def test_case_insensitive_add(self, tmp_dict):
        tmp_dict.add_replacement("Pitom", "Python")
        replacements = dict(tmp_dict.get_replacements())
        assert "pitom" in replacements

    def test_load_existing(self, populated_dict):
        replacements = dict(populated_dict.get_replacements())
        assert replacements["pitom"] == "Python"
        assert replacements["jsson"] == "JSON"


class TestSnippets:
    def test_add_snippet(self, tmp_dict):
        tmp_dict.add_snippet("git push", "git push origin main")
        assert tmp_dict.get_snippet("git push") == "git push origin main"

    def test_case_insensitive_snippet(self, tmp_dict):
        tmp_dict.add_snippet("Git Push", "git push origin main")
        assert tmp_dict.get_snippet("git push") == "git push origin main"

    def test_remove_snippet(self, tmp_dict):
        tmp_dict.add_snippet("git push", "git push origin main")
        assert tmp_dict.remove_snippet("git push") is True
        assert tmp_dict.get_snippet("git push") is None

    def test_remove_nonexistent_snippet(self, tmp_dict):
        assert tmp_dict.remove_snippet("nao_existe") is False

    def test_list_snippets(self, populated_dict):
        snippets = populated_dict.list_snippets()
        assert "git commit" in snippets

    def test_load_existing_snippets(self, populated_dict):
        assert populated_dict.get_snippet("git commit") == 'git commit -m ""'


class TestPromptHint:
    def test_empty_dict_hint(self, tmp_dict):
        assert tmp_dict.get_prompt_hint() == ""

    def test_populated_hint(self, populated_dict):
        hint = populated_dict.get_prompt_hint()
        assert "Python" in hint
        assert "JSON" in hint

    def test_hint_format(self, populated_dict):
        hint = populated_dict.get_prompt_hint()
        assert hint.startswith("Termos comuns: ")


class TestPersistence:
    def test_dict_saved_to_file(self, tmp_path):
        dict_file = tmp_path / "dictionary.json"
        snippets_file = tmp_path / "snippets.json"
        d = Dictionary(dict_file, snippets_file)
        d.add_replacement("teste", "Teste")

        # Recarrega
        d2 = Dictionary(dict_file, snippets_file)
        replacements = dict(d2.get_replacements())
        assert replacements["teste"] == "Teste"

    def test_snippets_saved_to_file(self, tmp_path):
        dict_file = tmp_path / "dictionary.json"
        snippets_file = tmp_path / "snippets.json"
        d = Dictionary(dict_file, snippets_file)
        d.add_snippet("hello", "print('hello')")

        d2 = Dictionary(dict_file, snippets_file)
        assert d2.get_snippet("hello") == "print('hello')"
