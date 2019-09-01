import sys
from html import unescape

import discord

import bot.display.show as show
from bot import log
from bot.constants import bot_channel, db_uri
from bot.manage.discord_data import get_command_args


def display(part):
    lines = part.split('\n')
    for line in lines:
        print(line)


async def interrupt(self, message, embed_color=None, embed_name=None, keep_locking=False):
    parts = show.display_parts(message)
    for part in parts:

        display(part)
        if embed_color is None or embed_name is None:
            await self.channel.send(part)
        else:
            embed = discord.Embed(color=embed_color)
            embed.add_field(name=embed_name, value=part, inline=False)
            await self.channel.send(embed=embed)

    if not keep_locking:
        self.lock = False
    return


def check(self, engine):
    if self.channel is None:
        log.warn(f'{bot_channel} is not a valid channel name')
        log.warn('Please update the channel name used by the bot '
                 'in ./bot/constants.py')
        sys.exit(0)

    if not engine.table_names():
        log.warn(f'Cannot connect to database using {db_uri}')
        log.warn('Please update the db_uri field used by the bot '
                 'in ./bot/constants.py')
        sys.exit(0)


async def ready(self, engine):
    check(self, engine)
    print('CTFdBot is coming !')

    tosend = ('Hello, it seems that it\'s the first time you are '
              'using my services.\nYou might use `>>help` to know '
              'more about my features.')

    embed_color, embed_name = 0x000000, "CTFd Bot"
    await interrupt(self, tosend, embed_color=embed_color, embed_name=embed_name)


async def scoreboard(self, all_players=False):
    self.lock = True
    tosend = show.display_scoreboard(self.bot, all_players=all_players)
    await interrupt(self, tosend, embed_color=0x4200d4, embed_name="Scoreboard")


async def categories(self):
    self.lock = True
    tosend = show.display_categories(self.bot)
    await interrupt(self, tosend, embed_color=0xB315A8, embed_name="Categories")


async def category(self, context):
    self.lock = True

    args = get_command_args(context)
    category = ' '.join(args)
    category = unescape(category.strip())
    if len(args) < 1:
        tosend = 'Use !category <category>'
        await interrupt(self, tosend, embed_color=0xD81948, embed_name="ERROR")
        return

    tosend = show.display_category(category, self.bot)
    embed_name = f"Category {category}"
    await interrupt(self, tosend, embed_color=0xB315A8, embed_name=embed_name)


async def who_solved(self, context):
    self.lock = True

    args = get_command_args(context)
    challenge = ' '.join(args)
    challenge_selected = unescape(challenge.strip())
    if not challenge_selected:
        tosend = 'Use !who_solved <challenge>'
        await interrupt(self, tosend, embed_color=0xD81948, embed_name="ERROR")
        return

    tosend = show.display_who_solved(self.bot, challenge_selected)
    embed_name = f"Who solved {challenge_selected} ?"
    await interrupt(self, tosend, embed_color=0x29C1C5, embed_name=embed_name)


async def problem(self, context):
    self.lock = True

    args = get_command_args(context)
    challenge = ' '.join(args)
    challenge_selected = unescape(challenge.strip())
    if not challenge_selected:
        tosend = 'Use !problem <challenge>'
        await interrupt(self, tosend, embed_color=0xD81948, embed_name="ERROR")
        return

    tosend = show.display_problem(self.bot, context, challenge_selected)
    if 'Cannot find authors' in tosend:
        embed_name = f'Problem with "{challenge_selected}" ?'
        await interrupt(self, tosend, embed_color=0x29C1C5, embed_name=embed_name)
    else:
        await interrupt(self, tosend, embed_color=None, embed_name=None)


async def display_by_blocks_duration(self, tosend_list, color, duration_msg=''):
    for block in tosend_list:
        print(block)
        tosend = block['msg']

        if block['user'] is None:
            embed_name = f"Challenges solved {duration_msg}"
            tosend = tosend_list[0]['msg']
            await interrupt(self, tosend, embed_color=color, embed_name=embed_name)
            return

        if tosend:
            embed_name = f"Challenges solved by {block['user']} {duration_msg}"
            await interrupt(self, tosend, embed_color=color, embed_name=embed_name)


async def last_days(self, context):
    self.lock = True
    args = get_command_args(context)

    if len(args) < 1 or len(args) > 2:
        tosend = f'Use !solved_last_days <number_of_days> (<username>)'
        await interrupt(self, tosend, embed_color=0xD81948, embed_name="ERROR")
        return

    days_num = args[0]
    if not days_num.isdigit() or int(days_num) < 1:
        tosend = f'<number_of_days> is an integer >= 1.\nUse !solved_last_days <number_of_days> (<username>)'
        await interrupt(self, tosend, embed_color=0xD81948, embed_name="ERROR")
        return

    days_num = int(days_num)
    hours = f'{days_num * 24}h'
    username = None
    if len(args) == 2:
        username = unescape(args[1]).strip()

    tosend_list = show.display_last_days(self.bot, days_num, username)
    await display_by_blocks_duration(self, tosend_list, 0x00C7FF, duration_msg=f'since last {hours}')


async def display_by_blocks_diff(self, tosend_list, color):
    for block in tosend_list:
        if block['msg']:
            embed_name = f"Challenges solved by {block['user']} "
            await interrupt(self, block['msg'], embed_color=color, embed_name=embed_name, keep_locking=True)


async def diff(self, context):
    self.lock = True
    args = get_command_args(context)

    if len(args) != 2:
        tosend = 'Use !diff <username1> <username2>'
        await interrupt(self, tosend, embed_color=0xD81948, embed_name="ERROR")
        return

    pseudo1, pseudo2 = args[0], args[1]
    tosend_list = show.display_diff(self.bot, pseudo1, pseudo2)
    await display_by_blocks_diff(self, tosend_list, 0xFF00FF)


async def diff_with(self, context):
    self.lock = True
    args = get_command_args(context)

    if len(args) != 1:
        tosend = 'Use !diff_with <username>'
        await interrupt(self, tosend, embed_color=0xD81948, embed_name="ERROR")
        return

    pseudo = args[0]
    tosend_list = show.display_diff_with(self.bot, pseudo)
    await display_by_blocks_diff(self, tosend_list, 0xFF00FF)


async def flush(self, context):
    self.lock = True
    embed_color, embed_name = 0xD81948, 'FLUSH'
    tosend = f'{context.author} just launched !flush command.'
    await interrupt(self, tosend, embed_color=embed_color, embed_name=embed_name)
    tosend = await show.display_flush(self.channel, context)
    await interrupt(self, tosend, embed_color=embed_color, embed_name=embed_name)


async def cron(self):
    self.lock = True
    name, tosend_cron = await show.display_cron(self.bot)
    if tosend_cron is not None:
        await interrupt(self, tosend_cron, embed_color=0xFFCC00, embed_name=name)
    self.lock = False