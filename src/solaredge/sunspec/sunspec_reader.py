from time import time
import traceback

from pymodbus.client import ModbusSerialClient

SOLAREDGE_BAUDRATE = 115200
SOLAREDGE_PORT = "/dev/ttyUSB0"
SOLAREDGE_UNIT_ID = 1
SUNSPEC_BASE = 40000
SUNSPEC_INVERTER_MODEL = 101

class SunSpecReader:
    def __init__(self) -> None:
        self.__port = SOLAREDGE_PORT
        self.__unit_id = SOLAREDGE_UNIT_ID
        self.__baudrate = SOLAREDGE_BAUDRATE

    def __enter__(self) -> "SunSpecReader":
        self.__client = ModbusSerialClient(
            port=self.__port,
            baudrate=self.__baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=2,
        )

        if not self.__client.connect():
            raise SystemExit(f"Could not connect to SolarEdge inverter on {self.__port}")

        # SunSpec starts with the ASCII marker "SunS" (two 16-bit registers).
        signature = self.__client.read_holding_registers(
            address=SUNSPEC_BASE,
            count=2,
            device_id=self.__unit_id,
        )
        if signature.isError() or signature.registers != [0x5375, 0x6E53]:
            raise SystemExit("No SunSpec device found at the configured address")

        # Each model begins with a model ID and a register length.
        self.__model_address = SUNSPEC_BASE + 2
        while True:
            header = self.__client.read_holding_registers(
                address=self.__model_address,
                count=2,
                device_id=self.__unit_id,
            )
            if header.isError():
                raise SystemExit("Could not read the SunSpec model list")

            model_id, self.__model_length = header.registers
            if model_id == 0xFFFF:
                raise SystemExit("SunSpec inverter model 101 was not found")
            if model_id == SUNSPEC_INVERTER_MODEL:
                break
            self.__model_address += 2 + self.__model_length

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.__client.close()
        if exc_type is not None:
            print(f"An error occurred: {exc_val}")
            traceback.print_exception(exc_type, exc_val, exc_tb)
        return False 

    def read_inverter_measurements(self) -> dict:
            # Model 101 offsets are relative to the first register after its header.
            # This is the extended three-phase layout: phase fields precede the
            # shared scale factors for current, voltage, and power.
            values = self.__client.read_holding_registers(
                address=self.__model_address + 2,
                count=self.__model_length,
                device_id=self.__unit_id,
            )
            if values.isError():
                raise SystemExit("Could not read SunSpec inverter measurements")

            registers = values.registers
            try:
                # lifetime_energy = SunSpecReader.__unsigned32(registers[22], registers[23])
                data = {
                    "timestamp": int(time()),
                    "power": SunSpecReader.__scaled(SunSpecReader.__signed16(registers[12]), registers[13]),
                    "current": SunSpecReader.__scaled(registers[0], registers[4]),
                    "voltage": SunSpecReader.__scaled(registers[5], registers[8]),
                    "frequency": SunSpecReader.__scaled(registers[14], registers[15]),
                }
                return data
            except (IndexError, ValueError) as error:
                raw_registers = " ".join(f"{value:04x}" for value in registers)
                raise SystemExit(
                    f"Invalid SunSpec model 101 data: {error}. "
                    f"Model address={self.__model_address}, length={self.__model_length}; "
                    f"raw registers={raw_registers}"
                ) from error

    @staticmethod
    def __signed16(value: int) -> int:
        value &= 0xFFFF
        return value - 0x10000 if value & 0x8000 else value

    @staticmethod
    def __scaled(value: int, scale_factor: int) -> float:
        scale = SunSpecReader.__signed16(scale_factor)
        if not -100 <= scale <= 100:
            raise ValueError(f"invalid SunSpec scale factor {scale}")
        return value * (10**scale)

    @staticmethod
    def __unsigned32(high: int, low: int) -> int:
        return (high << 16) | low
