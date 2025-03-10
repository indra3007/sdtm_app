import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader

# Load free sentence transformer model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Define SOP folder
SOP_FOLDER = "sops/"

# Load documents
def load_documents(folder):
    docs = []
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if file.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file.endswith(".txt"):
            loader = TextLoader(file_path)
        else:
            continue
        docs.extend(loader.load())
    return docs

# Process documents
documents = load_documents(SOP_FOLDER)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_documents(documents)

# Convert text to embeddings
texts = [chunk.page_content for chunk in chunks]
embeddings = embedding_model.encode(texts, convert_to_numpy=True)

# Store embeddings in FAISS
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Save FAISS index
faiss.write_index(index, "sop_vector_db.faiss")
with open("sop_texts.pkl", "wb") as f:
    pickle.dump(texts, f)

print("SOPs successfully indexed with FAISS!")
