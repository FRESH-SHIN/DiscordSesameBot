import time
import asyncio
import logging
import platform
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Union, Callable

from pysesameos2.ble import CHBleManager
from pysesameos2.device import CHDeviceKey
from pysesameos2.helper import CHProductModel

from pysesameos2.chsesame2 import CHSesame2, CHSesame2Status
from pysesameos2.chsesamebot import CHSesameBot
from pysesameos2.helper import CHSesame2MechStatus, CHSesameBotMechStatus

class SesameHandler:
    public_key : str = ""
    secret_key : str = ""
    ble_info : object = None
    device : CHSesame2 | CHSesameBot = None
    state_change_callback = None
    def initialize(self, publicKey: str, secretKey: str, ble_mac: str, ble_uuid: str, state_change_callback) -> None:
        self.public_key = publicKey
        self.private_key = secretKey
        self.ble_info = (
            ble_mac
            if platform.system() != "Darwin"
            else ble_uuid
        )
        self.state_change_callback = state_change_callback
    async def connect(self):
        scan_duration = 20
        if not self.device is None:
            await self.device.disconnect()
        self.device = await CHBleManager().scan_by_address(
            ble_device_identifier=self.ble_info, scan_duration=scan_duration
        )
        your_key = CHDeviceKey()
        your_key.setSecretKey(self.private_key)
        your_key.setSesame2PublicKey(self.public_key)
        self.device.setKey(your_key)
        self.device.setDeviceStatusCallback(self.state_change_callback)
        await self.device.connect()
        await self.device.wait_for_login()
    async def unlock(self):
        logging.debug("opening")
        if self.device is None:
            await self.connect()
        await self.device.unlock(history_tag="My Script")

    async def lock(self):
        logging.debug("closing")
        if self.device is None:
            await self.connect()
        await self.device.lock(history_tag="My Script")
    