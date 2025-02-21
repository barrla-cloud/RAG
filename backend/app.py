from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from dotenv import load_dotenv
import time
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import weaviate
import os
import logging
from sentence_transformers import SentenceTransformer


# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

# ✅ Configure Logging (Tracks errors, AI calls, and scraping failures)
logging.basicConfig(
    filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# ✅ Initialize Google Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Initialize Weaviate Client (Handles database of scraped content)
client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(api_key=WEAVIATE_API_KEY)
)

# ✅ Load Pretrained Embedding Model (For converting text to vectors)
embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

# ✅ Initialize FastAPI app
app = FastAPI()

# ✅ CORS Middleware (Allows frontend requests from any domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Cache AI responses to optimize performance
ai_response_cache: Dict[str, str] = {}


# 📌 Request Models
class UrlList(BaseModel):
    """Represents a list of URLs for scraping."""
    urls: List[str]
    namespace: str  # Used for organizing scraped data


class UserQuery(BaseModel):
    """Represents a user’s query for AI processing."""
    query: str
    personality: str  # AI Personality (Formal, Casual, Humorous)


# ✅ Create Weaviate Schema (Executes only once if schema does not exist)
def create_weaviate_schema():
    """Ensures Weaviate database schema exists for storing scraped content."""
    schema = {
        "classes": [
            {
                "class": "ScrapedData",
                "vectorizer": "none",
                "properties": [
                    {"name": "url", "dataType": ["string"]},
                    {"name": "text", "dataType": ["text"]},
                ],
            }
        ]
    }

    existing_classes = [c["class"] for c in client.schema.get()["classes"]]

    if "ScrapedData" not in existing_classes:
        client.schema.create(schema)
        logging.info("✅ Weaviate Schema Created Successfully")
    else:
        logging.info("✅ Schema Already Exists")


# ✅ Ensure schema is created at startup
create_weaviate_schema()


def scrape_content(url: str, char_limit=None) -> str:
    """
    Scrapes all visible text from a given URL and saves it into a text file.
    
    Args:
        url (str): The website URL to scrape.
        char_limit (int, optional): Limit for the extracted text. Defaults to 5000.
    
    Returns:
        str: Extracted content from the page.
    """
    try:
        # Set headers to mimic a real browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # Send HTTP request
        response = requests.get(url, headers=headers, timeout=10)

        # Check if request was successful
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract only visible text
            visible_text = soup.get_text(separator="\n", strip=True)

            # Apply character limit (if set)
            extracted_text = visible_text[:char_limit] if char_limit else visible_text

            # ✅ Save to text file
            with open("extracted_text.txt", "a", encoding="utf-8") as file:
                file.write(f"\nURL: {url}\n")
                file.write(f"{extracted_text}\n")
                file.write("=" * 80 + "\n")  # Separator for readability

            logging.info(f"✅ Successfully scraped and saved content for {url}")
            return extracted_text

        else:
            logging.error(f"❌ Failed to retrieve {url}. HTTP Status: {response.status_code}")
            return ""

    except requests.RequestException as e:
        logging.error(f"❌ Failed to scrape {url}: {e}")
        return ""

# ✅ API Endpoint: Scrape Multiple URLs
@app.post("/scrape")
def scrape_multiple_urls(data: UrlList):
    """
    Scrapes multiple URLs and stores the content in Weaviate.

    Args:
        data (UrlList): Contains URLs and namespace.

    Returns:
        dict: Dictionary of scraped content.
    """
    results = {}
    namespace = data.namespace

    for url in data.urls:
        content = scrape_content(url)
        if content:
            results[url] = content
            try:
                embedding = generate_query_embedding(content)
                client.data_object.create(
                    class_name="ScrapedData",
                    data_object={"url": url, "text": content[:5000]},
                    vector=embedding,
                )
                logging.info(f"✅ Data inserted into Weaviate for {url}")
            except Exception as e:
                logging.error(f"❌ Embedding failed for {url}: {e}")

    if not results:
        raise HTTPException(status_code=400, detail="No valid content retrieved.")
    
    return {"content": results}


# ✅ API Endpoint: Ask AI a Question
@app.post("/ask")
def ask_question(data: UserQuery):
    """
    Retrieves relevant content using Weaviate and generates a response using AI.

    Args:
        data (UserQuery): User query and AI personality.

    Returns:
        dict: AI-generated response.
    """
    # ✅ Check Cache Before Querying AI
    if data.query in ai_response_cache:
        logging.info(f"✅ Returning cached AI response for query: {data.query}")
        return {"answer": ai_response_cache[data.query]}

    query_embedding = generate_query_embedding(data.query)

    response = client.query.get(
        class_name="ScrapedData", properties=["url", "text"]
    ).with_near_vector({"vector": query_embedding}).with_limit(5).do()

    matches = response.get("data", {}).get("Get", {}).get("ScrapedData", [])

    if matches:
        context = "\n".join([match.get("text", "") for match in matches if "text" in match])

        # ✅ AI Personality Implementation
        personality_prompt = {
            "formal": "Provide a professional and structured response.",
            "casual": "Respond in a friendly and conversational tone.",
            "humorous": "Reply in a funny and engaging manner."
        }.get(data.personality, "Provide a standard response.")

        # ✅ Generate Response with Gemini AI
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(f"Context: {context}\n\n{personality_prompt}\n\nAnswer the question: {data.query}")

        if response and hasattr(response, "text"):
            ai_response_cache[data.query] = response.text  # ✅ Cache AI response
            logging.info(f"✅ Cached AI response for query: {data.query}")
            return {"answer": response.text}

        logging.warning("⚠ AI model blocked response.")
        return {"answer": "AI model blocked response due to sensitive content."}

    logging.info("⚠ No relevant content found for the query.")
    return {"answer": "No relevant content found."}


# ✅ Helper Function: Generate Query Embeddings
def generate_query_embedding(query: str):
    """
    Converts a text query into a numerical vector embedding.

    Args:
        query (str): The input text.

    Returns:
        list: The vector representation of the query.
    """
    try:
        return embedding_model.encode(query).tolist()
    except Exception as e:
        logging.error(f"❌ Failed to generate query embedding: {e}")
        raise Exception(f"Failed to generate query embedding: {e}")
