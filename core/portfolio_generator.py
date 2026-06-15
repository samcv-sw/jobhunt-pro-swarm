"""
JobHunt Pro - Zero-Click Portfolio Generator (Item 3)
Generates a highly-aesthetic, responsive HTML/JS portfolio from the user's CV.
"""
import os
import json

def generate_portfolio(user_name: str, profession: str, email: str, linkedin_url: str, about: str, skills: list) -> str:
    """Generates an ultra-modern Next.js-style static HTML portfolio."""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{user_name} - {profession}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            background-color: #0f172a;
            color: #f8fafc;
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
        }}
        .glass-card {{
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
        }}
        .gradient-text {{
            background: linear-gradient(to right, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
    </style>
</head>
<body class="antialiased min-h-screen flex flex-col items-center justify-center p-6">
    <div class="max-w-4xl w-full space-y-12 animate-fade-in-up">
        
        <!-- Header -->
        <header class="text-center space-y-4">
            <h1 class="text-5xl md:text-7xl font-extrabold tracking-tight">
                {user_name}
            </h1>
            <h2 class="text-2xl md:text-3xl font-semibold gradient-text">
                {profession}
            </h2>
            <p class="text-slate-400 max-w-2xl mx-auto leading-relaxed text-lg">
                {about}
            </p>
        </header>

        <!-- Links -->
        <div class="flex justify-center space-x-6">
            <a href="mailto:{email}" class="px-8 py-3 bg-slate-800 hover:bg-slate-700 transition rounded-full font-medium border border-slate-600">
                Email Me
            </a>
            <a href="{linkedin_url}" target="_blank" class="px-8 py-3 bg-blue-600 hover:bg-blue-500 transition rounded-full font-medium shadow-[0_0_15px_rgba(37,99,235,0.5)]">
                LinkedIn Profile
            </a>
        </div>

        <!-- Skills -->
        <section class="glass-card p-8 mt-12">
            <h3 class="text-2xl font-bold mb-6 border-b border-slate-700 pb-2">Core Competencies</h3>
            <div class="flex flex-wrap gap-3">
                {"".join([f'<span class="px-4 py-2 bg-slate-800 rounded-lg text-sm font-medium text-slate-300 border border-slate-700">{skill}</span>' for skill in skills])}
            </div>
        </section>
        
        <footer class="text-center text-slate-500 text-sm mt-16 pb-8">
            Generated automatically by JobHunt Pro AI Core.
        </footer>
    </div>
</body>
</html>"""
    
    # Save the portfolio
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "static", "portfolios")
    os.makedirs(output_dir, exist_ok=True)
    
    # URL-friendly filename
    safe_name = user_name.lower().replace(" ", "_")
    file_path = os.path.join(output_dir, f"{safe_name}.html")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return f"/static/portfolios/{safe_name}.html"
