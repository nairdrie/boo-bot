# Boo Bot

Boo Bot is a Discord bot that can play music from YouTube and Spotify in your voice channel.

## Requirements

- Python 3.8 or higher
- `discord` and `spotipy` Python packages
- FFmpeg (https://ffmpeg.org/download.html)
- A Spotify Developer account (https://developer.spotify.com/dashboard/applications)

## Setup

1. Clone this repository to your local machine.
2. Install the required Python packages by running `pip install -r requirements.txt` in your terminal or command prompt.
3. Install FFmpeg from the link provided above.
4. Create a new Discord bot and obtain its token. Follow the instructions in the Discord Developer Portal (https://discord.com/developers/applications) to create a bot and obtain its token.
5. Create a new Spotify Developer application and obtain its client ID and client secret. Follow the instructions in the Spotify Developer Dashboard (https://developer.spotify.com/dashboard/applications) to create a new application and obtain its client ID and client secret.
6. Create a new file named `.env` in the root directory of the project.
7. In the `.env` file, add the following lines:

token=DISCORD_BOT_TOKEN
SPOTIFY_CLIENT_ID=SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET=SPOTIFY_CLIENT_SECRET


Replace `DISCORD_BOT_TOKEN`, `SPOTIFY_CLIENT_ID`, and `SPOTIFY_CLIENT_SECRET` with the values obtained in steps 4 and 5.
8. Run the bot by running `python boo_bot.py` in your terminal or command prompt.

## Usage

Boo Bot can be used with the following commands:

- `!join`: Joins the voice channel you are currently in.
- `!leave`: Leaves the voice channel.
- `!play <YouTube URL or search query> or <Spotify URL>`: Plays the audio from a YouTube video or a Spotify song, playlist, or album.
- `!skip`: Skips the current song and plays the next song in the queue.
- `!clear`: Clears the queue.
- `!shuffle`: Shuffles the queue.
- `!pause`: Pauses the audio.
- `!resume`: Resumes the audio.
- `!stop`: Stops the audio and clears the queue.
- `!volume <volume>`: Sets the volume of the audio (0-100).
- `!now_playing`: Displays the title of the currently playing song.

To use the Spotify feature, simply provide a Spotify URL instead of a YouTube URL or search query. Boo Bot can handle Spotify songs, playlists, and albums.

## Acknowledgements

This bot was created with the help of the following libraries:

- `discord.py` (https://github.com/Rapptz/discord.py)
- `yt-dlp` (https://github.com/yt-dlp/yt-dlp)
- `spotipy` (https://github.com/plamere/spotipy)

Thanks to the developers of these libraries for their hard work and contributions to the open-source community!
