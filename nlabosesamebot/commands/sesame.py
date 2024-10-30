import os
import traceback
import asyncio
from typing import TYPE_CHECKING, Union
from pysesameos2.helper import CHProductModel
from pysesameos2.chsesame2 import CHSesame2
from pysesameos2.chsesamebot import CHSesameBot
from pysesameos2.helper import CHSesame2MechStatus, CHSesameBotMechStatus
import discord
from discord import Interaction
from discord.ext import commands
from discord.ui import View
from bot import handler, client

doorlock_status = {"is_locked": True}
latest_interaction: Interaction = None
debug_mode: bool = True

def on_sesame_statechanged(device: Union[CHSesame2, CHSesameBot]) -> None:
    device_status = device.getDeviceStatus()
    print(device.getDeviceStatus())
    doorlock_status["is_locked"] = (device_status == "CHSesame2Status.Locked")

    status_text = f"Device status: {device_status}\n"
    if debug_mode:
        mech_status = device.getMechStatus()
        if mech_status is not None:
            status_text += f"Battery: {mech_status.getBatteryPercentage()}%\n"
            status_text += f"Battery Voltage: {mech_status.getBatteryVoltage():.2f}V\n"
            status_text += f"isInLockRange: {mech_status.isInLockRange()}\n"
            status_text += f"isInUnlockRange: {mech_status.isInUnlockRange()}\n"

    notification_channel_id = int(os.getenv('DISCORD_CHANNEL'))
    channel = client.get_channel(notification_channel_id)
    
    if channel:
        embed = discord.Embed(
            title="Device Status Update",
            description=status_text,
            color=discord.Color.blue()
        )
        event_loop = asyncio.get_event_loop()
        asyncio.ensure_future(channel.send(embed=embed), loop=event_loop)
    asyncio.ensure_future(update_lock_status_message(), loop=event_loop)

async def send_embed_notification(interaction: Interaction, action: str, color: discord.Color):
    notification_channel_id = int(os.getenv('DISCORD_CHANNEL'))
    channel = client.get_channel(notification_channel_id)
    
    if channel:
        action_text = "unlocked" if action == "🔓 Unlocked" else "locked"
        emoji = "🔓" if action == "🔓 Unlocked" else "🔒"
        
        embed = discord.Embed(
            description=f"{emoji} **{interaction.user.display_name} has {action_text} the door**",
            color=color
        )
        embed.set_author(name=f"{interaction.user.display_name} used {action_text.capitalize()}", icon_url=interaction.user.display_avatar.url)
        await channel.send(embed=embed)

async def send_status_embed(interaction: Interaction):
    device = handler.device
    mech_status = device.getMechStatus()
    device_status = device.getDeviceStatus()

    status_text = f"Device status: {device_status}\n"

    if debug_mode and mech_status is not None:
        status_text += f"Battery: {mech_status.getBatteryPercentage()}%\n"
        status_text += f"Battery Voltage: {mech_status.getBatteryVoltage():.2f}V\n"
        status_text += f"isInLockRange: {mech_status.isInLockRange()}\n"
        status_text += f"isInUnlockRange: {mech_status.isInUnlockRange()}\n"

        if device.productModel in [CHProductModel.SS2, CHProductModel.SS4]:
            if TYPE_CHECKING:
                assert isinstance(mech_status, CHSesame2MechStatus)
            status_text += f"Position: {mech_status.getPosition()}\n"
        elif device.productModel == CHProductModel.SesameBot1:
            if TYPE_CHECKING:
                assert isinstance(mech_status, CHSesameBotMechStatus)
            status_text += f"Motor Status: {mech_status.getMotorStatus()}\n"

    notification_channel_id = int(os.getenv('DISCORD_CHANNEL'))
    channel = client.get_channel(notification_channel_id)
    if channel:
        embed = discord.Embed(
            title="Device Status",
            description=status_text,
            color=discord.Color.blue()
        )
        await channel.send(embed=embed)

async def update_lock_status_message():
    global info_message
    button_channel_id = int(os.getenv('DISCORD_BUTTON_CHANNEL'))
    button_channel = client.get_channel(button_channel_id)

    if button_channel:
        lock_status = "🔒 **Locked**" if doorlock_status["is_locked"] else "🔓 **Unlocked**"
        debug_status = "ON" if debug_mode else "OFF"
        content = f"**Doorlock status:** {lock_status}\n**Debug mode:** {debug_status}"

        if info_message:
            try:
                await info_message.edit(content=content)
            except discord.errors.NotFound:
                info_message = await button_channel.send(content)
        else:
            info_message = await button_channel.send(content)

async def send_message_to_channel(message: str, channel_id: int, silent: bool = False):
    channel = client.get_channel(channel_id)
    if channel:
        await channel.send(content=message, silent=silent)

class SesameControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        lab_member_role = discord.utils.get(interaction.user.roles, name="ラボメン")
        if lab_member_role is None:
            await interaction.response.send_message("You do not have the 'ラボメン' role.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Unlock", style=discord.ButtonStyle.green, row=0)
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        global latest_interaction
        latest_interaction = interaction
        try:
            await handler.unlock()
            await send_embed_notification(interaction, "🔓 Unlocked", discord.Color.green())
            await update_lock_status_message()
        except Exception as e:
            notification_channel_id = int(os.getenv('DISCORD_CHANNEL'))
            await send_message_to_channel(
                f'## **Error** \n{type(e)}\n{e}\n### **Stack Trace**\n{traceback.format_exc()}',
                notification_channel_id,
                silent=True
            )
    
    @discord.ui.button(label="Lock", style=discord.ButtonStyle.red, row=0)
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        global latest_interaction
        latest_interaction = interaction
        try:
            await handler.lock()
            await send_embed_notification(interaction, "🔒 Locked", discord.Color.red())
            await update_lock_status_message() 
        except Exception as e:
            notification_channel_id = int(os.getenv('DISCORD_CHANNEL'))
            await send_message_to_channel(
                f'## **Error** \n{type(e)}\n{e}\n### **Stack Trace**\n{traceback.format_exc()}',
                notification_channel_id,
                silent=True
            )

    @discord.ui.button(label="Init", style=discord.ButtonStyle.gray, row=1)
    async def init_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        global latest_interaction
        latest_interaction = interaction
        try:
            await handler.connect()
            await interaction.followup.send("🔄 Device has been initialized.", ephemeral=True)
            await send_status_embed(interaction)
        except Exception as e:
            notification_channel_id = int(os.getenv('DISCORD_CHANNEL'))
            await send_message_to_channel(
                f'## **Error** \n{type(e)}\n{e}\n### **Stack Trace**\n{traceback.format_exc()}',
                notification_channel_id,
                silent=True
            )

    @discord.ui.button(label="Toggle Debug", style=discord.ButtonStyle.gray, row=1)
    async def toggle_debug_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global debug_mode
        debug_mode = not debug_mode
        status = "ON" if debug_mode else "OFF"
        await interaction.response.send_message(f"Debug mode: {status}", ephemeral=True)
        await update_lock_status_message()

@client.event
async def on_ready():
    global info_message

    print(f'Logged in as {client.user}!')

    button_channel_id = int(os.getenv('DISCORD_BUTTON_CHANNEL'))
    button_channel = client.get_channel(button_channel_id)
    if button_channel:
        view = SesameControlView()
        info_message = await button_channel.send(view=view)
        await update_lock_status_message()