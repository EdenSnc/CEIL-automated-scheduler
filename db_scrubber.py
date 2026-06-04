import sqlite3
import json
import os

def database_purge_routine():
    db_name = "ceil_scheduler.db"
    base_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    target_path = os.path.join(base_dir, db_name)

    if not os.path.exists(target_path):
        print(f"❌ Database execution target missing at: {target_path}")
        return

    try:
        conn = sqlite3.connect(target_path)
        cursor = conn.cursor()

        # 1. Clean Group Collection States
        cursor.execute("SELECT value FROM application_state WHERE key = 'groups';")
        group_row = cursor.fetchone()
        if group_row and group_row[0]:
            groups_list = json.loads(group_row[0])
            for group in groups_list:
                group.pop("allowed_days", None)
            cursor.execute(
                "INSERT INTO application_state (key, value) VALUES ('groups', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value;",
                (json.dumps(groups_list, ensure_ascii=False),)
            )
            print(f"✔ Purged 'allowed_days' fields from {len(groups_list)} student cohort vectors.")

        # 2. Clean Teacher Profile States
        cursor.execute("SELECT value FROM application_state WHERE key = 'teachers';")
        teacher_row = cursor.fetchone()
        if teacher_row and teacher_row[0]:
            teachers_list = json.loads(teacher_row[0])
            for teacher in teachers_list:
                teacher.pop("allowed_days", None)
            cursor.execute(
                "INSERT INTO application_state (key, value) VALUES ('teachers', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value;",
                (json.dumps(teachers_list, ensure_ascii=False),)
            )
            print(f"✔ Purged 'allowed_days' fields from {len(teachers_list)} instructor configuration models.")

        conn.commit()
        conn.close()
        print("🎉 SQLite application state fields fully unchained!")

    except Exception as exc:
        print(f"💥 Migration pipeline dropped execution: {exc}")

if __name__ == "__main__":
    database_purge_routine()