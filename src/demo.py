from langfuse import Langfuse
from langfuse.openai import openai
import dotenv
from pathlib import Path

dotenv.load_dotenv()
langfuse = Langfuse(environment="production")

def load_docs():
    docs = {}
    docs_dir = Path("data/ufcDocs")

    for file_path in docs_dir.glob("*.txt"):
        with open(file_path, 'r') as f:
            docs[file_path.stem] = f.read()

    return docs


def answer_question(question, session_id="demo_session", user_id="guest"):
    DOCS = load_docs()
    context = "\n\n".join(DOCS.values())
    
    response = openai.chat.completions.create(
        name="UFC Bot",
        model="gpt-5",
        messages=[
            {"role": "system", "content": "Answer based on context. Be brief."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
        ],
        metadata={
            "langfuse_session_id": session_id,
            "langfuse_user_id": user_id,
        }
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    session = "Ufc Questions no shipping"
    user_id = "Dana White"

    answer_question("What percentage of UFC fights take place at distance?", session, user_id)
    answer_question("What are the most common training injuries?", session, user_id)
    answer_question("What is the UFC PI training methodology?", session, user_id)
    