from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.ai.gemini import (
    analyze_bug,
    generate_resolution_assistance,
    generate_investigation_assistance,
    generate_embedding,
    generate_developer_recommendation
)

from app.database.database import get_db
from app.models.issue import Issue
from app.models.comment import Comment
from app.models.user import User
from app.auth.dependencies import get_current_user

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
# DEVELOPER RECOMMENDATION REQUEST MODEL
# =========================================================

class DeveloperRecommendationRequest(BaseModel):

    issue_id: int

# =========================================================
# ANALYZE BUG WITH AI
# =========================================================

@router.post("/ai/analyze")
def analyze(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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
# HISTORICAL RESOLUTION ASSISTANCE
# =========================================================

@router.post("/ai/historical-resolution")
def historical_resolution(
    request: SimilarDefectsRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    # =====================================================
    # 1. GENERATE EMBEDDING FOR CURRENT ISSUE
    # =====================================================

    embedding = generate_embedding(

        title=request.title,

        description=request.description

    )

    if not embedding:

        return {

            "historical_resolution": None,

            "message":
                "Unable to generate embedding."

        }


    # =====================================================
    # 2. CALCULATE COSINE DISTANCE
    # =====================================================

    distance = Issue.embedding.cosine_distance(

        embedding

    )


    # =====================================================
    # 3. SEARCH CLOSED HISTORICAL ISSUES
    # =====================================================

    closed_issues = (

        db.query(

            Issue,

            distance.label("distance")

        )

        .filter(

            # Do not compare current issue with itself
            Issue.id != request.issue_id,

            # Only issues having embeddings
            Issue.embedding.isnot(None),

            # Only CLOSED issues
            Issue.status == "Closed",

            # Must have previous AI resolution information
            or_(

                Issue.ai_root_cause.isnot(None),

                Issue.ai_suggested_fix.isnot(None),

                Issue.ai_recommended_solution.isnot(None)

            )

        )

        # IMPORTANT:
        # Cosine distance ASC means:
        # smallest distance = highest similarity
        .order_by(

            distance.asc()

        )

        .all()

    )


    # =====================================================
    # 4. FIND HIGHEST SIMILARITY
    # =====================================================

    best_match = None

    highest_similarity = -1


    for issue, similarity_distance in closed_issues:

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


        # Debug output
        print(

            f"[HISTORICAL] "
            f"Current Issue #{request.issue_id} "
            f"-> Closed Issue #{issue.id} "
            f"-> Similarity: {similarity}%"

        )


        # Only accept reasonably strong matches
        if similarity < 75:

            continue


        # Keep the HIGHEST similarity
        if similarity > highest_similarity:

            highest_similarity = similarity

            best_match = {

                "issue": issue,

                "similarity": similarity

            }


    # =====================================================
    # 5. NO SIMILAR CLOSED ISSUE FOUND
    # =====================================================

    if not best_match:

        return {

            "historical_resolution": None,

            "message":
                "No similar closed defect with previous resolution information was found."

        }


    # =====================================================
    # 6. GET BEST PREVIOUS ISSUE
    # =====================================================

    previous_issue = best_match["issue"]

    similarity = best_match["similarity"]


    print(

        f"[HISTORICAL] BEST MATCH -> "
        f"Issue #{previous_issue.id} "
        f"with {similarity}% similarity"

    )


    # =====================================================
    # 7. GET COMMENTS FROM PREVIOUS ISSUE
    # =====================================================

    comments = (

        db.query(Comment)

        .filter(

            Comment.issue_id == previous_issue.id

        )

        .order_by(

            Comment.created_at.asc()

        )

        .all()

    )


    # =====================================================
    # 8. COLLECT DEVELOPER / TEAM COMMENTS
    # =====================================================

    relevant_comments = []


    for comment in comments:

        if not comment.comment:

            continue


        relevant_comments.append(

            comment.comment

        )


    # Keep only latest 5 comments

    relevant_comments = (

        relevant_comments[-5:]

    )


    # =====================================================
    # 9. GET PREVIOUS RESOLUTION
    # =====================================================

    previous_resolution = (

        previous_issue.ai_recommended_solution

        or

        previous_issue.ai_suggested_fix

        or

        ""

    )


    # =====================================================
    # 10. RETURN HISTORICAL KNOWLEDGE
    # =====================================================

    return {

        "historical_resolution": {

            # ---------------------------------------------
            # RELATED DEFECT
            # ---------------------------------------------

            "related_defect": {

                "id":
                    previous_issue.id,

                "title":
                    previous_issue.title,

                "description":
                    previous_issue.description or "",

                "similarity":
                    similarity,

                "status":
                    previous_issue.status

            },


            # ---------------------------------------------
            # PREVIOUS ROOT CAUSE
            # ---------------------------------------------

            "previous_root_cause":

                previous_issue.ai_root_cause or "",


            # ---------------------------------------------
            # PREVIOUS RESOLUTION
            # ---------------------------------------------

            "previous_resolution":

                previous_resolution,


            # ---------------------------------------------
            # DEVELOPER COMMENTS
            # ---------------------------------------------

            "relevant_developer_comments":

                relevant_comments

        }

    }
# =========================================================
# AI RESOLUTION ASSISTANCE
# =========================================================
@router.post("/ai/resolve")
def resolve_defect(
    request: ResolutionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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
# =========================================================
# ROOT CAUSE INVESTIGATION ASSISTANCE
# =========================================================

@router.post("/ai/investigation")
def investigation_assistance(
    request: ResolutionRequest,
    current_user: dict = Depends(get_current_user)
):

    result = generate_investigation_assistance(

        title=request.title,

        project=request.project,

        description=request.description,

        category=request.category,

        module=request.module,

        defect_type=request.defect_type

    )

    return {

        "investigation_areas":
            result.get(
                "investigation_areas",
                []
            ),

        "explanation":
            result.get(
                "explanation",
                "These are investigation suggestions, not confirmed root causes."
            )

    }
# =========================================================
# AI DEVELOPER ASSIGNMENT RECOMMENDATION
# =========================================================

@router.post("/ai/recommend-developer")
def recommend_developer(
    request: DeveloperRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    # =====================================================
    # 1. GET CURRENT ISSUE
    # =====================================================

    issue = (
        db.query(Issue)
        .filter(
            Issue.id == request.issue_id
        )
        .first()
    )

    if not issue:
        return {
            "recommended_developer": None,
            "match_score": 0,
            "reasons": [],
            "workload": 0,
            "history_count": 0,
            "explanation": "Issue not found."
        }

    # =====================================================
    # 2. GET ONLY REGISTERED DEVELOPERS
    # =====================================================

    developers = (
        db.query(User)
        .filter(
            User.role == "Developer"
        )
        .all()
    )

    if not developers:
        return {
            "recommended_developer": None,
            "match_score": 0,
            "reasons": [],
            "workload": 0,
            "history_count": 0,
            "explanation": (
                "No registered developers are "
                "currently available."
            )
        }

    # =====================================================
    # 3. PREPARE DEVELOPER DATA
    # =====================================================

    developer_data = []

    for developer in developers:

        # -------------------------------------------------
        # GET ISSUES PREVIOUSLY ASSIGNED TO THIS DEVELOPER
        # -------------------------------------------------

        developer_issues = (
            db.query(Issue)
            .filter(
                Issue.assigned_to == developer.id,
                Issue.id != issue.id
            )
            .all()
        )

        total_assigned = len(
            developer_issues
        )

        # -------------------------------------------------
        # RESOLVED / CLOSED ISSUES
        # -------------------------------------------------

        resolved_issues = [
            item
            for item in developer_issues
            if item.status in [
                "Resolved",
                "Verified",
                "Closed"
            ]
        ]

        resolved_count = len(
            resolved_issues
        )

        # -------------------------------------------------
        # ACTIVE WORKLOAD
        # -------------------------------------------------

        active_issues = [
            item
            for item in developer_issues
            if item.status not in [
                "Resolved",
                "Verified",
                "Closed"
            ]
        ]

        active_count = len(
            active_issues
        )

        # -------------------------------------------------
        # MATCHING HISTORY
        # -------------------------------------------------

        project_matches = sum(
            1
            for item in developer_issues
            if (
                item.project
                and issue.project
                and item.project.lower()
                == issue.project.lower()
            )
        )

        module_matches = sum(
            1
            for item in developer_issues
            if (
                item.module
                and issue.module
                and item.module.lower()
                == issue.module.lower()
            )
        )

        category_matches = sum(
            1
            for item in developer_issues
            if (
                item.category
                and issue.category
                and item.category.lower()
                == issue.category.lower()
            )
        )

        defect_type_matches = sum(
            1
            for item in developer_issues
            if (
                item.defect_type
                and issue.defect_type
                and item.defect_type.lower()
                == issue.defect_type.lower()
            )
        )

        severity_matches = sum(
            1
            for item in developer_issues
            if (
                item.severity
                and issue.severity
                and item.severity.lower()
                == issue.severity.lower()
            )
        )

        priority_matches = sum(
            1
            for item in developer_issues
            if (
                item.priority
                and issue.priority
                and item.priority.lower()
                == issue.priority.lower()
            )
        )

        # =================================================
        # 4. CALCULATE BACKEND SUITABILITY SCORE
        # =================================================

        score = 0

        # Same project
        if project_matches > 0:
            score += 20

        # Same module
        if module_matches > 0:
            score += 25

        # Same category
        if category_matches > 0:
            score += 15

        # Same defect type
        if defect_type_matches > 0:
            score += 10

        # Same severity
        if severity_matches > 0:
            score += 5

        # Same priority
        if priority_matches > 0:
            score += 5

        # Resolution experience
        if resolved_count > 0:
            score += min(
                resolved_count * 2,
                10
            )

        # Lower workload gets advantage
        if active_count == 0:
            score += 10

        elif active_count <= 2:
            score += 7

        elif active_count <= 4:
            score += 4

        score = max(
            0,
            min(
                100,
                score
            )
        )

        # =================================================
        # 5. STORE ONLY DATABASE DEVELOPER INFORMATION
        # =================================================

        developer_data.append({

            "id":
                developer.id,

            "name":
                developer.name,

            "email":
                developer.email,

            "total_assigned":
                total_assigned,

            "resolved_issues":
                resolved_count,

            "active_issues":
                active_count,

            "project_matches":
                project_matches,

            "module_matches":
                module_matches,

            "category_matches":
                category_matches,

            "defect_type_matches":
                defect_type_matches,

            "severity_matches":
                severity_matches,

            "priority_matches":
                priority_matches,

            "score":
                score
        })

    # =====================================================
    # 6. SEND DATABASE DEVELOPERS TO GEMINI
    # =====================================================

    result = generate_developer_recommendation(

        title=issue.title,

        project=issue.project,

        description=issue.description or "",

        category=issue.category or "Other",

        module=issue.module or "General",

        defect_type=(
            issue.defect_type
            or "Other"
        ),

        priority=(
            issue.priority
            or "P2"
        ),

        severity=(
            issue.severity
            or "Medium"
        ),

        developers=developer_data
    )

    # =====================================================
    # 7. GET GEMINI'S RECOMMENDED ID
    # =====================================================

    recommended_id = result.get(
        "recommended_developer_id"
    )

    try:
        recommended_id = int(
            recommended_id
        )
    except (TypeError, ValueError):
        recommended_id = None

    # =====================================================
    # 8. VERIFY RECOMMENDED ID AGAINST DATABASE
    # =====================================================

    recommended_developer = None

    if recommended_id is not None:

        recommended_developer = (
            db.query(User)
            .filter(
                User.id == recommended_id,
                User.role == "Developer"
            )
            .first()
        )

    # =====================================================
    # 9. FALLBACK TO BACKEND SCORE
    # =====================================================

    if not recommended_developer:

        best_developer = max(
            developer_data,
            key=lambda x: x["score"]
        )

        recommended_developer = (
            db.query(User)
            .filter(
                User.id == best_developer["id"],
                User.role == "Developer"
            )
            .first()
        )

        recommended_id = (
            recommended_developer.id
        )

    # =====================================================
    # 10. GET VERIFIED DEVELOPER DATA
    # =====================================================

    verified_data = next(
        (
            developer
            for developer in developer_data
            if developer["id"] == recommended_id
        ),
        None
    )

    # =====================================================
    # 11. RETURN ONLY VERIFIED DATABASE DEVELOPER
    # =====================================================

    return {

        "recommended_developer": {

            "id":
                recommended_developer.id,

            "name":
                recommended_developer.name,

            "email":
                recommended_developer.email

        },

        "match_score":

            verified_data["score"]
            if verified_data
            else 0,

        "reasons":

            result.get(
                "reasons",
                []
            ),

        "workload":

            verified_data["active_issues"]
            if verified_data
            else 0,

        "history_count":

            verified_data["total_assigned"]
            if verified_data
            else 0,

        "explanation":

            result.get(
                "explanation",
                "Developer recommended based on database history and workload."
            )
    }