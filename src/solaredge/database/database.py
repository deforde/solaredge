import os
import traceback

import duckdb

DATABASE_FILE = "/home/debian/data/solaredge.db"
MEASUREMENT_COLUMNS = ("timestamp", "power", "current", "voltage", "frequency")

class Database:
    def __init__(self, database_file: str = DATABASE_FILE) -> None:
        self.__database_file = database_file
        database_directory = os.path.dirname(database_file)
        if database_directory:
            os.makedirs(database_directory, exist_ok=True)

    def __enter__(self) -> "Database":
        self.__conn = duckdb.connect(self.__database_file)
        self.__conn.execute(
            """
            CREATE TABLE IF NOT EXISTS measurements (
                timestamp BIGINT NOT NULL,
                power DOUBLE NOT NULL,
                current DOUBLE NOT NULL,
                voltage DOUBLE NOT NULL,
                frequency DOUBLE NOT NULL
            )
            """
        )
        self.__conn.execute(
            """
            CREATE INDEX IF NOT EXISTS measurements_timestamp_idx
            ON measurements (timestamp)
            """
        )
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
