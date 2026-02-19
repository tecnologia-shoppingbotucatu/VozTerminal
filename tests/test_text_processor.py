"""Testes para o TextProcessor."""

import pytest
from pathlib import Path
from vozterminal.text_processor import TextProcessor
from vozterminal.dictionary import Dictionary


@pytest.fixture
def tmp_dict(tmp_path):
    """Cria dicionário temporário para testes."""
    dict_file = tmp_path / "dictionary.json"
    snippets_file = tmp_path / "snippets.json"

    dict_file.write_text('{"pitom": "Python", "java script": "JavaScript"}')
    snippets_file.write_text('{"git commit": "git commit -m \\"\\""}')

    return Dictionary(dict_file, snippets_file)


@pytest.fixture
def processor(tmp_dict):
    return TextProcessor(dictionary=tmp_dict)


@pytest.fixture
def processor_no_dict():
    return TextProcessor()


class TestRemoveFillers:
    def test_remove_ee(self, processor_no_dict):
        result = processor_no_dict.process("éé então eu quero")
        assert "éé" not in result
        assert "então" in result.lower()

    def test_remove_hum(self, processor_no_dict):
        result = processor_no_dict.process("hum deixa eu ver")
        assert "hum" not in result.lower()

    def test_remove_tipo(self, processor_no_dict):
        result = processor_no_dict.process("tipo eu quero fazer isso")
        assert result.strip().lower().startswith("eu")

    def test_remove_multiple_fillers(self, processor_no_dict):
        result = processor_no_dict.process("éé hum tipo assim eu quero")
        assert "eu quero" in result.lower()


class TestPunctuation:
    def test_ponto(self, processor_no_dict):
        result = processor_no_dict.process("olá mundo ponto")
        assert result.rstrip().endswith(".")

    def test_virgula(self, processor_no_dict):
        result = processor_no_dict.process("primeiro vírgula segundo")
        assert "," in result

    def test_interrogacao(self, processor_no_dict):
        result = processor_no_dict.process("como vai interrogação")
        assert "?" in result

    def test_nova_linha(self, processor_no_dict):
        result = processor_no_dict.process("linha um nova linha linha dois")
        assert "\n" in result


class TestDictionary:
    def test_replace_pitom(self, processor):
        result = processor.process("eu uso pitom")
        assert "Python" in result

    def test_replace_javascript(self, processor):
        result = processor.process("eu gosto de java script")
        assert "JavaScript" in result


class TestSnippets:
    def test_expand_snippet(self, processor):
        result = processor.process("snippet git commit")
        assert 'git commit -m ""' == result


class TestAutoCapitalize:
    def test_capitalize_first(self, processor_no_dict):
        result = processor_no_dict.process("olá mundo")
        assert result[0] == "O"

    def test_capitalize_after_period(self, processor_no_dict):
        result = processor_no_dict.process("olá ponto mundo")
        # Deve ser "Olá. Mundo" ou similar
        assert ". M" in result or ". m" not in result


class TestEmptyInput:
    def test_empty_string(self, processor_no_dict):
        assert processor_no_dict.process("") == ""

    def test_only_fillers(self, processor_no_dict):
        result = processor_no_dict.process("éé hum")
        assert result.strip() == ""
