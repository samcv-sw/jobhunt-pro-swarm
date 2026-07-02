from fastapi import APIRouter, Response
import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/v1/calendar/sync/{interview_id}")
async def generate_calendar_invite(interview_id: str):
    """
    God Mode: Automatically generates an .ics file for the interview.
    When the user opens it on their phone, it syncs directly to Google/Apple Calendar.
    """
    # Mocking date parsing for demonstration.
    # In production, the AI parses the exact date/time from the HR email.

    start_time = datetime.datetime.now() + datetime.timedelta(days=3)
    end_time = start_time + datetime.timedelta(hours=1)

    dtstamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")
    dtstart = start_time.strftime("%Y%m%dT%H%M%SZ")
    dtend = end_time.strftime("%Y%m%dT%H%M%SZ")
    uid = str(uuid.uuid4())

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//JobHunt Pro//AI Auto-Interviewer//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:Technical Interview (Auto-Scheduled via JobHunt Pro)
DESCRIPTION:The AI has successfully negotiated this interview time based on your availability. Good luck!
LOCATION:Google Meet / Zoom
END:VEVENT
END:VCALENDAR"""

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=interview_{interview_id}.ics"
        },
    )
