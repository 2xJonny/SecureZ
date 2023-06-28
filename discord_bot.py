import discord
from discord.ext import commands
# from discord import app_commands
import os
import asyncio

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
    
    for guild in bot.guilds: # Automatically pulls server_id 
        server_id = guild.id
        return server_id

discord_server_id = on_ready()  # TODO: Test that this works

client_obj = firebase.get_client_file_as_obj(discord_server_id)

discord_owner_email = client_obj.ownerEmail # In case we want to access the owner or use the name in messages
discord_owner_name = client_obj.ownerName

zoom_client_id = client_obj.clientID
zoom_client_secret = client_obj.clientSecret
zoom_account_id = client_obj.accountID
zoom_meeting_id = "81866150394" # TODO: Pull from Firebase (unique to server)

zoom_meeting_ids = client_obj.zoomMeetings.keys # In firebase, each meetingID maps to a list of the acceptedRoles, so we get the keys of the dict which are just the meetingID's

# Role ID of the allowed role to access bot commands
meeting_id = "" # NOTE: I need the meeting ID of what we are runnning the script for 
meeting_obj = firebase.get_meeting_file_as_obj(meeting_id)

accepted_role_ids = meeting_obj.acceptedRoles   # allowed_role_id = 11060347034222080 # TODO: Pull from Firebase (unique to server), change to list (multiple roles allowed)

meeting_registrants = meeting_obj.registrants



    # NOTE: I need a meeeting ID before I am able to get the allowed_role_ids

# email_data = {}  # Dictionary to store user email data

# Load email data from file
# def load_email_data():
#     try:
#         with open("email_data.txt", "r") as file:
#             lines = file.readlines()
#             for line in lines:
#                 user_id, email = line.strip().split(":")
#                 email_data[int(user_id)] = email
#     except FileNotFoundError:
#         # Create the file if it doesn't exist
#         with open("email_data.txt", "w"):
#             pass

# Save email data to file
# def save_email_data():  
#     with open("email_data.txt", "w") as file:
#         for user_id, email in email_data.items():
#             file.write(f"{user_id}:{email}\n")



# @bot.event
# async def on_member_join(member):
#     if "Member" in [role.name for role in member.roles]:
#         dm_channel = await member.create_dm()
#         await dm_channel.send("Welcome to SecureZ! To access exclusive Zoom meetings, please provide the email associated with your Zoom account.")

# @bot.event 
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.CommandNotFound):
#         return

def check_role(ctx):
    role = discord.utils.get(ctx.guild.roles, id=allowed_role_id)
    return role is not None and role in ctx.author.roles

# Function to delete the command message after a delay
async def delete_command_message(message, delay):
    await asyncio.sleep(delay)
    await message.delete()

#allows users with the whitelisted role id to use the bot
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

#/bot_help embed message
@bot.tree.command(name="bot_help")
async def bot_help_slash(interaction: discord.Interaction):
    help_embed = discord.Embed(title="SecureZ Bot Help", description="Available commands:")
    help_embed.add_field(name="/bot_help", value="Display this help message.", inline=False)
    help_embed.add_field(name="!add_email", value="Add email registered with your Zoom account.", inline=False)
    help_embed.add_field(name="!change_email", value="Change the current email listed as your Zoom account email.", inline=False)
    help_embed.add_field(name="!delete_email", value="Delete the email listed as your Zoom account email.", inline=False)
    help_embed.add_field(name="!view_email", value="View the email currently on file.", inline=False)
    message_content = f'**Hey, {interaction.user.mention}, click my profile picture and DM me with a command listed below!**'
    help_embed.color = discord.Color.from_rgb(0x2D, 0x8C, 0xFF)
    await interaction.response.send_message(content=message_content, embed=help_embed, ephemeral=True)


@bot.command()
async def add_email(ctx): # TODO: Add comments, integrate zoom + firebase
    meeting_obj = firebase.get_meeting_file_as_obj(meetingID)
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id)   # NOTE: CAP

    if current_email:
        await dm_channel.send("You already have an email saved. Would you like to change it? (Y or N)")

        # if user already has email added and uses command, it will ask them if they want to change the email already listed
        def check_response(message):
            return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)

        try:
            response = await bot.wait_for('message', check=check_response, timeout=60) 
            if response.content.lower() == 'y':
                await bot.get_command('change_email').invoke(ctx) # Call change_email command
                new_email = await bot.wait_for('message', check=check_email, timeout=60)    # BUG: This could be wrong line of code but i needed a way to get the new email
                meeting_obj.change_email(current_email, new_email.content)   # NOTE: how do I get the response of the new email
            elif response.content.lower() == 'n':
                await dm_channel.send(f"No changes will be made to your current email: {current_email}")
            else:
                await dm_channel.send("Invalid response. No changes will be made to your current email. If you would still like to change your email, use the command '!change_email'.") # If user inputs improper format, it will follow up
        except asyncio.TimeoutError:
            await dm_channel.send("Response timed out. No changes will be made to your current email.") 
    else:
        await dm_channel.send("Please provide the email associated with your Zoom account. The email must be in the format 'user@gmail.com'.") # Allows users to add email for the first time
        def check_email(message):
            return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)

        try:
            while True:
                message = await bot.wait_for('message', check=check_email, timeout=60)
                if "@" not in message.content:
                    await dm_channel.send('The email must be in the format "user@domain.com". Please try again.')
                else:
                    # email_data[ctx.author.id] = message.content
                    # save_email_data()1

                    zoomService.add_participant_to_meeting(meeting_id, message.content)
                    local_role_ID = "get bot command \@role_name to run"    # TODO: need to get the roleID of the user the bot is chatting with rn 
                    meeting_obj.add_registrant(email=message.content, firstName=ctx.author.name, roleID=local_role_ID)
                    
                    await dm_channel.send("Email saved successfully.")
                    break
        except asyncio.TimeoutError:
            await dm_channel.send("Email submission timed out. Please try again later.")

    # Schedule deletion of command message after 4 seconds
    await asyncio.create_task(delete_command_message(ctx.message, 4))

@bot.command()
async def change_email(ctx): # TODO: Add comments, integrate zoom + firebase
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id) # TODO: Get email from firebase (specific to user on server)
    if current_email:
        await dm_channel.send(f"Your current email on file is: {current_email}\n\nPlease enter the new email you would like to associate with your Zoom account. The email must be in the format 'user@gmail.com'.")
        def check(message):
            return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)
        try:
            while True: # Prompt user until a valid email is provided
                message = await bot.wait_for('message', check=check, timeout=60)
                if "@" not in message.content:
                    await dm_channel.send("The email must be in the format 'user@gmail.com'. Please try again.") # Checks for proper email format
                else:
                    # email_data[ctx.author.id] = message.content
                    # save_email_data()
                    # TODO: Change email in firebase server for user
                    meeting_obj.change_email(email, message.content)    # NOTE: What is curretn user email??
                    zoomService.change_participant_email(meeting_id=zoom_meeting_id, old_email=current_email, new_email=message.content, first_name=ctx.author.name, last_name ="-")
                    await dm_channel.send(f"Email changed successfully. Your new email is: {message.content}")
                    break
        except asyncio.TimeoutError:
            await dm_channel.send("Email change request timed out. Please try again later.")
    else:
        await dm_channel.send("You don't have an email on file. Please use the !add_email command to provide your email first.")

    # Schedule deletion of command message after 4 seconds
    await asyncio.create_task(delete_command_message(ctx.message, 4))

@bot.command()
async def delete_email(ctx): # TODO: Add comments, integrate zoom + firebase
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id) # TODO: Get email from firebase   (Need a discord ID or something)
    if current_email:
        meeting_obj.remove_individual_registrant(current_email)
        # del email_data[ctx.author.id]
        # save_email_data()
        
        zoomService.remove_participant_from_meeting(zoom_meeting_id, current_email)
        await dm_channel.send("Your email has been deleted successfully.")
    else:
        await dm_channel.send("You do not have an email on file.")
    await asyncio.sleep(4)  # Delay for 4 seconds
    await ctx.message.delete()  # Delete the command message


@bot.command()
async def view_email(ctx): # TODO: Integrate zoom + firebase
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id)   # TODO: get email from firebase (but need discord ID or identifier)
    # TODO: Get user email from firebase
    if current_email:
        await dm_channel.send(f"Your current email on file is: {current_email}")
    else:
        await dm_channel.send("You don't have an email on file.")
    await asyncio.sleep(4)  # Delay for 4 seconds
    await ctx.message.delete()  # Delete the command message

@bot.event # TODO: Integrate zoom + firebase
async def on_member_update(before, after):
    monitored_role_id = allowed_role_id  # Replace with the ID of the whitelisted role

    if monitored_role_id in [role.id for role in before.roles] and monitored_role_id not in [role.id for role in after.roles]:
        # Whitelisted role was removed from the member
        member_id = before.id

        # Remove member from meetings if they lose the whitelisted role
        if member_id in email_data:
            del email_data[member_id]  # Remove the member ID and email from the dictionary 
            save_email_data()  # Save the updated email data to the file

            email = "" # TODO: Get email from firebase
            # TODO: Remove email from meeting on firebase

            zoomService.remove_participant_from_meeting(zoom_meeting_id, email)

    # TODO: Add member to meetings (or at least DM them) if they gain a whitelisted role
        
            
# Run the bot
load_dotenv()
bot.run(os.environ.get('DISCORD_TOKEN'))