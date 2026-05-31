import os
from openai import OpenAI
from anthropic import Anthropic


def get_llm_response(query_context: str, llm_model: str) -> str:
    """
    Queries the selected LLM provider using the provided context and prompt.
    """
    # We prepend a system-style instruction directly to the user prompt for simplicity
    prompt = f"""
You are a highly capable research assistant. Answer the user's query strictly based on the provided context.
If the context does not contain sufficient information to answer the question, respectfully state that the information is not found in the documents.

Provide the answer clearly and concisely.

=== PROVIDED CONTEXT ===
{query_context}

=== USER QUERY ===
"""

    # Determine provider
    model_lower = llm_model.lower()

    # 1. OpenAI
    if "gpt" in model_lower:
        if not os.environ.get("OPENAI_API_KEY"):
            return "⚠️ Error: `OPENAI_API_KEY` is missing in the environment."

        openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        try:
            response = openai_client.chat.completions.create(
                model=llm_model, messages=[{"role": "user", "content": prompt}], temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ OpenAI API Error: {e}"

    # 2. Anthropic
    elif "claude" in model_lower:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return "⚠️ Error: `ANTHROPIC_API_KEY` is missing in the environment."

        anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        try:
            response = anthropic_client.messages.create(
                model=llm_model, max_tokens=1024, messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"⚠️ Anthropic API Error: {e}"

    # 3. Google Gemini
    elif "gemini" in model_lower:
        if not os.environ.get("GOOGLE_API_KEY"):
            return "⚠️ Error: `GOOGLE_API_KEY` is missing in the environment."

        try:
            import google.generativeai as genai

            genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            model = genai.GenerativeModel(model_name=llm_model, safety_settings=safety_settings)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ Google Gemini API Error: {e}"

    else:
        return f"⚠️ Unsupported model provider: {llm_model}"
