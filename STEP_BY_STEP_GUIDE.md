# JobHunt Pro — Step by Step Guide (Zero Knowledge)

Follow these steps exactly. Don't skip any.

---

## STEP 1: Install Python (5 minutes)

```
1. Open browser, go to: https://www.python.org/downloads/
2. Click "Download Python 3.12" (big yellow button)
3. Run the downloaded file
4. IMPORTANT: Check the box "Add python.exe to PATH"
5. Click "Install Now"
6. Wait for it to finish
7. Click "Close"
```

### Verify Python is installed:
```
1. Press Windows key
2. Type "cmd"
3. Press Enter (black window opens)
4. Type: python --version
5. Press Enter
6. You should see: Python 3.12.x
```

---

## STEP 2: Open the Project Folder (1 minute)

```
1. Open File Explorer
2. Go to: C:\Users\samde\Desktop\cv sam new ma3 kimi
3. This is your project folder
```

---

## STEP 3: Install Dependencies (5 minutes)

```
1. In the project folder, click the address bar at the top
2. Type: cmd
3. Press Enter (black window opens in the project folder)
4. Type: pip install -r requirements.txt
5. Press Enter
6. Wait for it to finish (2-3 minutes)
7. You should see "Successfully installed"
```

---

## STEP 4: Get Gmail App Password (10 minutes)

This lets the system send emails from your Gmail.

```
1. Open browser
2. Go to: https://myaccount.google.com/security
3. Sign in with your Gmail (samsalameh.cv@gmail.com)
4. On the left, click "2-Step Verification"
5. If not enabled:
   - Click "Get Started"
   - Enter your phone number
   - Enter the code sent to your phone
   - Click "Turn On"
6. Go back to Security page
7. Search for "App passwords" (or go to: https://myaccount.google.com/apppasswords)
8. At the bottom, click "Create"
9. Type name: "JobHunt"
10. Click "Create"
11. You'll see a 16-character password like: abcd efgh ijkl mnop
12. COPY this password (you won't see it again!)
13. Click "Done"
```

---

## STEP 5: Configure .env File (2 minutes)

```
1. In the project folder, find the file ".env"
2. Right-click it → "Open with" → "Notepad"
3. Find this line:
   GMAIL_APP_PASSWORD_1=

4. After the = sign, paste your 16-character password:
   GMAIL_APP_PASSWORD_1=abcd efgh ijkl mnop

5. Find this line:
   DRY_RUN=true

6. Change it to:
   DRY_RUN=false

7. Save the file (Ctrl+S)
8. Close Notepad
```

---

## STEP 6: Start the System (1 minute)

```
1. In the project folder, click the address bar at the top
2. Type: cmd
3. Press Enter (black window opens)
4. Type: python auto_run.py
5. Press Enter
6. You should see:
   "JobHunt Pro starting..."
   "Web server: http://localhost:8000"
   "Dashboard: http://localhost:8000/dashboard"
```

---

## STEP 7: Open the Dashboard (30 seconds)

```
1. Open browser
2. Go to: http://localhost:8000/dashboard
3. You should see the Cyberpunk Dashboard
4. It shows:
   - 200 agents (green dots)
   - Job search stats
   - Email provider status
   - Activity feed
```

---

## STEP 8: Watch It Work

The system will automatically:
```
1. Search for jobs (DuckDuckGo, Bing, Google)
2. Find company email addresses
3. Generate personalized cover letters
4. Send applications via Gmail
5. Follow up after 4 days
6. Parse responses
7. Auto-reply to interviews
```

You don't need to do anything. It runs by itself.

---

## STEP 9: Check What Was Sent

```
1. Open File Explorer
2. Go to: C:\Users\samde\Desktop\cv sam new ma3 kimi\sent_mails
3. You'll see .eml files (emails that were sent)
4. Double-click any .eml file to open it in Outlook/Gmail
```

---

## Common Problems & Solutions

### "Python is not recognized"
```
Solution:
1. Restart your computer
2. Try again: python --version
```

### "pip is not recognized"
```
Solution:
1. Type: python -m pip --version
2. If that works, use: python -m pip install -r requirements.txt
```

### "ModuleNotFoundError: No module named 'xyz'"
```
Solution:
1. Type: pip install xyz
2. Example: pip install aiosqlite
```

### "Address already in use"
```
Solution:
1. Close the black window
2. Open Task Manager (Ctrl+Shift+Esc)
3. Find "python" process
4. Right-click → End Task
5. Try again: python auto_run.py
```

### "No emails being sent"
```
Solution:
1. Check DRY_RUN=false in .env
2. Check Gmail app password is correct
3. Check internet connection
```

### Dashboard shows "Not Found"
```
Solution:
1. Make sure system is running (Step 6)
2. Use exact URL: http://localhost:8000/dashboard
3. Don't use https://
```

---

## What You Get

```
✅ 200 agents searching jobs 24/7
✅ Cover letters auto-generated
✅ Applications sent automatically
✅ Follow-ups sent after 4 days
✅ Responses parsed and categorized
✅ Dashboard shows everything
✅ 2,100 emails/day capacity
✅ 150 search combinations (15 titles × 10 locations)
```

---

## To Stop the System

```
1. Go to the black window
2. Press Ctrl+C
3. Type: Y
4. Press Enter
```

---

## To Restart the System

```
1. Open the project folder
2. Click address bar → type: cmd → Press Enter
3. Type: python auto_run.py
4. Press Enter
```

---

## Daily Routine

```
Every day:
  - System runs automatically
  - Check dashboard: http://localhost:8000/dashboard
  - Check sent_mails folder for what was sent
  - Check your email for responses

Every week:
  - Review interview invitations
  - Update your calendar
  - Prepare for interviews
```

---

## Need Help?

```
- Check the sent_mails folder
- Read the README.md file
- Read the ARCHITECTURE_BLUEPRINT.md file
```

---

**You're done! The system is running. Good luck with your job search!**
