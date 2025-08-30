import streamlit as st
import PyPDF2
import docx
import docx2txt
import requests
from dotenv import load_dotenv
import os

load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not PERPLEXITY_API_KEY:
    st.error("Perplexity API key not found.")
    st.stop()

st.set_page_config(page_title="Dharma Decode", page_icon="📜", layout="wide")
st.title("Dharma Decode 📜")
st.markdown("Upload your documents and get insights using AI.")
st.divider()

if 'uploaded_files' not in st.session_state:
    st.session_state['uploaded_files'] = []
if 'document_text' not in st.session_state:
    st.session_state['document_text'] = ""

uploaded_files = st.file_uploader("Choose a file", type=["pdf", "docx", "txt"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_type = uploaded_file.type
        text = ""
        if file_type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
        elif file_type == "text/plain":
            text = uploaded_file.read().decode("utf-8")
        else:
            st.error(f"Unsupported file type: {file_type}")
            st.stop()
        
        st.success(f"Uploaded {uploaded_file.name} successfully!")
        st.session_state['uploaded_files'].append(uploaded_file.name)
        st.session_state['document_text'] += text + "\n"

if st.session_state['document_text']:
    st.subheader("Chat with your document")
    user_input = st.text_input("Ask a question about your legal document:", key="user_question")

    if user_input:
        with st.spinner("Dharma decode is thinking..."):
            prompt = f"""
            You are Dharma decode, an AI that simplifies legal jargon.
            The user has uploaded a legal document. Here is its content:
            ---
            {st.session_state['document_text']}
            ---
            The user asks: {user_input}
            Please answer clearly and simply, avoiding legal jargon.
            """
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": prompt}]
            }
            response = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=data)
            if response.status_code == 200:
                answer = response.json()["choices"][0]["message"]["content"]
                st.write(f"**Dharma decode:** {answer}")
            else:
                st.error(f"⚠️ API error: {response.status_code} - {response.text}")
else:
    st.info("Please upload a document to get started.")
