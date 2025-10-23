from langfuse.openai import openai
import dotenv
from pathlib import Path

dotenv.load_dotenv()

def load_docs():
    docs = {}
    docs_dir = Path("ufcDocs")

    for file_path in docs_dir.glob("*.txt"):
        with open(file_path, 'r') as f:
            docs[file_path.stem] = f.read()

    return docs

def search(query):
    DOCS = load_docs()
    query_words = query.lower().split()
    results = []
    
    for name, content in DOCS.items():
        if any(word in content.lower() for word in query_words):
            results.append(content)
    
    return results[:2]

def answer_question(question, session_id="demo_session"):
    docs = search(question)
    context = "\n".join(docs) if docs else "No info found."
    response = openai.chat.completions.create(
        name="qa-bot",
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": "Answer based on context. Be brief."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
        ],
        metadata={
            "langfuse_session_id": session_id,
            "langfuse_user_id": "robert"
        }
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    session = "convo-1"

    answer_question("What is your refund policy???", session)
    answer_question("What does your pricing plan look like?", session)
    answer_question("How is the shipping?", session)