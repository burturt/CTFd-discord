import sys
from html import unescape
from typing import Dict, List, Optional

import discord
from discord.ext import commands

import bot.display.show as show
from bot import log
from bot.constants import DB_URI, BOT_CHANNEL, OTHER_CHANNELS, CTFD_MODE, CATCH_MODE
from bot.manage.discord_data import get_command_args, get_channel


def display(part: str) -> None:
    lines = part.split('\n')
    for line in lines:
        print(line)


async def interrupt(channel: discord.channel.TextChannel, message: str, embed_color: Optional[int] = None,
                    embed_name: Optional[str] = None) -> None:
    if channel.id != BOT_CHANNEL and str(channel) not in OTHER_CHANNELS and channel.type != discord.ChannelType.private:  # prevent to respond if message/command is not sent from BOT_CHANNEL
        log.warn(f'Unexpected channel != {BOT_CHANNEL}', channel=str(channel))
        return
    parts = show.display_parts(message)
    for part in parts:

        display(part)
        if embed_color is None or embed_name is None:
            await channel.send(part)
        else:
            embed = discord.Embed(color=embed_color)
            embed.add_field(name=embed_name, value=part, inline=False)
            await channel.send(embed=embed)


def check(bot: commands.bot.Bot) -> Optional[discord.channel.TextChannel]:
    channel = get_channel(bot)
    if channel is None:
        log.warn(f'Unexpected discord channel name', BOT_CHANNEL=BOT_CHANNEL)
        log.warn('Please configuration in ./bot/constants.py')
        sys.exit(0)

    if not bot.db.engine.table_names():
        log.warn('Cannot connect to database', DB_URI=DB_URI)
        log.warn('Please configuration in ./bot/constants.py')
        sys.exit(0)

    if CTFD_MODE not in ['users', 'teams'] or CATCH_MODE not in ['all', 'user', 'admin']:
        log.warn('Unexpected configuration', CATCH_MODE=CATCH_MODE, CTFD_MODE=CTFD_MODE)
        log.warn('Please configuration in ./bot/constants.py')
        sys.exit(0)

    return channel


async def ready(bot: commands.bot.Bot) -> None:
    channel = check(bot)
    bot.channel = channel  # necessary from cron tasks, context.channel is used in others functions
    log.info('CTFdBot is ready!')


async def scoreboard(context: commands.context.Context, all_players=False) -> None:
    to_send = show.display_scoreboard(context.bot.db, all_players=all_players)
    if not to_send:
        to_send = 'No users have resolved at least one challenge at this time'
    await interrupt(context.channel, to_send, embed_color=0xeed37b, embed_name='Scoreboard')


async def categories(context: commands.context.Context) -> None:
    to_send = show.display_categories(context.bot.db)
    if not to_send:
        to_send = 'There are no categories at this time'
    await interrupt(context.channel, to_send, embed_color=0xB315A8, embed_name='Categories')


async def category(context: commands.context.Context) -> None:
    args = get_command_args(context)
    category_name = ' '.join(args)
    category_name = unescape(category_name.strip())
    if len(args) < 1:
        to_send = f'Use {context.bot.command_prefix}{context.command} {context.command.help.strip()}'
        await interrupt(context.channel, to_send, embed_color=0xD81948, embed_name="ERROR")
        return

    to_send = show.display_category(context.bot.db, category_name)
    embed_name = f"Category {category_name}"
    await interrupt(context.channel, to_send, embed_color=0x90e173, embed_name=embed_name)


async def who_solved(context: commands.context.Context) -> None:
    args = get_command_args(context)
    challenge = ' '.join(args)
    challenge_selected = unescape(challenge.strip())
    if not challenge_selected:
        to_send = f'Use {context.bot.command_prefix}{context.command} {context.command.help.strip()}'
        await interrupt(context.channel, to_send, embed_color=0xD81948, embed_name="ERROR")
        return

    to_send = show.display_who_solved(context.bot.db, challenge_selected)
    embed_name = f"Solves for {challenge_selected}"
    await interrupt(context.channel, to_send, embed_color=0x29C1C5, embed_name=embed_name)


async def problem(context: commands.context.Context) -> None:
    args = get_command_args(context)
    challenge = ' '.join(args)
    challenge_selected = unescape(challenge.strip())
    if not challenge_selected:
        to_send = f'Use {context.bot.command_prefix}{context.command} {context.command.help.strip()}'
        await interrupt(context.channel, to_send, embed_color=0xD81948, embed_name="ERROR")
        return

    to_send = show.display_problem(context.bot.db, context, challenge_selected)
    if to_send.startswith('Ping:'):
        await interrupt(context.channel, to_send, embed_color=None, embed_name=None)
    else:
        embed_name = f'Problem with "{challenge_selected}" ?'
        await interrupt(context.channel, to_send, embed_color=0x29C1C5, embed_name=embed_name)


async def recent(context: commands.context.Context) -> None:
    args = get_command_args(context)

    days_num = args[0] if len(args) > 0 else 1

    try:
        days_num = float(days_num)
        if days_num < 0.1:
            raise ValueError('days_num invalid')
    except:
        to_send = f'<number_of_days> is a number >= 0.1.\nUse {context.bot.command_prefix}recent {context.command.help.strip()}'
        await interrupt(context.channel, to_send, embed_color=0xD81948, embed_name="ERROR")
        return

    username = None
    if len(args) == 2:
        username = unescape(args[1]).strip()

    to_send = show.display_recent(context.bot.db, days_num, username)
    await interrupt(context.channel, to_send, 0x00C7FF, embed_name=f'Solves in the last {round(days_num * 24, 2)} hours')


async def display_by_blocks_diff(context: commands.context.Context, to_send_list: List[Dict[str, str]], color: int) \
        -> None:
    if not any([block['msg'] for block in to_send_list]):  # msg is empty for all blocks
        to_send = 'There is no difference of challenge solved between those players.'
        await interrupt(context.channel, to_send, embed_color=color, embed_name='DIFF')
        return
    for block in to_send_list:
        if block['msg']:
            embed_name = f"Challenges solved by {block['user']} "
            await interrupt(context.channel, block['msg'], embed_color=color, embed_name=embed_name)


async def diff(context: commands.context.Context) -> None:
    args = get_command_args(context)

    if len(args) != 2:
        to_send = f'Use {context.bot.command_prefix}{context.command} {context.command.help.strip()}'
        await interrupt(context.channel, to_send, embed_color=0xD81948, embed_name="ERROR")
        return

    pseudo1, pseudo2 = args[0], args[1]
    to_send_list = show.display_diff(context.bot.db, pseudo1, pseudo2)
    await display_by_blocks_diff(context, to_send_list, 0xFF00FF)


async def flush(context: commands.context.Context) -> None:
    embed_color, embed_name = 0xD81948, 'FLUSH'
    to_send = f'{context.message.author} just launched {context.bot.command_prefix}flush command.'
    await interrupt(context.channel, to_send, embed_color=embed_color, embed_name=embed_name)
    to_send = await show.display_flush(context)
    await interrupt(context.channel, to_send, embed_color=embed_color, embed_name=embed_name)


async def cron(bot: commands.bot.Bot) -> None:
    name, to_send_cron, embed_color = await show.display_cron(bot.db)
    if to_send_cron:
        await interrupt(bot.channel, to_send_cron, embed_color=embed_color, embed_name=name)

async def help(bot: commands.bot.Bot) -> None:
    if (bot.channel.id != BOT_CHANNEL and str(bot.channel) not in OTHER_CHANNELS and bot.channel.type != discord.ChannelType.private:  # prevent to respond if message/command is not sent from BOT_CHANNEL
        log.warn(f'Unexpected channel != {BOT_CHANNEL}', channel=str(bot.channel))
        return
    cp = bot.command_prefix
    about_msg = 'This bot is a [fork](https://github.com/josephsurin/CTFd-discord) of [zteeed\'s CTFd-discord bot](https://github.com/zteeed/CTFd-discord)'
    help_msg = f"""**Available Commands:**
```
{cp}categories                      - lists all challenge categories
{cp}category <category>             - lists challenges in the specified category
{cp}diff <user1> <user2>            - displays the difference of solved challenges between two users
{cp}help                            - displays this message
{cp}scoreboard                      - displays the top 20 teams
{cp}scoreboard_complete             - displays the entire scoreboard
{cp}recent (<num>) (<user>)         - displays recent solves (up to <num> days for a specific <user>)
{cp}who_solved <chall_name>         - displays the solves for the specified challenge
```
"""
    embed = discord.Embed(color=0x90e173)
    embed.add_field(name='About', value=about_msg, inline=False)
    await bot.channel.send(help_msg, embed=embed)
