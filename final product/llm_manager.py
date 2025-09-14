import requests
from dotenv import dotenv_values
from llm_manager import query_llm

env = dotenv_values(".env")
SEARCH_API_KEY = env.get("SEARCH_API_KEY")  # Serper API key
SEARCH_ENGINE = "serper"

def fetch_search_results(query):
    """Fetch search results using Serper API."""
    if not SEARCH_API_KEY:
        return "⚠ Search API key missing."

    try:
        if SEARCH_ENGINE == "serper":
            url = "https://google.serper.dev/search"
            headers = {"X-API-KEY": SEARCH_API_KEY, "Content-Type": "application/json"}
            payload = {"q": query}
            res = requests.post(url, headers=headers, json=payload).json()
            results = []
            for r in res.get("organic", [])[:5]:
                results.append(f"{r.get('title')} - {r.get('link')}")
            return "\n".join(results) if results else "No search results found."
        
        return "⚠ Search engine not implemented."
    except Exception as e:
        return f"⚠ Search fetch failed: {e}"

def RealtimeSearchEngine(query, history=None):
    """Fetch results and summarize with LLM (Groq → OpenAI fallback)."""
    search_results = fetch_search_results(query)

    prompt = f"""
    You are a helpful assistant. A user searched for:
    "{query}"

    Here are the top search results:
    {search_results}

    Summarize the results clearly and give a useful answer.
    """

    return query_llm(prompt, history)