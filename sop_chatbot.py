import streamlit as st
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# Load FAISS index
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index("sop_vector_db.faiss")

# Load text chunks
with open("sop_texts.pkl", "rb") as f:
    texts = pickle.load(f)

# Load local chat model
chatbot = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.1")

# Streamlit UI
st.title("📄 Free SOP Chatbot")
st.write("Ask any question related to your SOP documents!")

# User query
query = st.text_input("Enter your question:")
if query:
    # Convert query to embedding
    query_embedding = embedding_model.encode([query], convert_to_numpy=True)

    # Search in FAISS
    _, top_indices = index.search(query_embedding, k=3)
    relevant_texts = " ".join([texts[i] for i in top_indices[0]])

    # Generate response using a free model
    response = chatbot(f"Context: {relevant_texts} \n Question: {query}", max_length=200)[0]["generated_text"]
    
    st.write("### Answer:")
    st.write(response)
