"""Evaluation tab — RAG performance history, quantitative stats, and qualitative review."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from ragapp.core.evaluator import EvaluationManager


def render_evaluation_tab() -> None:
    """Render the RAG Evaluation tab."""
    st.header("📊 RAG Evaluation Dashboard")
    st.caption(
        "Monitor the quantitative performance (latency, semantic match distance) "
        "and qualitative alignment (user feedback, AI-as-a-judge scorecards) of your local RAG system."
    )

    manager = EvaluationManager()
    records = manager.get_records()

    if not records:
        st.info("No query evaluation logs found yet. Run some queries in the **Query** tab to populate this dashboard.")
        return

    # 1. Summary Statistics & Metric Cards
    total_queries = len(records)
    
    # Calculate thumbs up percentage
    thumbs_up_count = sum(1 for r in records if r.rating == "thumbs_up")
    thumbs_down_count = sum(1 for r in records if r.rating == "thumbs_down")
    total_feedback = thumbs_up_count + thumbs_down_count
    pos_feedback_pct = (thumbs_up_count / total_feedback * 100) if total_feedback > 0 else 0.0

    avg_latency = sum(r.latency for r in records) / total_queries
    avg_distance = sum(r.avg_distance for r in records) / total_queries

    # Filter LLM judge rated records
    judged_records = [r for r in records if r.faithfulness_score is not None and r.faithfulness_score > 0]
    avg_faithfulness = sum(r.faithfulness_score for r in judged_records) / len(judged_records) if judged_records else 0.0
    avg_relevance = sum(r.relevance_score for r in judged_records) / len(judged_records) if judged_records else 0.0

    st.markdown("### 📈 Performance Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Queries", f"{total_queries}")
    with col2:
        if total_feedback > 0:
            st.metric("User Approval", f"{pos_feedback_pct:.1f}%", f"{thumbs_up_count} 👍 / {thumbs_down_count} 👎")
        else:
            st.metric("User Approval", "N/A", "No feedback yet")
    with col3:
        st.metric("Avg Latency", f"{avg_latency:.2f}s")
    with col4:
        st.metric("Avg Match Distance", f"{avg_distance:.3f}")

    if judged_records:
        st.write("")
        col_j1, col_j2 = st.columns(2)
        with col_j1:
            st.metric("Avg Faithfulness (AI Judge)", f"{avg_faithfulness:.2f} / 5 ⭐", help="1 = unsupported, 5 = fully grounded in context")
        with col_j2:
            st.metric("Avg Relevance (AI Judge)", f"{avg_relevance:.2f} / 5 ⭐", help="1 = irrelevant, 5 = fully relevant to user query")

    st.write("---")

    # 2. Search, Filters & Logs Table
    st.markdown("### 🗂️ Evaluation Logs")

    # Filters
    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    with f_col1:
        search_query = st.text_input("🔍 Search Query or Answer", placeholder="Type a term to search...")
    with f_col2:
        model_options = ["All"] + list(set(r.model for r in records))
        selected_filter_model = st.selectbox("Filter by Model", model_options)
    with f_col3:
        rating_options = ["All", "Liked (👍)", "Disliked (👎)", "No Feedback"]
        selected_rating = st.selectbox("Filter by Feedback", rating_options)

    # Filter records list
    filtered_records = records.copy()
    
    if search_query:
        search_query_lower = search_query.lower()
        filtered_records = [
            r for r in filtered_records 
            if search_query_lower in r.query.lower() or search_query_lower in r.answer.lower()
        ]

    if selected_filter_model != "All":
        filtered_records = [r for r in filtered_records if r.model == selected_filter_model]

    if selected_rating == "Liked (👍)":
        filtered_records = [r for r in filtered_records if r.rating == "thumbs_up"]
    elif selected_rating == "Disliked (👎)":
        filtered_records = [r for r in filtered_records if r.rating == "thumbs_down"]
    elif selected_rating == "No Feedback":
        filtered_records = [r for r in filtered_records if r.rating is None]

    if not filtered_records:
        st.info("No evaluation logs match your search and filter criteria.")
    else:
        # Build pandas DataFrame for display
        table_data = []
        for r in filtered_records:
            rating_symbol = "👍" if r.rating == "thumbs_up" else ("👎" if r.rating == "thumbs_down" else "—")
            faith_str = f"{r.faithfulness_score}/5" if r.faithfulness_score else "—"
            rel_str = f"{r.relevance_score}/5" if r.relevance_score else "—"
            
            table_data.append({
                "Timestamp": r.timestamp.split("T")[0] + " " + r.timestamp.split("T")[1][:8] if "T" in r.timestamp else r.timestamp,
                "Query": r.query[:60] + ("..." if len(r.query) > 60 else ""),
                "Model": r.model,
                "Latency (s)": round(r.latency, 2),
                "Avg Distance": round(r.avg_distance, 3),
                "Rating": rating_symbol,
                "Faithfulness": faith_str,
                "Relevance": rel_str,
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # 3. Actions Row (Download / Clear)
        act_col1, act_col2, act_col3 = st.columns([1, 1, 2])
        
        # JSON Export bytes
        all_dicts = [r.to_dict() for r in filtered_records]
        json_str = json.dumps(all_dicts, indent=2, ensure_ascii=False)
        with act_col1:
            st.download_button(
                label="📥 Export Logs (JSON)",
                data=json_str,
                file_name="rag_evaluation_logs.json",
                mime="application/json",
                use_container_width=True
            )

        # CSV Export bytes
        csv_df = pd.DataFrame([r.to_dict() for r in filtered_records])
        csv_str = csv_df.to_csv(index=False)
        with act_col2:
            st.download_button(
                label="📥 Export Logs (CSV)",
                data=csv_str,
                file_name="rag_evaluation_logs.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with act_col3:
            # Double confirm clear
            if st.button("🗑️ Clear Evaluation History", type="secondary", use_container_width=True):
                st.session_state._show_clear_confirm = True
                
            if st.session_state.get("_show_clear_confirm", False):
                st.warning("Are you sure? This will delete all evaluation logs forever.")
                conf_col1, conf_col2 = st.columns(2)
                with conf_col1:
                    if st.button("Yes, delete it", type="primary", key="confirm_delete"):
                        manager.clear_logs()
                        st.session_state._show_clear_confirm = False
                        st.rerun()
                with conf_col2:
                    if st.button("Cancel", key="cancel_delete"):
                        st.session_state._show_clear_confirm = False
                        st.rerun()

        st.write("---")

        # 4. Detailed History Inspector
        st.markdown("### 🔍 Detail Inspector")
        for i, r in enumerate(filtered_records):
            time_str = r.timestamp.split("T")[0] + " " + r.timestamp.split("T")[1][:8] if "T" in r.timestamp else r.timestamp
            rating_symbol = "👍 Good" if r.rating == "thumbs_up" else ("👎 Bad" if r.rating == "thumbs_down" else "None")
            
            expander_title = f"Query {i+1}: {r.query[:50]}... | Model: {r.model} | {time_str}"
            with st.expander(expander_title):
                st.markdown(f"**Full Query:** {r.query}")
                st.markdown(f"**AI Answer:**\n{r.answer}")
                st.markdown(f"**Model:** `{r.model}` | **Retrieval Mode:** `{r.retrieval_mode}` | **Retrieved Chunks:** `{r.num_chunks}`")
                
                det_col1, det_col2 = st.columns(2)
                with det_col1:
                    st.markdown("**Quantitative Metrics:**")
                    st.write(f"- ⏱️ Generation Latency: `{r.latency:.2f} seconds`")
                    st.write(f"- 📊 Average Semantic Match Distance: `{r.avg_distance:.3f}`")
                    st.write(f"- 📄 Distances per chunk: `{['{:.3f}'.format(d) for d in r.chunk_distances]}`")
                
                with det_col2:
                    st.markdown("**Qualitative Metrics:**")
                    st.write(f"- 👤 User Rating: `{rating_symbol}`")
                    st.write(f"- 💬 User Comments: `{r.feedback_comment or 'None'}`")
                    
                    if r.faithfulness_score is not None:
                        st.markdown(f"- 🤖 Faithfulness (AI Judge): `{r.faithfulness_score}/5 ⭐`")
                        st.caption(f"Reason: {r.faithfulness_reason}")
                        st.markdown(f"- 🤖 Relevance (AI Judge): `{r.relevance_score}/5 ⭐`")
                        st.caption(f"Reason: {r.relevance_reason}")
                    else:
                        st.write("- 🤖 LLM Judge Self-Assessment: `Not evaluated yet`")
