import logging

import discord
from discord import app_commands

logger = logging.getLogger(__name__)


class PolicyModule:
    def __init__(self, bot):
        self.bot = bot
        self.add_commands()

    def add_commands(self):
        @app_commands.command(
            name="privacy_policy", description="View the Privacy Policy"
        )
        async def privacy_policy(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                privacy_policy_text = """
                **Privacy Policy**

                1. **Data Collection**
                   - We collect your Discord user ID and messages sent to the bot.
                   - No sensitive personal data is collected.

                2. **Data Usage**
                   - Your data is used to provide and improve the bot's functionality.
                   - We do not share your data with third parties.

                3. **Data Storage**
                   - Data is stored securely on our servers.
                   - Data is retained for as long as necessary to provide our services.

                4. **Your Rights**
                   - You have the right to access, modify, and delete your data.
                   - To exercise these rights, contact the bot admin.

                5. **Changes to Privacy Policy**
                   - We may update this policy from time to time.
                   - You will be notified of any significant changes.

                6. **Contact**
                   - For any questions about this policy, contact the bot admin.
                """
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Privacy Policy",
                        description=privacy_policy_text,
                        color=discord.Color.blue(),
                    )
                )
                logger.info(f"User {interaction.user.id} viewed the privacy policy")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in privacy_policy command: {e}")

        @app_commands.command(
            name="terms_of_service", description="View the Terms of Service"
        )
        async def terms_of_service(interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                tos_text = """
                **Terms of Service**

                1. **Acceptance of Terms**
                   - By using this bot, you agree to these terms.
                   - If you do not agree, do not use the bot.

                2. **Use of the Bot**
                   - You must follow all applicable laws and regulations.
                   - Do not use the bot for any illegal or unauthorized purpose.

                3. **Changes to Terms**
                   - We may update these terms from time to time.
                   - You will be notified of any significant changes.

                4. **Termination**
                   - We reserve the right to terminate or restrict your access to the bot at any time, without notice or liability.

                5. **Disclaimer of Warranties**
                   - The bot is provided "as is" without warranties of any kind.
                   - We do not guarantee that the bot will be error-free or uninterrupted.

                6. **Limitation of Liability**
                   - We shall not be liable for any damages arising from your use of the bot.

                7. **Contact**
                   - For any questions about these terms, contact the bot admin.
                """
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Terms of Service",
                        description=tos_text,
                        color=discord.Color.blue(),
                    )
                )
                logger.info(f"User {interaction.user.id} viewed the terms of service")
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")
                logger.error(f"Error in terms_of_service command: {e}")

        self.bot.tree.add_command(privacy_policy)
        self.bot.tree.add_command(terms_of_service)


async def setup(bot):
    PolicyModule(bot)
