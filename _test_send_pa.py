"""Test SMTP on PA — writes result to file"""
import asyncio, json, sys, traceback, os
sys.path.insert(0, '/home/JHFGUF/jobhunt')
os.chdir('/home/JHFGUF/jobhunt')

async def test():
    try:
        from core.email_engine import EmailEngine
        engine = EmailEngine()
        success, result = await engine.send_application(
            to_email="samatou683@gmail.com",
            company="TestFromPA",
            title="Network Engineer v16.322",
            cover_html="<p>Test email from PA pipeline debug</p>",
            cv_path=None,
            user_details={"name": "Sam Salameh"}
        )
        return {"success": success, "result": str(result)}
    except Exception as e:
        return {"success": False, "error": str(e), "trace": traceback.format_exc()}

result = asyncio.run(test())
with open('/home/JHFGUF/jobhunt/_test_result.json', 'w') as f:
    json.dump(result, f)
print('DONE')
