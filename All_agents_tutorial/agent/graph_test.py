from agent.persistence.database import initialize_database
from agent.services.investigation_service import execute_investigation
from data.loader import DB_PATH, load_csv_data


initialize_database()


if __name__ == "__main__":

    from pathlib import Path

    DATA_DIRECTORY = Path("data/ecommerce_demo")

    conn, _ = load_csv_data(DATA_DIRECTORY)

    result = execute_investigation(
        objective="How many records are available in every table?",
        analytics_connection=conn,
    )
    
    print(result["run_id"])
    print(result["thread_id"])
    print(result["status"])
    print(result["final_report"])



