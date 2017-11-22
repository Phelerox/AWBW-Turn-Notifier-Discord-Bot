import discord
from discord.ext import commands
import asyncio
import aiohttp
import async_timeout


bot = commands.Bot(command_prefix='$', description="notify_me_about <game_id>")
global game_id_list
game_id_list = ["254555"]
global ended_games
ended_games = []
username_map = {"Phelerox":"Phelerox#5519", "Frazz3":"Frazz3#1777", "Quik":"[Q]uik#4332"}
username_to_discord_user = {"Phelerox":None, "Frazz3":None, "Quik":None}
aw_channel = discord.Object(id='378694324915011596')

@bot.command()
async def notify_me_about(ctx, game_id, pm_instead : str = ""):
    pass


async def check_turn_in_game(game_id, send_pm_instead=False, pm_reminders=False):
    global ended_games, game_id_list
    await bot.wait_until_ready()
    await bot.wait_until_login()
    same_turn_counter = 0
    counter = 0
    last_turn_was = ""
    while not bot.is_closed:
        username = ""
        counter += 1
        print("Poll number: " + str(counter) + " for game id: " + str(game_id))
        async with aiohttp.ClientSession() as session:
            html = await get_html(session, game_id)
            for line in html.splitlines():
                if 'href="profile.php?username=' in line and '</b>' in line:
                    start_b = line.find('<b>')
                    end_b = line.find('</b>')
                    username = line[start_b+3:end_b]
            if '<span class="small_text">Game&nbsp;Ended:&nbsp;' in html:
                print("Game " + game_id + " ended!")
                if send_pm_instead:
                    await send_message(username_to_discord_user[username], "Game " + game_id + " ended!")
                    if last_turn_was != "":
                        await send_message(username_to_discord_user[last_turn_was], "Game " + game_id + " ended!")
                else:
                    await send_message(aw_channel, "Game " + game_id + " ended!")
                ended_games += game_id
                try:
                    game_id_list.remove(game_id)
                except ValueError:
                    pass
                break #terminates the task
        print(username + "'s turn! Last turn was: " + last_turn_was)
        if username != "" and username != last_turn_was:
            same_turn_counter = 0
            last_turn_was = username
            print("Sending message")
            if send_pm_instead:
                await send_message(username_to_discord_user[username], "It's your turn!")
            else:
                mention = '<@' + str(username_to_discord_user[username].id) + '>'
                await send_message(aw_channel, "%s's turn!" % mention)
                print(username_to_discord_user[username].id)
        elif username != "" and username == last_turn_was:
            same_turn_counter += 1
            if pm_reminders and same_turn_counter % 90 == 0: #Remind by PM every 6 hours
                print("It's been " + username + "'s turn for " + str(int(same_turn_counter / 15)) + " hours!")
                await send_message(username_to_discord_user[username], "It's been your turn for " + str(int(same_turn_counter/15)) + " hours!")
                if username != "Phelerox": #For debug purposes, tell dev when reminder is issued
                    await send_message(username_to_discord_user["Phelerox"], "It's been " + username + "'s turn for " + str(int(same_turn_counter / 15)) + " hours!")

        await asyncio.sleep(240) # task runs every fourth minute
    print("Shutting down task to monitor game " + game_id)

async def get_html(session, game_id):
    try:
        with async_timeout.timeout(40):
            async with session.get('http://awbw.amarriner.com/game.php?games_id=' + str(game_id)) as response:
                return await response.text()
    except TimeoutError as te:
        await send_message(username_to_discord_user["Phelerox"], "TimeoutError! " + str(te))
        return get_html(session, game_id)
    except Exception as e:
        await send_message(username_to_discord_user["Phelerox"], "Unknown exception when fetching html! " + str(e.__class__.__name__))
        return get_html(session, game_id)

async def send_message(destination, message):
    try:
        await bot.send_message(destination, message)
    except Exception as e:
        print("Unknown exception when sending message: " + str(e.__class__.__name__))
        await send_message(destination, message)


@bot.event
async def on_ready():
    for server in bot.servers:
        for discord_user in server.members:
            for username, discord_username in username_map.items():
                if discord_username == str(discord_user):
                    username_to_discord_user[username] = discord_user
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


bot.loop.create_task(check_turn_in_game(game_id_list[0], pm_reminders=True))

token = '' #The token should be on the first line in a file named 'token'.
with open('token', 'r') as token_file:
    token = token_file.readline()
bot.run(token)