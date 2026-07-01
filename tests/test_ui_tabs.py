"""Tests for src/ragapp/ui/builder_tab.py and query_tab.py logic."""

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch


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
        mock_retriever = MagicMock()
        mock_retriever.vector_store = mock_vs

        render_query_tab(mock_retriever, "gpt-4o-mini")
        assert st.warning.call_count >= 1

    def test_query_not_called_when_no_results(self):
        _unstub_streamlit()
        st = ModuleType("streamlit")
        mock_vs = MagicMock()
        mock_vs.get_collection_size.return_value = 5
        mock_retriever = MagicMock()
        mock_retriever.vector_store = mock_vs
        mock_retriever.retrieve = MagicMock(return_value=[])

        st.text_input = MagicMock(return_value="test")
        st.button = MagicMock(return_value=True)
        st.spinner = MagicMock(context_enter=MagicMock(return_value=MagicMock()), context_exit=MagicMock())
        st.header = MagicMock()
        st.info = MagicMock()
        st.session_state = {
            "_selected_provider_index": 0,
            "_selected_model": "gpt-4o-mini",
            "_temp_slider": None,
        }
        sys.modules["streamlit"] = st

        from ragapp.ui.query_tab import render_query_tab

        render_query_tab(mock_retriever, "gpt-4o-mini")
        assert mock_retriever.retrieve.call_count == 1

    @patch("ragapp.core.evaluator.EvaluationManager")
    @patch("ragapp.core.evaluator.EvaluationRecord")
    def test_context_retrieved(self, mock_record_cls, mock_manager_cls):
        _unstub_streamlit()
        
        mock_record = MagicMock()
        mock_record.avg_distance = 0.0
        mock_record.record_id = "test-id"
        mock_record_cls.return_value = mock_record

        st = ModuleType("streamlit")
        mock_vs = MagicMock()
        mock_vs.get_collection_size.return_value = 5
        mock_results = [{"text": "Context A", "metadata": {"source": "a.txt", "page": 1}}]
        mock_retriever = MagicMock()
        mock_retriever.vector_store = mock_vs
        mock_retriever.retrieve = MagicMock(return_value=mock_results)
        mock_retriever.format_context = MagicMock(return_value="Context A")

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
        st.columns = MagicMock(side_effect=lambda n: [MagicMock() for _ in range(n)])
        st.metric = MagicMock()
        st.toast = MagicMock()
        st.rerun = MagicMock()
        st.markdown = MagicMock()
        st.error = MagicMock()
        st.session_state = {
            "_selected_provider_index": 0,
            "_selected_model": "gpt-4o-mini",
            "_temp_slider": None,
            "last_query_result": {
                "record_id": "test-id",
                "query": "What is this?",
                "answer": "AI Answer",
                "model": "gpt-4o-mini",
                "latency": 1.0,
                "avg_distance": 0.0,
                "num_chunks": 1,
                "results": mock_results,
            }
        }
        sys.modules["streamlit"] = st

        mock_llm_mod = ModuleType("ragapp.core.llm")
        mock_llm_mod.get_llm_response = MagicMock(return_value="AI Answer")
        sys.modules["ragapp.core.llm"] = mock_llm_mod

        from ragapp.ui.query_tab import render_query_tab

        render_query_tab(mock_retriever, "gpt-4o-mini")

        assert mock_retriever.retrieve.called

    @patch("ragapp.core.evaluator.EvaluationManager")
    @patch("ragapp.core.evaluator.EvaluationRecord")
    def test_feedback_thumbs_up(self, mock_record_cls, mock_manager_cls):
        _unstub_streamlit()
        
        mock_record = MagicMock()
        mock_record.avg_distance = 0.0
        mock_record.record_id = "test-id"
        mock_record_cls.return_value = mock_record

        mock_eval_manager = MagicMock()
        mock_manager_cls.return_value = mock_eval_manager

        st = ModuleType("streamlit")
        mock_vs = MagicMock()
        mock_vs.get_collection_size.return_value = 5
        mock_results = [{"text": "Context A", "metadata": {"source": "a.txt", "page": 1}}]
        mock_retriever = MagicMock()
        mock_retriever.vector_store = mock_vs
        mock_retriever.retrieve = MagicMock(return_value=mock_results)
        mock_retriever.format_context = MagicMock(return_value="Context A")

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
        st.columns = MagicMock(side_effect=lambda n: [MagicMock() for _ in range(n)])
        st.metric = MagicMock()
        st.toast = MagicMock()
        st.rerun = MagicMock()
        st.markdown = MagicMock()
        st.error = MagicMock()
        
        # st.feedback returns 1 for thumbs_up
        st.feedback = MagicMock(return_value=1)
        
        st.session_state = {
            "_selected_provider_index": 0,
            "_selected_model": "gpt-4o-mini",
            "_temp_slider": None,
            "last_query_result": {
                "record_id": "test-id",
                "query": "What is this?",
                "answer": "AI Answer",
                "model": "gpt-4o-mini",
                "latency": 1.0,
                "avg_distance": 0.0,
                "num_chunks": 1,
                "results": mock_results,
            }
        }
        sys.modules["streamlit"] = st

        from ragapp.ui.query_tab import render_query_tab
        render_query_tab(mock_retriever, "gpt-4o-mini")

        mock_eval_manager.update_feedback.assert_any_call("test-id", rating="thumbs_up")

    @patch("ragapp.core.evaluator.EvaluationManager")
    @patch("ragapp.core.evaluator.EvaluationRecord")
    def test_feedback_thumbs_down(self, mock_record_cls, mock_manager_cls):
        _unstub_streamlit()
        
        mock_record = MagicMock()
        mock_record.avg_distance = 0.0
        mock_record.record_id = "test-id"
        mock_record_cls.return_value = mock_record

        mock_eval_manager = MagicMock()
        mock_manager_cls.return_value = mock_eval_manager

        st = ModuleType("streamlit")
        mock_vs = MagicMock()
        mock_vs.get_collection_size.return_value = 5
        mock_results = [{"text": "Context A", "metadata": {"source": "a.txt", "page": 1}}]
        mock_retriever = MagicMock()
        mock_retriever.vector_store = mock_vs
        mock_retriever.retrieve = MagicMock(return_value=mock_results)
        mock_retriever.format_context = MagicMock(return_value="Context A")

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
        st.columns = MagicMock(side_effect=lambda n: [MagicMock() for _ in range(n)])
        st.metric = MagicMock()
        st.toast = MagicMock()
        st.rerun = MagicMock()
        st.markdown = MagicMock()
        st.error = MagicMock()
        
        # st.feedback returns 0 for thumbs_down
        st.feedback = MagicMock(return_value=0)
        
        st.session_state = {
            "_selected_provider_index": 0,
            "_selected_model": "gpt-4o-mini",
            "_temp_slider": None,
            "last_query_result": {
                "record_id": "test-id",
                "query": "What is this?",
                "answer": "AI Answer",
                "model": "gpt-4o-mini",
                "latency": 1.0,
                "avg_distance": 0.0,
                "num_chunks": 1,
                "results": mock_results,
            }
        }
        sys.modules["streamlit"] = st

        from ragapp.ui.query_tab import render_query_tab
        render_query_tab(mock_retriever, "gpt-4o-mini")

        mock_eval_manager.update_feedback.assert_any_call("test-id", rating="thumbs_down")
