import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load embedding model
print("Loading embedding model for folder suggester...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("Folder suggester ready.")


def get_all_folders(root_path):
    """
    Get all unique folders containing PDFs.

    Args:
        root_path: Root directory to scan.

    Returns:
        List of folder paths containing PDFs.
    """
    folders = set()

    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                folders.add(dirpath)

    return list(folders)


def build_folder_embeddings(root_path, save_path="folder_embeddings.json"):
    """
    Build and save embeddings for each folder.
    Embeddings are based on PDF filenames in each folder.

    Args:
        root_path: Root directory to scan.
        save_path: Path to save folder embeddings.

    Returns:
        Dictionary of folder embeddings.
    """
    print("Building folder embeddings...")

    folders = get_all_folders(root_path)
    folder_data = {}

    for folder in folders:

        # Get all PDF names in this folder
        pdf_names = []

        for filename in os.listdir(folder):
            if filename.lower().endswith(".pdf"):
                # Clean filename for better embedding
                clean_name = filename.replace(
                    "_", " "
                ).replace(
                    "-", " "
                ).replace(
                    ".pdf", ""
                )
                pdf_names.append(clean_name)

        if not pdf_names:
            continue

        # Create folder description from PDF names
        folder_description = " ".join(pdf_names)

        # Create embedding for this folder
        embedding = embedder.encode([folder_description])[0]

        folder_data[folder] = {
            "pdf_names": pdf_names,
            "embedding": embedding.tolist(),
        }

        print(f"  Folder indexed: {folder} ({len(pdf_names)} PDFs)")

    # Save to file
    with open(save_path, "w") as f:
        json.dump(
            {k: {"pdf_names": v["pdf_names"]} for k, v in folder_data.items()},
            f,
            indent=2
        )

    print(f"Folder embeddings saved. Total folders: {len(folder_data)}")
    return folder_data


def suggest_folders(query, folder_data, current_folders, top_k=3, threshold=0.3):
    """
    Suggest relevant folders based on the query.
    Excludes folders already being searched.

    Args:
        query: User's question.
        folder_data: Dictionary of folder embeddings.
        current_folders: List of folders already selected.
        top_k: Number of suggestions to return.
        threshold: Minimum similarity score.

    Returns:
        List of suggested folders with similarity scores.
    """
    if not folder_data:
        return []

    # Embed the query
    query_embedding = embedder.encode([query])[0]

    suggestions = []

    for folder, data in folder_data.items():

        # Skip folders already being searched
        if folder in current_folders:
            continue

        # Calculate similarity
        folder_embedding = np.array(data["embedding"])
        similarity = cosine_similarity(
            [query_embedding],
            [folder_embedding]
        )[0][0]

        if similarity >= threshold:
            suggestions.append({
                "folder": folder,
                "similarity": float(similarity),
                "pdf_count": len(data["pdf_names"]),
                "pdf_names": data["pdf_names"],
            })

    # Sort by similarity score
    suggestions.sort(key=lambda x: x["similarity"], reverse=True)

    return suggestions[:top_k]


def check_answer_confidence(answer):
    """
    Check if the answer confidence is low.
    Returns True if answer seems incomplete or not found.

    Args:
        answer: Generated answer text.

    Returns:
        True if answer confidence is low.
    """
    low_confidence_phrases = [
        "not found",
        "not mentioned",
        "not available",
        "cannot find",
        "no information",
        "does not contain",
        "not in the document",
        "answer not found",
        "i don't know",
        "unclear",
    ]

    answer_lower = answer.lower()

    for phrase in low_confidence_phrases:
        if phrase in answer_lower:
            return True

    return False


# Test
if __name__ == "__main__":
    root_path = "./sample_pdfs"

    # Build folder embeddings
    folder_data = build_folder_embeddings(root_path)

    # Test suggestion
    query = input("\nEnter query to test suggestions: ")

    suggestions = suggest_folders(
        query,
        folder_data,
        current_folders=[],
    )

    if suggestions:
        print(f"\nSuggested folders for '{query}':")
        for s in suggestions:
            print(f"  - {s['folder']} (similarity: {s['similarity']:.2f})")
            print(f"    PDFs: {', '.join(s['pdf_names'])}")
    else:
        print("No suggestions found.")