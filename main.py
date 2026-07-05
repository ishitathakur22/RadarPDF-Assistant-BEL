# Import functions for building folder embeddings,
# suggesting relevant folders, and checking answer confidence
from folder_suggester import (
    build_folder_embeddings,
    suggest_folders,
    check_answer_confidence,
)

# Import functions for scanning folders, searching PDFs, and saving the PDF index
from file_indexer import scan_folders, search_pdf_by_name, save_index

# Import function to extract text from PDF pages
from pdf_processor import extract_pdf_pages

# Auto-detect ColPali or Tesseract based on hardware
from scanned_handler import (
    is_scanned_pdf,
    extract_text_from_scanned_pdf,
)

# Import functions for chunk creation, vector database creation,
# and similarity search
from vector_db_manager import (
    create_chunks,
    create_vector_store,
    search_similar_chunks,
)

# Import function to generate answers using Ollama
from ollama_connector import get_answer

# Import function to get voice input from the user
from voice_input import get_voice_query


def select_and_process_pdfs(pdf_index):
    """
    Search, select, and process one or more PDF files.

    Returns:
        tuple:
            (index, all_chunks) if PDFs are successfully processed.
            (None, None) if the user chooses to return.
    """

    while True:

        # Ask the user to search for a PDF
        search_query = input(
            "\nEnter the PDF name to search (minimum 3 characters), or type 'back' to return: "
        )

        # Return to the previous menu
        if search_query.lower() == "back":
            return None, None

        # Validate the search query length
        if len(search_query) < 3:
            print("Please enter at least 3 characters.")
            continue

        # Search for matching PDF files
        results = search_pdf_by_name(pdf_index, search_query)

        # Display a message if no PDFs are found
        if not results:
            print("No PDF found with that name. Please try again.")
            continue

        # Display the matching PDFs
        print(f"\nFound {len(results)} PDF(s):")

        for i, pdf in enumerate(results):
            print(f"{i + 1}. {pdf['name']}")

        # Ask the user to select one or more PDFs
        print("\nEnter the PDF numbers to select.")
        print("Use commas to select multiple PDFs (Example: 1,2,3)")
        print("Type 'search' to perform another search.")

        choices = input("Enter your choice: ")

        # Start a new search
        if choices.lower() == "search":
            continue

        try:
            # Convert the user's input into a list of indices
            selected_indices = [
                int(choice.strip()) - 1
                for choice in choices.split(",")
            ]

            # Retrieve the selected PDFs
            selected_pdfs = [
                results[index]
                for index in selected_indices
            ]

        except (ValueError, IndexError):
            print("Invalid selection. Please enter valid PDF numbers.")
            continue

        # Display the selected PDFs
        print(f"\nSelected {len(selected_pdfs)} PDF(s):")

        for pdf in selected_pdfs:
            print(f"- {pdf['name']}")

        # Store chunks from all selected PDFs
        all_chunks = []

        # Process each selected PDF
        for pdf in selected_pdfs:

            print(f"\nProcessing PDF: {pdf['name']}")

            # Check if PDF is scanned or text-based
            if is_scanned_pdf(pdf["path"]):
                # Use OCR for scanned PDFs
                print("Scanned PDF detected. Using OCR...")
                pages = extract_text_from_scanned_pdf(pdf["path"])
            else:
                # Use normal text extraction
                pages = extract_pdf_pages(pdf["path"])

            # Create chunks from extracted pages
            chunks = create_chunks(pages)

            # Tag each chunk with source PDF name
            for chunk in chunks:
                chunk["pdf_name"] = pdf["name"]

            # Add chunks to master list
            all_chunks.extend(chunks)
            print(f"Created {len(chunks)} chunk(s).")

        # Display the total number of chunks
        print(f"\nTotal chunks: {len(all_chunks)}")

        # Create the FAISS vector database
        index, all_chunks = create_vector_store(all_chunks)

        print("The selected PDFs are ready for question answering.")

        return index, all_chunks


def main():

    # Display the application title
    print("=" * 50)
    print("PDF Q&A System")
    print("=" * 50)

    # Specify the folder containing PDF files
    root_path = "./sample_pdfs"

    print(f"\nScanning folder: {root_path}")

    # Scan the folder and create the PDF index
    pdf_index = scan_folders(root_path)
    save_index(pdf_index)
    print(f"Found {len(pdf_index)} PDF(s).")

    # Build folder embeddings for smart suggestions
    print("Building folder index for suggestions...")
    folder_data = build_folder_embeddings(root_path)

    # Main application loop
    while True:

        # Search, select, and process PDFs
        index, all_chunks = select_and_process_pdfs(pdf_index)

        # Exit if user typed back
        if index is None:
            print("\nGoodbye.")
            break

        # Display usage instructions
        print("\n" + "=" * 50)
        print("PDF Q&A System - Ask your questions")
        print("=" * 50)

        # Question answering loop
        while True:

            # Display available options before every question
            print("\n" + "-" * 50)
            print("Type 'exit'       - Quit the program")
            print("Type 'new search' - Search different PDFs")
            print("Type 'voice'      - Use voice input")
            print("-" * 50)

            # Get input from the user
            user_input = input("\nEnter your question: ").strip()

            # Exit the application
            if user_input.lower() == "exit":
                print("\nExiting the program. Goodbye.")
                return

            # Return to PDF search
            if user_input.lower() == "new search":
                print("\nReturning to the PDF search menu...")
                break

            # Handle voice input
            elif user_input.lower() == "voice":
                print("\nStarting voice input. Please speak your question.")
                query = get_voice_query(duration=10)
                print(f"Voice input received: {query}")

            # Handle text input
            else:
                query = user_input

            # Handle empty input
            if not query.strip():
                print("No input detected. Please try again.")
                continue

            # Retrieve the most relevant chunks
            relevant_chunks = search_similar_chunks(
                query,
                index,
                all_chunks,
            )

            # Generate an answer using Ollama
            answer = get_answer(
                query,
                relevant_chunks,
            )

            # Display the generated answer
            print(f"\nAnswer:\n{answer}")

            # Display the source PDFs and page numbers
            print("\nAnswer retrieved from:")
            for chunk in relevant_chunks:
                print(
                    f"- {chunk['pdf_name']} "
                    f"(Page {chunk['page_number']})"
                )

            # Check if answer confidence is low
            if check_answer_confidence(answer):
                print("\nAnswer not found in selected PDFs.")
                print("You may find the answer in these folders:")

                # Get current folders being searched
                current_folders = list(set([
                    chunk["pdf_name"] for chunk in all_chunks
                ]))

                # Get folder suggestions
                suggestions = suggest_folders(
                    query,
                    folder_data,
                    current_folders=current_folders,
                )

                if suggestions:
                    for s in suggestions:
                        print(f"\n  Folder: {s['folder']}")
                        print(f"  Similarity: {s['similarity']:.0%}")
                        print(f"  PDFs available:")
                        for pdf in s["pdf_names"]:
                            print(f"    - {pdf}")
                else:
                    print("  No similar folders found.")

            print("-" * 50)


# Run the application
if __name__ == "__main__":
    main()