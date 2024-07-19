import aiohttp
import asyncio
import base64
import tweepy
from time import sleep
import os
from dotenv import load_dotenv

load_dotenv()

async def get_access_token(session):
    client_id_spotify = os.getenv('CLIENT_ID_SPOTIFY')
    client_secret_spotify = os.getenv('CLIENT_SECRET_SPOTIFY')
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_header = base64.b64encode(f"{client_id_spotify}:{client_secret_spotify}".encode()).decode()

    auth_data = {
        'grant_type': 'client_credentials'
    }

    auth_headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        async with session.post(auth_url, headers=auth_headers, data=auth_data) as response:
            if response.status == 200:
                data = await response.json()
                return data['access_token']
            else:
                raise Exception('Não foi possível obter o token de acesso')
    except Exception as e:
        print(f"Erro ao obter token de acesso: {e}")
        return None


async def get_top_tracks(session, access_token, playlist_id, limit=33):
    top_charts_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    try:
        async with session.get(top_charts_url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data['items'][:limit]
            else:
                raise Exception('Não foi possível obter o Top 50 do Spotify')
    except Exception as e:
        print(f"Erro ao obter Top {limit}: {e}")
        return None


async def tweet_thread(title, tracks):
    bearer_token_twitter = os.getenv('BEARER_TOKEN_TWITTER')
    consumer_key_twitter = os.getenv('CONSUMER_KEY_TWITTER')
    consumer_secret_twitter = os.getenv('CONSUMER_SECRET_TWITTER')
    access_token_twitter = os.getenv('ACCESS_TOKEN_TWITTER')
    access_token_secret_twitter = os.getenv('ACCESS_TOKEN_SECRET_TWITTER')

    client = tweepy.Client(bearer_token_twitter, consumer_key_twitter, consumer_secret_twitter, access_token_twitter, access_token_secret_twitter)
    auth = tweepy.OAuth1UserHandler(consumer_key_twitter, consumer_secret_twitter, access_token_twitter, access_token_secret_twitter)
    api = tweepy.API(auth)

    previous_tweet_id = None

    # Post the title as the first tweet
    title_tweet = client.create_tweet(text=title)
    previous_tweet_id = title_tweet.data['id']

    # Post the tracks in a thread
    max_tweet_length = 280
    tweet_content = ""

    for idx, item in enumerate(tracks, start=1):
        track = item['track']
        track_info = f"{idx}. {track['name']} - {track['artists'][0]['name']}\n"

        if len(tweet_content) + len(track_info) > max_tweet_length:
            tweet = client.create_tweet(text=tweet_content.strip(), in_reply_to_tweet_id=previous_tweet_id)
            previous_tweet_id = tweet.data['id']
            tweet_content = ""

        tweet_content += track_info

    if tweet_content:
        client.create_tweet(text=tweet_content.strip(), in_reply_to_tweet_id=previous_tweet_id)


def format_tracks(tracks, max_length=280):
    formatted_tracks = []
    total_length = 0

    for idx, item in enumerate(tracks):
        track = item['track']
        track_info = f"{idx + 1}. {track['name']} - {track['artists'][0]['name']}\n"
        track_length = len(track_info)

        if total_length + track_length <= max_length:
            formatted_tracks.append(track_info)
            total_length += track_length
        else:
            break

    return "".join(formatted_tracks)


async def main():
    while True:
        async with aiohttp.ClientSession() as session:
            access_token = await get_access_token(session)
            if access_token:
                # Top 33 Global
                global_playlist_id = '37i9dQZEVXbMDoHDwVN2tF'
                global_top_33_tracks = await get_top_tracks(session, access_token, global_playlist_id, 33)
                if global_top_33_tracks:
                    await tweet_thread('Top 33 Global Spotify', global_top_33_tracks)

                # Top 33 Brasil
                brasil_playlist_id = '37i9dQZEVXbMXbN3EUUhlg'
                brasil_top_33_tracks = await get_top_tracks(session, access_token, brasil_playlist_id, 33)
                if brasil_top_33_tracks:
                    await tweet_thread('Top 33 Brasil Spotify', brasil_top_33_tracks)
        
        await asyncio.sleep(24 * 60 * 60)  # espere por 24 horas

if __name__ == '__main__':
    asyncio.run(main())
