import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json


# -------------------------------
# Load embedding model (only once)
# -------------------------------
print("Loading embedding model...")

# Load the pretrained MiniLM embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

print("Model loaded! ")

# Function to split PDF pages into smaller chunks

def create_chunks(pages_data,chunk_size=500,overlap=50):
    """
    Split each PDF page into smaller overlapping chunks.

    Parameters:
        pages_data : list of page dictionaries
        chunk_size : maximum words in one chunk
        overlap    : repeated words between consecutive chunks

    Returns:
        List of chunk dictionaries.
    """
    chunks=[]

    for page in pages_data:
        text = page["text_content"]
        words = text.split()
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])

            # Ignore empty chunks
            if chunk:

                # Save chunk information
                chunks.append({
                    "text": chunk,
                    "page_number": page["page_number"],
                    "chunk_id": len(chunks)
                })

    print(f"Total chunks created: {len(chunks)}")

    return chunks 

# Create embeddings and FAISS vector database

def create_vector_store(chunks):
    """
    Convert chunks into embeddings and store them in FAISS.

    Returns:
        FAISS index and original chunks.
    """

    print("Creating embeddings...")

    texts = [chunk["text"] for chunk in chunks]
    embeddings =embedder.encode(texts,show_progress_bar=True)
    embeddings=np.array(embeddings).astype("float32")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    print(f"vectors store created! Total vectors :{index.ntotal}")
    
    return index, chunks

# Search the most similar text chunks

def search_similar_chunks(query,index,chunks,top_k=5):
    """
    Find the top_k most relevant chunks for a user query.
    """
    query_embedding=embedder.encode([query])
    query_embedding=np.array(query_embedding).astype("float32")
    distances,indices=index.search(query_embedding,top_k)
    results =[]

    # Retrieve original chunk information
    for idx in indices[0]:
        if idx < len(chunks):
            results.append(chunks[idx])

    return results


# Main program

if __name__ == "__main__":
    from pdf_processor import extract_pdf_pages
    pdf_path = "./sample_pdfs/programming/python_programming_test.pdf"
    pages = extract_pdf_pages(pdf_path)
    chunks = create_chunks(pages)
    index, chunks = create_vector_store(chunks)
    query = input("\nEnter your query: ")
    results = search_similar_chunks(query, index, chunks)

    # Display results
    print(f"\nTop results for '{query}':")

    for r in results:
        print(f"\n📄 Page {r['page_number']}:")
        print(r["text"][:200])  # Show first 200 characters of the chunk

