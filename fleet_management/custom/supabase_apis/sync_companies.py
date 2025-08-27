import frappe
import requests
import json
from datetime import date, datetime

SUPABASE_URL = "https://ifhgdipxetfordemdlyw.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmaGdkaXB4ZXRmb3JkZW1kbHl3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzI0NTQzMiwiZXhwIjoyMDU4ODIxNDMyfQ.eXi20s2f8utoN6_q57Yqf5i0hzaJc6reWFtXM-VjvJ8"

SUPABASE_HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}

@frappe.whitelist()
def sync_companies_to_supabase():
    try:
        companies = frappe.get_all(
            "Company",
            fields=[
                "company_name",
                "default_currency",
                "country",
                "traccar_group_id",
                "abbr"
            ]
        )

        print(f"📌 Companies fetched from ERPNext: {len(companies)}")

        formatted_companies = []
        for comp in companies:
            mapped = {
                "company_name": comp.get("company_name"),
                "default_currency": comp.get("default_currency"),
                "country": comp.get("country"),
                "traccar_group_id": comp.get("traccar_group_id"),
                "abbr": comp.get("abbr")
            }
            formatted_companies.append(mapped)

        print("📦 Payload to send to Supabase:")
        print(json.dumps(formatted_companies, indent=2))

        url = f"{SUPABASE_URL}/rest/v1/companies"
        response = requests.post(url, headers=SUPABASE_HEADERS, data=json.dumps(formatted_companies))

        print("🔄 Supabase response:")
        print("Status:", response.status_code)
        print("Body:", response.text)

        if response.status_code in [200, 201]:
            frappe.msgprint(f"✅ Synced {len(formatted_companies)} companies to Supabase")
        else:
            frappe.msgprint(f"❌ Sync failed → {response.status_code}\n{response.text}")

    except Exception as e:
        print("🚨 Exception occurred:", str(e))
        frappe.msgprint(f"🚨 Exception: {str(e)}")

