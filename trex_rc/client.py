"""Async BLE client for the remote-control T-rex."""
from __future__ import annotations

import asyncio

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

from . import protocol


class TrexNotFound(Exception):
    pass


async def find_device(timeout: float = 10.0,
                      name_prefix: str = protocol.DEVICE_NAME_PREFIX) -> BLEDevice:
    """Scan for the toy and return the first matching device."""
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: (d.name or "").startswith(name_prefix),
        timeout=timeout,
    )
    if device is None:
        raise TrexNotFound(
            f"no device advertising a name starting with {name_prefix!r} found "
            f"within {timeout:.0f}s — is the toy on and in range?"
        )
    return device


class Trex:
    """Connect to the toy, unlock it, and send commands."""

    def __init__(self, device: BLEDevice):
        self._device = device
        self._client = BleakClient(device)

    async def __aenter__(self) -> "Trex":
        await self.connect()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.disconnect()

    @property
    def address(self) -> str:
        return self._device.address

    async def connect(self) -> None:
        await self._client.connect()
        # The toy drops every motion command until it receives the unlock packet, so
        # send it before anything else.
        await self.unlock()

    async def unlock(self) -> None:
        await self._write(protocol.UNLOCK_PACKET)
        # Give the firmware a moment to arm after the unlock before we drive it.
        await asyncio.sleep(0.1)

    async def disconnect(self) -> None:
        if self._client.is_connected:
            try:
                await self.send(protocol.stop())
            finally:
                await self._client.disconnect()

    async def _write(self, packet: bytes) -> None:
        await self._client.write_gatt_char(protocol.CMD_CHAR_UUID, packet, response=False)

    async def send(self, packet: bytes) -> None:
        """Send a prebuilt command packet (see protocol.build / the convenience fns)."""
        await self._write(packet)

    # High-level moves -------------------------------------------------------------
    async def forward(self, speed: int = protocol.DEFAULT_SPEED) -> None:
        await self.send(protocol.forward(speed))

    async def backward(self, speed: int = protocol.DEFAULT_SPEED) -> None:
        await self.send(protocol.backward(speed))

    async def left(self, speed: int = protocol.DEFAULT_SPEED) -> None:
        await self.send(protocol.turn_left(speed))

    async def right(self, speed: int = protocol.DEFAULT_SPEED) -> None:
        await self.send(protocol.turn_right(speed))

    async def stop(self) -> None:
        await self.send(protocol.stop())

    async def head_up(self) -> None:
        await self.send(protocol.head_up())

    async def head_down(self) -> None:
        await self.send(protocol.head_down())

    async def roar(self) -> None:
        await self.send(protocol.roar())
