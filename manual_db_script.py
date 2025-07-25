import os
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from datetime import datetime

# SQLite database URL
DATABASE_URL = "sqlite:///./credential.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

applications = [
    ("APP-002", "P54321", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. Emily White", "In-Progress", 75, "Bob Williams", "CAQH Integration", "California", "Dermatology", "456 Skin Ave, Suite 200, Beverly Hills, CA, 90210", "0987654321"),
    ("APP-003", "P67890", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. Michael Brown", "In-Progress", 50, "Charlie Davis", "Email Parsing", "New York", "Neurology", "789 Brain Blvd, Thinktown, NY, 10001", "1122334455"),
    ("APP-005", "P44556", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. David Wilson", "Needs Further Review", 90, "Unassigned", "Manual Entry", "Florida", "Orthopedics", "202 Bone Ln, Jointsville, FL, 33101", "1231231234"),
    ("APP-006", "P77889", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. Jessica Garcia", "Completed", 100, "Bob Williams", "CAQH Integration", "National", "Oncology", "303 Hope Dr, Cure City, WA, 98101", "4564564567"),
    ("APP-007", "P99999", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. Robert King", "Pending Review", 10, "Unassigned", "Manual Entry", "California", "Cardiology", "1 Heart Way, Loveland, CA, 90210", "9998887776"),
    ("APP-008", "P88888", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. Linda Martinez", "Pending Review", 10, "Unassigned", "Manual Entry", "New York", "Neurology", "2 Nerve St, Big Apple, NY, 10001", "8887776665"),
    ("APP-009", "P10101", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. Kevin Lee", "In-Progress", 60, "Charlie Davis", "Manual Entry", "California", "Dermatology", "101 Skin Ave, Beverly Hills, CA, 90210", "1010101010"),
    ("APP-010", "P20202", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. Karen Hall", "Pending Review", 20, "Unassigned", "Manual Entry", "Texas", "Pediatrics", "202 Child Way, Kidston, TX, 75001", "2020202020"),
    ("APP-011", "P30303", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. Steven Young", "In-Progress", 80, "Bob Williams", "CAQH Integration", "Florida", "Orthopedics", "303 Bone Ln, Jointsville, FL, 33101", "3030303030"),
    ("APP-012", "P40404", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. James Lee", "Needs Further Review", 95, "Alice Johnson", "Email Parsing", "New York", "Cardiology", "404 Heart Way, Loveland, NY, 10001", "4040404040"),
    ("APP-013", "P12345", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. John Smith", "Completed", 100, "Alice Johnson", "Manual Entry", "National", "Cardiology", "123 Health St, Suite 100, Medville, CA, 90210", "1234567890"),
    ("APP-014", "P11223", "410246d0-0e54-4700-9af7-d97107e22b37", "Dr. Sarah Miller", "Closed", 100, "Alice Johnson", "Availity API", "Texas", "Pediatrics", "101 Child Way, Kidston, TX, 75001", "6677889900"),
]

def bulk_insert():
    now = datetime.now()
    insert_sql = text("""
        INSERT OR IGNORE INTO applications (
            id, provider_id, form_id, name, status, progress, assignee,
            source, market, specialty, address, npi,
            create_dt, last_updt_dt
        ) VALUES (
            :id, :provider_id, :form_id, :name, :status, :progress, :assignee,
            :source, :market, :specialty, :address, :npi,
            :create_dt, :last_updt_dt
        )
    """)

    with engine.begin() as conn:
        for app in applications:
            conn.execute(insert_sql, {
                "id": app[0],
                "provider_id": app[1],
                "form_id": app[2],
                "name": app[3],
                "status": app[4],
                "progress": app[5],
                "assignee": app[6],
                "source": app[7],
                "market": app[8],
                "specialty": app[9],
                "address": app[10],
                "npi": app[11],
                "create_dt": now,
                "last_updt_dt": now,
            })
        print("✅ Applications inserted successfully.")

def run_manual_sql():
    print("Enter SQL to run (end with semicolon `;`):")
    user_sql = ""
    while not user_sql.strip().endswith(";"):
        user_sql += input("> ")

    with engine.connect() as conn:
        try:
            result = conn.execute(text(user_sql.strip().rstrip(";")))
            if result.returns_rows:
                for row in result.fetchall():
                    print(row)
            else:
                print("✅ Statement executed successfully.")
            conn.commit()
        except Exception as e:
            print(f"❌ Error: {e}")


def run_defined_sql():
    user_sql = "DELETE FROM form_file_uploads;"
    with engine.connect() as conn:
        try:
            result = conn.execute(text(user_sql.strip().rstrip(";")))
            if result.returns_rows:
                for row in result.fetchall():
                    print(row)
            else:
                print("✅ Statement executed successfully.")
            conn.commit()
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # run_defined_sql()

    print("Manual DB Runner")
    print("1. Insert demo application data")
    print("2. Run SQL manually")
    print("3. Run SQL defined")
    choice = input("Choose (1 2 3): ")

    if choice == "1":
        bulk_insert()
    elif choice == "2":
        run_manual_sql()
    elif choice == "3":
        run_defined_sql()
    else:
        print("Invalid choice.")


# C:/Users/sarfaraz.ansari/AppData/Local/Programs/Python/Python313/python.exe 
# uvicorn app.main:app --reload