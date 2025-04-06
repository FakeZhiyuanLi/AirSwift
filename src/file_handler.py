import os
from PIL import Image
from llm_client import LLMClient
import pypdf
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import csv

llm_api = LLMClient()

def process_file(file_path):
    root, extension = os.path.splitext(file_path)
    if extension == ".txt":
        return process_text_file(file_path)
    elif extension == ".csv":
        return process_csv_file(file_path)
    elif (extension == ".jpg" or extension == ".png" or extension == ".jpeg"):
        return process_image_file(file_path)
    else:
        print("File type not supported")

def process_text_file(abs_file_path) -> str:
    with open(abs_file_path, 'r') as fp:
        text_content = fp.read()
    text_desc = llm_api.caption_text(text_content)
    return text_desc

def process_image_file(abs_file_path: str) -> str:
    image = llm_api.encode_image(abs_file_path)
    image_desc = llm_api.caption_image(image)
    return image_desc

def process_csv_file(abs_file_path: str) -> str:
    text = []
    with open(abs_file_path, 'r') as fp:
        csv_reader = csv.reader(fp)
        header = next(csv_reader)
        for row in csv_reader:
            text.append(row)
    csv_desc = llm_api.caption_csv(str(text))
    return csv_desc

def process_pdf_file(abs_file_path: str) -> str:
    if pdf_has_text(abs_file_path):
        text = extract_text_pdf(abs_file_path)
        return text
    else:
        text = extract_text_scanned_pdf(abs_file_path)
        return text
    
#Gets content from all pages, text pdf
def extract_text_pdf(abs_file_path) -> str:
    text = []
    with pdfplumber.open(abs_file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)

#Scans page, gets content and returns
def extract_text_scanned_pdf(abs_file_path) -> str:
    pages = convert_from_path(abs_file_path, dpi=200)
    text = []
    for page in pages:
        page_text = pytesseract.image_to_string(page, lang='eng')
        text.append(page_text)
    return "\n".join(text)

def pdf_has_text(abs_file_path) -> bool:
    try:
        with open(abs_file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            if reader.is_encrypted:
                reader.decrypt("") #descrypts without password  
            if len(reader.pages) == 0: #checks if no pages
                return False
            first_page = reader.pages[0]
            text = first_page.extract_text()
            if text and text.strip(): #checks if there is text, no text means scanned
                return True
            return False
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return False