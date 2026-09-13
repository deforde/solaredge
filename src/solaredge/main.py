import os

from pymodbus.client import ModbusSerialClient

SUNSPEC_BASE = 40000
SUNSPEC_INVERTER_MODEL = 101


def _signed16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def _scaled(value: int, scale_factor: int) -> float:
    scale = _signed16(scale_factor)
    if not -100 <= scale <= 100:
        raise ValueError(f"invalid SunSpec scale factor {scale}")
    return value * (10**scale)


def _unsigned32(high: int, low: int) -> int:
    return (high << 16) | low


def main() -> None:
    port = os.getenv("SOLAREDGE_PORT", "/dev/ttyUSB0")
    unit_id = int(os.getenv("SOLAREDGE_UNIT_ID", "1"))

    client = ModbusSerialClient(
        port=port,
        baudrate=int(os.getenv("SOLAREDGE_BAUDRATE", "115200")),
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=2,
    )

    if not client.connect():
        raise SystemExit(f"Could not connect to SolarEdge inverter on {port}")

    try:
        # SunSpec starts with the ASCII marker "SunS" (two 16-bit registers).
        signature = client.read_holding_registers(
            address=SUNSPEC_BASE,
            count=2,
            device_id=unit_id,
        )
        if signature.isError() or signature.registers != [0x5375, 0x6E53]:
            raise SystemExit("No SunSpec device found at the configured address")

        # Each model begins with a model ID and a register length.
        model_address = SUNSPEC_BASE + 2
        while True:
            header = client.read_holding_registers(
                address=model_address,
                count=2,
                device_id=unit_id,
            )
            if header.isError():
                raise SystemExit("Could not read the SunSpec model list")

            model_id, model_length = header.registers
            if model_id == 0xFFFF:
                raise SystemExit("SunSpec inverter model 101 was not found")
            if model_id == SUNSPEC_INVERTER_MODEL:
                break
            model_address += 2 + model_length

        # Model 101 offsets are relative to the first register after its header.
        # This is the extended three-phase layout: phase fields precede the
        # shared scale factors for current, voltage, and power.
        values = client.read_holding_registers(
            address=model_address + 2,
            count=model_length,
            device_id=unit_id,
        )
        if values.isError():
            raise SystemExit("Could not read SunSpec inverter measurements")

        registers = values.registers
        try:
            print(f"AC power: {_scaled(_signed16(registers[12]), registers[13]):.0f} W")
            print(f"AC current: {_scaled(registers[0], registers[4]):.2f} A")
            print(f"AC voltage: {_scaled(registers[5], registers[8]):.1f} V")
            print(f"Frequency: {_scaled(registers[14], registers[15]):.2f} Hz")
            lifetime_energy = _unsigned32(registers[22], registers[23])
            print(f"Lifetime energy: {_scaled(lifetime_energy, registers[24]):.0f} Wh")
        except (IndexError, ValueError) as error:
            raw_registers = " ".join(f"{value:04x}" for value in registers)
            raise SystemExit(
                f"Invalid SunSpec model 101 data: {error}. "
                f"Model address={model_address}, length={model_length}; "
                f"raw registers={raw_registers}"
            ) from error
    finally:
        client.close()


if __name__ == "__main__":
    main()
