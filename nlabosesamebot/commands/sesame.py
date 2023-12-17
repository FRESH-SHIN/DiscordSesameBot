import os
import traceback
from typing import TYPE_CHECKING, Union
import asyncio
from pysesameos2.helper import CHProductModel
from pysesameos2.chsesame2 import CHSesame2
from pysesameos2.chsesamebot import CHSesameBot
from pysesameos2.helper import CHSesame2MechStatus, CHSesameBotMechStatus
import discord
from discord import app_commands, Message, Interaction
from bot import handler, tree, client
latest_interaction : Interaction= None
debug_mode : bool = True

async def send_message_to_channel(msg : str, silent: bool = False):
    channel = client.get_channel(int(os.getenv('DISCORD_CHANNEL')))
    print(msg)
    await channel.send(msg, silent=silent)

async def appendMessageToInteraction(interaction : Interaction, text : str):
    interaction_message = await interaction.original_response()
    message = await interaction_message.fetch()
    await interaction_message.reply(content=text, silent=True)

def on_sesame_statechanged(device: Union[CHSesame2, CHSesameBot]) -> None:
    mech_status = device.getMechStatus()
    device_status = device.getDeviceStatus()
    text = "=" * 10
    text +=f'\n'+("Device status is updated!")
    #text =f'\n'+("UUID: {}".format(device.getDeviceUUID()))
    #text =f'\n'+("Product Model: {}".format(device.productModel))
    text +=f'\n'+("Device status: {}".format(device_status))

    """
    Note that even if `getDeviceStatus` succeeds, `getMechStatus` may return `None`.

    The reason is that `DeviceStatus` is a state transition of the device,
    and it always exists, regardless of the connection status with the device.
    https://doc.candyhouse.co/ja/flow_charts#sesame-%E7%8A%B6%E6%85%8B%E9%81%B7%E7%A7%BB%E5%9B%B3

    `getMechStatus` can be retrieved after the connection to the device is
    successfully established.
    """
    if mech_status is not None:
        text +=f'\n'+("Battery: {}%".format(mech_status.getBatteryPercentage()))
        text +=f'\n'+("Battery: {:.2f}V".format(mech_status.getBatteryVoltage()))
        text +=f'\n'+("isInLockRange: {}".format(mech_status.isInLockRange()))
        text +=f'\n'+("isInUnlockRange: {}".format(mech_status.isInUnlockRange()))
        if device.productModel in [CHProductModel.SS2, CHProductModel.SS4]:
            if TYPE_CHECKING:
                assert isinstance(mech_status, CHSesame2MechStatus)
            text +=f'\n'+("Position: {}".format(mech_status.getPosition()))
        elif device.productModel == CHProductModel.SesameBot1:
            if TYPE_CHECKING:
                assert isinstance(mech_status, CHSesameBotMechStatus)
            text +=f'\n'+("Motor Status: {}".format(mech_status.getMotorStatus()))
    text +=f'\n'+("=" * 10)
    if debug_mode:
        event_loop = asyncio.get_event_loop()
        asyncio.ensure_future(appendMessageToInteraction(latest_interaction, text), loop=event_loop)
    else:
        event_loop = asyncio.get_event_loop()
        asyncio.ensure_future(send_message_to_channel("Device status: {}".format(device_status), silent=True), loop=event_loop)
    # await channel.send(text)

@tree.command(name="lock", description="Look the door.")
@app_commands.checks.has_role("ラボメン")
async def lock(interaction: discord.Interaction):
    """ドアを閉めます"""
    await interaction.response.send_message(f'Attempting to lock the door', silent=True)
    global latest_interaction 
    latest_interaction = interaction
    try:
        await handler.lock()
    except Exception as e:
        await send_message_to_channel(f'**Error** \n{type(e)}\n{e}\nStack Trace\n{traceback.format_exc()}',silent=True)


@tree.command(name="unlock", description="Unlook the door.")
@app_commands.checks.has_role("ラボメン")
async def unlock(interaction: discord.Interaction):
    """ドアを閉めます"""
    await interaction.response.send_message(f'Attempting to unlock the door', silent=True)
    global latest_interaction 
    latest_interaction = interaction
    try:
        await handler.unlock()
    except Exception as e:
        await send_message_to_channel(f'**Error** \n{type(e)}\n{e}\nStack Trace\n{traceback.format_exc()}',silent=True)

@tree.command(name="init", description="Initialize the bot.")
@app_commands.checks.has_role("ラボメン")
async def init(interaction: discord.Interaction):
    await interaction.response.send_message(f'Attempting to connect to the device...', silent=True)
    global latest_interaction 
    latest_interaction = interaction
    try:
        await handler.connect()
    except Exception as e:
        await send_message_to_channel(f'**Error** \n{type(e)}\n{e}\nStack Trace\n{traceback.format_exc()}',silent=True)

@tree.command(name="debug", description="Debug on/off")
@app_commands.checks.has_role("ラボメン")
@app_commands.describe(mode='on or off')
async def toggle_debug(interaction: discord.Interaction, mode : str):
    global debug_mode
    if mode.lower() == "on":
        debug_mode = True
    elif mode.lower() == "off":
        debug_mode = False
    await interaction.response.send_message(f'Debug mode: {str(debug_mode)}', silent=True)
