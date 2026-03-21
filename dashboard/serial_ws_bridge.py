#!/usr/bin/env python3
"""Serial <-> WebSocket bridge for VibraARM dashboard.

Telemetry direction:
  Pico B serial line (JSON) -> WebSocket clients

Config direction:
  WebSocket client JSON -> Pico B serial line

Expected serial line format from Pico B:
  {"type":"telemetry", ...}\n
Expected config format from UI:
  {"type":"config", ...}
"""

import argparse
import asyncio
import contextlib
import json
import signal
import sys
from typing import Optional, Set

try:
    import serial  # type: ignore
except Exception as exc:  # pragma: no cover
    serial = None
    SERIAL_IMPORT_ERROR = exc
else:
    SERIAL_IMPORT_ERROR = None

try:
    import websockets  # type: ignore
except Exception as exc:  # pragma: no cover
    websockets = None
    WS_IMPORT_ERROR = exc
else:
    WS_IMPORT_ERROR = None


class BridgeState:
    def __init__(self) -> None:
        self.clients: Set = set()
        self.serial_port: Optional[serial.Serial] = None
        self.stop_event = asyncio.Event()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VibraARM serial/websocket bridge")
    parser.add_argument("--serial-port", default="/dev/tty.usbmodem0000000000001", help="Serial device path")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    parser.add_argument("--host", default="127.0.0.1", help="WebSocket host")
    parser.add_argument("--port", type=int, default=8080, help="WebSocket port")
    parser.add_argument("--path", default="/telemetry", help="Expected WS path from UI")
    parser.add_argument("--no-serial", action="store_true", help="Run WS only (no serial forwarding)")
    return parser.parse_args()


def require_deps(no_serial: bool) -> None:
    if websockets is None:
        raise RuntimeError(
            "Missing dependency 'websockets'. Install with: pip install websockets"
        ) from WS_IMPORT_ERROR
    if not no_serial and serial is None:
        raise RuntimeError(
            "Missing dependency 'pyserial'. Install with: pip install pyserial"
        ) from SERIAL_IMPORT_ERROR


def log(msg: str) -> None:
    print(msg, flush=True)


async def broadcast(state: BridgeState, payload: dict) -> None:
    if not state.clients:
        return
    raw = json.dumps(payload)
    stale = []
    for ws in state.clients:
        try:
            await ws.send(raw)
        except Exception:
            stale.append(ws)
    for ws in stale:
        state.clients.discard(ws)


async def serial_reader_loop(state: BridgeState) -> None:
    if state.serial_port is None:
        return

    while not state.stop_event.is_set():
        try:
            line = await asyncio.to_thread(state.serial_port.readline)
        except Exception as exc:
            log(f"[serial] read error: {exc}")
            await asyncio.sleep(0.2)
            continue

        if not line:
            await asyncio.sleep(0.01)
            continue

        text = line.decode("utf-8", errors="ignore").strip()
        if not text:
            continue

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            log(f"[serial] non-json line: {text}")
            continue

        if "type" not in payload:
            payload["type"] = "telemetry"

        await broadcast(state, payload)


def serial_write_line(state: BridgeState, message: dict) -> None:
    if state.serial_port is None:
        return
    data = (json.dumps(message) + "\n").encode("utf-8")
    state.serial_port.write(data)
    state.serial_port.flush()


async def ws_handler(websocket, path: str, state: BridgeState, expected_path: str) -> None:
    if expected_path and path != expected_path:
        log(f"[ws] client connected on unexpected path: {path} (expected {expected_path})")

    state.clients.add(websocket)
    log(f"[ws] client connected ({len(state.clients)} total)")

    # Send immediate hello state.
    await websocket.send(json.dumps({"type": "bridge_status", "status": "connected"}))

    try:
        async for msg in websocket:
            try:
                payload = json.loads(msg)
            except json.JSONDecodeError:
                log(f"[ws] ignoring non-json: {msg}")
                continue

            if payload.get("type") == "config":
                if state.serial_port is not None:
                    try:
                        await asyncio.to_thread(serial_write_line, state, payload)
                        log(f"[ws->serial] config sent: {payload}")
                    except Exception as exc:
                        log(f"[ws->serial] write error: {exc}")
                else:
                    log(f"[ws] config received (serial disabled): {payload}")
            else:
                log(f"[ws] message received: {payload}")
    finally:
        state.clients.discard(websocket)
        log(f"[ws] client disconnected ({len(state.clients)} total)")


async def run_server(args: argparse.Namespace) -> None:
    state = BridgeState()

    if not args.no_serial:
        try:
            state.serial_port = serial.Serial(args.serial_port, args.baud, timeout=0.1)
            log(f"[serial] opened {args.serial_port} @ {args.baud}")
        except Exception as exc:
            raise RuntimeError(f"Failed to open serial port {args.serial_port}: {exc}") from exc
    else:
        log("[serial] disabled (--no-serial)")

    async def wrapped_handler(websocket, path):
        await ws_handler(websocket, path, state, args.path)

    server = await websockets.serve(wrapped_handler, args.host, args.port)
    log(f"[ws] listening on ws://{args.host}:{args.port}{args.path}")

    reader_task = asyncio.create_task(serial_reader_loop(state))

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, state.stop_event.set)
        except NotImplementedError:
            pass

    await state.stop_event.wait()

    reader_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await reader_task

    server.close()
    await server.wait_closed()

    if state.serial_port is not None:
        state.serial_port.close()
        log("[serial] closed")


async def amain(args: argparse.Namespace) -> int:
    require_deps(args.no_serial)
    try:
        await run_server(args)
    except RuntimeError as exc:
        log(f"[error] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    cli_args = parse_args()
    try:
        code = asyncio.run(amain(cli_args))
    except KeyboardInterrupt:
        code = 0
    sys.exit(code)
