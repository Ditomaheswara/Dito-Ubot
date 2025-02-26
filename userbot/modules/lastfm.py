# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
# Recode by @mrismanaziz
# FROM ZELDA USERBOT <https://github.com/fhmyngrh/Zelda-Ubot>
# t.me/SharingUserbot & t.me/Lunatic0de
#

from asyncio import sleep
from os import environ
from re import sub
from sys import setrecursionlimit
from urllib import parse

from pylast import MalformedResponseError, User, WSError
from telethon.errors import AboutTooLongError
from telethon.errors.rpcerrorlist import FloodWaitError
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.users import GetFullUserRequest

from userbot import BIO_PREFIX, BOTLOG, BOTLOG_CHATID
from userbot import CMD_HANDLER as cmd
from userbot import CMD_HELP, DEFAULT_BIO, LASTFM_USERNAME, bot, lastfm
from userbot.events import zelda_cmd

# =================== CONSTANT ===================
LFM_BIO_ENABLED = "**last.fm current music to bio is now enabled.**"
LFM_BIO_DISABLED = (
    "**last.fm current music to bio is now disabled. Bio reverted to default.**"
)
LFM_BIO_RUNNING = "**last.fm current music to bio is already running.**"
LFM_ERR_NO_OPT = "**No option specified.**"
LFM_LOG_ENABLED = "**last.fm logging to bot log is now enabled.**"
LFM_LOG_DISABLED = "**last.fm logging to bot log is now disabled.**"
ERROR_MSG = "**last.fm module halted, got an unexpected error.**"

ARTIST = 0
SONG = 0
USER_ID = 0

BIOPREFIX = BIO_PREFIX or None
LASTFMCHECK = False
RUNNING = False
LastLog = False
# ================================================


@bot.on(zelda_cmd(outgoing=True, pattern=r"lastfm$"))
async def last_fm(lastFM):
    """For .lastfm command, fetch scrobble data from last.fm."""
    await lastFM.edit("`Processing...`")
    preview = None
    playing = User(LASTFM_USERNAME, lastfm).get_now_playing()
    username = f"https://www.last.fm/user/{LASTFM_USERNAME}"
    if playing is not None:
        try:
            image = User(LASTFM_USERNAME, lastfm).get_now_playing().get_cover_image()
        except IndexError:
            image = None
        try:
            tags = await gettags(isNowPlaying=True, playing=playing)
        except WSError as err:
            return await lastFM.edit(f"**{err}**")
        rectrack = parse.quote(f"{playing}")
        rectrack = sub("^", "https://open.spotify.com/search/", rectrack)
        if image:
            output = (
                f"[‎]({image})[{LASTFM_USERNAME}]({username}) __is now listening to:"
                f"__\n\n• [{playing}]({rectrack})\n`{tags}`"
            )
            preview = True
        else:
            output = (
                f"[{LASTFM_USERNAME}]({username}) __is now listening to:"
                f"__\n\n• [{playing}]({rectrack})\n`{tags}`"
            )
    else:
        recent = User(LASTFM_USERNAME, lastfm).get_recent_tracks(limit=5)
        playing = User(LASTFM_USERNAME, lastfm).get_now_playing()
        output = f"[{LASTFM_USERNAME}]({username}) __was last listening to:__\n\n"
        for i, track in enumerate(recent):
            print(i)
            printable = await artist_and_song(track)
            try:
                tags = await gettags(track)
            except WSError as err:
                return await lastFM.edit(f"**{err}**")
            rectrack = parse.quote(str(printable))
            rectrack = sub("^", "https://open.spotify.com/search/", rectrack)
            output += f"• [{printable}]({rectrack})\n"
            if tags:
                output += f"`{tags}`\n\n"
    if preview is not None:
        await lastFM.edit(f"{output}", parse_mode="md", link_preview=True)
    else:
        await lastFM.edit(f"{output}", parse_mode="md")


async def gettags(track=None, isNowPlaying=None, playing=None):
    if isNowPlaying:
        tags = playing.get_top_tags()
        arg = playing
        if not tags:
            tags = playing.artist.get_top_tags()
    else:
        tags = track.track.get_top_tags()
        arg = track.track
    if not tags:
        tags = arg.artist.get_top_tags()
    tags = "".join([" #" + t.item.__str__() for t in tags[:5]])
    tags = sub("^ ", "", tags)
    tags = sub(" ", "_", tags)
    tags = sub("_#", " #", tags)
    return tags


async def artist_and_song(track):
    return f"{track.track}"


async def get_curr_track(lfmbio):
    global ARTIST
    global SONG
    global LASTFMCHECK
    global RUNNING
    global USER_ID
    oldartist = ""
    oldsong = ""
    while LASTFMCHECK:
        try:
            if USER_ID == 0:
                USER_ID = (await lfmbio.client.get_me()).id
            user_info = await bot(GetFullUserRequest(USER_ID))
            RUNNING = True
            playing = User(LASTFM_USERNAME, lastfm).get_now_playing()
            SONG = playing.get_title()
            ARTIST = playing.get_artist()
            oldsong = environ.get("oldsong", None)
            oldartist = environ.get("oldartist", None)
            if playing is not None and SONG != oldsong and ARTIST != oldartist:
                environ["oldsong"] = str(SONG)
                environ["oldartist"] = str(ARTIST)
                if BIOPREFIX:
                    lfmbio = f"{BIOPREFIX} 🎧: {ARTIST} - {SONG}"
                else:
                    lfmbio = f"🎧: {ARTIST} - {SONG}"
                try:
                    if BOTLOG and LastLog:
                        await bot.send_message(
                            BOTLOG_CHATID, f"**Attempted to change bio to**\n{lfmbio}"
                        )
                    await bot(UpdateProfileRequest(about=lfmbio))
                except AboutTooLongError:
                    try:
                        SONG = sub(r"\[.*\]", "", SONG)
                        lfmbio = f"🎧: {ARTIST} - {SONG}"
                        if BOTLOG and LastLog:
                            await bot.send_message(
                                BOTLOG_CHATID,
                                f"**Attempted to change bio to**\n{lfmbio}",
                            )
                        await bot(UpdateProfileRequest(about=lfmbio))
                    except AboutTooLongError:
                        try:
                            SONG = sub(r"\(.*\)", "", SONG)
                            lfmbio = f"🎧: {ARTIST} - {SONG}"
                            if BOTLOG and LastLog:
                                await bot.send_message(
                                    BOTLOG_CHATID,
                                    f"**Attempted to change bio to**\n{lfmbio}",
                                )
                            await bot(UpdateProfileRequest(about=lfmbio))
                        except AboutTooLongError:
                            short_bio = f"🎧: {SONG}"
                            if BOTLOG and LastLog:
                                await bot.send_message(
                                    BOTLOG_CHATID,
                                    f"**Attempted to change bio to**\n{lfmbio}",
                                )
                            await bot(UpdateProfileRequest(about=short_bio))
            if playing is None and user_info.about != DEFAULT_BIO:
                await sleep(6)
                await bot(UpdateProfileRequest(about=DEFAULT_BIO))
                if BOTLOG and LastLog:
                    await bot.send_message(
                        BOTLOG_CHATID, f"**Reset bio back to**\n{DEFAULT_BIO}"
                    )
        except AttributeError:
            try:
                if user_info.about != DEFAULT_BIO:
                    await sleep(6)
                    await bot(UpdateProfileRequest(about=DEFAULT_BIO))
                    if BOTLOG and LastLog:
                        await bot.send_message(
                            BOTLOG_CHATID, f"**Reset bio back to**\n{DEFAULT_BIO}"
                        )
            except FloodWaitError as err:
                if BOTLOG and LastLog:
                    await bot.send_message(
                        BOTLOG_CHATID, f"**Error changing bio:**\n{err}"
                    )
        except FloodWaitError as err:
            if BOTLOG and LastLog:
                await bot.send_message(BOTLOG_CHATID, f"**Error changing bio:**\n{err}")
        except (WSError, MalformedResponseError, AboutTooLongError) as err:
            if BOTLOG and LastLog:
                await bot.send_message(BOTLOG_CHATID, f"**Error changing bio:**\n{err}")
        await sleep(10)
    RUNNING = False


@bot.on(zelda_cmd(outgoing=True, pattern=r"lastbio (on|off)"))
async def lastbio(lfmbio):
    arg = lfmbio.pattern_match.group(1).lower()
    global LASTFMCHECK
    global RUNNING
    if arg == "on":
        setrecursionlimit(700000)
        if not LASTFMCHECK:
            LASTFMCHECK = True
            environ["errorcheck"] = "0"
            await lfmbio.edit(LFM_BIO_ENABLED)
            await sleep(4)
            await get_curr_track(lfmbio)
        else:
            await lfmbio.edit(LFM_BIO_RUNNING)
    elif arg == "off":
        LASTFMCHECK = False
        RUNNING = False
        await bot(UpdateProfileRequest(about=DEFAULT_BIO))
        await lfmbio.edit(LFM_BIO_DISABLED)
    else:
        await lfmbio.edit(LFM_ERR_NO_OPT)


@bot.on(zelda_cmd(outgoing=True, pattern=r"lastlog (on|off)"))
async def lastlog(lstlog):
    arg = lstlog.pattern_match.group(1).lower()
    global LastLog
    LastLog = False
    if arg == "on":
        LastLog = True
        await lstlog.edit(LFM_LOG_ENABLED)
    elif arg == "off":
        LastLog = False
        await lstlog.edit(LFM_LOG_DISABLED)
    else:
        await lstlog.edit(LFM_ERR_NO_OPT)


CMD_HELP.update(
    {
        "lastfm": f"**Plugin : **`lastfm`\
        \n\n  •  **Syntax :** `{cmd}lastfm`\
        \n  •  **Function : **Menampilkan trek scrobbling saat ini atau scrobble terbaru jika tidak ada yang diputar.\
        \n\n  •  **Syntax :** `{cmd}lastbio` <on/off>\
        \n  •  **Function : **Mengaktifkan / Menonaktifkan pemutaran last.fm saat ini ke bio.\
        \n\n  •  **Syntax :** `{cmd}lastlog` <on/off>\
        \n  •  **Function : **Mengaktifkan / Menonaktifkan bio logging last.fm di grup bot-log.\
    "
    }
)
