"""Comprehensive page audit - check every route on the site"""
import urllib.request, urllib.parse, http.cookiejar, json, re

BASE = 'https://jhfguf.pythonanywhere.com'

# Routes to check
ROUTES = [
    '/', '/login', '/register', '/logout', '/forgot-password',
    '/user-dashboard', '/new-campaign', '/upload-cv',
    '/pricing', '/checkout', '/checkout-v2',
    '/services', '/services-new', '/wallet', '/stats',
    '/sent-emails', '/contact', '/referral',
    '/battle-station', '/war-room',
    '/funnel-analytics', '/ats-scorer', '/resume-tailor',
    '/for-employers', '/api-docs', '/trust',
    '/api/cron/tick',
]

# Check each route
for route in ROUTES:
    try:
        req = urllib.request.Request(BASE + route)
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode('utf-8', errors='replace')
        status = resp.getcode()
        
        # Check for issues
        issues = []
        if 'error' in html.lower() and 'traceback' in html.lower():
            issues.append('ERROR PAGE (traceback)')
        if status != 200 and status not in [301, 302, 303, 307, 308]:
            issues.append(f'UNEXPECTED STATUS {status}')
        
        # For 200 responses, check content
        if status == 200:
            has_doctype = '<!DOCTYPE html>' in html
            has_html = '<html' in html
            has_body = '<body' in html
            has_sidebar = '<div class="sidebar"' in html
            
            # Check cyberpunk theme
            has_cyberpunk = 'cyberpunk.css' in html
            
            if not has_doctype and not status in [301, 302, 303]:
                issues.append('MISSING DOCTYPE')
            
            # Check for broken content
            if len(html) < 100 and status == 200:
                issues.append('EMPTY PAGE')
            
            print(f'{status:3d} {route:25s} sidebar={1 if has_sidebar else 0} cyber={1 if has_cyberpunk else 0} | size={len(html):>6}')
            if issues:
                print(f'    ⚠️  {" | ".join(issues)} {html[:200]}')
        else:
            print(f'{status:3d} {route:25s} | redirect')
            
    except urllib.request.HTTPError as e:
        print(f'{e.code:3d} {route:25s} | HTTP {e.code} {str(e.reason)[:50]}')
    except Exception as e:
        print(f'--- {route:25s} | ERROR: {str(e)[:60]}')
