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

# hooray!

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

zoom_meeting_ids = client_obj.zoomMeetings.keys # In firebase, each meetingID maps to a list of the acceptedRoles, so we get the keys of the dict which are just the meetingID's
zoom_meeting_id = zoom_meeting_ids[0]

zoomService = ZoomService(zoom_client_id, zoom_client_secret, zoom_account_id)

# Role ID of the allowed role to access bot commands
allowed_role_id = 1106034703422722080

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

    user_id = interaction.user.id
    username = interaction.user.name
    role_id = None

    # Check if the user has any roles
    if interaction.guild:
        member = interaction.guild.get_member(user_id)
        if member and member.roles:
            # Assuming the desired role is the second role in the member's role list
            if len(member.roles) >= 2:
                role_id = member.roles[1].id




    help_embed = discord.Embed(title="SecureZ Bot Help", description="Available commands:")
    help_embed.add_field(name="/bot_help", value="Display this help message.", inline=False)
    help_embed.add_field(name="!add_email", value="Add email registered with your Zoom account.", inline=False)
    help_embed.add_field(name="!change_email", value="Change the current email listed as your Zoom account email.", inline=False)
    help_embed.add_field(name="!delete_email", value="Delete the email listed as your Zoom account email.", inline=False)
    help_embed.add_field(name="!view_email", value="View the email currently on file.", inline=False)
    message_content = f'**Hey, {interaction.user.mention}, click my profile picture and DM me with a command listed below!**'
    
    # Create firebase file for user 
    meeting_obj.add_registrant(email="temp", firstName=username, roleID=role_id, discord_member_ID=user_id)
    help_embed.color = discord.Color.from_rgb(0x2D, 0x8C, 0xFF)
    await interaction.response.send_message(content=message_content, embed=help_embed, ephemeral=True)


@bot.command()
async def add_email(ctx):
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id)
    if current_email:
        await dm_channel.send("You already have an email saved. Would you like to change it? (Y or N)")

        # if user already has email added and uses command, it will ask them if they want to change the email already listed
        def check_response(message):
            return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)

        try:
            response = await bot.wait_for('message', check=check_response, timeout=60) 
            if response.content.lower() == 'y':
                await bot.get_command('change_email').invoke(ctx)
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
                    email_data[ctx.author.id] = message.content
                    save_email_data()
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
async def delete_email(ctx): # TODO: Add comments, integrate zoom + firebase
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id)
    if current_email:
        del email_data[ctx.author.id]
        save_email_data()
        await dm_channel.send("Your email has been deleted successfully.")
    else:
        await dm_channel.send("You do not have an email on file.")
    await asyncio.sleep(4)  # Delay for 4 seconds
    await ctx.message.delete()  # Delete the command message


@bot.command()
async def view_email(ctx): # TODO: Integrate zoom + firebase
    dm_channel = await ctx.author.create_dm()
    current_email = email_data.get(ctx.author.id)
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