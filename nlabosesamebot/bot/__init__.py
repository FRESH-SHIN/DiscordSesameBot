import os
import discord
from discord import app_commands
from sesame.handler import SesameHandler

handler = SesameHandler()
MY_GUILD = discord.Object(id=int(os.getenv('DISCORD_GUILD')))  # replace with your guild id
handler = SesameHandler()

class Bot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.default()
client = Bot(intents=intents)
tree = client.tree

handler.initialize(publicKey=os.getenv('PUBLIC_KEY'),
                            secretKey=os.getenv('SECRET_KEY'),
                            ble_mac=os.getenv('BLE_MAC'),
                            ble_uuid=os.getenv('BLE_UUID'),
                            state_change_callback=commands.sesame.on_sesame_statechanged)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

client.run(os.getenv('DISCORD_TOKEN'))
channel = client.get_channel(os.getenv('DISCORD_CHANNEL'))
import commands