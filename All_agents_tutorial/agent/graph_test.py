# # from agent.persistence.database import initialize_database
# from agent.services.investigation_service import execute_investigation
# from data.loader import DB_PATH, load_csv_data


# # initialize_database()


# if __name__ == "__main__":

#     from pathlib import Path

#     DATA_DIRECTORY = Path("data/ecommerce_demo")

#     conn, _ = load_csv_data(DATA_DIRECTORY)

#     result = execute_investigation(
#         objective="How many records are available in every table?",
#         analytics_connection=conn,
#     )
    
#     print(result["run_id"])
#     print(result["thread_id"])
#     print(result["status"])
#     print(result["final_report"])



from pathlib import Path
import sqlite3

from agent.config import setting
from agent.services.investigation_service import execute_investigation
from agent.gaurdrails.input_gaurd import validate_objective
from data.loader import load_csv_data


if __name__ == "__main__":
    conn, _ = load_csv_data(Path("data/ecommerce_demo"))

    objective = validate_objective(
        "Inspect the database and tell me how many records exist in each table.",
        max_characters=setting.max_objective_characters,
    )

    first_result = execute_investigation(
        objective=objective,
        analytics_connection=conn,
    )

    second_result = execute_investigation(
        objective="Using the previous investigation, tell me which table has the most records.",
        analytics_connection=conn,
        thread_id=first_result["thread_id"],
    )

    print("Thread ID:", first_result["thread_id"])
    print("First report:", first_result["final_report"])
    print("Second report:", second_result["final_report"])

    # with sqlite3.connect(setting.app_database_path) as connection:
    #     print(
    #         connection.execute(
    #             "SELECT thread_id, COUNT(*) "
    #             "FROM checkpoints "
    #             "GROUP BY thread_id"
    #         ).fetchall()
    #     )

    #     print(
    #         connection.execute(
    #             "SELECT thread_id, COUNT(*) "
    #             "FROM investigation_runs "
    #             "GROUP BY thread_id"
    #         ).fetchall()
    #     )
    print(
        "Conversation summary:",
        second_result["state"]["conversation_summary"],
    )

    print(
        "Summarized message count:",
        second_result["state"]["summarized_message_count"],
    )

    conn.close()