import streamlit as st
import re
import nltk
from nltk.tokenize import sent_tokenize
import pandas as pd
import requests
import json

def search_gutenberg(query):
    """Search Project Gutenberg catalog"""
    base_url = "https://gutendex.com/books/"
    params = {'search': query}
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        books = []
        for book in data['results']:
            books.append({
                'title': book['title'],
                'author': book['authors'][0]['name'] if book['authors'] else 'Unknown',
                'id': book['id'],
                'download_count': book['download_count'],
                'languages': book['languages'],
                'text_url': next((fmt['url'] for fmt in book['formats'].values() 
                                if '.txt' in fmt['url']), None)
            })
        
        return books
    except Exception as e:
        st.error(f"Error searching Gutenberg: {e}")
        return []

def fetch_book_text(url):
    """Fetch book text from URL"""
    try:
        response = requests.get(url)
        return response.text
    except Exception as e:
        st.error(f"Error fetching book: {e}")
        return None

def main():
    st.set_page_config(
        page_title="Book Chapter Splitter",
        page_icon="📚",
        layout="wide"
    )

    st.title("📚 Book Chapter Splitter v0.01")
    
    st.markdown("""
    ### Process public domain books into organized chapters and sections
    
    Search for books from Project Gutenberg or upload your own text files.
    Each book will be split into chapters and organized into 500-byte sections.
    """)

    # Add search interface
    search_col, upload_col = st.columns(2)
    
    with search_col:
        st.subheader("Search Project Gutenberg")
        search_query = st.text_input("Search for a book", placeholder="e.g., Pride and Prejudice")
        if search_query:
            books = search_gutenberg(search_query)
            
            if books:
                st.write(f"Found {len(books)} books:")
                for book in books:
                    with st.expander(f"📖 {book['title']} by {book['author']}"):
                        st.write(f"Languages: {', '.join(book['languages'])}")
                        st.write(f"Downloads: {book['download_count']}")
                        
                        if book['text_url']:
                            if st.button(f"Process this book", key=book['id']):
                                text = fetch_book_text(book['text_url'])
                                if text:
                                    st.session_state.book_text = text
                                    st.session_state.book_title = book['title']
                                    st.experimental_rerun()
    
    with upload_col:
        st.subheader("Or Upload Your Own Text")
        uploaded_file = st.file_uploader("Upload a text file", type=['txt'])
        if uploaded_file:
            st.session_state.book_text = uploaded_file.read().decode('utf-8')
            st.session_state.book_title = uploaded_file.name

if __name__ == "__main__":
    main()