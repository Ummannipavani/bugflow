import os
import json

from dotenv import load_dotenv
from google import genai


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# CREATE GEMINI CLIENT
# =========================================================

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    return genai.Client(api_key=api_key)
client = get_gemini_client()

# =========================================================
# HELPER: CLEAN GEMINI JSON RESPONSE
# =========================================================

def clean_json_response(text: str):

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


# =========================================================
# ANALYZE BUG
# =========================================================

def analyze_bug(
    title: str,
    project: str,
    description: str
):

    prompt = f"""
You are an experienced Senior Software QA Engineer
and professional bug-report writer.

Analyze the following software defect and convert the
user's description into a detailed, professional,
developer-friendly defect report.

BUG INFORMATION

Title:
"{title}"

Project:
"{project}"

Original Description:
"{description}"


TASK

Perform two things:

1. Create a detailed professional improved defect description.
2. Classify the defect.


IMPROVED DESCRIPTION

Use the following structure when supported by the information:

Summary:
Briefly explain what is wrong.

Steps to Reproduce:
List steps provided or clearly implied.

Actual Result:
Explain what currently happens.

Expected Result:
Explain what should happen.

Impact:
Explain how the defect affects the user or application.

Additional Information:
Include useful information actually provided.


IMPORTANT:

- Preserve the original meaning.
- Make the description professional.
- Do not invent technical facts.
- Do not invent error messages.
- Do not invent browser information.
- Do not invent operating system information.
- Do not invent database details.
- Do not invent API endpoints.
- Do not invent root causes.
- If information is unavailable, omit that section.


ALLOWED CATEGORY VALUES

- Authentication
- UI/UX
- Performance
- Database
- API
- Payment
- Security
- Functional
- Compatibility
- Crash
- Other


ALLOWED DEFECT TYPE VALUES

- Functional
- UI/UX
- Performance
- Security
- Compatibility
- Database
- API
- Integration
- Crash
- Data
- Other


SEVERITY VALUES

- Critical
- High
- Medium
- Low


PRIORITY VALUES

- P1
- P2
- P3


MODULE

Identify the most likely affected module.

Examples:

- Login
- Authentication
- User Management
- Dashboard
- Payment Gateway
- Checkout
- Database
- API
- Search
- Profile
- Notifications
- File Upload
- Reporting
- General

Do not invent a specific technical component.

If the module cannot reasonably be determined, use:

"General"


SEVERITY GUIDELINES

Critical:
Application crashes, causes major data loss,
creates a serious security problem, or makes a major
core feature completely unusable.

High:
A major feature is broken but the application
is still usable elsewhere.

Medium:
A noticeable problem exists but there is a workaround.

Low:
Minor UI, spelling, cosmetic, or small inconvenience.


PRIORITY GUIDELINES

P1:
Immediate attention because critical functionality
is blocked or many users are affected.

P2:
Important and should be fixed soon.

P3:
Minor or cosmetic issue that can be fixed later.


OUTPUT

Return ONLY valid JSON.

Do not return Markdown.

Do not return ```json.

Use exactly this structure:

{{
    "improved_description": "Detailed professional QA defect description",
    "category": "Functional",
    "module": "General",
    "defect_type": "Functional",
    "priority": "P2",
    "severity": "Medium"
}}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        text = response.text.strip()

        print("========== GEMINI RESPONSE ==========")
        print(text)
        print("=====================================")

        text = clean_json_response(text)

        result = json.loads(text)

        # =================================================
        # ALLOWED VALUES
        # =================================================

        allowed_categories = [
            "Authentication",
            "UI/UX",
            "Performance",
            "Database",
            "API",
            "Payment",
            "Security",
            "Functional",
            "Compatibility",
            "Crash",
            "Other"
        ]

        allowed_defect_types = [
            "Functional",
            "UI/UX",
            "Performance",
            "Security",
            "Compatibility",
            "Database",
            "API",
            "Integration",
            "Crash",
            "Data",
            "Other"
        ]

        allowed_priorities = [
            "P1",
            "P2",
            "P3"
        ]

        allowed_severities = [
            "Critical",
            "High",
            "Medium",
            "Low"
        ]

        # =================================================
        # GET VALUES
        # =================================================

        improved_description = result.get(
            "improved_description",
            description
        )

        if not improved_description:
            improved_description = description

        category = result.get(
            "category",
            "Other"
        )

        if category not in allowed_categories:
            category = "Other"

        module = result.get(
            "module",
            "General"
        )

        if not module:
            module = "General"

        defect_type = result.get(
            "defect_type",
            "Other"
        )

        if defect_type not in allowed_defect_types:
            defect_type = "Other"

        priority = result.get(
            "priority",
            "P2"
        )

        if priority not in allowed_priorities:
            priority = "P2"

        severity = result.get(
            "severity",
            "Medium"
        )

        if severity not in allowed_severities:
            severity = "Medium"

        # =================================================
        # FINAL RESULT
        # =================================================

        return {
            "improved_description": improved_description,
            "category": category,
            "module": module,
            "defect_type": defect_type,
            "priority": priority,
            "severity": severity
        }

    except Exception as e:

        print("Gemini Analyze Error:", e)

        return {
            "improved_description": description,
            "category": "Other",
            "module": "General",
            "defect_type": "Other",
            "priority": "P2",
            "severity": "Medium"
        }

# =========================================================
# AI-GENERATED DEFECT SUMMARY
# =========================================================

def generate_defect_summary(
    title: str,
    description: str
):
    """
    Generate a concise summary of a defect.
    """

    prompt = f"""
You are an experienced software QA engineer.

Create a concise, professional summary of the following
software defect.

DEFECT TITLE:
"{title}"

DEFECT DESCRIPTION:
"{description}"

REQUIREMENTS:

- Summarize the defect in 1-3 sentences.
- Clearly explain what is wrong.
- Preserve the original meaning.
- Use simple, professional developer-friendly language.
- Do not invent technical details.
- Do not invent error messages.
- Do not invent root causes.
- Do not provide a solution.
- Do not provide investigation steps.
- Return ONLY the summary text.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        summary = response.text.strip()

        if not summary:
            return description

        return summary

    except Exception as e:

        print(
            "Gemini Defect Summary Error:",
            e
        )

        return description
# =========================================================
# FIND SIMILAR DEFECTS
# =========================================================

def find_similar_defects(
    title: str,
    description: str,
    existing_defects: list
):

    if not existing_defects:
        return []

    # =====================================================
    # PREPARE EXISTING DEFECTS
    # =====================================================

    defects_text = ""

    for defect in existing_defects:

        defects_text += f"""
Defect ID: {defect["id"]}
Title: {defect["title"]}
Description: {defect["description"]}
Category: {defect.get("category", "Unknown")}
Module: {defect.get("module", "Unknown")}

----------------------------------------
"""

    # =====================================================
    # PROMPT
    # =====================================================

    prompt = f"""
You are an experienced Senior Software QA Engineer.

Identify whether any existing defects are meaningfully
similar to the new defect.

NEW DEFECT

Title:
"{title}"

Description:
"{description}"


EXISTING DEFECTS

{defects_text}


SIMILARITY RULES

Consider defects similar when they involve related:

- functionality
- application behavior
- module/component
- error behavior
- failure scenario
- user action
- underlying problem description

Do not consider defects similar simply because they
contain generic words such as issue, error, problem,
application, user, or page.

Return at most 3 similar defects.

If there are no meaningfully similar defects,
return an empty list.


SIMILARITY SCORE

90-100:
Very strongly related or almost duplicate.

75-89:
Clearly related.

60-74:
Somewhat related.

Below 60:
Do not return.


IMPORTANT:

- Never return the new defect itself.
- Only return IDs from the EXISTING DEFECTS list.
- Do not invent defect IDs.


OUTPUT

Return ONLY valid JSON.

Do not return Markdown.

Use exactly this structure:

{{
    "similar_defects": [
        {{
            "id": 12,
            "similarity": 92,
            "reason": "Both defects describe a payment submission failure."
        }}
    ]
}}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        text = response.text.strip()

        print("========== SIMILAR DEFECT RESPONSE ==========")
        print(text)
        print("==============================================")

        text = clean_json_response(text)

        result = json.loads(text)

        similar_defects = result.get(
            "similar_defects",
            []
        )

        if not isinstance(similar_defects, list):
            return []

        # =================================================
        # VALIDATE RETURNED DEFECT IDS
        # =================================================

        existing_ids = {
            defect["id"]
            for defect in existing_defects
        }

        valid_results = []

        for item in similar_defects:

            if not isinstance(item, dict):
                continue

            defect_id = item.get("id")

            if defect_id not in existing_ids:
                continue

            similarity = item.get(
                "similarity",
                0
            )

            try:
                similarity = int(similarity)
            except:
                similarity = 0

            if similarity < 60:
                continue

            if similarity > 100:
                similarity = 100

            valid_results.append({
                "id": defect_id,
                "similarity": similarity,
                "reason": item.get(
                    "reason",
                    "The defects have related behavior or functionality."
                )
            })

        return valid_results[:3]

    except Exception as e:

        print(
            "Gemini Similar Defect Error:",
            e
        )

        return []


# =========================================================
# AI RESOLUTION ASSISTANCE
# =========================================================

def generate_resolution_assistance(
    title: str,
    project: str,
    description: str,
    category: str = "Other",
    module: str = "General",
    defect_type: str = "Other",
    priority: str = "P2",
    severity: str = "Medium"
):

    prompt = f"""
You are an experienced Senior Software Developer,
Software QA Engineer, and debugging specialist.

Analyze the following software defect and provide
practical resolution assistance for a developer.


DEFECT INFORMATION

Title:
"{title}"

Project:
"{project}"

Description:
"{description}"

Category:
"{category}"

Module:
"{module}"

Defect Type:
"{defect_type}"

Priority:
"{priority}"

Severity:
"{severity}"


TASK

Provide the following:

1. Root Cause Analysis

Explain the most likely reason for the defect.

If the exact root cause cannot be determined,
clearly say that it is a possible root cause,
not a confirmed root cause.


2. Investigation Steps

Provide clear steps a developer should follow
to reproduce and investigate the defect.


3. Recommended Solution

Provide practical steps that could resolve
the defect.


4. Suggested Fix

Describe the likely fix at a high level.

Do not invent specific code if the defect
information does not contain enough technical detail.


5. Prevention

Suggest practical measures that can prevent
similar defects.


6. Confidence

Return one of:

- High
- Medium
- Low

This represents confidence in the analysis,
NOT the severity of the defect.


IMPORTANT RULES

- Base the analysis ONLY on the provided information.
- Do not invent specific code.
- Do not invent APIs.
- Do not invent database tables.
- Do not invent error messages.
- Do not invent browser information.
- Do not invent operating systems.
- Do not invent libraries or frameworks.
- Do not invent configuration details.
- Do not claim a root cause is confirmed without evidence.
- Clearly distinguish likely causes from confirmed causes.
- Keep the response professional and developer-friendly.
- Do not repeat the entire defect description.


OUTPUT

Return ONLY valid JSON.

Do not return Markdown.

Do not return ```json.

Use exactly this structure:

{{
    "root_cause": "Most likely root cause or possible causes",
    "suggested_fix": "High-level suggested fix",
    "investigation_steps": [
        "Step 1",
        "Step 2",
        "Step 3"
    ],
    "recommended_solution": "Practical steps to resolve the defect",
    "confidence": "Medium",
    "explanation": "Brief explanation of why this analysis was made",
    "prevention": "Recommended measures to prevent similar defects"
}}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        text = response.text.strip()

        print(
            "========== GEMINI RESOLUTION RESPONSE =========="
        )

        print(text)

        print(
            "================================================="
        )

        text = clean_json_response(text)

        result = json.loads(text)

        # =================================================
        # ROOT CAUSE
        # =================================================

        root_cause = result.get(
            "root_cause",
            "The exact root cause could not be determined from the available information."
        )

        if not root_cause:
            root_cause = (
                "The exact root cause could not be determined "
                "from the available information."
            )

        # =================================================
        # SUGGESTED FIX
        # =================================================

        suggested_fix = result.get(
            "suggested_fix",
            "Investigate the affected functionality and apply an appropriate fix."
        )

        if not suggested_fix:
            suggested_fix = (
                "Investigate the affected functionality and "
                "apply an appropriate fix."
            )

        # =================================================
        # INVESTIGATION STEPS
        # =================================================

        investigation_steps = result.get(
            "investigation_steps",
            []
        )

        if not isinstance(
            investigation_steps,
            list
        ):
            investigation_steps = []

        # =================================================
        # RECOMMENDED SOLUTION
        # =================================================

        recommended_solution = result.get(
            "recommended_solution",
            "Reproduce the defect, identify the failing behavior, and apply an appropriate fix."
        )

        if not recommended_solution:
            recommended_solution = (
                "Reproduce the defect, identify the failing "
                "behavior, and apply an appropriate fix."
            )

        # =================================================
        # CONFIDENCE
        # =================================================

        confidence = result.get(
            "confidence",
            "Medium"
        )

        if confidence not in [
            "High",
            "Medium",
            "Low"
        ]:
            confidence = "Medium"

        # =================================================
        # EXPLANATION
        # =================================================

        explanation = result.get(
            "explanation",
            ""
        )

        # =================================================
        # PREVENTION
        # =================================================

        prevention = result.get(
            "prevention",
            "Add appropriate validation and regression testing."
        )

        if not prevention:
            prevention = (
                "Add appropriate validation and regression testing."
            )

        # =================================================
        # FINAL RESULT
        # =================================================

        return {

            "root_cause": root_cause,

            "suggested_fix": suggested_fix,

            "investigation_steps": investigation_steps,

            "recommended_solution": recommended_solution,

            "confidence": confidence,

            "explanation": explanation,

            "prevention": prevention

        }

    except Exception as e:

        print(
            "Gemini Resolution Assistance Error:",
            e
        )

        return {

            "root_cause": (
                "The exact root cause could not be determined "
                "from the available defect information."
            ),

            "suggested_fix": (
                "Reproduce the defect, inspect the affected "
                "functionality, identify the failing behavior, "
                "and apply a suitable fix."
            ),

            "investigation_steps": [
                "Reproduce the reported defect.",
                "Identify the affected functionality or module.",
                "Inspect the behavior leading to the failure.",
                "Verify the fix using regression testing."
            ],

            "recommended_solution": (
                "Reproduce the defect, identify the failing "
                "behavior, and apply an appropriate fix."
            ),

            "confidence": "Low",

            "explanation": (
                "The available defect information is insufficient "
                "to determine a specific technical root cause."
            ),

            "prevention": (
                "Add regression testing and validation around "
                "the affected functionality."
            )

        }
# =========================================================
# GENERATE DEFECT EMBEDDING
# =========================================================

def generate_embedding(
    title: str,
    description: str
):

    text = f"""
Title: {title}

Description: {description}
"""

    try:

        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text
        )

        embedding = response.embeddings[0].values

        return embedding

    except Exception as e:

        print(
            "Gemini Embedding Error:",
            e
        )

        return None
# =========================================================
# ROOT CAUSE INVESTIGATION ASSISTANCE
# =========================================================

def generate_investigation_assistance(
    title: str,
    project: str,
    description: str,
    category: str = "Other",
    module: str = "General",
    defect_type: str = "Other"
):

    prompt = f"""
You are an experienced Senior Software Developer
and Software QA Engineer.

Your task is to provide ROOT CAUSE INVESTIGATION
ASSISTANCE for the following software defect.

IMPORTANT:
The suggestions are NOT confirmed root causes.
They are only areas that developers should investigate.

DEFECT INFORMATION

Title:
"{title}"

Project:
"{project}"

Description:
"{description}"

Category:
"{category}"

Module:
"{module}"

Defect Type:
"{defect_type}"


TASK

Suggest practical areas that a developer should
investigate to understand the possible cause of
this defect.

Depending on the defect, consider areas such as:

- affected module
- recent code changes
- API behavior
- API timeout handling
- database behavior
- database connection errors
- authentication
- validation
- error handling
- application logs
- configuration
- integration points
- user input processing
- recent deployments


IMPORTANT RULES

- Suggestions must be related to the provided defect.
- Do NOT claim that any suggestion is the confirmed root cause.
- Do NOT invent technical details.
- Do NOT invent APIs.
- Do NOT invent database tables.
- Do NOT invent error messages.
- Do NOT invent frameworks or libraries.
- Do NOT invent browser information.
- Do NOT invent operating systems.
- Do NOT invent configuration details.
- Do NOT provide specific code.
- Keep suggestions practical and developer-friendly.
- Return between 3 and 5 investigation areas.


OUTPUT

Return ONLY valid JSON.

Do not return Markdown.

Do not return ```json.

Use exactly this structure:

{{
    "investigation_areas": [
        "Check API timeout handling.",
        "Review recent changes related to the affected module.",
        "Check application logs for errors."
    ],
    "explanation": "These are investigation suggestions based on the reported defect and are not confirmed root causes."
}}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        text = response.text.strip()

        print(
            "========== GEMINI INVESTIGATION RESPONSE =========="
        )

        print(text)

        print(
            "===================================================="
        )

        text = clean_json_response(text)

        result = json.loads(text)

        # =================================================
        # INVESTIGATION AREAS
        # =================================================

        investigation_areas = result.get(
            "investigation_areas",
            []
        )

        if not isinstance(
            investigation_areas,
            list
        ):
            investigation_areas = []

        investigation_areas = [
            str(item).strip()
            for item in investigation_areas
            if item
        ]

        # Keep maximum 5 suggestions
        investigation_areas = investigation_areas[:5]

        # =================================================
        # EXPLANATION
        # =================================================

        explanation = result.get(
            "explanation",
            "These are investigation suggestions, not confirmed root causes."
        )

        if not explanation:

            explanation = (
                "These are investigation suggestions, "
                "not confirmed root causes."
            )

        # =================================================
        # FINAL RESULT
        # =================================================

        return {

            "investigation_areas":
                investigation_areas,

            "explanation":
                explanation

        }

    except Exception as e:

        print(
            "Gemini Investigation Assistance Error:",
            e
        )

        return {

            "investigation_areas": [
                "Review the affected functionality.",
                "Check recent changes related to the defect.",
                "Review application logs and error handling."
            ],

            "explanation": (
                "These are general investigation suggestions "
                "and are not confirmed root causes."
            )

        }
# =========================================================
# AI DEVELOPER ASSIGNMENT RECOMMENDATION
# =========================================================

def generate_developer_recommendation(
    title: str,
    project: str,
    description: str,
    category: str,
    module: str,
    defect_type: str,
    priority: str,
    severity: str,
    developers: list
):
    """
    Recommend the most suitable developer for an issue.

    The developers list is prepared by the backend using
    real BugFlow database information.

    Gemini must only choose from the supplied developers
    and must not invent developer information.
    """

    # =====================================================
    # NO DEVELOPERS AVAILABLE
    # =====================================================

    if not developers:

        return {
            "recommended_developer_id": None,
            "recommended_developer_name": None,
            "match_score": 0,
            "reasons": [],
            "explanation": (
                "No developers are currently available "
                "for recommendation."
            )
        }

    # =====================================================
    # PREPARE DEVELOPER INFORMATION
    # =====================================================

    developer_text = ""

    for developer in developers:

        developer_text += f"""
Developer ID:
{developer.get("id")}

Developer Name:
{developer.get("name", "Unknown")}

Previously Assigned Issues:
{developer.get("total_assigned", 0)}

Previously Resolved Issues:
{developer.get("resolved_issues", 0)}

Issues in Same Module:
{developer.get("module_matches", 0)}

Issues in Same Category:
{developer.get("category_matches", 0)}

Issues with Same Defect Type:
{developer.get("defect_type_matches", 0)}

Similar Severity Experience:
{developer.get("severity_matches", 0)}

Similar Priority Experience:
{developer.get("priority_matches", 0)}

Current Active Workload:
{developer.get("active_issues", 0)}

Backend Suitability Score:
{developer.get("score", 0)}

--------------------------------------------
"""

    # =====================================================
    # PROMPT
    # =====================================================

    prompt = f"""
You are an AI assistant inside BugFlow,
an intelligent software defect tracking system.

Your task is to recommend the most suitable developer
for the provided software issue.

IMPORTANT:

The developer statistics below come from the real
BugFlow database.

You MUST use only the developers supplied below.

Do NOT invent developers.

Do NOT invent developer experience.

Do NOT invent technologies, skills, projects,
frameworks, or programming languages.

Do NOT assume information that is not provided.

The recommendation should mainly consider:

1. Experience with the same module
2. Experience with the same category
3. Experience with the same defect type
4. Number of successfully resolved issues
5. Experience with similar severity and priority
6. Current workload
7. Backend suitability score

A developer with relevant historical experience
should generally be preferred.

However, if two developers have similar experience,
the developer with the lower active workload may
be preferred.


==================================================
CURRENT ISSUE
==================================================

Title:
"{title}"

Project:
"{project}"

Description:
"{description}"

Category:
"{category}"

Module:
"{module}"

Defect Type:
"{defect_type}"

Priority:
"{priority}"

Severity:
"{severity}"


==================================================
AVAILABLE DEVELOPERS
==================================================

{developer_text}


==================================================
TASK
==================================================

Select ONE most suitable developer.

The recommended developer ID MUST exactly match
one of the Developer IDs supplied above.

Provide:

1. Developer ID
2. Developer name
3. Match score from 0 to 100
4. 2 to 4 short reasons explaining the recommendation
5. A brief explanation

The match score should represent suitability for
THIS issue.

Do not claim that the recommendation guarantees
successful resolution.


==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Do not return Markdown.

Do not return ```json.

Use exactly this structure:

{{
    "recommended_developer_id": 1,
    "recommended_developer_name": "Developer Name",
    "match_score": 85,
    "reasons": [
        "Has previous experience with this module.",
        "Has resolved similar category issues.",
        "Has a manageable current workload."
    ],
    "explanation": "This developer has the strongest relevant historical experience for the current issue."
}}
"""

    try:

        # =================================================
        # GEMINI REQUEST
        # =================================================

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        text = response.text.strip()

        print(
            "========== GEMINI DEVELOPER RECOMMENDATION =========="
        )

        print(text)

        print(
            "====================================================="
        )

        text = clean_json_response(text)

        result = json.loads(text)

        # =================================================
        # VALIDATE DEVELOPER ID
        # =================================================

        valid_developer_ids = {
            developer.get("id")
            for developer in developers
        }

        recommended_id = result.get(
            "recommended_developer_id"
        )

        try:
            recommended_id = int(recommended_id)

        except (TypeError, ValueError):
            recommended_id = None


        # =================================================
        # IF GEMINI RETURNS INVALID DEVELOPER
        # USE BACKEND'S HIGHEST-SCORED DEVELOPER
        # =================================================

        if recommended_id not in valid_developer_ids:

            best_developer = max(
                developers,
                key=lambda developer:
                    developer.get("score", 0)
            )

            recommended_id = best_developer.get("id")

            recommended_name = best_developer.get(
                "name",
                "Unknown"
            )

        else:

            selected_developer = next(
                (
                    developer
                    for developer in developers
                    if developer.get("id")
                    == recommended_id
                ),
                None
            )

            recommended_name = (
                selected_developer.get(
                    "name",
                    "Unknown"
                )
                if selected_developer
                else "Unknown"
            )


        # =================================================
        # MATCH SCORE
        # =================================================

        match_score = result.get(
            "match_score",
            0
        )

        try:
            match_score = int(match_score)

        except (TypeError, ValueError):
            match_score = 0


        if match_score < 0:
            match_score = 0

        if match_score > 100:
            match_score = 100


        # =================================================
        # REASONS
        # =================================================

        reasons = result.get(
            "reasons",
            []
        )

        if not isinstance(
            reasons,
            list
        ):
            reasons = []

        reasons = [
            str(reason).strip()
            for reason in reasons
            if reason
        ]

        reasons = reasons[:4]


        # =================================================
        # EXPLANATION
        # =================================================

        explanation = result.get(
            "explanation",
            (
                "The recommendation is based on "
                "the developer's historical defect "
                "experience and current workload."
            )
        )

        if not explanation:

            explanation = (
                "The recommendation is based on "
                "the developer's historical defect "
                "experience and current workload."
            )


        # =================================================
        # FINAL RESULT
        # =================================================

        return {

            "recommended_developer_id":
                recommended_id,

            "recommended_developer_name":
                recommended_name,

            "match_score":
                match_score,

            "reasons":
                reasons,

            "explanation":
                explanation
        }


    except Exception as e:

        print(
            "Gemini Developer Recommendation Error:",
            e
        )

        # =================================================
        # SAFE FALLBACK
        #
        # If Gemini temporarily fails, use the developer
        # with the highest score calculated by BugFlow.
        # =================================================

        best_developer = max(
            developers,
            key=lambda developer:
                developer.get("score", 0)
        )

        fallback_score = best_developer.get(
            "score",
            0
        )

        try:
            fallback_score = int(fallback_score)

        except (TypeError, ValueError):
            fallback_score = 0

        fallback_score = max(
            0,
            min(
                100,
                fallback_score
            )
        )

        return {

            "recommended_developer_id":
                best_developer.get("id"),

            "recommended_developer_name":
                best_developer.get(
                    "name",
                    "Unknown"
                ),

            "match_score":
                fallback_score,

            "reasons": [
                (
                    "Recommended using historical "
                    "BugFlow assignment and resolution data."
                )
            ],

            "explanation": (
                "The AI service was unavailable, so "
                "BugFlow selected the highest-scoring "
                "developer using stored developer history."
            )
        }