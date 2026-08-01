import os
from dotenv import load_dotenv
from google import genai

# Load .env file
load_dotenv()

# Create Gemini client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def improve_bug_report(description: str):

    prompt = f"""
You are an experienced Senior Software QA Engineer.

A user has entered the following bug description:

"{description}"

Your task is to convert it into a professional software bug report.

Instructions:

1. If the description is very short (example: "login broken"), intelligently infer a meaningful title and reasonable reproduction steps.

2. If any information is unavailable (OS, Browser, Version, etc.), write "Not Provided".

3. Do NOT leave any section empty.

4. Improve the grammar and make the report professional.

5. Return ONLY the bug report.

Use exactly this format:

Title:

Environment:
- Operating System:
- Browser:
- Application Version:

Steps to Reproduce:
1.
2.
3.

Expected Result:

Actual Result:

Additional Notes:
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:

        print("Gemini Error:", e)

        return "Unable to improve the bug report at the moment. Please try again."