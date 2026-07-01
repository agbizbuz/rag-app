"""Tests for src/ragapp/ui/db_tab.py -- DB info tab rendering and delete flow."""

import sys
from types import ModuleType
from unittest.mock import MagicMock


def _unstub_streamlit():
    """Remove cached streamlit so our mocks work."""
    sys.modules.pop("streamlit", None)
    if "ragapp.ui.db_tab" in sys.modules:
        del sys.modules["ragapp.ui.db_tab"]


class TestDbTabEmptyDB:
    """Tests for render_db_tab when the database is empty."""

    def test_info_message_when_empty(self):
        _unstub_streamlit()
        st = ModuleType("streamlit")
        st.info = MagicMock()
        st.header = MagicMock()
        st.metric = MagicMock()
        st.write = MagicMock()
        st.markdown = MagicMock()
        st.button = MagicMock(return_value=False)

        def _columns(n):
            if isinstance(n, list):
                return [MagicMock() for _ in n]
            return [MagicMock() for _ in range(n)]

        st.columns = MagicMock(side_effect=_columns)

        mock_vs = MagicMock()
        mock_vs.get_collection_size.return_value = 0
        mock_vs._ensure_collection = MagicMock()
        st.session_state = {"confirm_delete": False}
        sys.modules["streamlit"] = st

        from ragapp.ui.db_tab import render_db_tab

        render_db_tab(mock_vs)
        st.info.assert_called_once()
        assert "empty" in str(st.info.call_args).lower()


class TestDbTabWithDocuments:
    """Tests for render_db_tab when documents are present."""

    def test_displays_pdf_doc(self):
        _unstub_streamlit()
        st = ModuleType("streamlit")
        st.header = MagicMock()
        st.metric = MagicMock()
        st.write = MagicMock()
        st.dataframe = MagicMock()
        st.markdown = MagicMock()
        st.button = MagicMock(return_value=False)

        def _columns(n):
            if isinstance(n, list):
                return [MagicMock() for _ in n]
            return [MagicMock() for _ in range(n)]

        st.columns = MagicMock(side_effect=_columns)

        mock_vs = MagicMock()
        mock_vs.get_collection_size.return_value = 2
        mock_vs._ensure_collection = MagicMock()
        mock_vs.collection_name = "test_col"
        mock_vs.db_path = "./chroma_db"
        mock_vs.get_all_documents.return_value = [
            {
                "id": "abc12345",
                "text": "Page 1 content of document.pdf",
                "metadata": {"source": "document.pdf", "page": 1},
            },
            {
                "id": "def67890",
                "text": "Row A,B,C from data.csv",
                "metadata": {"source": "data.csv", "row": 2},
            },
        ]
        st.session_state = {"confirm_delete": False}
        sys.modules["streamlit"] = st

        from ragapp.ui.db_tab import render_db_tab

        render_db_tab(mock_vs)

        assert st.dataframe.called
        df_call = st.dataframe.call_args[0][0]
        sources = list(df_call["source"])
        assert "document.pdf" in sources
        assert "data.csv" in sources
        types_list = list(df_call["type"])
        assert "PDF" in types_list
        assert "CSV" in types_list

    def test_displays_txt_and_docx(self):
        _unstub_streamlit()
        st = ModuleType("streamlit")
        st.header = MagicMock()
        st.metric = MagicMock()
        st.write = MagicMock()
        st.dataframe = MagicMock()
        st.markdown = MagicMock()
        st.button = MagicMock(return_value=False)

        def _columns(n):
            if isinstance(n, list):
                return [MagicMock() for _ in n]
            return [MagicMock() for _ in range(n)]

        st.columns = MagicMock(side_effect=_columns)

        mock_vs = MagicMock()
        mock_vs.get_collection_size.return_value = 2
        mock_vs._ensure_collection = MagicMock()
        mock_vs.collection_name = "test_col"
        mock_vs.db_path = "./chroma_db"
        mock_vs.get_all_documents.return_value = [
            {
                "id": "aaaa1111",
                "text": "Line 1 of readme.txt\nLine 2",
                "metadata": {"source": "readme.txt", "chunk": 0},
            },
            {
                "id": "bbbb2222",
                "text": "Heading: Introduction",
                "metadata": {"source": "report.docx", "paragraph": 5},
            },
        ]
        st.session_state = {"confirm_delete": False}
        sys.modules["streamlit"] = st

        from ragapp.ui.db_tab import render_db_tab

        render_db_tab(mock_vs)

        assert st.dataframe.called
        df_call = st.dataframe.call_args[0][0]
        types_list = list(df_call["type"])
        assert "TXT" in types_list
        assert "DOCX" in types_list
        locations = list(df_call["location"])
        assert any("Chunk" in loc for loc in locations)
        assert any("Paragraph" in loc for loc in locations)


class TestDbTabDeleteFlow:
    """Tests for the database delete confirmation flow."""

    def test_delete_confirmation_sets_flag(self):
        _unstub_streamlit()
        st = ModuleType("streamlit")
        st.header = MagicMock()
        st.metric = MagicMock()
        st.write = MagicMock()
        st.dataframe = MagicMock()
        st.markdown = MagicMock()
        st.warning = MagicMock()

        def _columns(n):
            if isinstance(n, list):
                return [MagicMock() for _ in n]
            return [MagicMock() for _ in range(n)]

        st.columns = MagicMock(side_effect=_columns)
        st.toast = MagicMock()

        mock_vs = MagicMock()
        mock_vs.get_collection_size.return_value = 10
        mock_vs._ensure_collection = MagicMock()
        mock_vs.collection_name = "test_col"
        mock_vs.db_path = "./chroma_db"
        mock_vs.get_all_documents.return_value = [
            {
                "id": "cccc3333",
                "text": "Some content",
                "metadata": {"source": "file.pdf", "page": 1},
            },
        ]

        # First render: "Clear Database" button clicked
        st.button = MagicMock(return_value=True)
        st.session_state = {"confirm_delete": False, "vector_store": MagicMock()}
        sys.modules["streamlit"] = st

        from ragapp.ui.db_tab import render_db_tab

        render_db_tab(mock_vs)
        assert st.session_state["confirm_delete"] is True

        # Second render: confirm delete button clicked (side_effect[0] = True)
        mock_vs.delete_collection = MagicMock()
        st.button.reset_mock()
        st.button.side_effect = [True]  # Confirm Delete pressed
        render_db_tab(mock_vs)

        mock_vs.delete_collection.assert_called_once()
        assert st.session_state["confirm_delete"] is False
        assert st.toast.called
