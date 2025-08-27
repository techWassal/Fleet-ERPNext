import frappe
import requests
import json

SUPABASE_URL = "https://ifhgdipxetfordemdlyw.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmaGdkaXB4ZXRmb3JkZW1kbHl3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzI0NTQzMiwiZXhwIjoyMDU4ODIxNDMyfQ.eXi20s2f8utoN6_q57Yqf5i0hzaJc6reWFtXM-VjvJ8"

def sync_gosi_worker_data_to_supabase():
    try:
        # Fetch records from ERPNext Doctype
        records = frappe.get_all(
            "GOSI Worker Data",
            fields=[
                "subscriber_name",
                "identity_number",
                "nationality",
                "gender",
                "date_of_birth",
                "occupation",
                "joining_date",
                "basic_salary",
                "housing",
                "commissions",
                "other_allowances",
                "total_salary",
                "contributable_salary",
                "status",
            ]
        )

        print(f"🔍 Found {len(records)} GOSI Worker Data records in ERPNext")

        if not records:
            print("⚠️ No records found to sync.")
            return

        # Prepare headers
        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_API_KEY}",
            "Content-Type": "application/json"
        }

        # Send to Supabase (insert in bulk)
        url = f"{SUPABASE_URL}/rest/v1/gosi_worker_data"

        # Debugging: print payload before sending
        print("📦 Payload to be sent:")
        print(json.dumps(records, indent=2, default=str))

        response = requests.post(url, headers=headers, data=json.dumps(records))

        # Debugging: print response details
        print(f"✅ Status Code: {response.status_code}")
        try:
            print("🔍 Supabase Response:", response.json())
        except Exception:
            print("🔍 Raw Supabase Response:", response.text)

    except Exception as e:
        print(f"❌ Error in sync_gosi_worker_data_to_supabase: {e}")

