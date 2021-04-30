import spotipy
from spotipy.oauth2 import SpotifyOAuth
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument("username")
parser.add_argument("playlist_name")

args = parser.parse_args()

def main():
    username = args.username
    playlist_name = args.playlist_name

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="INSERT_CLIENT_ID",
                                                   client_secret="INSERT_CLIENT_SECRET",
                                                   redirect_uri="http://localhost:8888/callback",
                                                   scope="user-library-modify playlist-modify-public"))
    explicit_songs = 0
    search_time = 0
    saved_id = ""
    user_id = sp.user(username)['id']
    playlist = None  # assign a variable that will be playlist that we clean

    # loops through the users followed playlists to check for already cleaned playlists of same name
    for item in sp.current_user_playlists()['items']:
        if playlist_name + ' [clean]' in item['name']:
            saved_id = item['id']  # saves id (playlist should be deleted when unfollowed, but issue with rapidly deleting and remaking playlist of same name leaves "ghost" playlists)
            sp.current_user_unfollow_playlist(saved_id)  # actually unfollows the playlist so it disappears from users library
        if playlist_name in item['name']:
            playlist = item

    if playlist is None:
        playlist_search = sp.search(playlist_name, type='playlist')  # fetches search results for playlist_name
        for playlist_itr in playlist_search['playlists']['items']:
            if playlist_itr['id'] in saved_id or 'Daily Wellness' in \
                    playlist_itr['name']:  # Daily Wellness check is for bug with Daily Mix cleaning
                continue
            else:
                if playlist_itr['name'].lower() == playlist_name.lower():
                    playlist = playlist_itr
                    break
                elif playlist_itr['name'] is playlist_search['playlists']['items'][len(playlist_search['playlists']['items']) - 1]['name']:
                    print("Playlist not found. Please ensured that you have entered the name of the playlist correctly (case sensitive).")
                    return

    playlist_length = int(playlist['tracks']['total'])
    uri_playlist = sp.user_playlist_create(user_id, playlist['name'] + " [clean]", public=True, collaborative=False,
                                           description="clean version of " + playlist['name'] + ". Please be reminded that any songs without clean versions were not added to the playlist.")[
        'id']

    for i in range(playlist_length):
        track = sp.playlist_items(playlist['uri'], limit=1, offset=i, additional_types=[
            'track'])['items'][0]['track']
        if track['explicit']:
            start_time = time.time()
            track_name = track['name']  # grabs track name for search
            artist = track['artists'][0][
                'name']  # pulls artist name to narrow down results (eliminate extraneous songs of same name)
            search = sp.search(track_name + " artist:" + artist, limit=10,
                               type='track')  # query for all tracks with that name and by that artist

            # keeps list to the top ten results - if a non-explict track is not found within these first ten results, likely no non-explicit track is offered
            for new_track in search['tracks']['items']:
                if new_track['artists'][0]['name'] != track['artists'][0]['name'] or new_track['explicit']:
                    continue
                else:
                    sp.playlist_add_items(uri_playlist, [new_track['uri']])
                    break
            end_time = time.time()
            search_time += end_time - start_time
            explicit_songs += 1
        else:
            sp.playlist_add_items(uri_playlist, [track['uri']])
    if explicit_songs > 0:
        print("Average time to search for a new song: " + str(search_time / explicit_songs) + " seconds.")
    else:
        print("No explicit songs found.")


if __name__ == '__main__':
    main_start_time = time.time()
    main()
    print("Time to process playlist: " + str(time.time() - main_start_time) + " seconds")
