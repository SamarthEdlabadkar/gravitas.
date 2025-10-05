import os
from groq import Groq
import instructor
from dotenv import load_dotenv

load_dotenv()


prompt: str = """
    Role and Goal: You are an expert academic research analyst. Your primary goal is to synthesize and summarize a research paper's core contribution based on its provided title, abstract, and publication date.

Structure & Content Requirements:

1.  Core Contribution : State the single most important finding or argument of the paper.
2.  Methodology/Approach : Briefly describe the primary method, model, or approach used to conduct the research.
3.  Key Findings : List the most significant results or conclusions.
4.  Significance and Context : Explain why this paper is important to its field and how the publication date might offer historical context.

Tone and Style: The summary must be objective, formal, and strictly academic. Do not use conversational language or qualifiers unless absolutely necessary. 

Constraint: The total length of the summary must not exceed 5 bullet points in the order of the above mentioned sections. Prioritize clarity and density of information over verbose explanation.

Input Data:
"""


api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)
client = instructor.from_groq(client)

result = client.chat.completions.create(
        model='llama-3.1-8b-instant',  # currently working - llama-3.3-70b-versatile, llama3-8b-8192
        messages=[
            {
                "role": "user",
                "content": prompt + "Stuff Stuff Stuff" + "\n\n Query: query" # type:ignore
            }
        ],
        temperature=0.2,
        max_retries=3,
        response_model=None
    ) # type:ignore

print(result)