import discord
from discord.ext import commands
# from discord import app_commands
import os
import asyncio
import re
from zoom_service import ZoomService
from database_service import Meeting, Client
import database_service as firebase
from dotenv import load_dotenv


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

print(meeting_obj.registrants)


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
email_data = {}  # Dictionary to store user email and role data


@bot.event
async def on_ready():
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


def check_if_valid_role(ctx):
    allowed_role_ids = meeting_obj.acceptedRoles
    print(allowed_role_ids)

    user_roles_list = meeting_obj.get_registrant(str(ctx.author.id))[2].split(",")
    print(user_roles_list)


    for user_role in user_roles_list:
        if user_role in allowed_role_ids:
            return True

        
    if ctx.author.id in meeting_obj.registrants:
        meeting_obj.remove_individual_registrant(ctx.author.id)

    return False

    
@bot.tree.command(name="bot_help")
async def bot_help_slash(interaction: discord.Interaction):



    # roles_of_registrant_list = meeting_obj.get_registrant(str(interaction.user.id))[2].split(",")
    # print(roles_of_registrant_list)

    isValidSet = set()# set(roles_of_registrant_list) & set(meeting_obj.acceptedRoles)

    if len(isValidSet) == 0:

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

    else:
        user = bot.get_user(interaction.user.id)
        await user.send("You dont have access to this command: /bot_help")





@bot.command()
async def add_email(ctx):

    isValidRole = check_if_valid_role(ctx)

    print(isValidRole)

    dm_channel = await ctx.author.create_dm()

    if isValidRole:

        current_email = meeting_obj.get_registrant_email(str(ctx.author.id))

        await ctx.message.delete(delay=4)

        if current_email != "temp":
            await dm_channel.send("You already have an email associated with your Zoom account. If you want to change it, please use the `!change_email` command.")

        else:
            await dm_channel.send("Please provide the email associated with your Zoom account. The email must be in the format 'user@gmail.com'.")

            def check_email(message):
                return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)

            try:
                message = await bot.wait_for('message', check=check_email, timeout=60)
                if "@" not in message.content:
                    await dm_channel.send('The email must be in the format "user@domain.com". Please try again.')
                    return

                email = message.content
                meeting_obj.change_email(str(ctx.author.id), email)

                await dm_channel.send("Email saved successfully.")
            except asyncio.TimeoutError:
                await dm_channel.send("Email submission timed out. Please try again later.")
            

    else:

        await dm_channel.send("You dont have access to this command: !add_email")



@bot.command()
async def change_email(ctx):

    isValidRole = check_if_valid_role(ctx)

    dm_channel = await ctx.author.create_dm()

    if isValidRole:

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

    else:

        await dm_channel.send("You dont have access to this command: !change_email")



@bot.command()
async def delete_email(ctx):

    dm_channel = await ctx.author.create_dm()

    isValidRole = check_if_valid_role(ctx)

    if isValidRole:

        current_email = meeting_obj.get_registrant_email(str(ctx.author.id))
        await ctx.message.delete(delay=4)

        if current_email != "temp":
            meeting_obj.change_email(str(ctx.author.id), "temp")
            await dm_channel.send("Your email has been deleted successfully.")
        else:
            await dm_channel.send("You don't have an email on file.")
        
    else:

        await dm_channel.send("You dont have access to this command: !delete_email")


# Function to delete the command message after a delay
async def delete_command_message(message, delay):
    await asyncio.sleep(delay)
    await message.delete()

@bot.command()
async def view_email(ctx):
    dm_channel = await ctx.author.create_dm()

    isValidRole = check_if_valid_role(ctx)

    if isValidRole:

        current_email = meeting_obj.get_registrant_email(str(ctx.author.id))
        await ctx.message.delete(delay=4)

        if current_email != "temp":
            await dm_channel.send(f"Your current email on file is: {current_email}")
        else:
            await dm_channel.send("You don't have an email on file.")

    else:

        await dm_channel.send("You dont have access to this command: !view_email")


@bot.command()
async def bot_help(ctx):
    message = await ctx.send("Please use the command '/bot_help' instead.")
    await ctx.message.delete(delay=6)
    await message.delete(delay=6)

@bot.event
async def on_member_update(before, after):  # TODO: fix this shit

    discord_ID = str(after.id)   # ID of current discord user

    allowed_role_ids = meeting_obj.acceptedRoles

    after_role_ids = []

    role_string_list = ""

    for role_obj in after.roles:    # populating roles of user for future use

        after_role_ids.append(str(role_obj.id))
        role_string_list = role_string_list + "," + str(role_obj.id)


    current_registrant_discord_ids = list(meeting_obj.registrants.keys())   # discord ID's of current ppl in firebase

    print(current_registrant_discord_ids)

    if (discord_ID in current_registrant_discord_ids): # checking if user is in firebase

        meeting_obj.change_role(role_string_list, discord_ID)   # works for 1 -> 0 and 1 -> 1

        if len(set(after_role_ids) & set(allowed_role_ids)) == 0:   # this means Firebase user has roles that is NOT valid
            print("remove from zoom!")
            ZoomService.remove_participant_from_meeting(meeting_id=meeting_obj.meetingID, email=meeting_obj.get_registrant_email(discord_ID)) # remove them from zoom whitelist

        else:
            # add to zoom meeting 
            print("add to zoom!")
            
    else: 

        if len(set(after_role_ids) & set(allowed_role_ids)) > 0:   # this means the NEW user has a role that is valid

            meeting_obj.add_registrant(discord_member_ID=discord_ID, email="temp", firstName=str(after.name), roleID=role_string_list) # added new user to firebase
            print("PROMPT TO ADD EMAIL")
            # prompt to get their email


            









        
        # if len(set(after_role_ids) & set(allowed_role_ids)) == 0:   # this means the user doesnt have a role that is required
        #     meeting_obj.change_role(role_string_list, discord_ID)
        #     # update their roles list with new roles   # This takes care of if a user gets demoted (1 -> 0)
        #     return 

        # else:




            # current_registrant_discord_ids = list(meeting_obj.registrants.keys())   # discord ID's of current ppl in firebase

            # if (discord_ID in current_registrant_discord_ids): # checking if user is in firebase
            #     # Handling user coming back to paid member (0 -> 1 -> 0)
            #     meeting_obj.change_role(role_string_list, discord_ID)
                

            # else:
            # Handling new user (0 -> 1)
            





    


    


    # if len(set(after_role_ids) & set(allowed_role_ids)) == 0:   # this means the user doesnt have a role that is required

    #     discord_id = str(before.id)

    #     if discord_id in list_of_registrant_discord_IDs:
    #         meeting_obj.delete_registrant(discord_id)





    

    



    







    # if user file is in firebase but dont have the allowed role, but then they get added back --> need to update firebase with new roles 


    
    # if len(set(after_role_ids) & set(allowed_role_ids)) == 0:
    #     list_of_registrant_discord_IDs = list(meeting_obj.get_registrants().keys())
    #     print(list_of_registrant_dscord_IDs)
    #     print(before.id)



# # Run bot
load_dotenv()
bot.run(os.environ.get('DISCORD_TOKEN'))