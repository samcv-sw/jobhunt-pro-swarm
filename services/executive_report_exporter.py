"""
Executive Analytics & Campaign Exporter Service for JobHunt Pro.
Generates CSV spreadsheets and executive HTML/PDF report summaries for outreach campaigns.
"""

import io
import csv
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ReportExportRequest(BaseModel):
    campaign_id: str = Field(default="cmp_gcc_2026", description="Campaign identifier")
    campaign_name: str = Field(default="GCC Enterprise Tech Outreach", description="Campaign name")
    leads_data: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"lead_id": "L101", "name": "Ahmad Al-Mansoor", "company": "Aramco Tech", "channel": "WhatsApp", "status": "Responded", "conversion_score": 92},
            {"lead_id": "L102", "name": "Sarah Jenkins", "company": "Dubai Future Corp", "channel": "Email", "status": "Meeting Scheduled", "conversion_score": 98},
            {"lead_id": "L103", "name": "Fahad Al-Qatani", "company": "Neom Mobility", "channel": "LinkedIn", "status": "Contacted", "conversion_score": 85}
        ]
    )


class ExecutiveReportExporter:
    def export_campaign_csv(self, req: ReportExportRequest) -> str:
        """
        Generates RFC 4180 compliant CSV string for campaign leads data.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(["Lead ID", "Candidate / Contact Name", "Company", "Outreach Channel", "Campaign Status", "AI Conversion Score"])
        
        # Write rows
        for lead in req.leads_data:
            writer.writerow([
                lead.get("lead_id", ""),
                lead.get("name", ""),
                lead.get("company", ""),
                lead.get("channel", ""),
                lead.get("status", ""),
                lead.get("conversion_score", 0)
            ])
            
        return output.getvalue()

    def export_executive_html_report(self, req: ReportExportRequest) -> Dict[str, Any]:
        """
        Generates an executive HTML report summary for campaign metrics.
        """
        total_leads = len(req.leads_data)
        avg_score = sum([l.get("conversion_score", 0) for l in req.leads_data]) / max(total_leads, 1)
        
        html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Executive Summary - {req.campaign_name}</title>
    <style>
        body {{ font-family: 'Cairo', 'Tajawal', sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; }}
        .header {{ border-bottom: 2px solid #3b82f6; padding-bottom: 12px; margin-bottom: 24px; }}
        .metric-card {{ background: #1e293b; padding: 16px; border-radius: 8px; margin-bottom: 16px; border-inline-start: 4px solid #10b981; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
        th, td {{ padding: 12px; text-align: right; border-bottom: 1px solid #334155; }}
        th {{ background: #1e293b; color: #60a5fa; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>تقرير أداء الحملة التنفيذي: {req.campaign_name}</h1>
        <p>معرّف الحملة: {req.campaign_id}</p>
    </div>
    <div class="metric-card">
        <h3>إجمالي العملاء المستهدفين: {total_leads}</h3>
        <p>متوسط مؤشر التحويل الذكي: {avg_score:.1f}%</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>اسم العميل / المستهدف</th>
                <th>الشركة</th>
                <th>قناة التواصل</th>
                <th>الحالة</th>
                <th>مؤشر التحويل</th>
            </tr>
        </thead>
        <tbody>
"""
        for lead in req.leads_data:
            html_content += f"""            <tr>
                <td>{lead.get('name', '')}</td>
                <td>{lead.get('company', '')}</td>
                <td>{lead.get('channel', '')}</td>
                <td>{lead.get('status', '')}</td>
                <td>{lead.get('conversion_score', 0)}%</td>
            </tr>\n"""

        html_content += """        </tbody>
    </table>
</body>
</html>"""

        return {
            "status": "success",
            "campaign_id": req.campaign_id,
            "campaign_name": req.campaign_name,
            "metrics": {
                "total_leads": total_leads,
                "average_conversion_score": round(avg_score, 2)
            },
            "html_report": html_content
        }


executive_report_exporter = ExecutiveReportExporter()
