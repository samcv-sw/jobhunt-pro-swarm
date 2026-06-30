#!/usr/bin/env python
import os
import sys
import asyncio

# Add project root to sys.path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_provider_pool import LLMProviderPool

# Candidate Profile Mock Data
CANDIDATE_PROFILE = {
    "name": "Samir Doe",
    "email": "samir.doe@example.com",
    "linkedin": "https://linkedin.com/in/samir-doe-fastapi",
    "experience": (
        "5 years of experience in Python and FastAPI backend development. "
        "Built and scaled REST and GraphQL APIs for enterprise platforms. "
        "Expert in asynchronous programming (asyncio), databases (PostgreSQL/SQLite), "
        "and integrating LLMs/Generative AI into software agents."
    )
}

async def generate_ai_answer(question: str, pool: LLMProviderPool) -> str:
    """Generates an answer to a custom job application question using AI, falling back to a smart mock if no API keys are present."""
    prompt = f"""
    You are applying for a software engineering job.
    Here is your professional experience:
    {CANDIDATE_PROFILE["experience"]}

    Write a concise, professional, and compelling answer (2-3 sentences) to this application question:
    "{question}"
    """
    
    # Check if any LLM providers are configured
    if any(p.config.is_configured for p in pool._providers.values() if p.config.name.value != "dummy"):
        try:
            print(f"Generating AI response for: '{question[:40]}...' using LLM Pool...")
            response = await pool.complete(prompt=prompt, system_prompt="You are a professional software engineer applicant.")
            if response and response.strip():
                return response.strip()
        except Exception as e:
            print(f"LLM generation failed ({e}), falling back to local simulation...")
            
    # Local simulation fallback if no API keys configured
    print(f"No active API keys found. Simulating AI response for: '{question[:40]}...'")
    if "why" in question.lower() or "join" in question.lower() or "team" in question.lower():
        return (
            f"I want to join the team because of your focus on cutting-edge AI automation. "
            f"With my background in Python and backend APIs, I am excited to help build scalable, "
            f"autonomous job hunting solutions that deliver immediate value to users."
        )
    elif "experience" in question.lower() or "python" in question.lower() or "fastapi" in question.lower() or "async" in question.lower():
        return (
            f"I have extensive experience building microservices with FastAPI and asynchronous Python. "
            f"I regularly leverage asyncio for high-throughput tasks, integrate SQLite/PostgreSQL databases, "
            f"and optimize background task workers for maximum reliability."
        )
    else:
        return f"Based on my 5 years of Python experience, I am confident in my ability to contribute effectively, write clean, async-native code, and implement intelligent AI systems."

async def run_ai_application():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: playwright is not installed!")
        print("To run this demo, please install Playwright using:")
        print("  pip install playwright")
        print("  playwright install chromium")
        return

    # Initialize LLM Pool
    pool = LLMProviderPool().initialize()

    print("==================================================================")
    print("🤖 STARTING AUTONOMOUS PLAYWRIGHT + AI APPLY DEMO")
    print("==================================================================")
    
    async with async_playwright() as p:
        # Launch browser in headful mode so the user can watch!
        print("Launching Chromium browser...")
        browser = await p.chromium.launch(headless=False, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to our mock job form
        url = "http://localhost:8000/mock-job-form"
        print(f"Navigating to job form: {url}...")
        try:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Failed to connect to {url}. Is the FastAPI server running?")
            print(e)
            await browser.close()
            return
            
        print("\nForm loaded! Autofilling standard fields...")
        
        # 1. Autofill standard fields
        await page.fill("#first_name", CANDIDATE_PROFILE["name"])
        await asyncio.sleep(0.5)
        await page.fill("#email", CANDIDATE_PROFILE["email"])
        await asyncio.sleep(0.5)
        await page.fill("#linkedin_url", CANDIDATE_PROFILE["linkedin"])
        await asyncio.sleep(0.5)
        
        # 2. Scrape custom questions and use AI to write answers
        print("\nScanning page for custom questions...")
        
        # Question 1
        q1_label = await page.inner_text("label[for='custom_q1']")
        print(f"Detected Custom Question 1: '{q1_label}'")
        q1_answer = await generate_ai_answer(q1_label, pool)
        print(f"AI Generated Answer 1:\n  \"{q1_answer}\"")
        await page.fill("#custom_q1", q1_answer)
        await asyncio.sleep(1)
        
        # Question 2
        q2_label = await page.inner_text("label[for='custom_q2']")
        print(f"Detected Custom Question 2: '{q2_label}'")
        q2_answer = await generate_ai_answer(q2_label, pool)
        print(f"AI Generated Answer 2:\n  \"{q2_answer}\"")
        await page.fill("#custom_q2", q2_answer)
        await asyncio.sleep(1)
        
        # Take a screenshot before submitting
        screenshot_path = "scratch/pre_submit_form.png"
        os.makedirs("scratch", exist_ok=True)
        await page.screenshot(path=screenshot_path)
        print(f"\nForm complete! Saved screenshot to: {screenshot_path}")
        
        # 3. Submit application
        print("Submitting application form...")
        await page.click(".btn-submit")
        await page.wait_for_load_state("networkidle")
        
        # Verify success page
        success_title = await page.title()
        print(f"\nSuccess Page Loaded: '{success_title}'")
        success_text = await page.inner_text("h1")
        print(f"Heading: '{success_text}'")
        
        # Take a success screenshot
        success_screenshot = "scratch/success_submitted.png"
        await page.screenshot(path=success_screenshot)
        print(f"Saved submission success screenshot to: {success_screenshot}")
        
        print("\n==================================================================")
        print("🎉 SUCCESS: Autonomous application completed successfully!")
        print("==================================================================")
        
        await asyncio.sleep(5) # Let the user see the browser for a few seconds before closing
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_ai_application())
