from langfuse import Langfuse
from langfuse.openai import openai
from langfuse import observe, get_client
import dotenv
from pathlib import Path

dotenv.load_dotenv()
langfuse = Langfuse(environment="testing")

@observe()
def load_docs():
    docs = {}
    docs_dir = Path("data/ufcDocs")

    for file_path in docs_dir.glob("*.txt"):
        with open(file_path, 'r') as f:
            docs[file_path.stem] = f.read()

    return docs

@observe()
def answer_question(question, session_id="demo_session", user_id="guest", tags=[]):
    langfuse.update_current_trace(
        name="UFC Q&A",
        session_id=session_id,
        user_id=user_id,
        tags=tags
    )
    DOCS = load_docs()
    context = "\n\n".join(DOCS.values())
    
    response = openai.chat.completions.create(
        name="UFC Bot",
        model="gpt-5",
        messages=[
            {"role": "system", "content": "Answer based on context. Be brief."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
        ]
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    session = "Ufc Questions"
    user_id = "Dana White"
    answer_question("What percentage of UFC fights take place at distance?", 
                    session, user_id, ['UFC', 'Competition Analysis'])
    answer_question("What are the most common training injuries?", 
                    session, user_id, ["UFC", "Injury"])
    answer_question("What is the UFC PI training methodology?", 
                    session, user_id, ["UFC", "Training Methodology"])
