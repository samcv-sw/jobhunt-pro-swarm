"""
PHASE 3: Cyberpunk UI Redesign Engine
Apex Glassmorphism + RTL/LTR Responsive Design
V1 Versioning Badge + Premium Visual Identity
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class GlassmorphismLevel(str, Enum):
    """Opacity and blur intensity levels"""
    SUBTLE = "subtle"      # 65% opacity, 10px blur
    STANDARD = "standard"  # 85% opacity, 20px blur
    INTENSE = "intense"    # 95% opacity, 30px blur


class ColorTheme(str, Enum):
    """Cyberpunk color schemes"""
    CYAN_DARK = "cyan_dark"    # Cyan/Purple on dark
    NEON_PINK = "neon_pink"    # Neon pink/Blue
    HOLOGRAPHIC = "holographic"  # Rainbow gradient


@dataclass
class GlassCard:
    """Apex Glass Card styling configuration"""
    title: str
    content: str
    glassmorphism_level: GlassmorphismLevel = GlassmorphismLevel.STANDARD
    icon: Optional[str] = None
    cta_button: Optional[str] = None
    rtl: bool = False  # Right-to-left support


class CyberpunkUIEngine:
    """Transform JobHunt Pro UI to Cyberpunk + Glassmorphism design"""
    
    def __init__(self, theme: ColorTheme = ColorTheme.CYAN_DARK):
        self.theme = theme
        self.version = "V 1"
        self.colors = self._init_colors()
        
    def _init_colors(self) -> Dict[str, str]:
        """Initialize cyberpunk color palette"""
        if self.theme == ColorTheme.CYAN_DARK:
            return {
                "primary": "#00F0FF",      # Bright cyan
                "secondary": "#9D00FF",   # Purple
                "accent": "#FF006E",      # Pink
                "background": "#0A121A",  # Dark navy
                "surface": "rgba(10, 18, 26, 0.85)",
                "border": "rgba(0, 240, 255, 0.15)",
                "text_primary": "#FFFFFF",
                "text_secondary": "#00F0FF"
            }
        elif self.theme == ColorTheme.NEON_PINK:
            return {
                "primary": "#FF006E",
                "secondary": "#00D9FF",
                "accent": "#FFB81C",
                "background": "#0D0221",
                "surface": "rgba(13, 2, 33, 0.85)",
                "border": "rgba(255, 0, 110, 0.15)",
                "text_primary": "#FFFFFF",
                "text_secondary": "#FF006E"
            }
        else:  # HOLOGRAPHIC
            return {
                "primary": "#00F0FF",
                "secondary": "#9D00FF",
                "accent": "#FF006E",
                "background": "#0A0E27",
                "surface": "rgba(10, 14, 39, 0.85)",
                "border": "rgba(157, 0, 255, 0.15)",
                "text_primary": "#FFFFFF",
                "text_secondary": "#00F0FF"
            }
    
    def generate_glass_card_css(self, level: GlassmorphismLevel = GlassmorphismLevel.STANDARD) -> str:
        """Generate Apex Glass Card CSS"""
        blur_map = {
            GlassmorphismLevel.SUBTLE: "10px",
            GlassmorphismLevel.STANDARD: "20px",
            GlassmorphismLevel.INTENSE: "30px"
        }
        opacity_map = {
            GlassmorphismLevel.SUBTLE: "0.65",
            GlassmorphismLevel.STANDARD: "0.85",
            GlassmorphismLevel.INTENSE: "0.95"
        }
        
        blur = blur_map[level]
        opacity = opacity_map[level]
        
        return f"""
.apex-glass-card {{
    background: rgba(10, 18, 26, {opacity});
    border: 1px solid {self.colors['border']};
    border-radius: 24px;
    padding: 24px 32px;
    backdrop-filter: blur({blur});
    -webkit-backdrop-filter: blur({blur});
    box-shadow: 0 8px 32px rgba(0, 240, 255, 0.1);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
    overflow: hidden;
}}

.apex-glass-card:hover {{
    border-color: {self.colors['primary']};
    box-shadow: 0 8px 48px rgba(0, 240, 255, 0.25);
    transform: translateY(-4px);
}}

.apex-glass-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, {self.colors['primary']}, transparent);
    opacity: 0.3;
}}
"""
    
    def generate_rtl_logical_css(self) -> str:
        """Generate CSS with RTL logical properties"""
        return """
/* RTL/LTR Logical Properties */
.apex-container {
    margin-inline-start: auto;
    margin-inline-end: auto;
    padding-inline-start: 24px;
    padding-inline-end: 24px;
}

.apex-card {
    margin-block-start: 16px;
    margin-block-end: 16px;
    padding-block-start: 20px;
    padding-block-end: 20px;
    padding-inline-start: 24px;
    padding-inline-end: 24px;
}

.apex-text {
    text-align: start;
    direction: var(--direction, ltr);
}

.apex-button {
    padding-inline-start: 20px;
    padding-inline-end: 20px;
    border-radius: 12px;
    transition: all 0.2s ease;
}

.apex-button:hover {
    padding-inline-start: 24px;
    padding-inline-end: 24px;
}

/* Arabic typography */
html[lang="ar"] {
    font-family: 'Cairo', 'Tajawal', 'Droid Arabic Kufi', sans-serif;
    direction: rtl;
}

html[lang="en"] {
    font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
    direction: ltr;
}
"""
    
    def generate_version_badge_html(self) -> str:
        """Generate V1 versioning badge HTML"""
        return f"""
<div class="version-badge-container">
    <div class="version-badge">
        <span class="version-text">{self.version}</span>
        <span class="version-label">Next-Gen</span>
    </div>
    <style>
        .version-badge-container {{
            position: fixed;
            top: 16px;
            right: 16px;
            z-index: 1000;
        }}
        
        .version-badge {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, {self.colors['primary']}, {self.colors['secondary']});
            border: 1px solid {self.colors['border']};
            border-radius: 20px;
            padding: 8px 16px;
            backdrop-filter: blur(20px);
            box-shadow: 0 4px 16px rgba(0, 240, 255, 0.2);
        }}
        
        .version-text {{
            font-weight: 700;
            font-size: 14px;
            color: {self.colors['text_primary']};
        }}
        
        .version-label {{
            font-size: 12px;
            color: {self.colors['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
    </style>
</div>
"""
    
    def generate_header_html(self) -> str:
        """Generate Cyberpunk header with glassmorphism"""
        return f"""
<header class="cyberpunk-header apex-glass-card">
    <div class="header-content">
        <div class="logo-section">
            <h1 class="brand-title">JobHunt Pro</h1>
            <span class="brand-subtitle">AI-Powered Job Automation</span>
        </div>
        <nav class="header-nav">
            <a href="#features" class="nav-link">Features</a>
            <a href="#pricing" class="nav-link">Pricing</a>
            <a href="#dashboard" class="nav-link">Dashboard</a>
        </nav>
    </div>
    
    <style>
        .cyberpunk-header {{
            position: sticky;
            top: 0;
            z-index: 100;
            margin-bottom: 32px;
        }}
        
        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 24px;
        }}
        
        .logo-section {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        
        .brand-title {{
            font-size: 24px;
            font-weight: 700;
            color: {self.colors['primary']};
            text-shadow: 0 0 10px {self.colors['primary']};
            margin: 0;
        }}
        
        .brand-subtitle {{
            font-size: 12px;
            color: {self.colors['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        
        .header-nav {{
            display: flex;
            gap: 24px;
        }}
        
        .nav-link {{
            color: {self.colors['text_primary']};
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            position: relative;
            padding-bottom: 4px;
            transition: color 0.3s ease;
        }}
        
        .nav-link::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 0;
            height: 2px;
            background: linear-gradient(90deg, {self.colors['primary']}, {self.colors['secondary']});
            transition: width 0.3s ease;
        }}
        
        .nav-link:hover {{
            color: {self.colors['primary']};
        }}
        
        .nav-link:hover::after {{
            width: 100%;
        }}
    </style>
</header>
"""
    
    def generate_job_card_template(self, job_data: Dict) -> str:
        """Generate cyberpunk job card"""
        return f"""
<div class="job-card apex-glass-card">
    <div class="job-header">
        <div class="company-section">
            <h3 class="job-title">{job_data.get('title', 'Position')}</h3>
            <p class="company-name">{job_data.get('company', 'Company')}</p>
        </div>
        <span class="match-score">{job_data.get('match_score', 0):.0%} Match</span>
    </div>
    
    <div class="job-details">
        <div class="detail-item">
            <span class="detail-label">Location</span>
            <span class="detail-value">{job_data.get('location', 'Remote')}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Salary</span>
            <span class="detail-value">${job_data.get('salary_min', 0):,.0f} - ${job_data.get('salary_max', 0):,.0f}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Level</span>
            <span class="detail-value">{job_data.get('level', 'Mid')}</span>
        </div>
    </div>
    
    <div class="job-actions">
        <button class="btn-primary">Apply Now</button>
        <button class="btn-secondary">Save Job</button>
    </div>
    
    <style>
        .job-card {{
            margin-bottom: 20px;
            animation: slideIn 0.3s ease-out;
        }}
        
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .job-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid {self.colors['border']};
        }}
        
        .job-title {{
            font-size: 18px;
            font-weight: 700;
            color: {self.colors['primary']};
            margin: 0 0 8px 0;
        }}
        
        .company-name {{
            font-size: 14px;
            color: {self.colors['text_secondary']};
            margin: 0;
        }}
        
        .match-score {{
            background: linear-gradient(135deg, {self.colors['primary']}, {self.colors['secondary']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            font-size: 16px;
        }}
        
        .job-details {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 16px;
        }}
        
        .detail-item {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        
        .detail-label {{
            font-size: 12px;
            color: {self.colors['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .detail-value {{
            font-size: 14px;
            color: {self.colors['text_primary']};
            font-weight: 500;
        }}
        
        .job-actions {{
            display: flex;
            gap: 12px;
        }}
        
        .btn-primary, .btn-secondary {{
            flex: 1;
            padding: 12px 16px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, {self.colors['primary']}, {self.colors['secondary']});
            color: #000;
        }}
        
        .btn-primary:hover {{
            box-shadow: 0 0 20px {self.colors['primary']};
            transform: translateY(-2px);
        }}
        
        .btn-secondary {{
            background: transparent;
            border: 1px solid {self.colors['primary']};
            color: {self.colors['primary']};
        }}
        
        .btn-secondary:hover {{
            background: rgba(0, 240, 255, 0.1);
            border-color: {self.colors['secondary']};
            color: {self.colors['secondary']};
        }}
    </style>
</div>
"""


# Global instance
ui_engine = CyberpunkUIEngine(theme=ColorTheme.CYAN_DARK)


async def generate_full_cyberpunk_stylesheet() -> str:
    """Generate complete cyberpunk stylesheet"""
    styles = ""
    styles += ui_engine.generate_glass_card_css()
    styles += ui_engine.generate_rtl_logical_css()
    
    # Additional animations
    styles += """
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 10px rgba(0, 240, 255, 0.5); }
        50% { box-shadow: 0 0 20px rgba(0, 240, 255, 0.8); }
    }
    
    .glow-effect { animation: glow 2s infinite; }
    
    @keyframes scanlines {
        0% { transform: translateY(0); }
        100% { transform: translateY(10px); }
    }
    
    .scanline {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(0, 240, 255, 0.5), transparent);
        animation: scanlines 8s linear infinite;
        opacity: 0.3;
    }
    """
    
    return styles
