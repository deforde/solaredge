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

## Run on the BBB

Install the project into a virtual environment on the BBB. The service files
assume the project is deployed at `/home/debian/solaredge`:

```bash
cd /home/debian/solaredge
python3 -m venv .venv
.venv/bin/python -m pip install .
sudo usermod -aG dialout debian
```

Copy the service files and enable both processes at boot:

```bash
sudo cp systemd/solaredge.service /etc/systemd/system/
sudo cp systemd/solaredge-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now solaredge.service solaredge-dashboard.service
```

Check their status and logs with:

```bash
systemctl status solaredge.service solaredge-dashboard.service
journalctl -u solaredge.service -f
journalctl -u solaredge-dashboard.service -f
```

The dashboard is available at `http://<BBB-IP>:5000`. If the serial device or
unit ID differs, edit the `Environment=` values in `solaredge.service` before
copying it, or update the installed unit and run `sudo systemctl daemon-reload`.