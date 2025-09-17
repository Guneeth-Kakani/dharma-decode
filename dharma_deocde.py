import streamlit as st
import PyPDF2
import docx
import requests
from dotenv import load_dotenv
import os
from gtts import gTTS
import io
import hashlib

# Load environment variables
load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not PERPLEXITY_API_KEY:
    st.error("Perplexity API key not found. Please check your .env file.")
    st.stop()

# --- Page Configuration and UI Elements ---
st.set_page_config(page_title="Dharma Decode", page_icon="📜", layout="wide")
st.title("Dharma Decode 📜")
st.markdown("Upload your documents and get insights using AI.")
st.divider()

# Initialize session state
if 'uploaded_files' not in st.session_state:
    st.session_state['uploaded_files'] = []
if 'document_text' not in st.session_state:
    st.session_state['document_text'] = ""
if 'current_audio_hash' not in st.session_state:
    st.session_state['current_audio_hash'] = ""

# File uploader
uploaded_files = st.file_uploader("Choose a file", type=["pdf", "docx", "txt"], accept_multiple_files=True)

# --- Document Processing Logic ---
if uploaded_files:
    # Clear previous document text if new files are uploaded
    if set(f.name for f in uploaded_files) != set(st.session_state['uploaded_files']):
        st.session_state['document_text'] = ""
        st.session_state['uploaded_files'] = []
    
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in st.session_state['uploaded_files']:
            file_type = uploaded_file.type
            text = ""
            
            try:
                if file_type == "application/pdf":
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text
                
                elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    doc = docx.Document(uploaded_file)
                    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                
                elif file_type == "text/plain":
                    text = uploaded_file.read().decode("utf-8")
                
                else:
                    st.error(f"Unsupported file type: {file_type}")
                    continue
                
                if text.strip():
                    st.success(f"✅ Uploaded {uploaded_file.name} successfully!")
                    st.session_state['uploaded_files'].append(uploaded_file.name)
                    st.session_state['document_text'] += f"\n--- Content from {uploaded_file.name} ---\n{text}\n"
                else:
                    st.warning(f"⚠️ No text content found in {uploaded_file.name}")
                    
            except Exception as e:
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")

# --- Chat Interface and API Call ---
if st.session_state['document_text'].strip():
    st.subheader("💬 Chat with your document")
    
    # Show uploaded files
    if st.session_state['uploaded_files']:
        st.write(f"**Loaded files:** {', '.join(st.session_state['uploaded_files'])}")
    
    user_input = st.text_input("Ask a question about your legal document:", key="user_question")

    if user_input:
        with st.spinner("🤔 Dharma Decode is thinking..."):
            prompt = f"""
            You are Dharma Decode, an AI assistant that simplifies legal jargon and explains legal documents in plain English.
            
            Document content:
            ---
            {st.session_state['document_text']}
            ---
            
            User question: {user_input}
            
            Please provide a clear, simple explanation avoiding complex legal terminology. 
            If you reference specific sections, please quote them briefly.
            """
            
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            try:
                response = requests.post(
                    "https://api.perplexity.ai/chat/completions", 
                    headers=headers, 
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        answer = response_data["choices"][0]["message"]["content"]
                        st.write(f"**🤖 Dharma Decode:** {answer}")

                        # Text-to-speech functionality
                        try:
                            # Generate audio hash for this specific answer
                            audio_hash = hashlib.md5(answer.encode()).hexdigest()
                            
                            # Only generate new audio if it's different from current
                            if audio_hash != st.session_state.get('current_audio_hash', ''):
                                tts = gTTS(text=answer, lang="en", slow=False)
                                buf = io.BytesIO()
                                tts.write_to_fp(buf)
                                buf.seek(0)
                                audio_bytes = buf.getvalue()
                                
                                st.session_state['current_audio_hash'] = audio_hash
                                st.session_state['current_audio_bytes'] = audio_bytes
                            
                            # Audio controls
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                if st.button("🔊 Play Audio"):
                                    st.audio(st.session_state['current_audio_bytes'], format="audio/mpeg")
                            
                            with col2:
                                st.download_button(
                                    label="📥 Download Audio",
                                    data=st.session_state['current_audio_bytes'],
                                    file_name=f"dharma_decode_answer.mp3",
                                    mime="audio/mpeg",
                                )
                                
                        except Exception as e:
                            st.warning(f"⚠️ Text-to-speech unavailable: {str(e)}")
                    else:
                        st.error("❌ Invalid response format from API")
                else:
                    st.error(f"❌ API Error: {response.status_code}")
                    if response.text:
                        st.error(f"Details: {response.text}")
                        
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Network error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")

# --- Initial Prompt for New Users ---
else:
    st.info("📤 Please upload a document to get started.")
    st.markdown("""
    **Supported file types:**
    - PDF documents (.pdf)
    - Word documents (.docx)
    - Text files (.txt)
    """)
