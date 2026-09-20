from datetime import datetime
from time import monotonic
import os
import sqlite3
import traceback

DATABASE_FILE = "/home/debian/data/solaredge.db"
MEASUREMENT_COLUMNS = ("timestamp", "power", "current", "voltage", "frequency")
DATABASE_BACKUP_PERIOD = 3600  # seconds
MAX_DATABASE_BACKUPS = 5

class Database:
    def __init__(self, database_file: str = DATABASE_FILE) -> None:
        self.__database_file = database_file
        database_directory = os.path.dirname(database_file)
        if database_directory:
            os.makedirs(database_directory, exist_ok=True)
        self.__last_backup_timestamp = 0

    def __enter__(self) -> "Database":
        self.__conn = sqlite3.connect(self.__database_file)
        self.__conn.execute("PRAGMA journal_mode = WAL")
        self.__conn.execute("PRAGMA synchronous = FULL")
        self.__conn.execute("PRAGMA busy_timeout = 5000")
        self.__conn.execute(
            """
            CREATE TABLE IF NOT EXISTS measurements (
                timestamp INTEGER NOT NULL,
                power REAL NOT NULL,
                current REAL NOT NULL,
                voltage REAL NOT NULL,
                frequency REAL NOT NULL
            )
            """
        )
        self.__conn.execute(
            """
            CREATE INDEX IF NOT EXISTS measurements_timestamp_idx
            ON measurements (timestamp)
            """
        )
        self.__conn.commit()
        return self

    def add_measurement(
        self,
        measurements: dict,
    ) -> None:
        missing_columns = [
            column for column in MEASUREMENT_COLUMNS if column not in measurements
        ]
        if missing_columns:
            raise ValueError(f"Missing measurement values: {', '.join(missing_columns)}")

        self.__conn.execute(
            """
            INSERT INTO measurements
                (timestamp, power, current, voltage, frequency)
            VALUES (?, ?, ?, ?, ?)
            """,
            [measurements[column] for column in MEASUREMENT_COLUMNS],
        )
        self.__conn.commit()

        self.__backup_database()

    def get_measurements(
        self,
        start_timestamp: int,
        end_timestamp: int,
    ) -> list[tuple]:
        query = """
            SELECT timestamp, power, current, voltage, frequency
            FROM measurements
            WHERE (? IS NULL OR timestamp >= ?)
              AND (? IS NULL OR timestamp <= ?)
            ORDER BY timestamp
        """
        return self.__conn.execute(
            query,
            [start_timestamp, start_timestamp, end_timestamp, end_timestamp],
        ).fetchall()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.__conn.close()
        if exc_type is not None:
            print(f"An error occurred: {exc_val}")
            traceback.print_exception(exc_type, exc_val, exc_tb)
        return False

    def __backup_database(self) -> None:
        now = monotonic()
        if now - self.__last_backup_timestamp >= DATABASE_BACKUP_PERIOD:
            backup_file = (
                f"{self.__database_file}_"
                f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.bak"
            )
            try:
                with sqlite3.connect(backup_file) as backup_conn:
                    self.__conn.backup(backup_conn)
                self.__last_backup_timestamp = now
                print(f"Database backup created at {backup_file}")
                self.__remove_old_backups()
            except Exception as e:
                print(f"Failed to create database backup: {e}")

    def __remove_old_backups(self) -> None:
        backup_prefix = f"{self.__database_file}_"
        backup_directory = os.path.dirname(self.__database_file) or "."
        backup_files = [
            entry.path
            for entry in os.scandir(backup_directory)
            if entry.is_file()
            and entry.path.startswith(backup_prefix)
            and entry.path.endswith(".bak")
        ]
        backup_files.sort(reverse=True)

        for old_backup in backup_files[MAX_DATABASE_BACKUPS:]:
            os.remove(old_backup)
            print(f"Old database backup deleted: {old_backup}")
