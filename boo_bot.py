import os
import re
import random
import asyncio
import discord
import yt_dlp as youtube_dl
from discord.ext import commands
from discord.voice_client import VoiceClient
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
# import speech_recognition as sr
import io

# Load environment variables
load_dotenv()

# Get bot token from environment variables
TOKEN = os.getenv('token')

# Set up Spotify API client using environment variables
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=os.getenv("SPOTIFY_CLIENT_ID"), client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")))

# Set up discord intents
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.messages = True
intents.message_content = True

# Initialize bot with the specified command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Configure YouTube-DL options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -bufsize 2048k',
    'before_options': '-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Dictionary to store song queues for each guild
queues = {}
listen_tasks = {}

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        # Add these two lines to print the filename and FFmpeg command
        print(f"Filename: {filename}")
        print(f"FFmpeg command: ffmpeg {ffmpeg_options['before_options']} -i {filename} {ffmpeg_options['options']}")

        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class DiscordPCMStream(io.BytesIO):
    def __init__(self, guild):
        self.guild = guild
        super().__init__(None)

    def read(self, size):
        data = self.guild.voice_client.source.original.read(size)
        print(f"Data: {data}, Size: {size}")
        return data

async def listen_for_speech(ctx):
    print(-1)
    if not ctx.guild.voice_client:
        return
    # r = sr.Recognizer()
    print(0)
    while not ctx.bot.is_closed():
        print(1)
        if not ctx.voice_client:
            continue
        print(2)
        # ctx.voice_client.start_recording(discord.sinks.MP3Sink(), got_recording, ctx) 
        await asyncio.sleep(5)
        print(3)
        # ctx.voice_client.stop_recording()


async def got_recording(sink, ctx):
    print(4)
    # Here you can access the recorded files:
    recorded_users = [
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]
    await ctx.channel.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.", files=files) 
    return


# Function to play the next song in the queue
async def play_next_song(ctx):
    global queues

    # Check if there are songs in the queue
    if len(queues[ctx.guild.id]) > 0:
        # Get the next song in the queue
        next_song = queues[ctx.guild.id].pop(0)

        # Create a player for the next song and play it
        player = await YTDLSource.from_url(next_song, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(ctx), bot.loop))
        await ctx.send(f'Now playing: {player.title}')


# --------------------------- Bot Events ---------------------------

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print("Connected servers:")
    for guild in bot.guilds:
        print(f"{guild.name} (id: {guild.id})")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    print(f"Message from {message.author}: {message.content}")
    print(f"Content: {message.content}")
    print(f"System Content: {message.system_content}")
    print(f"Clean Content: {message.clean_content}")
    print(f"Embeds: {message.embeds}")
    print(f"Attachments: {message.attachments}")
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error


# --------------------------- Bot Commands ---------------------------
@bot.command()
async def skip(ctx):
    if ctx.voice_client.is_playing():
        # Stop the current song
        ctx.voice_client.stop()
        await ctx.send("Skipped the current song.")
        # Play the next song in the queue
        await play_next_song(ctx)
    else:
        await ctx.send("No song is currently playing.")

@bot.command()
async def clear(ctx):
    global queues

    # Check if there's a queue for the current guild
    if ctx.guild.id in queues:
        # Clear the queue
        queues[ctx.guild.id] = []
        await ctx.send("Queue has been cleared.")
    else:
        await ctx.send("There is no queue to clear.")

@bot.command()
async def shuffle(ctx):
    global queues

    # Check if there's a queue for the current guild
    if ctx.guild.id in queues:
        # Shuffle the queue
        random.shuffle(queues[ctx.guild.id])
        await ctx.send("Queue has been shuffled.")
    else:
        await ctx.send("There is no queue to shuffle.")


@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()

    if ctx.guild.id not in listen_tasks:
        listen_tasks[ctx.guild.id] = ctx.bot.loop.create_task(listen_for_speech(ctx))


@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()
    # await ctx.message.delete()

# Modify the play command to handle Spotify URLs
@bot.command()
async def play(ctx, *, url):
    global queues

    # If the bot is not connected to a voice channel, join the user's voice channel
    if ctx.voice_client is None:
        channel = ctx.author.voice.channel
        await channel.connect()

    # Check if the input is a Spotify URL
    spotify_url_pattern = re.compile(r'(https?://)?(www\.)?open\.spotify\.com/(track|playlist|album)/[A-Za-z0-9]+')
    if spotify_url_pattern.match(url):
        try:
            # Get the content of the Spotify URL
            spotify_item = sp.track(url) if 'track' in url else sp.playlist(url) if 'playlist' in url else sp.album(url)

            if 'playlist' in url or 'album' in url:
                # If it's a playlist or an album, add each song to the queue
                songs = spotify_item['tracks']['items']
                for song in songs:
                    song_title = song['track']['name'] if 'playlist' in url else song['name']
                    artists = ', '.join([artist['name'] for artist in song['track']['artists']]) if 'playlist' in url else ', '.join([artist['name'] for artist in song['artists']])
                    search_query = f"{song_title} {artists}"
                    if ctx.guild.id not in queues:
                        queues[ctx.guild.id] = []
                    queues[ctx.guild.id].append(search_query)
                await ctx.send("All songs have been added to the queue.")
                url = queues[ctx.guild.id].pop(0)
            else:
                # If it's a song, search it on YouTube
                song_title = spotify_item['name']
                artists = ', '.join([artist['name'] for artist in spotify_item['artists']])
                search_query = f"{song_title} {artists}"
                url = search_query
        except Exception as e:
            await ctx.send(f"An error occurred while handling the Spotify URL: {e}")
            return

    # Check if a song is already playing
    if ctx.voice_client.is_playing():
        # Add the new song to the queue
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []
        queues[ctx.guild.id].append(url)
        await ctx.send(f'Added to queue: {url}')
    else:
        # If no song is playing, start playing the requested song
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(ctx), bot.loop))

        await ctx.send(f'Now playing: {player.title}')

@bot.command()
async def pause(ctx):
    ctx.voice_client.pause()
    await ctx.send("Playback paused.")

@bot.command()
async def resume(ctx):
    ctx.voice_client.resume()
    await ctx.send("Playback resumed.")

@bot.command()
async def stop(ctx):
    ctx.voice_client.stop()
    await ctx.send("Playback stopped.")

@bot.command()
async def volume(ctx, volume: int):
    if ctx.voice_client is None:
        return await ctx.send("Not connected to a voice channel.")

    if 0 > volume > 100:
        return await ctx.send("Volume must be between 0 and 100.")

    ctx.voice_client.source.volume = volume / 100
    await ctx.send(f"Volume set to {volume}%.")

@bot.command()
async def now_playing(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        return await ctx.send("No audio is currently playing.")

    source = ctx.voice_client.source
    await ctx.send(f"Now playing: {source.title}")


# --------------------------- Bot Errors ---------------------------
@play.error
async def play_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('You need to provide a YouTube URL or a search query.')
    else:
        await ctx.send(f'An error occurred: {error}')



print("Starting the bot...")
bot.run(TOKEN)