"""
Natural-language AI assistant for a single project (spec: "Create an AI
assistant that can answer questions such as: Which tasks are overdue?
Who is overloaded? ... The AI should use relevant project data rather
than inventing information.").

Design, matching the rest of the app's AI features:
1. Gather REAL structured context first (project status, active sprint,
   task risk, quality risk, team workload) by calling the existing
   Module 2-6 service functions -- never recomputed or duplicated here.
2. Retrieve relevant project documents via rag_service (vector search if
   available, keyword search otherwise).
3. If Gemini is configured, send it the question plus that real context
   and use its written answer.
4. If Gemini is NOT configured (or the call fails), answer from a small
   set of keyword-matched intents (overdue tasks, workload, sprint
   status, critical bugs, availability, prioritization) using ONLY the
   real context gathered in step 1-2 -- never a generic canned reply,
   and never a fabricated answer to a question with no matching data.
"""
from datetime import date, timedelta
import re

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.sprint import SprintStatus
from app.services import sprint_service, project_member_service, availability_service, rag_service
from app.services.ai_service import _call_gemini, task_risk_analysis, quality_risk_analysis


def _gather_context(db: Session, project: Project, *, client_safe: bool = False) -> dict:
    members = project_member_service.list_members(db, project.id)
    sprints = sprint_service.list_sprints(db, project.id)
    active_sprint = next((s for s in sprints if s.status == SprintStatus.ACTIVE), None)

    context = {
        "project": {
            "code": project.code, "name": project.name, "status": project.status.value,
            "priority": project.priority.value, "methodology": project.methodology.value,
        },
    }
    if not client_safe:
        context.update({
            "team": [{"name": m.full_name, "role": m.project_role.value} for m in members],
            "task_risk": task_risk_analysis(db, project),
            "quality_risk": quality_risk_analysis(db, project),
        })

    if active_sprint:
        detail = sprint_service.get_sprint_detail(db, active_sprint)
        context["active_sprint"] = {
            "name": detail.name, "goal": detail.goal,
            "start_date": str(detail.start_date), "end_date": str(detail.end_date),
            "total_points": detail.total_points, "completed_points": detail.completed_points,
        }
    else:
        context["active_sprint"] = None

    if client_safe:
        return context

    today = date.today()
    availability = availability_service.team_availability(
        db, [m.user_id for m in members], today, today + timedelta(days=6),
    )
    unavailable_today = [a.full_name for a in availability if a.date == today and a.status.value == "unavailable"]
    context["unavailable_today"] = unavailable_today

    return context


def _rule_based_answer(question: str, context: dict, sources: list[dict]) -> tuple[str, bool]:
    """Returns (answer, used_sources) -- `used_sources` is True only when
    the answer text actually drew on the retrieved documents, so the API
    response never attaches sources to an answer they didn't inform."""
    q = question.lower()
    q_words = set(re.findall(r"[a-z]+", q))

    def has_all(*words) -> bool:
        return all(w in q_words for w in words)

    def has_any(*phrases) -> bool:
        return any(p in q for p in phrases)

    if has_any("overdue", "late", "missed deadline"):
        overdue = context["task_risk"]["overdue_tasks"]
        if not overdue:
            return "No tasks are currently overdue.", False
        return "Overdue tasks: " + ", ".join(f"{t['key']} ({t['title']})" for t in overdue) + ".", False

    if has_any("overload", "workload", "capacity"):
        return (
            f"Task risk data shows {len(context['task_risk']['over_estimate_tasks'])} task(s) have exceeded "
            f"their time estimate. See the Workload page for a full team breakdown."
        ), False

    if has_any("sprint status", "current sprint", "this sprint"):
        s = context["active_sprint"]
        if not s:
            return "There is no active sprint for this project right now.", False
        return (
            f"Sprint \"{s['name']}\" ({s['start_date']} to {s['end_date']}) has completed "
            f"{s['completed_points']} of {s['total_points']} story points."
            + (f" Goal: {s['goal']}." if s['goal'] else "")
        ), False

    if has_all("critical", "bug") or has_all("critical", "bugs"):
        bugs = context["quality_risk"]["critical_open_bugs"]
        if not bugs:
            return "No critical bugs are currently open.", False
        return "Critical open bugs: " + ", ".join(f"{b['key']} ({b['title']})" for b in bugs) + ".", False

    if has_any("risk of delay", "at risk", "is the project at risk"):
        return context["quality_risk"]["recommendation"], False

    if has_any("prioritize", "next", "what should we"):
        bugs = context["quality_risk"]["critical_open_bugs"]
        overdue = context["task_risk"]["overdue_tasks"]
        if bugs:
            return f"Highest priority: fix critical open bug {bugs[0]['key']} ({bugs[0]['title']}).", False
        if overdue:
            return f"Highest priority: address overdue task {overdue[0]['key']} ({overdue[0]['title']}).", False
        return "No urgent items found in overdue tasks or critical bugs right now.", False

    if has_any("available", "who is free", "who can"):
        unavailable = context["unavailable_today"]
        team_names = [m["name"] for m in context["team"]]
        available = [n for n in team_names if n not in unavailable]
        if not available:
            return "No team members are marked available today.", False
        return "Available today: " + ", ".join(available) + ".", False

    if sources:
        bullets = "; ".join(f"\"{s['title']}\" says: {s['snippet'].split(chr(10), 1)[-1][:150]}" for s in sources)
        return f"I couldn't map that to a specific metric, but relevant project documentation says: {bullets}", True

    return (
        "I don't have enough project data or documentation to answer that confidently. "
        "Try asking about overdue tasks, sprint status, critical bugs, or team availability, "
        "or add relevant project documents so I can search them."
    ), False


def answer_question(db: Session, project: Project, question: str, *, client_safe: bool = False) -> dict:
    context = _gather_context(db, project, client_safe=client_safe)
    sources, retrieval_method = ([], "none") if client_safe else rag_service.search(db, project.id, question, top_k=3)

    if client_safe:
        q = question.lower()
        if any(x in q for x in ("progress", "status", "project", "milestone", "roadmap")):
            s = context.get("active_sprint")
            if s:
                answer = (f"Project {project.name} is currently {project.status.value.replace('_', ' ')}. "
                          f"The active sprint has completed {s['completed_points']} of {s['total_points']} story points.")
            else:
                answer = f"Project {project.name} is currently {project.status.value.replace('_', ' ')} and has no active sprint."
            return {"answer": answer, "ai_generated": False, "retrieval_method": "none", "sources": []}
        return {"answer": "I can provide client-visible project status and progress, but internal employee, QA, workload, leave, and engineering information is not available to client accounts.", "ai_generated": False, "retrieval_method": "none", "sources": []}

    prompt = (
        f"You are an AI assistant embedded in an Agile project management tool. Answer the user's "
        f"question about project '{project.name}' using ONLY the structured data and document excerpts "
        f"below. If the data doesn't answer the question, say so plainly rather than guessing.\n\n"
        f"Structured project data: {context}\n\n"
        f"Relevant document excerpts: {sources}\n\n"
        f"Question: {question}\n\n"
        "Answer in 2-4 sentences, plain language, and don't claim certainty the data doesn't support."
    )
    ai_text = _call_gemini(prompt)
    ai_generated = bool(ai_text)

    if ai_generated:
        answer = ai_text
        used_sources = bool(sources)  # Gemini saw the retrieved excerpts as context
    else:
        answer, used_sources = _rule_based_answer(question, context, sources)

    returned_sources = sources if used_sources else []
    return {
        "answer": answer,
        "ai_generated": ai_generated,
        "retrieval_method": retrieval_method if returned_sources else "none",
        "sources": returned_sources,
    }
