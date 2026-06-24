"""BLE protocol for the remote-control T-rex.

The toy exposes a custom GATT service with a single write characteristic for commands
and a notify characteristic for status.

Packet format (write characteristic):

    [ 0x55, 0xAA, CMD, ARG, CHK ]

    0x55 0xAA  fixed header
    CMD        command byte (see Cmd)
    ARG        command argument (speed 0-255, angle, etc.)
    CHK        checksum = (CMD + ARG) & 0xFF
"""
from __future__ import annotations

from enum import IntEnum

# --- GATT ---------------------------------------------------------------------------
# Custom 128-bit service/characteristics the toy advertises.
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
CMD_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"     # write
STATUS_CHAR_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"  # notify

# Name the toy advertises (prefix match; firmware revisions append a suffix).
DEVICE_NAME_PREFIX = "Robo-Rex"

# --- Unlock -------------------------------------------------------------------------
# The decompiled command set alone doesn't work: the toy ignores every motion command.
# Comparing a BLE capture from a working client against ours, the only difference is one
# extra packet the working client writes immediately after connecting — an unlock/auth
# step the toy requires before it will accept commands. This is that packet.
UNLOCK_PACKET = bytes([0x55, 0xAA, 0xF1, 0x6B, 0x5C])


class Cmd(IntEnum):
    STOP = 0x00
    FORWARD = 0x01
    BACKWARD = 0x02
    TURN_LEFT = 0x03
    TURN_RIGHT = 0x04
    HEAD_UP = 0x10
    HEAD_DOWN = 0x11
    ROAR = 0x20


DEFAULT_SPEED = 0x80  # mid speed
MAX_SPEED = 0xFF


def checksum(cmd: int, arg: int) -> int:
    return (cmd + arg) & 0xFF


def build(cmd: int, arg: int = 0) -> bytes:
    """Build a framed command packet."""
    cmd &= 0xFF
    arg &= 0xFF
    return bytes([0x55, 0xAA, cmd, arg, checksum(cmd, arg)])


# Convenience builders ---------------------------------------------------------------
def stop() -> bytes:
    return build(Cmd.STOP)


def forward(speed: int = DEFAULT_SPEED) -> bytes:
    return build(Cmd.FORWARD, speed)


def backward(speed: int = DEFAULT_SPEED) -> bytes:
    return build(Cmd.BACKWARD, speed)


def turn_left(speed: int = DEFAULT_SPEED) -> bytes:
    return build(Cmd.TURN_LEFT, speed)


def turn_right(speed: int = DEFAULT_SPEED) -> bytes:
    return build(Cmd.TURN_RIGHT, speed)


def head_up() -> bytes:
    return build(Cmd.HEAD_UP)


def head_down() -> bytes:
    return build(Cmd.HEAD_DOWN)


def roar() -> bytes:
    return build(Cmd.ROAR)
