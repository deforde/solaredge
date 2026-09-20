from pprint import pprint

from solaredge.sunspec.sunspec_reader import SunSpecReader

def main() -> None:
    with SunSpecReader() as reader:
        data = reader.read_inverter_measurements()
        pprint(data)

if __name__ == "__main__":
    main()
