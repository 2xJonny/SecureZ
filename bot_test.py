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
    if "PaidMember" in [role.name for role in member.roles]:
        dm_channel = await member.create_dm()
        await dm_channel.send("Welcome to SecureZ! To access exclusive Zoom meetings, please provide the email associated with your Zoom account.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    

# Dictionary to store allowed role names for different servers
allowed_roles = {
    758744436908883978: ["discordian"],
    758744436908883978: ["sun wukong"],
    # Add more server IDs and role names as needed
}

def check_role(ctx):
    server_id = ctx.guild.id
    if server_id in allowed_roles:
        allowed_role_names = allowed_roles[server_id]
        for role_name in allowed_role_names:
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role in ctx.author.roles:
                return True
    return False

def check_role(ctx):
    server_id = ctx.guild.id
    if server_id in allowed_roles:
        allowed_role_ids = allowed_roles[server_id]
        for role_id in allowed_role_ids:
            role = ctx.guild.get_role(role_id)
            if role in ctx.author.roles:
                return True
    return False

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
    await ctx.send(embed=help_embed)


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
                await dm_channel.send("Invalid response. No changes will be made to your current email.")
        except asyncio.TimeoutError:
            await dm_channel.send("Response timed out. No changes will be made to your current email.")
    else:
        await dm_channel.send("Please provide the email associated with your Zoom account.")

        def check_email(message):
            return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)

        try:
            message = await bot.wait_for('message', check=check_email, timeout=60)
            email_data[ctx.author.id] = message.content
            save_email_data()
            await dm_channel.send("Email saved successfully.")
        except asyncio.TimeoutError:
            await dm_channel.send("Email submission timed out. Please try again later.")
            
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

@bot.command()
async def change_email(ctx):
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id)
    if current_email:
        await dm_channel.send(f"Your current email on file is: {current_email}\n\nPlease enter the new email you would like to associate with your Zoom account.")

        def check(message):
            return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)

        try:
            message = await bot.wait_for('message', check=check, timeout=60)
            email_data[ctx.author.id] = message.content
            save_email_data()
            await dm_channel.send(f"Email changed successfully. Your new email is: {message.content}")
        except asyncio.TimeoutError:
            await dm_channel.send("Email change request timed out. Please try again later.")
    else:
        await dm_channel.send("You don't have an email on file. Please use the !add_email command to provide your email first.")

@bot.command()
async def view_email(ctx):
    current_email = email_data.get(ctx.author.id)
    if current_email:
        await ctx.send(f"The email currently on file for you is: {current_email}")
    else:
        await ctx.send("You don't have an email on file. Please use the !add_email command to provide your email first.")

# To check who is on the email list, comment out the 'bot.run' line and uncomment the 'read_email_data_file()' line.
def read_email_data_file():
    try:
        with open("email_data.txt", "r") as file:
            lines = file.readlines()
            for line in lines:
                print(line.strip())
    except FileNotFoundError:
        print("Email data file not found.")

# Call the function to read and print the email data file
# read_email_data_file()

bot.run('MTEwMjQ0MTk5MTQ2OTU0MzQ3NQ.G56oAO.1LjskROt0sVuFnBCyFKI1sTIh4jrQKEpNCAsmI')

