from app.database.database import SessionLocal

# Import related models so SQLAlchemy can resolve relationships
from app.models.sprint import Sprint
from app.models.user import User
from app.models.issue import Issue

from app.ai.gemini import generate_embedding


def generate_missing_embeddings():

    db = SessionLocal()

    try:

        issues = (
            db.query(Issue)
            .filter(Issue.embedding.is_(None))
            .all()
        )

        print(
            f"Found {len(issues)} issues without embeddings."
        )

        for issue in issues:

            print(
                f"\nGenerating embedding for "
                f"Issue #{issue.id}: {issue.title}"
            )

            embedding = generate_embedding(
                issue.title,
                issue.description or ""
            )

            if embedding:

                issue.embedding = embedding

                db.commit()

                print(
                    f"✓ Issue #{issue.id} embedding saved "
                    f"({len(embedding)} dimensions)"
                )

            else:

                print(
                    f"✗ Failed to generate embedding "
                    f"for Issue #{issue.id}"
                )

        print("\nFinished generating embeddings.")

    except Exception as e:

        db.rollback()

        print("ERROR:", e)

    finally:

        db.close()


if __name__ == "__main__":

    generate_missing_embeddings()