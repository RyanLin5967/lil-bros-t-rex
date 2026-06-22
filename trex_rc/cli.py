"""Keyboard driving for the remote-control T-rex.

    python3 -m trex_rc            # scan, connect, drive
    python3 -m trex_rc --scan     # just list matching devices and exit

Controls:
    W / S       forward / backward
    A / D       turn left / right
    space       stop
    ↑ / ↓       head up / down
    R           roar
    + / -       speed up / down
    Q           quit
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from bleak import BleakScanner

from . import protocol
from .client import Trex, TrexNotFound, find_device

HELP = """\
  W/S forward/back   A/D left/right   space stop
  up/down head       R roar           +/- speed   Q quit"""


async def do_scan(timeout: float) -> None:
    print(f"scanning {timeout:.0f}s ...")
    devices = await BleakScanner.discover(timeout=timeout)
    matches = [d for d in devices if (d.name or "").startswith(protocol.DEVICE_NAME_PREFIX)]
    if not matches:
        print("no matching devices found.")
        return
    for d in matches:
        print(f"  {d.address}  {d.name}")


# --- terminal key reader (Unix) -----------------------------------------------------
class RawKeys:
    """Context manager yielding single keypresses from stdin without Enter.

    Arrow keys arrive as escape sequences; we map the two we use.
    """

    def __enter__(self):
        import termios
        import tty
        self._fd = sys.stdin.fileno()
        self._old = termios.tcgetattr(self._fd)
        tty.setcbreak(self._fd)
        return self

    def __exit__(self, *exc):
        import termios
        termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old)

    async def get(self) -> str:
        loop = asyncio.get_running_loop()
        ch = await loop.run_in_executor(None, sys.stdin.read, 1)
        if ch == "\x1b":  # escape — possible arrow sequence
            seq = await loop.run_in_executor(None, sys.stdin.read, 2)
            return {"[A": "UP", "[B": "DOWN", "[C": "RIGHT", "[D": "LEFT"}.get(seq, "ESC")
        return ch


async def drive(trex: Trex) -> None:
    speed = protocol.DEFAULT_SPEED
    print("connected to", trex.address)
    print(HELP)
    with RawKeys() as keys:
        while True:
            k = (await keys.get()).lower()
            if k == "q":
                break
            elif k == "w":
                await trex.forward(speed)
            elif k == "s":
                await trex.backward(speed)
            elif k == "a":
                await trex.left(speed)
            elif k == "d":
                await trex.right(speed)
            elif k == " ":
                await trex.stop()
            elif k == "up":
                await trex.head_up()
            elif k == "down":
                await trex.head_down()
            elif k == "r":
                await trex.roar()
            elif k in ("+", "="):
                speed = min(protocol.MAX_SPEED, speed + 0x20)
                print("speed", speed)
            elif k == "-":
                speed = max(0x20, speed - 0x20)
                print("speed", speed)


async def main_async(args) -> int:
    if args.scan:
        await do_scan(args.timeout)
        return 0
    try:
        device = await find_device(timeout=args.timeout)
    except TrexNotFound as e:
        print(e, file=sys.stderr)
        return 1
    async with Trex(device) as trex:
        await drive(trex)
    print("stopped.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="trex_rc", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scan", action="store_true", help="list matching devices and exit")
    ap.add_argument("--timeout", type=float, default=10.0, help="scan timeout seconds")
    args = ap.parse_args()
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
