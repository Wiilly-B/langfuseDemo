from langfuse.openai import openai
import dotenv

dotenv.load_dotenv()
from langfuse.openai import openai
 
DOCS = {
    "refund": "Full refund within 30 days. 50'%' refund within 90 days. Email support@company.com. Processing: 5-7 days.",
    "pricing": "Basic: $29/month. Pro: $99/month with API access. Enterprise: Custom pricing.",
    "shipping": "US: 3-5 days, free over $50. International: 7-14 days, $15 flat."
}


def search(query):
    results = []
    for name, content in DOCS.items():
        if any(word in content.lower() for word in query.lower().split()):
            results.append(content)
    return results[:2]

def answerQuestion(question, session_id="demo_session"):
    docs = search(question)
    context = "\n".join(docs) if docs else "No info found."

    response = openai.chat.completions.create(
        name="qa-bot",
        model="gpt-5",
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

    answerQuestion("What is your refund policy???", session)
    answerQuestion("What does your pricing plan look like?", session)
    answerQuestion("How is the shipping?", session)