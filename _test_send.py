"""Test SMTP email sending from local machine"""
import asyncio, sys
sys.path.insert(0, r'C:\Users\samde\Desktop\cv sam new ma3 kimi')

async def test_send():
    from core.email_engine import EmailEngine
    
    engine = EmailEngine()
    print("Testing email_engine.send_application...")
    
    success, result = await engine.send_application(
        to_email="samatou683@gmail.com",
        company="Test Corp",
        title="Network Engineer",
        cover_html="<p>Test email from JobHunt Pro pipeline debug.</p>",
        cv_path=None,
        user_details={"name": "Sam Salameh", "skills": "Cisco, MikroTik, Fortinet"}
    )
    print(f"Success: {success}")
    print(f"Result: {result}")

asyncio.run(test_send())
