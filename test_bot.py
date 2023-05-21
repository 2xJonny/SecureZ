import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.dm_messages = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
email_data = {}  # Dictionary to store user email data

# Load email data from file
def load_email_data():
    try:
        with open("email_data.txt", "r") as file:
            lines = file.readlines()
            for line in lines:
                user_id, email = line.strip().split(":")
                email_data[int(user_id)] = email
    except FileNotFoundError:
        # Create the file if it doesn't exist
        with open("email_data.txt", "w"):
            pass

# Save email data to file
def save_email_data():
    with open("email_data.txt", "w") as file:
        for user_id, email in email_data.items():
            file.write(f"{user_id}:{email}\n")

@bot.event
async def on_ready():
    load_email_data()
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

@bot.event
async def on_member_join(member):
    if "Member" in [role.name for role in member.roles]:
        dm_channel = await member.create_dm()
        await dm_channel.send("Welcome to SecureZ! To access exclusive Zoom meetings, please provide the email associated with your Zoom account.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

# Role ID of the allowed role to access bot commands
allowed_role_id = 1106034703422722080

def check_role(ctx):
    role = discord.utils.get(ctx.guild.roles, id=allowed_role_id)
    return role is not None and role in ctx.author.roles

@bot.check
async def global_check(ctx):
    if ctx.guild is None:
        # Allow DM messages to the bot
        return True
    elif check_role(ctx):
        # Allow access to bot commands for users with the allowed role
        return True
    else:
        # Restrict access to bot commands for other users
        await ctx.send("You don't have the required role to use this bot command.")
        return False

@bot.command()
async def bot_help(ctx):
    help_embed = discord.Embed(title="SecureZ Bot Help", description="Here are the available commands:")
    help_embed.add_field(name="!bot_help", value="Display this help message.", inline=False)
    help_embed.add_field(name="!add_email", value="Privately message the bot to provide the email associated with your Zoom account.", inline=False)
    help_embed.add_field(name="!change_email", value="Privately message the bot to change your current email.", inline=False)
    help_embed.add_field(name="!delete_email", value="Display this help message.", inline=False)
    help_embed.add_field(name="!view_email", value="View the email currently on file.", inline=False)
    dm_channel = await ctx.author.create_dm()
    await dm_channel.send(embed=help_embed)
    await asyncio.sleep(4)  # Delay for 4 seconds
    await ctx.message.delete()  # Delete the command message

@bot.command()
async def add_email(ctx):
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id)
    if current_email:
        await dm_channel.send("You already have an email saved. Would you like to change it? (Y or N)")
        def check_response(message):
            return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)
        try:
            response = await bot.wait_for('message', check=check_response, timeout=60)
            if response.content.lower() == 'y':
                await change_email.invoke(ctx)
            elif response.content.lower() == 'n':
                await dm_channel.send(f"No changes will be made to your current email: {current_email}")
            else:
                await dm_channel.send("Invalid response. No changes will be made to your current email. If you would still like to change your email, use the command '!change_email'.")
        except asyncio.TimeoutError:
            await dm_channel.send("Response timed out. No changes will be made to your current email.")
    else:
        await dm_channel.send("Please provide the email associated with your Zoom account. The email must be in the format 'user@gmail.com'.")
        def check_email(message):
            return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)
        try:
            while True:
                message = await bot.wait_for('message', check=check_email, timeout=60)
                if "@" not in message.content:
                    await dm_channel.send("The email must be in the format 'user@gmail.com'. Please try again.")
                else:
                    email_data[ctx.author.id] = message.content
                    save_email_data()
                    await dm_channel.send("Email saved successfully.")
                    break
        except asyncio.TimeoutError:
            await dm_channel.send("Email submission timed out. Please try again later.")

    # Schedule deletion of command message after 4 seconds
    await asyncio.create_task(delete_command_message(ctx.message, 4))

@bot.command()
async def change_email(ctx):
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id)
    if current_email:
        await dm_channel.send(f"Your current email on file is: {current_email}\n\nPlease enter the new email you would like to associate with your Zoom account. The email must be in the format 'user@gmail.com'.")
        def check(message):
            return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)
        try:
            while True:
                message = await bot.wait_for('message', check=check, timeout=60)
                if "@" not in message.content:
                    await dm_channel.send("The email must be in the format 'user@gmail.com'. Please try again.")
                else:
                    email_data[ctx.author.id] = message.content
                    save_email_data()
                    await dm_channel.send(f"Email changed successfully. Your new email is: {message.content}")
                    break
        except asyncio.TimeoutError:
            await dm_channel.send("Email change request timed out. Please try again later.")
    else:
        await dm_channel.send("You don't have an email on file. Please use the !add_email command to provide your email first.")

    # Schedule deletion of command message after 4 seconds
    await asyncio.create_task(delete_command_message(ctx.message, 4))


@bot.command()
async def delete_email(ctx):
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id)
    if current_email:
        del email_data[ctx.author.id]
        save_email_data()
        await dm_channel.send("Your email has been deleted successfully.")
    else:
        await dm_channel.send("You don't have an email on file.")
    await asyncio.sleep(4)  # Delay for 4 seconds
    await ctx.message.delete()  # Delete the command message

# Function to delete the command message after a delay
async def delete_command_message(message, delay):
    await asyncio.sleep(delay)
    await message.delete()

@bot.command()
async def view_email(ctx):
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id)
    if current_email:
        await dm_channel.send(f"Your current email on file is: {current_email}")
    else:
        await dm_channel.send("You don't have an email on file.")
    await asyncio.sleep(4)  # Delay for 4 seconds
    await ctx.message.delete()  # Delete the command message

@bot.event
async def on_member_update(before, after):
    monitored_role_id = 1106034703422722080  # Replace with the ID of the whitelisted role

    if monitored_role_id in [role.id for role in before.roles] and monitored_role_id not in [role.id for role in after.roles]:
        # Whitelisted role was removed from the member
        member_id = before.id

        if member_id in email_data:
            del email_data[member_id]  # Remove the member ID and email from the dictionary
            save_email_data()  # Save the updated email data to the file

# Run the bot
bot.run('MTEwMjQ0MTk5MTQ2OTU0MzQ3NQ.G56oAO.1LjskROt0sVuFnBCyFKI1sTIh4jrQKEpNCAsmI')