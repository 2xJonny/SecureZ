import discord
from discord.ext import commands
# from discord import app_commands
import os
import asyncio
import re
from dotenv import load_dotenv
from zoom_service import ZoomService
from database_service import Meeting, Client
import database_service as firebase

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    
    # for guild in bot.guilds: # Automatically pulls server_id 
    #     server_id = guild.id
    #     return server_id

# discord_server_id = on_ready()  # TODO: Test that this works

# Server ID
client_obj = firebase.get_client_file_as_obj('kjsgbuwneiwe')

discord_owner_email = client_obj.ownerEmail # In case we want to access the owner or use the name in messages
discord_owner_name = client_obj.ownerName

zoom_client_id = client_obj.clientID
zoom_client_secret = client_obj.clientSecret
zoom_account_id = client_obj.accountID
# zoom_meeting_ids = client_obj.zoomMeetings.keys()
# zoom_meeting_accepted_roles = client_obj.zoomMeetings[zoom_meeting_ids[0]]
 # TODO: Pull from Firebase (unique to server)

meeting_obj = firebase.get_meeting_file_as_obj("qqqmeetingIDqqq")


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
email_data = {}  # Dictionary to store user email and role data

# Load email and role data from file
def load_email_data():
    try:
        with open("email_data.txt", "r") as file:
            lines = file.readlines()
            for line in lines:
                values = line.strip().split(":")
                if len(values) >= 3:
                    user_id, email, role_id, role_name = values[:4]
                    email_data[int(user_id)] = {
                        "email": email,
                        "role_id": int(role_id),
                        "role_name": role_name
                    }
                    print(email_data)
    except FileNotFoundError:
        # Create the file if it doesn't exist
        with open("email_data.txt", "w"):
            pass

# Save email and role data to file
def save_email_data():
    with open("email_data.txt", "w") as file:
        for user_id, data in email_data.items():
            email = data["email"]
            role_id = data["role_id"]
            role_name = data["role_name"]
            file.write(f"{user_id}:{email}:{role_id}:{role_name}\n")

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

# Role ID and name of the allowed role to access bot commands

@bot.event
async def check_role(ctx,):
    allowed_role_ids = meeting_obj.acceptedRoles
    print(allowed_role_ids)

    user_roles = ctx.author.roles
    print(user_roles)

    overlapping_roles = (set(allowed_role_ids)).intersection((set(user_roles)))

    if len(overlapping_roles) == 0:
        await ctx.send(f"{ctx.author.mention}, you don't have the required role to use this bot command.")



# def check_role(ctx):
    # role = discord.utils.get(ctx.guild.roles, id=allowed_role_id)
    # print("!!!!!!!" + str(role))
    # return role is not None and role in ctx.author.roles

# @bot.check
# async def global_check(ctx):
#     if ctx.guild is None:
#         print("TESTING")
#         # Allow DM messages to the bot
#         return True
#     elif check_role(ctx):
#         # Allow access to bot commands for users with the allowed role
#         return True
#     else:
#         # Restrict access to bot commands for other users
#         await ctx.send("You don't have the required role to use this bot command.")
#         return False

@bot.tree.command(name="bot_help")
async def bot_help_slash(interaction: discord.Interaction):

    user_id = interaction.user.id
    username = interaction.user.name
    role_string_list = ""
    for role in interaction.user.roles:
        role_string_list = role_string_list + "," + str(role.id)

    # Check if the user has any roles
    if interaction.guild:
        member = interaction.guild.get_member(user_id)
        if member and member.roles:
            # Assuming the desired role is the second role in the member's role list
            if len(member.roles) >= 2:
                role_id = member.roles[1].id    # ???
    help_embed = discord.Embed(title="SecureZ Bot Help", description="Available commands:")
    help_embed.add_field(name="/bot_help", value="Display this help message.", inline=False)
    help_embed.add_field(name="!add_email", value="Add email registered with your Zoom account.", inline=False)
    help_embed.add_field(name="!change_email", value="Change the current email listed as your Zoom account email.", inline=False)
    help_embed.add_field(name="!delete_email", value="Delete the email listed as your Zoom account email.", inline=False)
    help_embed.add_field(name="!view_email", value="View the email currently on file.", inline=False)
    message_content = f'**Hey, {interaction.user.mention}, click my profile picture and DM me with a command listed below!**'
    
    # Create firebase file for user 
    meeting_obj.add_registrant(email="temp", firstName=str(username), roleID=role_string_list, discord_member_ID=str(user_id))
    help_embed.color = discord.Color.from_rgb(0x2D, 0x8C, 0xFF)
    await interaction.response.send_message(content=message_content, embed=help_embed, ephemeral=True)

@bot.command()
async def add_email(ctx):
    dm_channel = await ctx.author.create_dm()

    current_email = meeting_obj.get_registrant_email(str(ctx.author.id))
    await ctx.message.delete(delay=4)

    if current_email != "temp":
        await dm_channel.send("You already have an email associated with your Zoom account. If you want to change it, please use the `!change_email` command.")
        return

    await dm_channel.send("Please provide the email associated with your Zoom account. The email must be in the format 'user@gmail.com'.")

    def check_email(message):
        return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)

    try:
        message = await bot.wait_for('message', check=check_email, timeout=60)
        if "@" not in message.content:
            await dm_channel.send('The email must be in the format "user@domain.com". Please try again.')
            return

        email = message.content
        # Save the email to Firebase or perform any necessary operations
        meeting_obj.change_email(str(ctx.author.id), email)

        await dm_channel.send("Email saved successfully.")
    except asyncio.TimeoutError:
        await dm_channel.send("Email submission timed out. Please try again later.")


@bot.command()
async def change_email(ctx):
    dm_channel = await ctx.author.create_dm()

    current_email = meeting_obj.get_registrant_email(str(ctx.author.id))
    await ctx.message.delete(delay=4)

    if current_email != "temp":
        await dm_channel.send(f"Your current email on file is: {current_email}\n\nPlease enter the new email you would like to associate with your Zoom account. The email must be in the format 'user@domain.com'.")
        def check(message):
            return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)
        try:
            while True:
                message = await bot.wait_for('message', check=check, timeout=60)
                if "@" not in message.content:
                    await dm_channel.send("The email must be in the format 'user@gmail.com'. Please try again.")
                else:

                    newEmail = message.content

                    meeting_obj.change_email(str(ctx.author.id), newEmail)
                
                    await dm_channel.send(f"Email changed successfully. Your new email is: {message.content}")
                    break
        except asyncio.TimeoutError:
            await dm_channel.send("Email change request timed out. Please try again later.")
    else:
        await dm_channel.send("You don't have an email on file. Please use the !add_email command to provide your email first.")


@bot.command()
async def delete_email(ctx):

    dm_channel = await ctx.author.create_dm()
    current_email = meeting_obj.get_registrant_email(str(ctx.author.id))
    await ctx.message.delete(delay=4)

    if current_email != "temp":
        meeting_obj.change_email(str(ctx.author.id), "temp")
        await dm_channel.send("Your email has been deleted successfully.")
    else:
        await dm_channel.send("You don't have an email on file.")

# Function to delete the command message after a delay
async def delete_command_message(message, delay):
    await asyncio.sleep(delay)
    await message.delete()

@bot.command()
async def view_email(ctx):
    dm_channel = await ctx.author.create_dm()
    current_email = meeting_obj.get_registrant_email(str(ctx.author.id))
    await ctx.message.delete(delay=4)

    if current_email != "temp":
        await dm_channel.send(f"Your current email on file is: {current_email}")
    else:
        await dm_channel.send("You don't have an email on file.")

@bot.command()
async def bot_help(ctx):
    message = await ctx.send("Please use the command '/bot_help' instead.")
    await ctx.message.delete(delay=6)
    await message.delete(delay=6)

@bot.event
async def on_member_update(before, after):
    allowed_role_ids = meeting_obj.acceptedRoles

    after_role_ids = []

    for role_obj in after.roles:
        after_role_ids.append(role_obj.id)

    
    if len(set(after_role_ids) & set(allowed_role_ids)) == 0:
        list_of_registrant_discord_IDs = list(meeting_obj.get_registrants().keys())
        print(list_of_registrant_discord_IDs)
        print(before.id)

        discord_id = str(before.id)

        if discord_id in list_of_registrant_discord_IDs:
            meeting_obj.delete_registrant(discord_id)


# Run bot
load_dotenv()
bot.run(os.environ.get('DISCORD_TOKEN'))