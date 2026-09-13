# SolarEdge

Small Python utilities for SolarEdge data.

## Development

Install the project and development tools with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Run the application:

```bash
uv run solaredge
```

The default connection is `/dev/ttyUSB0`, SolarEdge unit ID `1`, and `115200 8N1`.
Override these values when needed:

```bash
SOLAREDGE_PORT=/dev/ttyUSB1 SOLAREDGE_UNIT_ID=2 uv run solaredge
```

The example discovers SunSpec model 101 and prints AC power, current, voltage,
frequency, and lifetime energy. The inverter must have RS485 Modbus/SunSpec
enabled, and the adapter must be connected to the inverter's RS485 terminals.

Run checks:

```bash
uv run ruff check .
uv run ruff format --check .
```