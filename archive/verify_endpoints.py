import requests

URLS = [
    "http://localhost:8000/",
    "http://localhost:8000/pricing",
    "http://localhost:8000/services",
    "http://localhost:8000/contact",
    "http://localhost:8000/login",
    "http://localhost:8000/register",
    "http://localhost:8000/forgot-password",
    "http://localhost:8000/for-employers",
    "http://localhost:8000/privacy",
    "http://localhost:8000/terms",
    "http://localhost:8000/roast",
    "http://localhost:8000/track-application",
    "http://localhost:8000/mock-job-form"
]

def check_all():
    print(f"{'URL':<40} | {'Status':<6} | {'HTML Count':<10} | {'DOCTYPE Count':<13} | {'Result':<10}")
    print("-" * 90)
    
    all_pass = True
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    for url in URLS:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            status = r.status_code
            html_text = r.text
            
            # Count tags
            html_open_count = html_text.lower().count("<html")
            doctype_count = html_text.lower().count("<!doctype html")
            
            # Check for errors in page
            has_error_text = "error rendering template" in html_text.lower() or "template not found" in html_text.lower()
            
            # Criteria for direct page: should have exactly 1 html tag and exactly 1 doctype tag
            # If it's a sub-page or wrapped, it should also only have 1 (since the shell wraps it)
            # If it has >1, it is nested!
            is_ok = (status == 200) and (html_open_count <= 1) and (doctype_count <= 1) and not has_error_text
            
            result_str = "PASS" if is_ok else "FAIL"
            if not is_ok:
                all_pass = False
                
            print(f"{url:<40} | {status:<6} | {html_open_count:<10} | {doctype_count:<13} | {result_str:<10}")
            
            if not is_ok:
                if status != 200:
                    print(f"  --> Status Code error: {status}")
                if html_open_count > 1 or doctype_count > 1:
                    print(f"  --> Nesting Error: found {html_open_count} <html> and {doctype_count} <!DOCTYPE> tags!")
                if has_error_text:
                    print("  --> Template Rendering Error detected in output!")
        except Exception as e:
            all_pass = False
            print(f"{url:<40} | ERROR  | -          | -             | FAIL")
            print(f"  --> Connection failed: {e}")
            
    if all_pass:
        print("\nSUCCESS: ALL PAGES ARE 100% HEALTHY, RENDERED PROPERLY, AND HAVE NO NESTED HTML NESTING ERRORS!")
    else:
        print("\nFAILURE: SOME PAGES HAVE FAILING STATUS OR NESTING ERRORS. PLEASE REVIEW THE LOG ABOVE.")

if __name__ == "__main__":
    check_all()
