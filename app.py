import streamlit as st
from streamlit_navigation_bar import st_navbar
import base64
import requests
from io import BytesIO



def reset_chat():
    st.session_state.messages = []  
    st.session_state.history = []  
    st.session_state.pdf_history = []  

def displayPDF(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
    pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%" height="700"
            type="application/pdf"
            style="min-width: 400px;"
        >
        </iframe>
        """
    st.markdown(pdf_display, unsafe_allow_html=True)


def upload_file_to_chatpdf(uploaded_file):
    files = [
        ('file', (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf'))
    ]
    headers = {
        'x-api-key': st.session_state.file_qa_api_key  
    }

    response = requests.post(
        'https://api.chatpdf.com/v1/sources/add-file', headers=headers, files=files, verify=False)

    if response.status_code == 200:  
        return response.json()['sourceId']
    else:
        st.error(f"Upload failed: {response.status_code}, {response.text}")  
        return None

def chatpdf_api_call(question, uploaded_file, url_chat=None):  
    headers = {
        'x-api-key': st.session_state.file_qa_api_key,
        "Content-Type": "application/json",
    }

    if uploaded_file:
        source_id = upload_file_to_chatpdf(uploaded_file)
    elif url_chat:
        source_id = upload_url_to_chatpdf(url_chat)

    data = {
        'sourceId': source_id,
        'messages': [
            {
                'role': "user",
                'content': question,
            }
        ]
    }

    response = requests.post(
        'https://api.chatpdf.com/v1/chats/message', headers=headers, json=data)

    if response.status_code == 200:
        return response.json().get('content', 'No content available')  
    else:
        st.error(f"Error: {response.status_code}, {response.text}")  
        return None

def upload_url_to_chatpdf(url_chat):
    headers = {
        'x-api-key': st.session_state.file_qa_api_key,
        'Content-Type': 'application/json'
    }
    data = {'url': url_chat}

    response = requests.post(
        'https://api.chatpdf.com/v1/sources/add-url', headers=headers, json=data)

    if response.status_code == 200:
        return response.json()['sourceId']
    else:
        st.error(f"Failed to upload URL: {response.status_code}, {response.text}")
        return None

def fetch_pdf_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content) 
    else:
        st.error(f"Failed to fetch PDF from URL: {response.status_code}, {response.text}")
        return None 

def download_history():
    if not st.session_state.messages:  
        st.error("No chat history available to download.")
        return  

    history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
    b64 = base64.b64encode(history.encode()).decode()  
    href = f'<a href="data:file/txt;base64,{b64}" download="history.txt">Download Chat History</a>'
    st.markdown(href, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Chat-PDF", page_icon="📖", layout="wide")
    page = st_navbar(["Home", "Documentation", "Examples", "Community", "About"])


    if "history" not in st.session_state:
        st.session_state.history = None
    if "file_qa_api_key" not in st.session_state:  
        st.session_state.file_qa_api_key = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pdf_history" not in st.session_state:
        st.session_state.pdf_history = []
        
    if page == "Home":  
        title = '<p style="font-family:sans-serif; color:white; font-size: 42px; text-align: center;">Chat Any PDF</p>'
        st.markdown(title, unsafe_allow_html=True)
        text = '<p style="font-family:sans-serif; color:grey; font-size: 25px; text-align: center;">Join millions of students, researchers and professionals to instantly answer questions and understand research with AI</p>'
        st.markdown(text, unsafe_allow_html=True) 
        uploaded_file = st.file_uploader(
                "Upload file", type=["pdf"], 
                help="Only PDF files are supported",
                key="file_uploaded_pdf"
                )
        url_input = st.text_input("Enter URL to convert to PDF", placeholder="https://example.com",help= "Only https://.pdf is supported")
        
        if url_input:
            source_id = upload_url_to_chatpdf(url_input)   
            if source_id:  
                pdf_data = fetch_pdf_from_url(url_input)
        

    if page == "Documentation":  
        with st.sidebar:  
            st.session_state.file_qa_api_key = "sec_jYRuRnRgI4ZunMd6eug2fQKzsV31twn8"

            uploaded_file = st.file_uploader(
                "Upload file", type=["pdf"], 
                help="Only PDF files are supported",
                key="file_uploaded_pdf"
                )
            url_input = st.text_input("Enter URL to convert to PDF", placeholder="https://example.com",help= "Only https://.pdf is supported")
            if url_input:
                source_id = upload_url_to_chatpdf(url_input)   
                if source_id:  
                    pdf_data = fetch_pdf_from_url(url_input)

            st.radio("All Chats", ("User",), key="chat_history_selection")

            
            if st.session_state.get("chat_history_selection") == "User":
                for message in st.session_state.messages:
                    if message["role"] == "user":
                        st.write(message["content"])  
            # else:
            #     for message in st.session_state.messages:
            #         if message["role"] == "assistant":
            #             st.write(message["content"])  
            
            
            if st.button("Download Chat History"):
                    download_history()

        col1, col2 = st.columns(spec=[2,1], gap="large")
        
        if uploaded_file or url_input:  
            with col1:
                if uploaded_file:  
                    displayPDF(uploaded_file)  
                elif url_input and source_id:  
                    pdf_data = fetch_pdf_from_url(url_input)  
                    if pdf_data:  
                        displayPDF(pdf_data) 
                    else:
                        st.error("Failed to fetch PDF data from the URL.")  
            with col2:
                
                messages = st.container(height=550)  
                
                for message in st.session_state.messages:
                    messages.chat_message(message["role"]).write(message["content"])

                if prompt := st.text_input("Ask something about the article", placeholder="Ask PDF", 
                                           disabled=not (uploaded_file or pdf_data),  
                                           value=st.session_state.get('question', '')):  
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    messages.chat_message("user").write(prompt)
                    question = prompt
                else:
                    question = None
                if st.button("New Chat"):
                    reset_chat()  

                if (uploaded_file or pdf_data) and question and not st.session_state.file_qa_api_key:
                    st.info("Please add your ChatPDF API key to continue.")

                if (uploaded_file or pdf_data) and question and st.session_state.file_qa_api_key:
                    response = chatpdf_api_call(question, uploaded_file, url_input)  
                    st.session_state.messages.append({"role": "assistant", "content": response})  
                    if response:
                        messages.chat_message("assistant").write(response)
                    else:
                        st.error("Failed to retrieve response from ChatPDF API.")
                else:
                    
                    st.session_state['question'] = ''  
        else:
            reset_chat()  

    if page == "Community":  
        st.markdown('<h1 style="text-align: center;">Join the ChatPDF Community</h1>', unsafe_allow_html=True)
        st.markdown("""
            <p style="text-align: center;">Connect with users, share tips, and enhance your ChatPDF experience!</p>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)  
            st.image("download.png", width=100)  
            st.markdown("<div style='text-align: center;'>Get support from ChatPDF experts 🤔</div>", unsafe_allow_html=True)  
            st.markdown("</div>", unsafe_allow_html=True)  
        with col2:
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)  
            st.image("share.png", width=100)  
            st.markdown("<div style='text-align: center;'>Share your ChatPDF success stories 👋</div>", unsafe_allow_html=True)  
            st.markdown("</div>", unsafe_allow_html=True)  
        with col3:
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)  
            st.image("cihuy.jpg", width=100)  
            st.markdown("<div style='text-align: center;'>Join a ChatPDF user group 👥</div>", unsafe_allow_html=True)  
            st.markdown("</div>", unsafe_allow_html=True)  
        with col4:
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)  
            st.image("kal.png", width=100)  
            st.markdown("<div style='text-align: center;'>Participate in ChatPDF events 🏅</div>", unsafe_allow_html=True)  
            st.markdown("</div>", unsafe_allow_html=True)  

        st.markdown('<h2 style="text-align: center;">Find your ChatPDF community events</h2>', unsafe_allow_html=True)
                

    if page == "About":  
        st.markdown('<h1 style="text-align: center;">Tentang ChatPDF</h1>', unsafe_allow_html=True)
        st.markdown("""
            <p style="text-align: center; font-size: 20px;">
                ChatPDF adalah alat inovatif yang memungkinkan Anda untuk berinteraksi dengan dokumen PDF secara langsung. 
                Dengan menggunakan teknologi AI canggih, Anda dapat mengajukan pertanyaan dan mendapatkan jawaban instan 
                dari konten PDF Anda. 
            </p>
            <p style="text-align: center; font-size: 20px;">
                Apakah Anda seorang pelajar, peneliti, atau profesional? ChatPDF membantu Anda memahami dan menganalisis 
                informasi dengan lebih efisien. Bergabunglah dengan jutaan pengguna yang telah merasakan manfaatnya!
            </p>
            <p style="text-align: center; font-size: 20px;">
                Temukan cara baru untuk belajar dan berkolaborasi dengan ChatPDF. 
                Mari kita ubah cara kita berinteraksi dengan informasi!
            </p>
        """, unsafe_allow_html=True)

if __name__ == '__main__':
    main()
