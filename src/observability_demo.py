from langfuse import Langfuse
from langfuse.openai import openai
from langfuse import observe
import dotenv
from pathlib import Path
import json
from datetime import datetime

dotenv.load_dotenv()
langfuse = Langfuse(environment="testing")

@observe(name="generate_traceName_and_tags", as_type="generation")
def extract_trace_and_tags(question):
    VALID_TAGS = [
        "fighters",
        "statistics",
        "rankings",
        "events",
        "history",
        "rules",
        "predictions",
        "records",
        "techniques",
        "general",
        "opinion",
        "weightclass",
        "training methodology",
        "injury",
        "competition analysis"
    ]
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""Extract a concise session name (1-2 words) and 1-2 relevant tags from the question.
            
            You MUST select tags ONLY from this list: {', '.join(VALID_TAGS)}
            
            Return as JSON: {{"session": "SessionName", "tags": ["Tag1", "Tag2"]}}
            
            Session should be the main topic. Tags must be from the valid list above."""},
            {"role": "user", "content": question}
        ],
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    
    tags = result.get("tags", ["general"])
    validated_tags = [tag for tag in tags if tag.lower() in [t.lower() for t in VALID_TAGS]]
    
    if not validated_tags:
        validated_tags = ["general"]
    
    return result.get("session", "General"), validated_tags

@observe(name="load_docs")
def load_docs():
    docs = {}
    docs_dir = Path("data/ufcDocs")

    for file_path in docs_dir.glob("*.txt"):
        with open(file_path, 'r') as f:
            docs[file_path.stem] = f.read()

    return docs

@observe(as_type="generation")
def answer_question(question, trace_name = "default", session_id="default", user_id="guest", tags=[]):
    
    DOCS = load_docs()
    context = "\n\n".join(DOCS.values())
    
    response = openai.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "Answer based on context. Be brief."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
        ]
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    user_id = input("Enter your user ID: ").strip() or "guest"
    session_id = f"{user_id}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    print(f"\n Welcome {user_id}!")

    while True:
        question = input("Your question: ").strip()
        if not question:
            break

        trace_name, tags = extract_trace_and_tags(question)

        langfuse.update_current_trace(
            name=trace_name,
            session_id=session_id,
            user_id=user_id,
            tags=tags
        )
        answer = answer_question(question, trace_name, session_id, user_id, tags)
        print(f"\n Answer: {answer}\n")
        