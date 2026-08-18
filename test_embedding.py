from app.ai.gemini import generate_embedding


embedding = generate_embedding(
    "Login is not working",
    "User cannot log in after entering valid credentials."
)

print("Embedding generated:", embedding is not None)

if embedding:
    print("Embedding dimensions:", len(embedding))