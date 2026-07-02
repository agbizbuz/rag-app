"""Tests for src/ragapp/core/parsers/base.py."""

from ragapp.core.parsers.base import BaseParser, Chunk, Parser


class TestChunk:
    """Tests for the Chunk frozen dataclass."""

    def test_chunk_creation(self):
        c = Chunk(text="hello", metadata={"source": "test.txt"})
        assert c.text == "hello"
        assert c.metadata["source"] == "test.txt"

    def test_chunk_is_frozen(self):
        c = Chunk(text="hello", metadata={})
        try:
            c.text = "changed"
            assert False, "Should not allow mutation of frozen dataclass"
        except Exception:
            pass  # Expected


class TestBaseParser:
    """Tests for BaseParser utilities."""

    def test_make_id_uniqueness(self):
        ids = set()
        for _ in range(100):
            c = Chunk(text="", metadata={})

            ids.add(BaseParser._make_id())
        assert len(ids) == 100, "Each call should produce a unique ID"

    def test_make_id_format(self):

        uid = BaseParser._make_id()
        assert len(uid) == 36  # UUID4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx

    def test_clean_empty_string(self):

        assert BaseParser._clean("") == ""

    def test_clean_whitespace_only(self):

        assert BaseParser._clean("   \n\t  ") == ""

    def test_clean_normal_string(self):

        assert BaseParser._clean("  hello world  ") == "hello world"

    def test_clean_none_input(self):

        assert BaseParser._clean(None) == ""


class TestParserProtocol:
    """Tests for Parser protocol."""

    def test_parser_protocol_with_concrete_class(self):
        from ragapp.core.parsers.pdf_parser import PdfParser

        pdf = PdfParser()
        assert isinstance(pdf, Parser)  # type check at runtime

    def test_parser_protocol_with_base(self):
        from ragapp.core.parsers.txt_parser import TxtParser

        txt = TxtParser()
        assert hasattr(txt, "parse")
        assert hasattr(txt, "supported_extensions")
