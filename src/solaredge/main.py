from time import time, sleep
from pprint import pprint

from solaredge.database.database import Database
from solaredge.sunspec.sunspec_reader import SunSpecReader

SAMPLE_PERIOD = 30 * 60  # seconds

def main() -> None:
    with SunSpecReader() as reader, Database() as database:
        now = time()
        next_sample_timestamp = (int(now) // SAMPLE_PERIOD + 1) * SAMPLE_PERIOD
        averages = {}

        while True:
            data = reader.read_inverter_measurements()
            for k, v in data.items():
                if k != "timestamp":
                    if k in averages:
                        cnt = averages[k]["cnt"]
                        avg = averages[k]["avg"]
                        cnt += 1
                        avg = avg + (v - avg) / cnt
                        averages[k]["cnt"] = cnt
                        averages[k]["avg"] = avg
                    else:
                        averages[k] = {
                            "avg": v,
                            "cnt": 1
                        }

            now = time()
            if now >= next_sample_timestamp:
                data = {k: v["avg"] for k, v in averages.items()}
                data["timestamp"] = next_sample_timestamp
                database.add_measurement(data)
                averages = {}
                pprint(data)
                while next_sample_timestamp <= now:
                    next_sample_timestamp += SAMPLE_PERIOD

            sleep(10)

if __name__ == "__main__":
    main()
