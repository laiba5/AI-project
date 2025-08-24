import streamlit as st
import requests
import PyPDF2
import os

st.set_page_config(page_title="🖊️PDF Summarizer Chatbot")

# Toggle light and dark mode themes
ms = st.session_state
if "themes" not in ms:
    ms.themes = {"current_theme": "light",
                 "refreshed": True,
                "light": {"theme.base": "dark",
                          "theme.backgroundColor": "#FFFFFF",
                          "theme.primaryColor": "#6200EE",
                          "theme.secondaryBackgroundColor": "#F5F5F5",
                          "theme.textColor": "000000",
                          "button_face": "🌜"},
                "dark":  {"theme.base": "light",
                          "theme.backgroundColor": "#121212",
                          "theme.primaryColor": "#BB86FC",
                          "theme.secondaryBackgroundColor": "#1F1B24",
                          "theme.textColor": "#E0E0E0",
                          "button_face": "🌞"}}

def ChangeTheme():
    previous_theme = ms.themes["current_theme"]
    tdict = ms.themes["light"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]
    for vkey, vval in tdict.items(): 
        if vkey.startswith("theme"): st._config.set_option(vkey, vval)

    ms.themes["refreshed"] = False
    if previous_theme == "dark": ms.themes["current_theme"] = "light"
    elif previous_theme == "light": ms.themes["current_theme"] = "dark"

btn_face = ms.themes["light"]["button_face"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]["button_face"]
st.button(btn_face, on_click=ChangeTheme)

if ms.themes["refreshed"] == False:
    ms.themes["refreshed"] = True
    st.rerun()

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    """Extract text from an uploaded PDF file."""
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Sidebar Section
with st.sidebar:
    st.title('🖊️PDF Summarizer Chatbot')
    
    # Load API key from secrets
    groq_api_key = st.secrets["groq"]["api_key"]

    if groq_api_key:
        st.success('API key loaded successfully!', icon='✅')
    else:
        st.warning('No API key found in secrets.toml. Please check!', icon='⚠️')

    # PDF Upload and question input in the sidebar
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
    question = st.text_input("Enter your question:")

# Main Section - Chat Area
st.title("Chatbot - PDF Summarizer")

# PDF Text extraction logic
def extract_text_from_pdf(pdf_file):
    """Extract text from an uploaded PDF file."""
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Store LLM generated responses in session state
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "Upload a PDF file from the sidebar to get started."}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Function to clear chat history
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "Upload a PDF file from the sidebar to get started."}]
    st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function to generate response from Groq API (Llama13B)
def generate_groq_response(text, question):
    prompt = f"Here is the context:\n\n{text[:5000]}\n\nNow answer this question:\n{question}"
    
    url = "https://api.groq.com/openai/v1/chat/completions"  # Correct Groq endpoint
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "llama-3.3-70b-versatile",  # Correct Groq model ID
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question},
            {"role": "user", "content": text}  # Pass the extracted text here
        ]
    }
    
    # Send a POST request to Groq API
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()  # Return the response JSON
    else:
        st.error(f"Error: {response.status_code} - {response.text}")
        return None

# Handle PDF Text extraction and response generation
if uploaded_file and question:
    with st.spinner("Extracting text from PDF..."):
        pdf_text = extract_text_from_pdf(uploaded_file)
    st.success("PDF uploaded and text extracted!")

    # Generate response based on extracted text and user question
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_groq_response(pdf_text, question)
            if response:
                placeholder = st.empty()
                full_response = response['choices'][0]['message']['content']  # Extract content
                placeholder.markdown(f"### Summary:\n\n{full_response}")
                message = {"role": "assistant", "content": full_response}
                st.session_state.messages.append(message)