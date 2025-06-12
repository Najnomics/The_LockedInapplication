import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict
from datetime import datetime
import os

# Setup credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(os.environ["GOOGLE_CREDENTIALS_PATH"], scope)
client = gspread.authorize(creds)

# Open the sheet
sheet = client.open(os.environ["GOOGLE_SHEET_NAME"]).sheet1  # or get_worksheet(0)

def insert_user(user_data: Dict):
    user_data['created_at'] = datetime.utcnow().isoformat()
    values = [user_data.get(key, "") for key in [
        "id", "name", "email", "phone", "goals", "reminder_times", "timezone", "created_at", "active"
    ]]
    values[4] = "|".join(user_data["goals"])  # Serialize list
    values[5] = "|".join(user_data["reminder_times"])
    sheet.append_row(values)

def get_user_by_phone(phone: str) -> Dict:
    records = sheet.get_all_records()
    for row in records:
        if row['phone'] == phone:
            row['goals'] = row['goals'].split('|')
            row['reminder_times'] = row['reminder_times'].split('|')
            return row
    return None

def update_user_reminder_times(phone: str, new_times: List[str]):
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        if row['phone'] == phone:
            cell = sheet.find(phone)
            sheet.update_cell(cell.row, 6, "|".join(new_times))  # 6 = reminder_times column
            return True
    return False
