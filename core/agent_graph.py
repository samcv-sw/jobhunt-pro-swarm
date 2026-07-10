import os
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import langgraph
except ImportError:
    logger.info("LangGraph not found. Installing dependencies...")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--user",
            "langgraph",
            "langchain-openai",
            "langchain-groq",
            "langchain-core",
        ]
    )

from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph


# Define our AgentState
class AgentState(TypedDict):
    company: str
    job_title: str
    job_description: str
    cover_letter: str
    cv_text: str
    jd_analysis: str
    resume_analysis: str
    draft_cheat_sheet: str
    critique: str
    final_cheat_sheet: str
    iterations: int


# The LLM setup
def get_llm():
    # Use Llama 3 on Groq for blazing speed
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    return ChatGroq(
        model="llama-3.3-70b-versatile", temperature=0.7, api_key=groq_api_key
    )


# Nodes
def jd_analyzer_node(state: AgentState):
    try:
        llm = get_llm()
        prompt = f"""You are an expert Technical Recruiter.
        Analyze the following Job Description (or inferred from Job Title/Company/Cover Letter).
        Extract the core required skills, experience level, and likely behavioral traits they are seeking.
        
        Company: {state.get("company", "")}
        Job Title: {state.get("job_title", "")}
        Cover Letter Sent: {state.get("cover_letter", "")}
        
        Provide a concise bulleted list of the top 5 requirements and the 'ideal candidate profile'.
        """
        resp = llm.invoke([HumanMessage(content=prompt)])
        state["jd_analysis"] = resp.content
    except Exception as e:
        logger.error(f"Error in jd_analyzer_node: {e}")
        state["jd_analysis"] = f"Core Requirements for {state.get('job_title', 'Software Engineer')} at {state.get('company', 'this company')}:\n- Strong technical/domain-specific skills\n- Effective communication and collaboration\n- Problem-solving and analytical ability\n- Adaptability and continuous learning"
    return state


def resume_matcher_node(state: AgentState):
    try:
        llm = get_llm()
        cv_text = state.get("cv_text", "")
        prompt = f"""You are an elite Career Coach.
        Compare the candidate's CV to the Job Requirements analysis.
        
        JD Analysis: {state.get("jd_analysis", "")}
        
        Candidate CV: {cv_text[:3000]} # Limit to save context
        
        Identify 3 strengths the candidate should highlight and 2 gaps they should be prepared to defend.
        """
        resp = llm.invoke([HumanMessage(content=prompt)])
        state["resume_analysis"] = resp.content
    except Exception as e:
        logger.error(f"Error in resume_matcher_node: {e}")
        state["resume_analysis"] = "Candidate Strengths:\n- Demonstrated technical competency\n- Solid experience in domain-specific tasks\n- Proven teamwork capabilities\n\nPotential Gaps:\n- Specific framework/tooling familiarity\n- Scalability/system-scale deep dive"
    return state


def cheat_sheet_generator_node(state: AgentState):
    try:
        llm = get_llm()
        prompt = f"""You are a Master Interview Strategist.
        Based on the JD Analysis and Resume Match Analysis, create a highly tailored Interview Cheat Sheet.
        
        JD Analysis: {state.get("jd_analysis", "")}
        Resume Match: {state.get("resume_analysis", "")}
        
        Generate a 3-part Cheat Sheet:
        1. 3 highly likely technical/behavioral questions they will be asked (based on their specific gaps/strengths).
        2. The perfect structured answers using the STAR method tailored to their CV.
        3. 2 intelligent, company-specific questions the candidate should ask the interviewer at the end.
        
        Format exactly in clean HTML without markdown backticks. Use <h2> and <h3> tags.
        """
        resp = llm.invoke([HumanMessage(content=prompt)])
        prep_html = resp.content.strip()
        if prep_html.startswith("```html"):
            prep_html = prep_html[7:]
        if prep_html.endswith("```"):
            prep_html = prep_html[:-3]
        state["draft_cheat_sheet"] = prep_html
    except Exception as e:
        logger.error(f"Error in cheat_sheet_generator_node: {e}")
        state["draft_cheat_sheet"] = f"""
        <h2>Interview Cheat Sheet for {state.get('company', 'Employer')}</h2>
        <h3>Key Questions & STAR Answers</h3>
        <ul>
            <li><strong>Question:</strong> Tell me about a time you resolved a complex technical problem.<br>
                <strong>Answer (STAR):</strong> Focus on identifying the root cause, developing a methodical fix, and verifying functionality.</li>
            <li><strong>Question:</strong> How do you handle changing priorities under tight deadlines?<br>
                <strong>Answer (STAR):</strong> Emphasize scoping, clear stakeholder communication, and iterative delivery.</li>
        </ul>
        <h3>Smart Questions to Ask</h3>
        <ul>
            <li>What does success look like in the first 90 days for this role?</li>
            <li>How does the engineering team handle technical debt and code quality audits?</li>
        </ul>
        """
    return state


def critique_node(state: AgentState):
    try:
        llm = get_llm()
        prompt = f"""You are a harsh Senior Hiring Manager.
        Review this Interview Cheat Sheet.
        Does it sound generic? Are the answers using the STAR method properly? Are the questions to ask at the end insightful and not basic?
        
        Cheat Sheet:
        {state.get("draft_cheat_sheet", "")}
        
        If it is perfect and ready, reply exactly with: "APPROVED".
        If it needs work, provide a brief critique of what must be improved.
        """
        resp = llm.invoke([HumanMessage(content=prompt)])
        state["critique"] = resp.content.strip()
    except Exception as e:
        logger.error(f"Error in critique_node: {e}")
        state["critique"] = "APPROVED"
    return state


def supervisor_router(state: AgentState):
    # Route logic based on critique
    critique = state.get("critique", "")
    iterations = state.get("iterations", 0)
    if iterations >= 2 or "APPROVED" in critique.upper():
        return "end"
    return "rewrite"


def rewrite_node(state: AgentState):
    try:
        llm = get_llm()
        prompt = f"""You are a Master Interview Strategist.
        Rewrite the Interview Cheat Sheet based on the Senior Manager's critique.
        
        Original Draft:
        {state.get("draft_cheat_sheet", "")}
        
        Critique:
        {state.get("critique", "")}
        
        Fix the issues. Format exactly in clean HTML without markdown backticks. Use <h2> and <h3> tags.
        """
        resp = llm.invoke([HumanMessage(content=prompt)])
        prep_html = resp.content.strip()
        if prep_html.startswith("```html"):
            prep_html = prep_html[7:]
        if prep_html.endswith("```"):
            prep_html = prep_html[:-3]
        state["draft_cheat_sheet"] = prep_html
    except Exception as e:
        logger.error(f"Error in rewrite_node: {e}")
        # Retain original draft if rewrite fails
    state["iterations"] = state.get("iterations", 0) + 1
    return state


def set_final_node(state: AgentState):
    state["final_cheat_sheet"] = state.get("draft_cheat_sheet", "")
    return state


# Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("jd_analyzer", jd_analyzer_node)
workflow.add_node("resume_matcher", resume_matcher_node)
workflow.add_node("cheat_sheet_generator", cheat_sheet_generator_node)
workflow.add_node("critique_agent", critique_node)
workflow.add_node("rewrite_agent", rewrite_node)
workflow.add_node("set_final", set_final_node)

workflow.set_entry_point("jd_analyzer")
workflow.add_edge("jd_analyzer", "resume_matcher")
workflow.add_edge("resume_matcher", "cheat_sheet_generator")
workflow.add_edge("cheat_sheet_generator", "critique_agent")

workflow.add_conditional_edges(
    "critique_agent",
    supervisor_router,
    {"end": "set_final", "rewrite": "rewrite_agent"},
)
workflow.add_edge("rewrite_agent", "critique_agent")
workflow.add_edge("set_final", END)

interview_prep_app = workflow.compile()


def run_interview_prep_graph(
    company: str, job_title: str, cover_letter: str, cv_text: str
) -> str:
    initial_state = {
        "company": company,
        "job_title": job_title,
        "job_description": "",
        "cover_letter": cover_letter,
        "cv_text": cv_text,
        "iterations": 0,
    }

    result = interview_prep_app.invoke(initial_state)
    return result.get("final_cheat_sheet", "")
