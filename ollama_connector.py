import ollama
import base64


def get_answer(query, context_chunks, chat_history=None):
    """
    Generate answer using Ollama.
    Supports both text chunks and visual chunks.

    Args:
        query: User question.
        context_chunks: List of relevant chunks.
        chat_history: List of previous {"role":..., "content":...} messages.

    Returns:
        Generated answer string.
    """
    # Build conversation history text (last 3 exchanges = 6 messages)
    history_text = ""
    if chat_history:
        recent = chat_history[-6:]
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"

    # Check if any chunk has visual content
    has_visual = any("base64_image" in chunk for chunk in context_chunks)

    if has_visual:
        # Vision based answer for scanned PDFs
        content = []

        for chunk in context_chunks:
            if "base64_image" in chunk:
                content.append({
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{chunk['base64_image']}"
                })

        content.append({
            "type": "text",
            "text": f"""Previous conversation:
{history_text}

Answer this question based on the document images:
{query}

If the question refers to something from the previous conversation (like "them", "it", "explain more"), use that context.
If the answer is not visible, say 'Answer not found in document.'"""
        })

        messages = [{"role": "user", "content": content}]

    else:
        # Text based answer
        context = ""
        for chunk in context_chunks:
            text = chunk.get('text_content', chunk.get('text', '[No content]'))
            context += f"Page {chunk['page_number']}:\n{text}\n\n"

        prompt = f"""You are a helpful assistant.
Answer the question based ONLY on the provided context.
If the question refers to something from the previous conversation (like "them", "it", "explain more", "continue"), use the conversation history to understand what is being asked.
If the answer is not in the context, say "Answer not found in document."

Previous conversation:
{history_text}

Context:
{context}

Question: {query}

Answer:"""

        messages = [{"role": "user", "content": prompt}]

    print("Generating answer using Ollama...")

    response = ollama.chat(
        model="llama3.2",
        messages=messages
    )

    return response["message"]["content"]