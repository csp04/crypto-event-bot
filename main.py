# ==================================================================
# ------------------------------------------------------------------
# CRYPTO EVENT BOT
# ------------------------------------------------------------------
#
# This bot is created to gather informations about
# crypto events and all happenings in the crypto space.
#
# author - Charlie Porciuncula
# started - May 01, 2021 5:00 PM
#
# API - https://coindar.org/
# ==================================================================

from datetime import datetime, timedelta
import os
import json
# from dotenv import load_dotenv
import discord
from discord.ext import commands

import requests

# load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COINDAR_TOKEN = os.getenv('COINDAR_TOKEN')

coins = []
tags = []


def get(url, params={}):
    params.update({'access_token': COINDAR_TOKEN})
    return requests.get(url, params=params)


def getCoins():
    return get('https://coindar.org/api/v2/coins').json()


def getTags():
    return get('https://coindar.org/api/v2/tags').json()


def getEvents(ids=[], start_date=None, end_date=None):
    events = []
    for page_index in range(100):
        r = get('https://coindar.org/api/v2/events', params={
            'page': page_index + 1,
            'page_size': 100,
            'filter_coins': ','.join([str(id) for id in ids]),
            'filter_date_start': start_date,
            'filter_date_end': end_date
        })
        event_part = r.json()
        if len(event_part) == 0:
            return events

        events += event_part
    return events


def init():
    global coins
    global tags
    coins = getCoins()
    tags = getTags()


print('Initializing...')

init()

print(f'coins: {len(coins)}')
print(f'tags: {len(tags)}')

print('Initialization done.')

bot = commands.Bot(command_prefix='.')


@bot.event
async def on_ready():
    print(f'{bot.user} is connected to the ff. guild:')

    for guild in bot.guilds:
        print(f' - {guild.name}(id: {guild.id})')


@bot.command()
async def sev(ctx, symbols='*', start_date=None, end_date=None):
    symbols_arr = symbols.split(',')
    symbol_ids = []

    if symbols_arr[0] != '*':
        await ctx.send(f'Checking symbols: {" ".join(symbols_arr)}')
        for s in symbols_arr:
            for c in coins:
                if c['symbol'] == s:
                    symbol_ids.append({
                        'id': c['id'],
                        'symbol': s,
                        'name': c['name'],
                        'thumbnail': c['image_64']
                    })

    if symbols_arr[0] != '*' and len(symbol_ids) == 0:
        await ctx.send('Invalid symbol/s.')
    else:
        if start_date == None:
            start_date = datetime.today().strftime('%Y-%m-%d')

        if len(symbol_ids) != 0:
            for s in symbol_ids:
                events = getEvents([s['id']],
                                   start_date=start_date, end_date=end_date)

                if len(events) == 0:
                    arg = {
                        'symbol': s['symbol'],
                        'name': s['name'],
                        'caption': 'No event found.',
                        'thumbnail': s['thumbnail'],
                    }
                    embed = createEmbedMessageForEvent(arg)
                    await ctx.send(embed=embed)
                else:
                    for e in events:
                        tag = [x['name']
                               for x in tags if str(x['id']) == e['tags']]

                        arg = {
                            'symbol': s['symbol'],
                            'name': s['name'],
                            'caption': e['caption'],
                            'thumbnail': s['thumbnail'],
                            'date_start': e['date_start'],
                            'source': e['source'],
                            'tag': None if len(tags) == 0 else tag[0]
                        }

                        embed = createEmbedMessageForEvent(arg)

                        await ctx.send(embed=embed)
        else:
            if end_date == None:
                end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=7)
                            ).strftime('%Y-%m-%d')

            events = getEvents(start_date=start_date, end_date=end_date)
            if len(events) == 0:
                arg = {
                    'symbol': s['symbol'],
                    'name': s['name'],
                    'caption': 'No event found.',
                    'thumbnail': s['thumbnail'],
                }
                embed = createEmbedMessageForEvent(arg)
                await ctx.send(embed=embed)
            else:

                for e in events:
                    s = None
                    for c in coins:
                        if c['id'] == e['coin_id']:
                            s = {
                                'symbol': c['symbol'],
                                'name': c['name'],
                                'thumbnail': c['image_64']
                            }
                            break

                    tag = [x['name']
                           for x in tags if str(x['id']) == e['tags']]

                    arg = {
                        'symbol': s['symbol'],
                        'name': s['name'],
                        'caption': e['caption'],
                        'thumbnail': s['thumbnail'],
                        'date_start': e['date_start'],
                        'source': e['source'],
                        'tag': None if len(tags) == 0 else tag[0]
                    }
                    embed = createEmbedMessageForEvent(arg)

                    await ctx.send(embed=embed)

    await ctx.send('`Send events done.`')


def createEmbedMessageForEvent(arg):
    embed = discord.Embed(
        title=f'({arg["symbol"]}) {arg["name"]}', description=arg['caption'], color=0xFF5733)

    if 'thumbnail' in arg:
        embed.set_thumbnail(url=arg['thumbnail'])

    if 'date_start' in arg:
        embed.add_field(
            name='When', value=arg['date_start'], inline=False)

    if 'tag' in arg:
        embed.add_field(name='Tag', value=arg['tag'])

    if 'source' in arg:
        embed.add_field(
            name='Source', value=arg['source'], inline=False)

    return embed


@bot.command()
async def cid(ctx, symbol):

    for c in coins:
        if c['symbol'] == symbol:
            await ctx.send(f"({c['symbol']}) {c['name']} \n id: {c['id']}")


@bot.command()
async def rc(ctx):
    await ctx.send('`Refreshing...`')
    init()
    await ctx.send('`Done...`')


@bot.command(aliases=['h'])
async def _help(ctx):
    msg_fmt = '```\n{content}\n```'

    content = 'Crypto Event Bot powered by Coindar\n'
    content += 'List of commands:\n - '

    commands = [
        '.sev [* | [symbols,]] [start date yyyy-mm-dd] [end date yyyy-mm-dd] - send events',
        '.cid [symbol] - get id for symbol',
        '.rc - refresh coins',
        '.h - list all commands']

    content += '\n - '.join(commands)

    content = msg_fmt.replace('{content}', content)

    await ctx.send(content)

print('Connecting...')
bot.run(DISCORD_TOKEN)
