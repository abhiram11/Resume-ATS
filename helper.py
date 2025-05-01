import google.generativeai as genai
import PyPDF2 as pdf
import json
import requests  # For Deepseek API
from docx import Document  # For Word document processing
import io  # For handling file objects


def configure_genai(api_key):
    """Configure the Generative AI API with error handling."""
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        raise Exception(f"Failed to configure Generative AI: {str(e)}")

def configure_deepseek(api_key):
    """Configure Deepseek API key in session."""
    if not api_key:
        raise Exception("Deepseek API key is required")
    return api_key

def get_gemini_response(prompt):
    """Generate a response using Gemini with enhanced error handling and response validation."""
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        
        # Ensure response is not empty
        if not response or not response.text:
            raise Exception("Empty response received from Gemini")
            
        # Try to parse the response as JSON
        try:
            response_json = json.loads(response.text)
            
            # Validate required fields
            required_fields = ["Job Description Match", "Profile Summary", "Technical Skills Match", "Non-Technical and Soft Skills Match", "Missing Keywords"]
            for field in required_fields:
                if field not in response_json:
                    raise ValueError(f"Missing required field: {field}")
                    
            return response.text
            
        except json.JSONDecodeError:
            # If response is not valid JSON, try to extract JSON-like content
            import re
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, response.text, re.DOTALL)
            if match:
                return match.group()
            else:
                raise Exception("Could not extract valid JSON response")
                
    except Exception as e:
        raise Exception(f"Error generating Gemini response: {str(e)}")

def get_deepseek_response(prompt, api_key):
    """Generate a response using Deepseek API."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Deepseek API error: {response.text}")
            
        response_data = response.json()
        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not content:
            raise Exception("Empty response received from Deepseek")
            
        # Validate the response format
        try:
            response_json = json.loads(content)
            required_fields = ["Job Description Match", "Profile Summary", "Technical Skills Match", "Non-Technical and Soft Skills Match", "Missing Keywords"]
            for field in required_fields:
                if field not in response_json:
                    raise ValueError(f"Missing required field: {field}")
            return content
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, content, re.DOTALL)
            if match:
                return match.group()
            raise Exception("Could not extract valid JSON response from Deepseek")
            
    except Exception as e:
        raise Exception(f"Error generating Deepseek response: {str(e)}")

def extract_pdf_text(uploaded_file):
    """Extract text from PDF with enhanced error handling."""
    try:
        reader = pdf.PdfReader(uploaded_file)
        if len(reader.pages) == 0:
            raise Exception("PDF file is empty")
            
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
                
        if not text:
            raise Exception("No text could be extracted from the PDF")
            
        return " ".join(text)
        
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")
    

def extract_docx_text(uploaded_file):
    """Extract text from Word document (.docx) with error handling."""
    try:
        # Create a file-like object from the uploaded file
        file_stream = io.BytesIO(uploaded_file.read())
        
        # Load the document
        doc = Document(file_stream)
        
        # Extract text from all paragraphs
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():  # Skip empty paragraphs
                text.append(paragraph.text)
                
        if not text:
            raise Exception("No text could be extracted from the Word document")
            
        return "\n".join(text)
        
    except Exception as e:
        raise Exception(f"Error extracting Word document text: {str(e)}")

def prepare_prompt(resume_text, job_description):
    """Prepare the input prompt with improved structure and validation."""
    if not resume_text or not job_description:
        raise ValueError("Resume text and job description cannot be empty")
        
    prompt_template = """
    Act as an expert ATS (Applicant Tracking System) specialist with deep expertise in all professional, technical, non-technical, business, skills, evaluate the following resume against the job description. Consider that the job market is highly competitive. Provide detailed feedback for resume improvement.
    
    Resume:
    {resume_text}
    
    Job Description:
    {job_description}
    
    Provide a response in the following JSON format ONLY:
    {{
        "Job Description Match": "percentage between 0-100",
        "Profile Summary": "detailed analysis of the resume as an object with keys as {{'Full Name', 'Total Years of Experience', 'Skills', 'Education', 'Work Experiences - it can be a nested object'}}",
        "Technical Skills Match" : "percentage between 0-100 for technical skills",
        "Non-Technical and Soft Skills Match" :"percentage between 0-100",
        "Missing Keywords" : ["keyword1", "keyword2", ...],
    }}
    """
    
    return prompt_template.format(
        resume_text=resume_text.strip(),
        job_description=job_description.strip()
    )