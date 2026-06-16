"""Tests for src/ragapp/ui/builder_tab.py and query_tab.py logic."""

import sys
from types import ModuleType
from unittest.mock import MagicMock


def _unstub_streamlit():
    """Remove cached streamlit so our mocks work."""
    sys.modules.pop("streamlit", None)
    if "ragapp.ui.builder_tab" in sys.modules:
        del sys.modules["ragapp.ui.builder_tab"]
    if "ragapp.ui.query_tab" in sys.modules:
        del sys.modules["ragapp.ui.query_tab"]


class TestBuilderTab:
    """Tests for render_builder function."""

    def test_file_size_check(self):
        _unstub_streamlit()
        st = ModuleType("streamlit")
        mock_vs = MagicMock()
        st.session_state = {"vector_store": mock_vs}
        st.file_uploader = MagicMock(return_value=[MagicMock(name="big.pdf", size=60 * 1024 * 1024)])
        st.button = MagicMock(side_effect=[True, False])
        st.error = MagicMock()
        st.spinner = MagicMock(context_enter=MagicMock(return_value=MagicMock()), context_exit=MagicMock())
        sys.modules["streamlit"] = st

        from ragapp.ui.builder_tab import render_builder
        render_builder(mock_vs)
        st.error.assert_called()


class TestQueryTabLogic:
    """Tests for query_tab logic paths."""

    def test_empty_db_warning(self):
        _unstub_streamlit()
        st = ModuleType("streamlit")
        st.warning = MagicMock()
        st.info = MagicMock()
        st.page_link = MagicMock()
        st.text_input = MagicMock(return_value="test query")
        st.button = MagicMock(return_value=False)
        sys.modules["streamlit"] = st

        from ragapp.ui.query_tab import render_query_tab
        mock_vs = MagicMock()
        mock_vs.get_collection_size.return_value = 0
        render_query_tab(mock_vs, "gpt-4o-mini")
        assert st.warning.call_count >= 1

    def test_query_not_called_when_no_results(self):
        _unstub_streamlit()
        st = ModuleType("streamlit")
        mock_vs = MagicMock()
        mock_vs.get_collection_size.return_value = 5
        mock_vs.query = MagicMock(return_value=[])
        st.text_input = MagicMock(return_value="test")
        st.button = MagicMock(return_value=True)
        st.spinner = MagicMock(context_enter=MagicMock(return_value=MagicMock()), context_exit=MagicMock())
        st.header = MagicMock()
        st.info = MagicMock()
        sys.modules["streamlit"] = st

        from ragapp.ui.query_tab import render_query_tab
        render_query_tab(mock_vs, "gpt-4o-mini")
        assert mock_vs.query.call_count == 1

    def test_context_retrieved(self):
        _unstub_streamlit()
        st = ModuleType("streamlit")
        mock_vs = MagicMock()
        mock_vs.get_collection_size.return_value = 5
        mock_results = [{"text": "Context A", "metadata": {"source": "a.txt", "page": 1}}]
        mock_vs.query = MagicMock(return_value=mock_results)
        st.text_input = MagicMock(return_value="What is this?")
        st.button = MagicMock(return_value=True)
        st.spinner = MagicMock(context_enter=MagicMock(return_value=MagicMock()), context_exit=MagicMock())
        st.header = MagicMock()
        st.subheader = MagicMock()
        st.write = MagicMock()
        st.divider = MagicMock()
        st.expander = MagicMock(context_enter=MagicMock(return_value=MagicMock()), context_exit=MagicMock())
        st.caption = MagicMock()
        st.download_button = MagicMock()
        sys.modules["streamlit"] = st

        mock_llm_mod = ModuleType("ragapp.core.llm")
        mock_llm_mod.get_llm_response = MagicMock(return_value="AI Answer")
        sys.modules["ragapp.core.llm"] = mock_llm_mod

        from ragapp.ui.query_tab import render_query_tab
        render_query_tab(mock_vs, "gpt-4o-mini")

        assert mock_vs.query.called
