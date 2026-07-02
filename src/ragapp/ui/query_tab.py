"""Query tab — RAG execution and result display."""

from __future__ import annotations

import re
from datetime import datetime

import streamlit as st

# Absolute imports (requires PYTHONPATH=src)
from ragapp.core.llm import get_llm_response  # noqa: F401
from ragapp.core.retriever import RAGRetriever


def _build_export_markdown(
    query: str,
    answer: str,
    model: str,
    results: list[dict],
) -> str:
    """Build a markdown string suitable for file export."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# RAG Query Export",
        "",
        f"**Date:** {timestamp}  ",
        f"**Model:** `{model}`",
        "",
        "---",
        "",
        "## Query",
        "",
        query,
        "",
        "---",
        "",
        "## AI Response",
        "",
        answer,
        "",
        "---",
        "",
        "## Retrieved Sources",
        "",
    ]
    for i, res in enumerate(results, 1):
        source = res["metadata"].get("source", "N/A")
        page_or_chunk = res["metadata"].get(
            "page",
            res["metadata"].get(
                "chunk", res["metadata"].get("paragraph", "N/A")
            ),
        )
        lines.append(f"### Source {i}")
        lines.append("")
        lines.append(f"- **File:** {source}")
        lines.append(f"- **Page / Chunk:** {page_or_chunk}")
        lines.append("")
        lines.append(res["text"])
        lines.append("")

    return "\n".join(lines)


def _safe_filename(query: str, max_len: int = 40) -> str:
    """Derive a filesystem-safe filename from the user query."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", query).strip("_").lower()
    return slug[:max_len] if slug else "rag_export"


def render_query_tab(retriever: RAGRetriever, llm_model: str) -> None:
    """Render the Query tab with RAG execution and performance metrics."""
    import time

    from ragapp.core.evaluator import EvaluationManager, EvaluationRecord, LLMJudge

    if retriever.vector_store.get_collection_size() == 0:
        st.warning("\U0001F6A8 Database is empty.")
        st.info("Navigate to the **Builder** tab to ingest your documents first.")
        st.page_link("https://google.com", label="Google Search",
                     use_container_width=True)
        return

    st.header("Ask Your Documents")

    user_query = st.text_input(
        "What would you like to know?",
        placeholder="e.g., 'What are the main themes of the uploaded documents?'",
    )

    if not user_query.strip():
        # Clear last query if empty text
        if "last_query_result" in st.session_state:
            st.session_state["last_query_result"] = None
        return

    # Initalize evaluation manager
    eval_manager = EvaluationManager()

    # Search & Answer button triggers search
    if st.button("Search & Answer", type="primary"):
        with st.spinner("Retrieving relevant context and generating response..."):
            start_time = time.time()
            # 1. RAG: Get relevant chunks
            n_results = st.session_state.get("_n_results", 3)
            results = retriever.retrieve(user_query, n_results=n_results)

            if not results:
                st.info(
                    "No relevant documents found in the database matching your query.")
                st.session_state["last_query_result"] = None
                return

            # 2. Display LLM answer
            context_str = retriever.format_context(results)
            answer = get_llm_response(context_str, user_query, llm_model)
            latency = time.time() - start_time

            # 3. Create evaluation record
            chunk_distances = [res.get("distance", 0.0) for res in results if isinstance(res, dict)]
            
            record = EvaluationRecord(
                query=user_query,
                answer=answer,
                model=llm_model,
                latency=latency,
                retrieval_mode=st.session_state.get("_retrieval_mode", "hybrid"),
                num_chunks=len(results),
                chunk_distances=chunk_distances
            )
            eval_manager.add_record(record)

            st.session_state["last_query_result"] = {
                "record_id": record.record_id,
                "query": user_query,
                "answer": answer,
                "model": llm_model,
                "latency": latency,
                "avg_distance": record.avg_distance,
                "num_chunks": len(results),
                "results": results,
                "faithfulness_score": None,
                "faithfulness_reason": None,
                "relevance_score": None,
                "relevance_reason": None,
            }

    # Render results from session state to keep UI alive on feedback / evaluation reruns
    res_data = st.session_state.get("last_query_result")
    if res_data and res_data["query"] == user_query:
        record_id = res_data["record_id"]
        answer = res_data["answer"]
        latency = res_data["latency"]
        avg_distance = res_data["avg_distance"]
        num_chunks = res_data["num_chunks"]
        results = res_data["results"]
        faithfulness_score = res_data.get("faithfulness_score")
        faithfulness_reason = res_data.get("faithfulness_reason")
        relevance_score = res_data.get("relevance_score")
        relevance_reason = res_data.get("relevance_reason")

        st.subheader("\U0001F916 AI Response")
        st.write(answer)

        # Quantitative Metrics Row
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("⏱️ Latency", f"{latency:.2f}s")
        with metric_col2:
            st.metric("📊 Avg Match Distance", f"{avg_distance:.3f}")
        with metric_col3:
            st.metric("📄 Context Chunks", f"{num_chunks}")

        # Qualitative Feedback Row
        st.write("---")
        f_col1, f_col2 = st.columns(2)

        with f_col1:
            st.markdown("##### 👍 Qualitative Feedback")
            
            # Use streamlit feedback if available
            if hasattr(st, "feedback"):
                # Use key specific to this record_id so it resets on new queries
                rating_idx = st.feedback("thumbs", key=f"rating_{record_id}")
                if rating_idx is not None:
                    rating_str = "thumbs_up" if rating_idx == 1 else "thumbs_down"
                    eval_manager.update_feedback(record_id, rating=rating_str)
            else:
                # Fallback to buttons if streamlit doesn't support feedback (unlikely in 1.58.0)
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    if st.button("👍 Useful", key=f"like_{record_id}"):
                        eval_manager.update_feedback(record_id, rating="thumbs_up")
                        st.toast("Thank you for your feedback!")
                with sub_col2:
                    if st.button("👎 Not Useful", key=f"dislike_{record_id}"):
                        eval_manager.update_feedback(record_id, rating="thumbs_down")
                        st.toast("Feedback recorded.")

            comment_val = st.text_input("Feedback Comment", placeholder="Enter comments or corrections here...", key=f"comment_{record_id}")
            if st.button("Save Comment", key=f"btn_comment_{record_id}"):
                eval_manager.update_feedback(record_id, rating=None, feedback_comment=comment_val)
                st.toast("Comment saved!")

        with f_col2:
            st.markdown("##### 🤖 AI Judge Self-Assessment")
            if faithfulness_score is not None:
                st.markdown(f"**Faithfulness:** {faithfulness_score}/5 ⭐")
                st.caption(f"Reason: {faithfulness_reason}")
                st.markdown(f"**Relevance:** {relevance_score}/5 ⭐")
                st.caption(f"Reason: {relevance_reason}")
            else:
                if st.button("Run AI Judge Evaluation", key=f"judge_{record_id}", type="secondary"):
                    with st.spinner("AI Judge evaluating response..."):
                        context_str = retriever.format_context(results)
                        eval_res = LLMJudge.evaluate(user_query, context_str, answer, llm_model)
                        if "error" in eval_res:
                            st.error(eval_res["error"])
                        else:
                            # Save to JSON log
                            eval_manager.update_llm_judge(
                                record_id,
                                faithfulness_score=eval_res["faithfulness_score"],
                                faithfulness_reason=eval_res["faithfulness_reason"],
                                relevance_score=eval_res["relevance_score"],
                                relevance_reason=eval_res["relevance_reason"]
                            )
                            # Update local session state
                            res_data["faithfulness_score"] = eval_res["faithfulness_score"]
                            res_data["faithfulness_reason"] = eval_res["faithfulness_reason"]
                            res_data["relevance_score"] = eval_res["relevance_score"]
                            res_data["relevance_reason"] = eval_res["relevance_reason"]
                            st.rerun()

        # 4. Export to Markdown
        md_content = _build_export_markdown(
            user_query, answer, llm_model, results
        )
        filename = f"{_safe_filename(user_query)}.md"
        st.download_button(
            label="📥 Export Response to Markdown",
            data=md_content,
            file_name=filename,
            mime="text/markdown",
        )

        st.divider()
        st.subheader("\U0001F4D1 Relevant Context Retrieved")
        for i, res in enumerate(results):
            with st.expander(f"\U0001F4C4 Document Source {i + 1}"):
                st.write(res["text"])
                source = res["metadata"].get("source", "N/A")
                page_or_chunk = (
                    res["metadata"].get("page",
                                        res["metadata"].get("chunk",
                                                            res["metadata"].get("paragraph", "N/A")))
                )
                st.caption(
                    f"Source: {source} | Page/Chunk: {page_or_chunk} | Distance: {res.get('distance', 0.0):.4f}")
