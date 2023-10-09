# import necessary modules

#Based implementation on https://github.com/EthanRosenthal/discovered-weekly/blob/main/discovered_weekly.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import logging
import datetime
import sys
from spotipy.oauth2 import SpotifyOAuth


logger = logging.getLogger("discovered-weekly")
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter(fmt="%(asctime)s : %(levelname)s : %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def main():
    load_dotenv()

    CLIENT_ID = os.environ["CLIENT_ID"]
    CLIENT_SECRET = os.environ["CLIENT_SECRET"]
    REDIRECT_URI = os.environ["REDIRECT_URI"]
    REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]
    DISCOVER_WEEKLY_ID = os.environ["DISCOVER_WEEKLY_ID"]
    ALL_DISCOVERED_PLAYLIST_ID = os.environ["ALL_DISCOVERED_PLAYLIST_ID"]
    USER_ID = os.environ["USERNAME"]
    logger.info("Start discover weekly archiving")

    client = load_client(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, USER_ID, REFRESH_TOKEN)

    #parse this week's music
    playlist_date, dw_uris = parse_current_week(client, DISCOVER_WEEKLY_ID)
    
    logger.info(f"Found this week's playlist for {playlist_date}")

    logger.info("Adding to all time playlist")
    add_to_all_time_playlist(client, dw_uris, ALL_DISCOVERED_PLAYLIST_ID)

    logger.info("Adding to the weekly archive")
    add_to_weekly_archive(client, USER_ID, playlist_date, dw_uris)

    logger.info("Done discover weekly archiving")


def load_client(client_id, client_secret, redirect_uri, username, refresh_token):
    scopes = ["playlist-read-private", "playlist-modify-private"]

    #authenticate with creds
    auth_manager = SpotifyOAuth(
        scope=scopes,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        username=username
    )

    auth_manager.refresh_access_token(refresh_token=refresh_token)
    client = spotipy.Spotify(auth_manager=auth_manager)
    return client

def parse_current_week(client, discover_weekly_id):

    #Discover Weekly Items and parse for info
    dw_items = client.playlist_items(discover_weekly_id)
    playlist_created = datetime.datetime.strptime(
        dw_items["items"][0]["added_at"], "%Y-%m-%dT%H:%M:%Sz"
    )

    playlist_date = playlist_created.strftime("%Y-%m-%d")
    dw_uris = [item["track"]["uri"] for item in dw_items["items"]]
    return playlist_date, dw_uris

def add_to_all_time_playlist(client, dw_uris, all_discovered_playlist_id):
    # First, add to the all time DW

    # Determine total number of tracks
    total = client.playlist(all_discovered_playlist_id)["tracks"]["total"]
    # Now, query for the last 5 tracks
    offset = max(0, total - 5)
    last_five = client.playlist_items(all_discovered_playlist_id, offset=offset)
    # If the last 5 tracks match the last 5 from the current week, then we've already added
    # this week's playlist.
    match = len(last_five["items"]) >= 5 and all(
        [
            dw_uri == item["track"]["uri"]
            for dw_uri, item in zip(dw_uris[-5:], last_five["items"])
        ]
    )
    if match:
        logger.info(
            "This script has already been run for this week."
            " Skipping add to all time playlist."
        )
        return

    client.playlist_add_items(all_discovered_playlist_id, dw_uris)

def add_to_weekly_archive(client, username, playlist_date, dw_uris):
    # Second, create the weekly archive playlist
    this_weeks_playlist = f"Discovered Week {playlist_date}"

    # Need to search all user's playlists to see if this one already exists...
    limit = 50
    offset = 0
    total = 1e9
    found = False

    while offset + limit < total and not found:
        playlists = client.user_playlists(username, limit=limit, offset=offset)
        total = playlists["total"]
        found = any(
            [item["name"] == this_weeks_playlist for item in playlists["items"]]
        )
        offset += limit

    if found:
        logger.info(
            "This script has already been run for this week."
            " Skipping creation of weekly archive playlist."
        )
        return

    logger.info(f"Creating this week's archive playlist: {this_weeks_playlist}")
    saved_playlist = client.user_playlist_create(
        username, this_weeks_playlist, public=False
    )
    client.playlist_add_items(saved_playlist["id"], dw_uris)
    logger.info("Done creating this week's archive playlist.")

if __name__ == "__main__":
    main()
