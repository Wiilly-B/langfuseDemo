from langfuse.openai import openai
from langfuse import observe, get_client
import dotenv
from pathlib import Path
import json
from datetime import datetime

dotenv.load_dotenv()
langfuse = get_client()

VALID_TAGS = [
        "fighters", "statistics", "rankings",
        "events", "history", "rules",
        "predictions", "records", "techniques",
        "general", "opinion", "weightclass",
        "training methodology", "injury",
        "competition analysis"
    ]

def setup_prompts():
    langfuse.create_prompt(
        name="generate_traceName_and_tags",
        type="chat",
        prompt=[
            {"role": "system", 
             "content": f"""Extract a concise session name (1-2 words) and 1-2 relevant tags from the question.
            
            You MUST select tags ONLY from this list: {', '.join(VALID_TAGS)}
            
            Return as JSON: {{"session": "SessionName", "tags": ["Tag1", "Tag2"]}}
            
            Session should be the main topic. Tags must be from the valid list above."""},
            {"role": "user", 
             "content": "{{user_question}}"}
        ],
        labels=["testing"],
        config={
            "model": "gpt-4o-mini",
            "temperature": 0,
            "response_format": {"type": "json_object"}
        }
    )

    langfuse.create_prompt(
        name="answer_question",
        type="chat",
        prompt=[
            {"role": "system", 
             "content": "You are a UFC expert assistant. Answer questions based on the provided context. "
             "Be accurate and concise. CONTEXT {{user_context}}"},
            {"role": "user", "content": "{{user_question}}"
            }
        ],
        labels=["testing"],
        config={
            "model": "gpt-5",
            "temperature": 1,
        }
    )

@observe(name="load_docs")
def load_docs():
    docs = {}
    docs_dir = Path("data/ufcDocs")

    for file_path in docs_dir.glob("*.txt"):
        with open(file_path, 'r') as f:
            docs[file_path.stem] = f.read()

    return docs


@observe(name="process_question")
def process_question(question, session_id, user_id, conversation_history):
    trace_name, tags = extract_trace_and_tags(question)
    
    langfuse.update_current_trace(
        name=trace_name,
        session_id=session_id,
        user_id=user_id,
        tags=tags
    )
    
    return answer_question(question, conversation_history)


@observe(name="generate_traceName_and_tags", as_type="generation")
def extract_trace_and_tags(question):
    prompt = langfuse.get_prompt(
        name="generate_traceName_and_tags", type="chat", label="testing", cache_ttl_seconds=300)
    compiled_chat_prompt = prompt.compile(user_question=question)

    response = openai.chat.completions.create(
        messages=compiled_chat_prompt,
        model=prompt.config["model"],
        temperature=prompt.config["temperature"],
        response_format=prompt.config["response_format"],
        langfuse_prompt=prompt,
    )

    result = json.loads(response.choices[0].message.content)
    
    tags = result.get("tags", ["general"])
    validated_tags = [tag for tag in tags if tag.lower() in [t.lower() for t in VALID_TAGS]]
    
    if not validated_tags:
        validated_tags = ["general"]
    
    return result.get("session", "General"), validated_tags


@observe(name="answer_generation", as_type="generation")
def answer_question(question, conversation_history):
    DOCS = load_docs()
    context = "\n\n".join(DOCS.values())

    # Increasing cache_ttl_seconds meaning 1 api call every 300 seconds therefore improves performance
    prompt = langfuse.get_prompt(
        name="answer_question", type="chat", label="testing", cache_ttl_seconds=300)
    compiled_chat_prompt = prompt.compile(user_context=context, user_question=question)
    
    messages = [compiled_chat_prompt[0]] # System message with context
    messages.extend(conversation_history) # Prev Q&A pairs
    messages.append({"role": "user", "content": question})  # Current Question
    

    response = openai.chat.completions.create(
        messages=messages,
        model=prompt.config["model"],
        temperature=prompt.config["temperature"],
        langfuse_prompt=prompt,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    setup_prompts()
    while True:
        user_id = input("Enter your user ID: ").strip() or "guest"

        if user_id.lower() in {"quit", "exit"}:
            break
        
        session_id = f"{user_id}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        print(f"\n Welcome {user_id}!")

        conversation_history = []

        while True:
            question = input("Your question: ").strip() or "default question"

            if question.lower() in {"quit", "exit"}:
                break

            answer = process_question(question, session_id, user_id, conversation_history)

            # Update conversation history
            conversation_history.append({"role": "user", "content": question})
            conversation_history.append({"role": "assistant", "content": answer})
            print(f"\n Answer: {answer}\n")
        
    langfuse.flush() # Sends pending traces & waits for async ops to complete
