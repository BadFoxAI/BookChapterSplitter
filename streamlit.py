import streamlit as st
import requests

def main():
    st.set_page_config(
        page_title="Book Chapter Splitter",
        page_icon="📚",
        layout="wide"
    )

    st.title("📚 Book Chapter Splitter v0.02")
    
    st.markdown("""
    ### Test deployment
    
    Simple test to verify deployment works.
    """)

    if st.button("Test Connection"):
        try:
            response = requests.get("https://gutendex.com/books/")
            st.success("Connection to Gutenberg API successful!")
        except Exception as e:
            st.error(f"Connection test failed: {e}")

if __name__ == "__main__":
    main()