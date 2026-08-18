from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.gemini import (
    analyze_bug,
    generate_resolution_assistance,
    generate_embedding
)

from app.database.database import get_db
from app.models.issue import Issue


router = APIRouter()


# =========================================================
# ANALYZE REQUEST MODEL
# =========================================================

class AnalyzeRequest(BaseModel):

    title: str
    project: str
    description: str


# =========================================================
# SIMILAR DEFECT REQUEST MODEL
# =========================================================

class SimilarDefectsRequest(BaseModel):
    issue_id: int
    title: str
    description: str


# =========================================================
# RESOLUTION ASSISTANCE REQUEST MODEL
# =========================================================

class ResolutionRequest(BaseModel):

    title: str
    project: str
    description: str

    category: str = "Other"

    module: str = "General"

    defect_type: str = "Other"

    severity: str = "Medium"

    priority: str = "P2"


# =========================================================
# ANALYZE BUG WITH AI
# =========================================================

@router.post("/ai/analyze")
def analyze(
    request: AnalyzeRequest
):

    result = analyze_bug(

        title=request.title,

        project=request.project,

        description=request.description

    )

    return {

        "improved_description":
            result["improved_description"],

        "category":
            result["category"],

        "module":
            result["module"],

        "defect_type":
            result["defect_type"],

        "priority":
            result["priority"],

        "severity":
            result["severity"]

    }


# =========================================================
# FIND SIMILAR DEFECTS USING PGVECTOR
# =========================================================

@router.post("/ai/similar-defects")
def similar_defects(

    request: SimilarDefectsRequest,

    db: Session = Depends(get_db)

):

    # =====================================================
    # GENERATE EMBEDDING FOR CURRENT ISSUE
    # =====================================================

    embedding = generate_embedding(

        title=request.title,

        description=request.description

    )

    if not embedding:

        return {
            "similar_defects": [],
            "message": "Unable to generate embedding."
        }


    # =====================================================
    # COSINE DISTANCE
    # =====================================================

    distance = Issue.embedding.cosine_distance(
        embedding
    )


    # =====================================================
    # FIND CLOSEST DEFECTS
    # =====================================================

    results = (

        db.query(
            Issue,
            distance.label("distance")
        )

        .filter(

            # Do not compare issue with itself
            Issue.id != request.issue_id,

            # Only issues that have embeddings
            Issue.embedding.isnot(None)

        )

        .order_by(
            distance
        )

        .limit(3)

        .all()

    )


    # =====================================================
    # PREPARE RESULTS
    # =====================================================

    similar_defects = []


    for issue, similarity_distance in results:

        # Convert cosine distance to similarity percentage

        similarity = (
            1 - float(similarity_distance)
        ) * 100


        similarity = max(
            0,
            min(
                100,
                round(similarity)
            )
        )


        # Ignore weak matches

        if similarity < 60:
            continue


        similar_defects.append({

            "id":
                issue.id,

            "title":
                issue.title,

            "description":
                issue.description or "",

            "category":
                issue.category or "Unknown",

            "module":
                issue.module or "Unknown",

            "similarity":
                similarity

        })


    # =====================================================
    # RETURN RESULTS
    # =====================================================

    return {

        "similar_defects":
            similar_defects

    }

# =========================================================
# AI RESOLUTION ASSISTANCE
# =========================================================
@router.post("/ai/resolve")
def resolve_defect(
    request: ResolutionRequest,
    db: Session = Depends(get_db)
):

    # =====================================================
    # GENERATE AI RESOLUTION
    # =====================================================

    result = generate_resolution_assistance(

        title=request.title,

        project=request.project,

        description=request.description,

        category=request.category,

        module=request.module,

        defect_type=request.defect_type,

        priority=request.priority,

        severity=request.severity

    )


    # =====================================================
    # FIND CURRENT ISSUE
    # =====================================================

    issue = (
        db.query(Issue)
        .filter(
            Issue.title == request.title,
            Issue.project == request.project
        )
        .order_by(Issue.id.desc())
        .first()
    )


    # =====================================================
    # SAVE AI RESULT
    # =====================================================

    if issue:

        issue.ai_root_cause = result.get(
            "root_cause",
            ""
        )

        issue.ai_suggested_fix = result.get(
            "suggested_fix",
            ""
        )

        issue.ai_investigation_steps = "\n".join(
            result.get(
                "investigation_steps",
                []
            )
        )

        issue.ai_recommended_solution = result.get(
            "recommended_solution",
            ""
        )

        issue.ai_confidence = result.get(
            "confidence",
            "Medium"
        )

        issue.ai_explanation = result.get(
            "explanation",
            ""
        )

        issue.ai_prevention = result.get(
            "prevention",
            ""
        )

        db.commit()

        db.refresh(issue)


    # =====================================================
    # RETURN RESULT TO FRONTEND
    # =====================================================

    return {

        "root_cause":
            result.get(
                "root_cause",
                ""
            ),

        "suggested_fix":
            result.get(
                "suggested_fix",
                ""
            ),

        "investigation_steps":
            result.get(
                "investigation_steps",
                []
            ),

        "recommended_solution":
            result.get(
                "recommended_solution",
                ""
            ),

        "confidence":
            result.get(
                "confidence",
                "Medium"
            ),

        "explanation":
            result.get(
                "explanation",
                ""
            ),

        "prevention":
            result.get(
                "prevention",
                ""
            )

    }