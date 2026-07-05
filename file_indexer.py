import os
import json


#Function to scan folders and find PDF files
def scan_folders(root_path):
    """
    Scans all folders and subfolders
    Returns a list of all PDF files with their paths
    """
    pdf_index=[]

    for dirpath,dirnames,filenames in os.walk(root_path):
        for filename in filenames:
            if filename.lower().endswith('.pdf'):
                full_path=os.path.join(dirpath,filename)
                pdf_index.append({
                    "name": filename,
                    "path": full_path,
                    "folder": dirpath,
                    "size": os.path.getsize(full_path)
                })
    return pdf_index

def search_pdf_by_name(pdf_index, search_query):
    """
    Search PDFs by name
    Returns matching PDFs
    """

    results=[]
    search_query=search_query.lower()

    for pdf in pdf_index:
        if search_query in pdf["name"].lower():
            results.append(pdf)

    return results

def save_index(pdf_index,save_path="pdf_index.json"):
    """Save index to JSON file"""
    with open(save_path,"w")as f:
        json.dump(pdf_index,f,indent=2)
    print(f"Index saved! Total PDFs found: {len(pdf_index)}")

def load_index(save_path="pdf_index.json"):
    """Load existing index"""
    if os.path.exists(save_path):
        with open(save_path, "r") as f:
            return json.load(f)
    return []

#TEST

if __name__ == "__main__":
    root_path = "./sample_pdfs"
    
    print("Scanning folders...")
    index = scan_folders(root_path)
    
    print(f"\nFound {len(index)} PDFs:")
    for pdf in index:
        print(f"  - {pdf['name']} → {pdf['folder']}")
    
    save_index(index)
    
    query = input("\nSearch PDF name: ")
    results = search_pdf_by_name(index, query)
    print(f"\nSearch results for '{query}':")
    for r in results:
        print(f"  ✅ {r['name']} at {r['path']}")

