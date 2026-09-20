from pprint import pprint

from solaredge.database.database import Database
from solaredge.sunspec.sunspec_reader import SunSpecReader

def main() -> None:
    with SunSpecReader() as reader, Database() as database:
        data = reader.read_inverter_measurements()
        database.add_measurement(data)
        pprint(data)

if __name__ == "__main__":
    main()
