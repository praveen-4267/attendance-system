"""
4_export_report.py
STEP 4 (optional) of the workflow.

Exports attendance records to a CSV file so a teacher/admin can
open it in Excel. Prompts for a date range.
"""

import csv
from datetime import datetime
from database import get_connection

REPORTS_DIR = "reports"


def export(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.roll_no, s.name, s.class_name, a.date, a.time, a.status
        FROM attendance a
        JOIN students s ON s.student_id = a.student_id
        WHERE a.date BETWEEN ? AND ?
        ORDER BY a.date, s.roll_no
    """, (start_date, end_date))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No attendance records found for that date range.")
        return

    filename = f"{REPORTS_DIR}/attendance_{start_date}_to_{end_date}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Roll No", "Name", "Class", "Date", "Time", "Status"])
        writer.writerows(rows)

    print(f"Report exported: {filename} ({len(rows)} records)")


def main():
    print("=== Export Attendance Report ===")
    start_date = input("Start date (YYYY-MM-DD): ").strip()
    end_date = input("End date (YYYY-MM-DD): ").strip()

    for d in (start_date, end_date):
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")
            return

    export(start_date, end_date)


if __name__ == "__main__":
    main()
