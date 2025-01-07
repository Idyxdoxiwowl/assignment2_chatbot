import streamlit as st
import ollama
import chromadb
from chromadb.config import Settings
import os

persist_directory = "C:/Users/Acer/chromadb_storage"
os.makedirs(persist_directory, exist_ok=True)

chroma_client = chromadb.Client(Settings(persist_directory=persist_directory))
collection = chroma_client.get_or_create_collection(name="file_and_chat_embeddings")

st.title("Llama Chatbot with File Support")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "file_data" not in st.session_state:
    st.session_state["file_data"] = []

def get_response(prompt):
    client = ollama.Client()
    response = client.generate(model="llama3.2:1b", prompt=prompt)
    return response["response"]

def generate_embedding(text):
    client = ollama.Client()
    response = client.embeddings(model="llama3.2:1b", prompt=text)
    return response['embedding']

def process_file(file):
    try:
        content = file.read().decode("utf-8")
        embedding = generate_embedding(content)
        collection.add(
            ids=[file.name],
            embeddings=[embedding],
            documents=[content]
        )
        st.session_state["file_data"].append({"file_name": file.name, "content": content})
        st.success(f"File {file.name} uploaded and processed successfully!")
    except Exception as e:
        st.error(f"Failed to process file {file.name}: {e}")

st.sidebar.subheader("Search History")
search_query = st.sidebar.text_input("Search messages or embeddings")
if st.sidebar.button("Search"):
    if search_query.strip():
        try:
            query_embedding = generate_embedding(search_query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5
            )
            st.sidebar.write("Search Results:")
            for document in results.get("documents", [[]])[0]:
                st.sidebar.markdown(f"- {document}")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

st.sidebar.subheader("Uploaded Documents")
for file_data in st.session_state["file_data"]:
    with st.sidebar.expander(file_data["file_name"]):
        st.write(file_data["content"])

st.subheader("Chat")
with st.container():
    user_input = st.text_input("Type your message here...")

    if st.button("Send"):
        if user_input.strip():
            st.session_state["messages"].append({"user": "You", "content": user_input})
            try:
                query_embedding = generate_embedding(user_input)
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=5
                )
                relevant_content = "\n\n".join(results.get("documents", [[]])[0])
                bot_response = get_response(f"Based on the following context, answer the question: {user_input}\n\nContext:\n{relevant_content}")

                st.session_state["messages"].append({"user": "Bot", "content": bot_response})
            except Exception as e:
                st.error(f"Error: {e}")

    for message in st.session_state["messages"]:
        if message["user"] == "You":
            st.markdown(f"<div style='text-align: left; padding: 8px; background-color: #d9fdd3; border-radius: 10px; margin: 5px 0;'>{message['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align: left; padding: 8px; background-color: #f0f0f0; border-radius: 10px; margin: 5px 0;'>{message['content']}</div>", unsafe_allow_html=True)

st.subheader("Upload Documents")
uploaded_files = st.file_uploader("Upload one or more .txt files", type="txt", accept_multiple_files=True)
if uploaded_files:
    for uploaded_file in uploaded_files:
        process_file(uploaded_file)
