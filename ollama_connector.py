import ollama
import base64


def get_answer(query, context_chunks):
    """
    Generate answer using Ollama.
    Supports both text chunks and visual chunks.

    Args:
        query: User question.
        context_chunks: List of relevant chunks.

    Returns:
        Generated answer string.
    """
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
            "text": f"Answer this question based on the document images:\n{query}\n\nIf the answer is not visible, say 'Answer not found in document.'"
        })

        messages = [{"role": "user", "content": content}]

    else:
        # Text based answer
        context = ""
        for chunk in context_chunks:
            # Handle both text_content and text keys
            text = chunk.get('text_content', chunk.get('text', '[No content]'))
            context += f"Page {chunk['page_number']}:\n{text}\n\n"

        prompt = f"""You are a helpful assistant.
Answer the question based ONLY on the provided context.
If the answer is not in the context, say "Answer not found in document."

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
