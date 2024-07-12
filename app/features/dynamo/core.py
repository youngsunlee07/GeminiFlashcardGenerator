from fastapi import UploadFile
from app.features.dynamo.tools import summarize_transcript, generate_flashcards, generate_flashcards_from_files, get_loader
from app.services.logger import setup_logger
from app.api.error_utilities import VideoTranscriptError, LoaderError

logger = setup_logger(__name__)

def executor(youtube_url: str = None, files: list[UploadFile] = None, verbose=False, max_flashcards=10):
    sanitized_flashcards = []

    if youtube_url:
        try:
            summary = summarize_transcript(youtube_url, verbose=verbose)
            flashcards = generate_flashcards(summary, max_flashcards=max_flashcards, verbose=verbose)
            for flashcard in flashcards:
                if 'concept' in flashcard and 'definition' in flashcard:
                    sanitized_flashcards.append({
                        "concept": flashcard['concept'],
                        "definition": flashcard['definition']
                    })
                else:
                    logger.warning(f"Malformed flashcard skipped: {flashcard}")
        except VideoTranscriptError as e:
            logger.error(f"Error in processing YouTube URL -> {e}")
            raise ValueError(f"Error in processing YouTube URL: {e}")
        except Exception as e:
            logger.error(f"Error in executor: {e}")
            raise ValueError(f"Error in executor: {e}")

    if files:
        for file in files:
            try:
                loader_class = get_loader(file)
                flashcards = generate_flashcards_from_files(loader_class, [file], verbose=verbose, max_flashcards=max_flashcards)
                sanitized_flashcards.extend(flashcards)
            except LoaderError as e:
                logger.error(f"Error in processing {file.filename} -> {e}")
                raise ValueError(f"Error in processing {file.filename}: {e}")
            except Exception as e:
                logger.error(f"Error in executor: {e}")
                raise ValueError(f"Error in executor: {e}")

    return sanitized_flashcards
