from sqlalchemy import create_engine
import urllib.parse

def db_connection():
    # 🔁 Replace these with your actual MySQL credentials
    username = "root"
    password = urllib.parse.quote_plus("Farhan@123")  # Encoded password
    host = "localhost"
    database = "PhonePe_Transaction"

    connection_string = f"mysql+pymysql://{username}:{password}@{host}/{database}"
    engine = create_engine(connection_string)
    return engine
