# Flashcard Generator

Flashcard Generator is a web application that uses FastAPI and Google Gemini to generate flashcards from various document formats. This project helps in managing and summarizing study materials easily.

## Features
- Supports various document formats (PDF, DOCX, PPTX, XLSX, CSV)
- Generates flashcards from YouTube URLs
- Testable via Swagger UI

## Project Structure
```perl
<project_root>/
├── app/
│   ├── api/ 
│   │   ├── error_utilities.py
│   │   ├── router.py
│   │   ├── tool_utilities.py
│   │   └── tools_config.json
│   ├── features/ 
│   │   └── dynamo/
│   │        ├── loaders/
│   │        │   ├── docx_loader.py
│   │        │   ├── pdf_loader.py
│   │        │   ├── pptx_loader.py 
│   │        │   ├── xlsx_loader.py
│   │        │   ├── csv_loader.py
│   │        │   └── youtube_loader.py
│   │        ├── prompt/
│   │        │   ├── dynamo-prompt.txt
│   │        │   ├── examples.txt
│   │        │   └── summarize-prompt.txt
│   │        ├── core.py
│   │        ├── tools.py
│   │        └── metadata.json
│   ├── services/
│   │   ├── logger.py
│   │   ├── schemas.py
│   │   └── tool_registry.py
│   ├── utils/
│   │   ├── auth.py
│   └── main.py
├── .gitignore
├── Dockerfile
├── LICENSE
├── README.md
└── requirements.txt
``` 

## Installation and Running

### Running Locally
1. Clone the repository.
```bash
git clone https://github.com/youngsunlee07/GeminiFlashcardGenerator.git
cd flashcard-generator
```

2. Create and activate a virtual environment.

```bash
python -m venv venv
source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
```

3. Install the required packages.

```bash
pip install -r requirements.txt
```

4. Set up environment variables.

```bash
export GOOGLE_API_KEY=your_google_api_key
```

5. Create a .env file in the root folder based on the .env.sample file.

```bash
cp .env.sample .env
```

5. Run the application.

```bash
uvicorn app.main:app --reload
```

6. Open http://127.0.0.1:8000/docs in your browser to test the API using Swagger UI.


## Usage
1. Access Swagger UI: Open http://127.0.0.1:8000/docs in your browser.

2. Try it out:
- Click on the POST /upload-content section to expand it.
- Click the Try it out button to enable the input fields.

3. Fill in the Parameters: 
max_flashcards: Set the desired number of flashcards to generate (default is 10).
api-key: Enter dev as the API key.

4. Upload Content:
- YouTube URL: Enter a YouTube URL in the youtube_url field.
- Files: Click on the Add string item button under the files array to upload files. You can upload any supported document formats (PDF, DOCX, PPTX, XLSX, CSV).
- You can fill in either the YouTube URL, upload files, or do both.

5. Execute:
- Click the Execute button to send the request.

This process will generate flashcards based on the uploaded content or the provided YouTube URL. 
You can view the results in the response section of the Swagger UI.

## License
This project is distributed under the MIT License. See the LICENSE file for more information.

## Contact
For any inquiries about the project, please contact your-email@example.com.















