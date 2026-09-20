from time import monotonic, sleep
from pprint import pprint

from solaredge.database.database import Database
from solaredge.sunspec.sunspec_reader import SunSpecReader

SAMPLE_PERIOD = 5

def main() -> None:
    with SunSpecReader() as reader, Database() as database:
        last_sample_timestamp = 0
        while True:
            now = monotonic()
            if now - last_sample_timestamp >= SAMPLE_PERIOD:
                data = reader.read_inverter_measurements()
                database.add_measurement(data)
                pprint(data)
                last_sample_timestamp = now
            sleep(1)

if __name__ == "__main__":
    main()
