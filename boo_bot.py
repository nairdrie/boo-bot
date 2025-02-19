import os
import re
import random
import asyncio
import discord
from discord.ext import commands
from discord.voice_client import VoiceClient
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pytube import YouTube
import io
import boto3

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

# Dictionary to store song queues for each guild
queues = {}

class PCMStream(discord.PCMVolumeTransformer):
    def __init__(self, source, *, title, volume=0.5):
        super().__init__(source, volume)
        self.title = title

    @classmethod
    async def from_url(cls, url, *, loop=None, volume=0.5):
        loop = loop or asyncio.get_event_loop()
        yt = await loop.run_in_executor(None, lambda: YouTube(url))
        audio_stream = yt.streams.filter(only_audio=True).first()
        audio_file = audio_stream.download(filename=f"downloads/{yt.video_id}.mp4")
        return cls(discord.FFmpegPCMAudio(audio_file), title=yt.title, volume=volume)

# Function to play the next song in the queue
async def play_next_song(ctx):
    global queues
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        next_song = queues[ctx.guild.id].pop(0)
        player = await PCMStream.from_url(next_song, loop=bot.loop)
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(ctx), bot.loop))
        await ctx.send(f'Now playing: {player.title}')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
    else:
        await ctx.send("You need to be in a voice channel.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command()
async def play(ctx, *, url):
    global queues
    
    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()
    
    if ctx.voice_client.is_playing():
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []
        queues[ctx.guild.id].append(url)
        await ctx.send(f'Added to queue: {url}')
    else:
        async with ctx.typing():
            player = await PCMStream.from_url(url, loop=bot.loop)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(ctx), bot.loop))
        await ctx.send(f'Now playing: {player.title}')

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped the current song.")
        await play_next_song(ctx)

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Playback stopped.")

@bot.command()
async def volume(ctx, volume: int):
    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Volume set to {volume}%.")

@bot.command()
async def now_playing(ctx):
    if ctx.voice_client and ctx.voice_client.source:
        await ctx.send(f"Now playing: {ctx.voice_client.source.title}")
    else:
        await ctx.send("No audio is currently playing.")

print("Starting the bot...")
bot.run(TOKEN)
