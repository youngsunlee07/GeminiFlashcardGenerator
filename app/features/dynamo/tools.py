import os
from dotenv import load_dotenv

# Load the contents of the .env file
load_dotenv()

from fastapi import HTTPException, UploadFile
from app.services.logger import setup_logger
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser  # Modified here
from langchain_core.pydantic_v1 import BaseModel, Field
from app.api.error_utilities import VideoTranscriptError, LoaderError
from app.features.dynamo.loaders.youtube_loader import YoutubeLoader
from app.features.dynamo.loaders.pdf_loader import PDFLoader
from app.features.dynamo.loaders.docx_loader import DOCXLoader
from app.features.dynamo.loaders.pptx_loader import PPTXLoader 
from app.features.dynamo.loaders.xlsx_loader import XLSXLoader
from app.features.dynamo.loaders.csv_loader import CSVLoader
from app.features.dynamo.loaders.youtube_loader import YoutubeTranscriptLoader  

logger = setup_logger(__name__)

# Get Google API key
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("Please set the GOOGLE_API_KEY environment variable")

# Initialize AI model
model = GoogleGenerativeAI(model="gemini-1.0-pro", google_api_key=google_api_key)

def get_loader(file: UploadFile):
    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        return PDFLoader
    elif filename.endswith(".docx"):
        return DOCXLoader
    elif filename.endswith(".pptx"):
        return PPTXLoader
    elif filename.endswith(".csv"):
        return CSVLoader
    elif filename.endswith(".xlsx"):
        return XLSXLoader
    elif "youtube.com" in filename:
        return YoutubeTranscriptLoader
    else:
        raise ValueError(f"Unsupported file type: {file.filename}")

def read_text_file(file_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    absolute_file_path = os.path.join(script_dir, file_path)
    with open(absolute_file_path, 'r') as file:
        return file.read()

class Flashcard(BaseModel):
    concept: str = Field(description="The concept of the flashcard")
    definition: str = Field(description="The definition of the flashcard")

def process_chunk(chunk_subset, template, examples, verbose=False):
    full_text = " ".join(doc.page_content for doc in chunk_subset)
    cards_prompt = PromptTemplate(
        template=template,
        input_variables=["summary", "examples"],
        partial_variables={"format_instructions": JsonOutputParser(pydantic_object=Flashcard).get_format_instructions()}
    )

    cards_chain = cards_prompt | model | JsonOutputParser(pydantic_object=Flashcard)

    try:
        response = cards_chain.invoke({"summary": full_text, "examples": examples})
        if not isinstance(response, list):
            raise ValueError(f"Invalid json output: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to generate flashcards from PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards from PDF")

def generate_flashcards_from_files(loader_class, files: list[UploadFile], verbose=False, max_flashcards=10) -> list:
    try:
        loader = loader_class(files)
        documents = loader.load()
    except Exception as e:
        logger.error(f"Failed to load files: {e}")
        raise LoaderError(f"Failed to load files")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = splitter.split_documents(documents)

    chunk_limit = 30
    total_chunks = len(split_docs)
    flashcards = []

    template = read_text_file("prompt/dynamo-prompt.txt")
    examples = read_text_file("prompt/examples.txt")

    for i in range(0, total_chunks, chunk_limit):
        chunk_subset = split_docs[i:i + chunk_limit]
        try:
            result = process_chunk(chunk_subset, template, examples, verbose)
            flashcards.extend(result)
            if len(flashcards) >= max_flashcards:
                break
        except Exception as e:
            logger.error(f"Failed to process chunk: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate flashcards from files")

    return flashcards[:max_flashcards]

def summarize_transcript(youtube_url: str, max_video_length=2000, verbose=False) -> str:
    try:
        loader = YoutubeLoader.from_youtube_url(youtube_url, add_video_info=True)
    except Exception as e:
        logger.error(f"No such video found at {youtube_url} -> {e}")
        raise VideoTranscriptError(f"No video found", youtube_url) from e
    
    try:
        docs = loader.load()
        if not docs:
            logger.error(f"No documents loaded from video at {youtube_url}")
            raise VideoTranscriptError("No documents loaded from video", youtube_url)
        
        # Log the structure and content of the document for debugging
        logger.info(f"Loaded documents: {docs}")
        
        length = docs[0].metadata.get("length")
        title = docs[0].metadata.get("title")
        if not length or not title:
            logger.error(f"Missing metadata in video at {youtube_url}")
            raise VideoTranscriptError("Missing metadata in video", youtube_url)
    except Exception as e:
        logger.error(f"Video transcript might be private or unavailable in 'en' or the URL is incorrect -> {e}")
        raise VideoTranscriptError(f"No video transcripts available", youtube_url) from e
    
    if length > max_video_length:
        raise VideoTranscriptError(f"Video is {length} seconds long, please provide a video less than {max_video_length} seconds long", youtube_url)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0
    )
    
    split_docs = splitter.split_documents(docs)
    
    full_transcript = " ".join(doc.page_content for doc in split_docs)

    if verbose:
        logger.info(f"Found video with title: {title} and length: {length}")
        logger.info(f"Combined documents into a single string.")
        logger.info(f"Beginning to process transcript...")
    
    prompt_template = read_text_file("prompt/summarize-prompt.txt")
    summarize_prompt = PromptTemplate.from_template(prompt_template)

    summarize_model = GoogleGenerativeAI(model="gemini-1.0-pro", google_api_key=google_api_key)
    
    chain = summarize_prompt | summarize_model 
    
    return chain.invoke(full_transcript)

def generate_flashcards(summary: str, verbose=False, max_flashcards=10) -> list:
    parser = JsonOutputParser(pydantic_object=Flashcard)
    
    if verbose: logger.info(f"Beginning to process flashcards from summary")
    
    template = read_text_file("prompt/dynamo-prompt.txt")
    examples = read_text_file("prompt/examples.txt")
    
    cards_prompt = PromptTemplate(
        template=template,
        input_variables=["summary", "examples"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    cards_chain = cards_prompt | model | parser
    
    try:
        response = cards_chain.invoke({"summary": summary, "examples": examples})
        if len(response) > max_flashcards:
            response = response[:max_flashcards]
    except Exception as e:
        logger.error(f"Failed to generate flashcards: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards from LLM")
    
    return response 