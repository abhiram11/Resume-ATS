import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import os
import json
from dotenv import load_dotenv
from helper import configure_genai, get_gemini_response, extract_pdf_text, prepare_prompt, configure_deepseek, get_deepseek_response
from helper import extract_docx_text  # Add this import

def init_session_state():
    """Initialize session state variables."""
    if 'processing' not in st.session_state:
        st.session_state.processing = False


def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize session state
    init_session_state()
    
    # Configure API keys
    google_api_key = os.getenv("GOOGLE_API_KEY")
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    
    # Sidebar
    with st.sidebar:
        st.title("🎯 Smart ATS")
        st.subheader("About")
        st.write("""
        This smart ATS helps you:
        - Evaluate resume-job description match
        - Get summarized candidate information
        - Find missing keywords to enhance match score
        """)
        
        # Model selection
        model_provider = st.selectbox(
            "Select AI Provider",
            ("Gemini", "Deepseek"),
            help="Choose which AI model to use for analysis"
        )

    # Main content
    st.title("📄 Smart ATS Resume Analyzer")
    st.subheader("Optimize Your Resume for ATS")
    
    # Input sections with validation
    jd = st.text_area(
        "Job Description",
        placeholder="Paste the job description here...",
        help="Enter the complete job description for accurate analysis"
    )
    
    # Resume input options
    resume_input_method = st.radio(
        "Resume Input Method",
        ("Upload PDF", "Upload Word (docx)", "Upload Text File", "Paste Text"),
        horizontal=True
    )
    
    resume_text = ""
    if resume_input_method == "Upload PDF":
        uploaded_file = st.file_uploader(
            "Resume (PDF)",
            type="pdf",
            help="Upload your resume in PDF format"
        )
        if uploaded_file:
            resume_text = extract_pdf_text(uploaded_file)

    elif resume_input_method == "Upload Word (docx)":
        uploaded_file = st.file_uploader(
            "Resume (Word)",
            type=["docx"],
            help="Upload your resume in Word document format"
        )
        if uploaded_file:
            resume_text = extract_docx_text(uploaded_file)
      
            
    elif resume_input_method == "Upload Text File":
        uploaded_file = st.file_uploader(
            "Resume (Text)",
            type=["txt"],
            help="Upload your resume as a text file"
        )
        if uploaded_file:
            resume_text = uploaded_file.read().decode("utf-8")
            
    else:  # Paste Text
        resume_text = st.text_area(
            "Paste Resume Text",
            placeholder="Paste your resume text here...",
            help="Directly paste your resume content"
        )

    # Process button with loading state
    if st.button("Analyze Resume", disabled=st.session_state.processing):
        if not jd:
            st.warning("Please provide a job description.")
            return
            
        if not resume_text:
            st.warning("Please provide your resume.")
            return
            
        st.session_state.processing = True
        
        try:
            with st.spinner("📊 Analyzing your resume..."):
                # Prepare prompt
                input_prompt = prepare_prompt(resume_text, jd)
                
                # Get response based on selected model
                if model_provider == "Gemini":
                    if not google_api_key:
                        st.error("Please set the GOOGLE_API_KEY in your .env file")
                        return
                    configure_genai(google_api_key)
                    response = get_gemini_response(input_prompt)
                else:  # Deepseek
                    if not deepseek_api_key:
                        st.error("Please set the DEEPSEEK_API_KEY in your .env file")
                        return
                    configure_deepseek(deepseek_api_key)
                    response = get_deepseek_response(input_prompt, deepseek_api_key)
                
                response_json = json.loads(response)
                
                # Display results
                st.success("✨ Analysis Complete!")
                
                # Match percentage
                match_percentage = response_json.get("Job Description Match", "N/A")
                st.metric("Match Score", match_percentage)
                
                # Profile summary
                st.subheader("Profile Summary")
                st.write(response_json.get("Profile Summary", "No summary available"))
                
                # Technical Skills Match
                st.subheader("Technical Skills Score")
                st.write(response_json.get("Technical Skills Match", "N/A"))
                
                # Profile summary
                st.subheader("Non-Technical and Soft Skills Score")
                st.write(response_json.get("Non-Technical and Soft Skills Match", "N/A"))
                
                # Missing keywords
                st.subheader("Missing Keywords")
                missing_keywords = response_json.get("Missing Keywords", [])
                if missing_keywords:
                    st.write(", ".join(missing_keywords))
                else:
                    st.write("No critical missing keywords found!")
                

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            
        finally:
            st.session_state.processing = False

if __name__ == "__main__":
    main()