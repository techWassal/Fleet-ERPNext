import pandas as pd
import frappe
from hijridate import Hijri
from datetime import datetime

def safe_log_error(title, row):
    MAX_LENGTH = 140
    msg = f"Failed to insert/update row: {row}"
    if len(msg) > MAX_LENGTH:
        msg = msg[:MAX_LENGTH - 3] + "..."
    frappe.log_error(msg, title)

def convert_hijri_to_gregorian(hijri_date):
    try:
        if not hijri_date or pd.isna(hijri_date):
            return None

        if isinstance(hijri_date, str):
            hijri_date = hijri_date.strip()
            if "-" in hijri_date:
                parts = hijri_date.split("-")
            elif "/" in hijri_date:
                parts = hijri_date.split("/")
            else:
                return None

            if len(parts) != 3:
                return None

            try:
                y, m, d = map(int, parts)
            except ValueError:
                d, m, y = map(int, parts)

        elif isinstance(hijri_date, datetime):
            return hijri_date.date()

        else:
            return None

        g_date = Hijri(y, m, d).to_gregorian()
        return datetime(g_date.year, g_date.month, g_date.day).date()

    except Exception as e:
        return None

@frappe.whitelist()
def import_vehicle_data(file_url):
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    file_path = frappe.utils.get_files_path(file_doc.file_name, is_private=file_doc.is_private)

    df_raw = pd.read_excel(file_path, header=None)

    header_row_idx = None
    for idx, row in df_raw.iterrows():
        if "Plate Number" in row.values and "Chassis Number" in row.values:
            header_row_idx = idx
            break

    if header_row_idx is None:
        frappe.throw("Header row not found. Please upload a valid vehicle file.")

    df = pd.read_excel(file_path, header=header_row_idx)

    df = df.rename(columns={
        "Plate Number": "plate_number",
        "Plate Type": "plate_type",
        "Branch Name": "branch_name",
        "Vehicle Maker": "vehicle_maker",
        "Vehicle Model": "vehicle_model",
        "Model Year": "model_year",
        "Sequence Number": "sequence_number",
        "Chassis Number": "chassis_number",
        "Major Color": "major_color",
        "vehicle Status": "vehicle_status",
        "Ownership Date": "ownership_date",
        "License Expiry Date": "license_expiry_date",
        "Inspection Expiry Date": "inspection_expiry_date",
        "Actual Driver Id": "actual_driver_id",
        "Actual Driver Name": "actual_driver_name",
        "MVPI Status": "mvpi_status",
        "Insurance Status": "insurance_status",
        "Restriction Status": "restriction_status",
        "Istemarah issue Date": "istemarah_issue_date",
        "Vehicle Status": "vehicle_status2",
        "Body Type": "body_type"
    })

    df = df.replace("-", None)
    df = df.applymap(lambda x: None if pd.isna(x) or str(x).strip() == "" else x)

    hijri_date_fields = ["ownership_date", "license_expiry_date", "inspection_expiry_date", "istemarah_issue_date"]
    for field in hijri_date_fields:
        if field in df.columns:
            df[field] = df[field].apply(convert_hijri_to_gregorian)

    skipped_rows = []

    for row in df.to_dict(orient="records"):
        plate_number = row.get("plate_number")
        sequence_number = row.get("sequence_number")

        if not plate_number and not sequence_number:
            skipped_rows.append(row)
            continue

        existing_doc = None

        if plate_number:
            existing_doc = frappe.db.get("Vehicle Data", {"plate_number": plate_number})
        if not existing_doc and sequence_number:
            existing_doc = frappe.db.get("Vehicle Data", {"sequence_number": sequence_number})

        try:
            if existing_doc:
                doc = frappe.get_doc("Vehicle Data", existing_doc.name)
                updated = False

                for key, value in row.items():
                    if doc.get(key) != value:
                        doc.set(key, value)
                        updated = True

                if updated:
                    doc.save(ignore_permissions=True)
            else:
                doc = frappe.get_doc({"doctype": "Vehicle Data", **row})
                doc.insert(ignore_permissions=True)

        except Exception as e:
            safe_log_error("Vehicle Data Import Error", row)

    if skipped_rows:
        frappe.log_error(f"{len(skipped_rows)} row(s) skipped due to missing Plate Number and Sequence Number.", "Vehicle Import Skipped Rows")

    return "✅ Vehicle Data Imported and Updated Successfully!"














import frappe
from frappe.custom.doctype.custom_field.custom_field import CustomField

@frappe.whitelist()
def transfer_to_vehicle():
    create_missing_vehicle_fields()

    vehicle_data_list = frappe.get_all("Vehicle Data", fields=["*"])
    created = 0
    updated = 0
    skipped = []

    for data in vehicle_data_list:
        plate_number = data.get("plate_number")
        sequence_number = data.get("sequence_number")
        make = data.get("vehicle_maker")
        model = data.get("vehicle_model")

        if not plate_number and not sequence_number:
            skipped.append(f"- Row: {data.get('name')} skipped: missing plate number & sequence number")
            continue

        filters = {}
        if plate_number:
            filters["license_plate"] = plate_number
        elif sequence_number:
            filters["sequence_number"] = sequence_number

        existing_vehicle = frappe.get_list("Vehicle", filters=filters, fields=["name"], limit=1)
        if existing_vehicle:
            # Update existing vehicle
            vehicle = frappe.get_doc("Vehicle", existing_vehicle[0].name)
            has_changed = False

            def set_if_changed(field, value):
                nonlocal has_changed
                if getattr(vehicle, field, None) != value:
                    setattr(vehicle, field, value)
                    has_changed = True

            # Required & common fields
            set_if_changed("license_plate", plate_number)
            set_if_changed("make", make)
            set_if_changed("model", model)
            set_if_changed("vehicle_model", model)
            set_if_changed("vehicle_maker", make)
            set_if_changed("last_odometer", data.get("last_odometer") or 0)
            set_if_changed("uom", data.get("uom") or "Kilometer")
            set_if_changed("fuel_type", data.get("fuel_type") or "Petrol")
            set_if_changed("color", data.get("major_color"))
            set_if_changed("wheels", data.get("wheels") or 0)
            set_if_changed("doors", data.get("doors") or 0)
            set_if_changed("chassis_no", data.get("chassis_number"))
            set_if_changed("chassis_number", data.get("chassis_number"))
            set_if_changed("engine_no", data.get("engine_no"))
            set_if_changed("seating_capacity", data.get("seating_capacity"))
            set_if_changed("owner_name", data.get("owner_name"))
            set_if_changed("acquisition_date", data.get("acquisition_date"))
            set_if_changed("vehicle_value", data.get("vehicle_value") or 0.0)
            set_if_changed("location", data.get("location"))
            set_if_changed("employee", data.get("employee"))
            set_if_changed("insurance_company", data.get("insurance_company"))
            set_if_changed("policy_no", data.get("policy_no"))
            set_if_changed("start_date", data.get("insurance_start_date"))
            set_if_changed("end_date", data.get("insurance_end_date"))
            set_if_changed("last_carbon_check", data.get("last_carbon_check"))
            set_if_changed("sequence_date", data.get("sequence_date"))
            set_if_changed("license_expiry_date", data.get("license_expiry_date"))
            set_if_changed("license_display_date", data.get("license_display_date"))

            # Custom fields
            set_if_changed("actual_driver_id", data.get("actual_driver_id"))
            set_if_changed("actual_driver_name", data.get("actual_driver_name"))
            set_if_changed("mvpi_status", data.get("mvpi_status"))
            set_if_changed("insurance_status", data.get("insurance_status"))
            set_if_changed("restriction_status", data.get("restriction_status"))
            set_if_changed("istemarah_issue_date", data.get("istemarah_issue_date"))
            set_if_changed("vehicle_status", data.get("vehicle_status"))
            set_if_changed("body_type", data.get("body_type"))
            set_if_changed("inspection_expiry_date", data.get("inspection_expiry_date"))
            set_if_changed("ownership_date", data.get("ownership_date"))
            set_if_changed("model_year", data.get("model_year"))
            set_if_changed("sequence_number", sequence_number)

            if has_changed:
                vehicle.save(ignore_permissions=True)
                updated += 1
            else:
                skipped.append(f"- Row: {plate_number or sequence_number}, No changes")

        else:
            # Create new vehicle
            vehicle = frappe.new_doc("Vehicle")
            vehicle.license_plate = plate_number
            vehicle.make = make
            vehicle.model = model
            vehicle.vehicle_model = model
            vehicle.vehicle_maker = make
            vehicle.last_odometer = data.get("last_odometer") or 0
            vehicle.uom = data.get("uom") or "Kilometer"
            vehicle.fuel_type = data.get("fuel_type") or "Petrol"
            vehicle.color = data.get("major_color")
            vehicle.wheels = data.get("wheels") or 0
            vehicle.doors = data.get("doors") or 0
            vehicle.chassis_no = data.get("chassis_number")
            vehicle.chassis_number = data.get("chassis_number")
            vehicle.engine_no = data.get("engine_no")
            vehicle.seating_capacity = data.get("seating_capacity")
            vehicle.owner_name = data.get("owner_name")
            vehicle.acquisition_date = data.get("acquisition_date")
            vehicle.vehicle_value = data.get("vehicle_value") or 0.0
            vehicle.location = data.get("location")
            vehicle.employee = data.get("employee")
            vehicle.insurance_company = data.get("insurance_company")
            vehicle.policy_no = data.get("policy_no")
            vehicle.start_date = data.get("insurance_start_date")
            vehicle.end_date = data.get("insurance_end_date")
            vehicle.last_carbon_check = data.get("last_carbon_check")
            vehicle.sequence_date = data.get("sequence_date")
            vehicle.license_expiry_date = data.get("license_expiry_date")
            vehicle.license_display_date = data.get("license_display_date")
            vehicle.actual_driver_id = data.get("actual_driver_id")
            vehicle.actual_driver_name = data.get("actual_driver_name")
            vehicle.mvpi_status = data.get("mvpi_status")
            vehicle.insurance_status = data.get("insurance_status")
            vehicle.restriction_status = data.get("restriction_status")
            vehicle.istemarah_issue_date = data.get("istemarah_issue_date")
            vehicle.vehicle_status = data.get("vehicle_status")
            vehicle.body_type = data.get("body_type")
            vehicle.inspection_expiry_date = data.get("inspection_expiry_date")
            vehicle.ownership_date = data.get("ownership_date")
            vehicle.model_year = data.get("model_year")
            vehicle.sequence_number = sequence_number

            vehicle.insert(ignore_permissions=True)
            created += 1

    return f"✅ Created: {created}, 🔄 Updated: {updated}, ❌ Skipped: {len(skipped)}\n" + "\n".join(skipped)



















def create_missing_vehicle_fields():
    doctype = "Vehicle"
    fields_to_add = [
        ("actual_driver_id", "Data", "Actual Driver ID"),
        ("actual_driver_name", "Data", "Actual Driver Name"),
        ("mvpi_status", "Data", "MVPI Status"),
        ("insurance_status", "Data", "Insurance Status"),
        ("restriction_status", "Data", "Restriction Status"),
        ("istemarah_issue_date", "Date", "Istemarah Issue Date"),
        ("__break1", "Column Break", "Column Break"),
        ("vehicle_status", "Data", "Vehicle Status"),
        ("body_type", "Data", "Body Type"),
        ("inspection_expiry_date", "Date", "Inspection Expiry Date"),
        ("license_expiry_date", "Datetime", "License Expiry Date"),
        ("ownership_date", "Date", "Ownership Date"),
        ("model_year", "Int", "Model Year"),
        ("sequence_number", "Data", "Sequence Number"),
        ("__break2", "Section Break", "Additional Info"),
    ]

    for fieldname, fieldtype, label in fields_to_add:
        if not fieldname.startswith("__"):
            safe_create_custom_field(doctype, fieldname, fieldtype, label=label)
        else:
            safe_create_custom_field(doctype, fieldname, fieldtype, label=label, insert_after="license_plate")


def safe_create_custom_field(doctype, fieldname, fieldtype, **kwargs):
    custom_field_name = f"{doctype}-{fieldname}"
    existing = frappe.db.get_value("Custom Field", custom_field_name, ["name", "fieldtype"])

    if existing:
        existing_name, existing_type = existing
        if existing_type != fieldtype:
            frappe.log_error(f"Field '{fieldname}' has type '{existing_type}', cannot convert to '{fieldtype}'.", "Fieldtype Mismatch")
        return

    field = frappe.new_doc("Custom Field")
    field.dt = doctype
    field.fieldname = fieldname
    field.fieldtype = fieldtype
    field.label = kwargs.get("label", fieldname.replace("_", " ").title())
    field.insert_after = kwargs.get("insert_after")
    field.insert(ignore_permissions=True)















