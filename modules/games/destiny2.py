import discord
from discord import app_commands
import requests
from datetime import datetime, timedelta
import asyncio
import logging
from config import config


class Destiny2:
    def __init__(self, bot):
        self.bot = bot
        self.api_key = config['BUNGIE_API_KEY']
        self.logger = logging.getLogger('Destiny2')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='destiny2.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.logger.addHandler(handler)

    async def fetch_item_details(self, item_hash):
        headers = {
            "X-API-Key": self.api_key
        }
        url = f"https://www.bungie.net/Platform/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}/"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            item_data = response.json()
            return item_data['Response']
        else:
            self.logger.error(f'Error fetching item details for {item_hash}: {response.status_code} - {response.text}')
            return None

    async def fetch_vendors(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Defer the interaction response

        headers = {
            "X-API-Key": self.api_key
        }
        url = "https://www.bungie.net/Platform/Destiny2/Vendors/"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self.logger.debug(f'Vendors data: {data}')
            try:
                vendors_info = data['Response']['vendors']
                embeds = []
                for vendor_hash, vendor_data in vendors_info.items():
                    vendor_name = vendor_data['vendorName']
                    vendor_icon = vendor_data['vendorIcon']
                    embed = discord.Embed(title=f"{vendor_name}'s Inventory", color=discord.Color.blue())
                    embed.set_thumbnail(url=f"https://www.bungie.net{vendor_icon}")
                    field_count = 0
                    for item in vendor_data['items']:
                        if field_count >= 25:
                            embeds.append(embed)
                            embed = discord.Embed(title=f"{vendor_name}'s Inventory (cont.)", color=discord.Color.blue())
                            embed.set_thumbnail(url=f"https://www.bungie.net{vendor_icon}")
                            field_count = 0
                        item_details = await self.fetch_item_details(item['itemHash'])
                        if item_details:
                            item_name = item_details['displayProperties']['name']
                            item_icon = item_details['displayProperties']['icon']
                            item_icon_url = f"https://www.bungie.net{item_icon}"
                            embed.add_field(
                                name=item_name,
                                value=f"Quantity: {item['quantity']}\n[Icon]({item_icon_url})",
                                inline=False
                            )
                            field_count += 1
                    embeds.append(embed)
                for embed in embeds:
                    await interaction.followup.send(embed=embed)
            except KeyError as e:
                self.logger.error(f'Error processing vendors data: {e}')
                await interaction.followup.send("Error processing vendor data.")
        else:
            self.logger.error(f'Error fetching vendors data: {response.status_code} - {response.text}')
            await interaction.followup.send("Error fetching vendor data.")

    async def fetch_xur(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Defer the interaction response

        headers = {
            "X-API-Key": self.api_key
        }
        url = "https://www.bungie.net/Platform/Destiny2/Vendors/?components=402"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self.logger.debug(f'Xur data: {data}')
            try:
                xur_info = data['Response']['sales']['data']['2190858386']
                embed = discord.Embed(title="Xur's Inventory", color=discord.Color.purple())
                embed.set_thumbnail(url="https://www.bungie.net/img/misc/xur.png")
                field_count = 0
                for item in xur_info['saleItems'].values():
                    if field_count >= 25:
                        await interaction.followup.send(embed=embed)
                        embed = discord.Embed(title="Xur's Inventory (cont.)", color=discord.Color.purple())
                        embed.set_thumbnail(url="https://www.bungie.net/img/misc/xur.png")
                        field_count = 0
                    item_details = await self.fetch_item_details(item['itemHash'])
                    if item_details:
                        item_name = item_details['displayProperties']['name']
                        item_icon = item_details['displayProperties']['icon']
                        item_icon_url = f"https://www.bungie.net{item_icon}"
                        embed.add_field(
                            name=item_name,
                            value=f"Quantity: {item['quantity']}\n[Icon]({item_icon_url})",
                            inline=False
                        )
                        field_count += 1
                await interaction.followup.send(embed=embed)
            except KeyError as e:
                self.logger.error(f'Error processing Xur data: {e}')
                await interaction.followup.send("Error processing Xur data.")
        else:
            self.logger.error(f'Error fetching Xur data: {response.status_code} - {response.text}')
            await interaction.followup.send("Error fetching Xur data.")

    def setup(self, tree):
        @app_commands.command(name='fetch_vendors', description='Fetch the current vendors')
        async def fetch_vendors_command(interaction: discord.Interaction):
            await self.fetch_vendors(interaction)

        @app_commands.command(name='fetch_xur', description='Fetch Xur\'s items')
        async def fetch_xur_command(interaction: discord.Interaction):
            await self.fetch_xur(interaction)

        tree.add_command(fetch_vendors_command)
        tree.add_command(fetch_xur_command)

    async def setup_hook(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            if datetime.utcnow().weekday() == 1:  # Check vendors every Tuesday
                await self.check_vendors()
            if datetime.utcnow().weekday() == 4:  # Check Xur every Friday
                await self.check_xur()
            await asyncio.sleep(86400)  # Check once every 24 hours

    async def check_vendors(self):
        headers = {
            "X-API-Key": self.api_key
        }
        url = "https://www.bungie.net/Platform/Destiny2/Vendors/"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self.logger.debug(f'Vendors data: {data}')
            try:
                vendors_info = data['Response']['vendors']
                embeds = []
                for vendor_hash, vendor_data in vendors_info.items():
                    vendor_name = vendor_data['vendorName']
                    vendor_icon = vendor_data['vendorIcon']
                    embed = discord.Embed(title=f"{vendor_name}'s Inventory", color=discord.Color.blue())
                    embed.set_thumbnail(url=f"https://www.bungie.net{vendor_icon}")
                    field_count = 0
                    for item in vendor_data['items']:
                        if field_count >= 25:
                            embeds.append(embed)
                            embed = discord.Embed(title=f"{vendor_name}'s Inventory (cont.)", color=discord.Color.blue())
                            embed.set_thumbnail(url=f"https://www.bungie.net{vendor_icon}")
                            field_count = 0
                        item_details = await self.fetch_item_details(item['itemHash'])
                        if item_details:
                            item_name = item_details['displayProperties']['name']
                            item_icon = item_details['displayProperties']['icon']
                            item_icon_url = f"https://www.bungie.net{item_icon}"
                            embed.add_field(
                                name=item_name,
                                value=f"Quantity: {item['quantity']}\n[Icon]({item_icon_url})",
                                inline=False
                            )
                            field_count += 1
                    embeds.append(embed)
                channel = self.bot.get_channel(config['CHANNEL_ID'])
                for embed in embeds:
                    await channel.send(embed=embed)
            except KeyError as e:
                self.logger.error(f'Error processing vendors data: {e}')
        else:
            self.logger.error(f'Error fetching vendors data: {response.status_code} - {response.text}')

    async def check_xur(self):
        headers = {
            "X-API-Key": self.api_key
        }
        url = "https://www.bungie.net/Platform/Destiny2/Vendors/?components=402"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self.logger.debug(f'Xur data: {data}')
            try:
                xur_info = data['Response']['sales']['data']['2190858386']
                embed = discord.Embed(title="Xur's Inventory", color=discord.Color.purple())
                embed.set_thumbnail(url="https://www.bungie.net/img/misc/xur.png")
                field_count = 0
                for item in xur_info['saleItems'].values():
                    if field_count >= 25:
                        await channel.send(embed=embed)
                        embed = discord.Embed(title="Xur's Inventory (cont.)", color=discord.Color.purple())
                        embed.set_thumbnail(url="https://www.bungie.net/img/misc/xur.png")
                        field_count = 0
                    item_details = await self.fetch_item_details(item['itemHash'])
                    if item_details:
                        item_name = item_details['displayProperties']['name']
                        item_icon = item_details['displayProperties']['icon']
                        item_icon_url = f"https://www.bungie.net{item_icon}"
                        embed.add_field(
                            name=item_name,
                            value=f"Quantity: {item['quantity']}\n[Icon]({item_icon_url})",
                            inline=False
                        )
                        field_count += 1
                channel = self.bot.get_channel(config['CHANNEL_ID'])
                await channel.send(embed=embed)
            except KeyError as e:
                self.logger.error(f'Error processing Xur data: {e}')
        else:
            self.logger.error(f'Error fetching Xur data: {response.status_code} - {response.text}')


def setup(bot):
    destiny2 = Destiny2(bot)
    bot.add_cog(destiny2)
    bot.setup_hook = destiny2.setup_hook
