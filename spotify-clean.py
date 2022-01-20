import spotipy
from spotipy.oauth2 import SpotifyOAuth
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument("username")
parser.add_argument("playlist_name")

args = parser.parse_args()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="INSERT_CLIENT_ID_HERE",
                                               client_secret="INSERT_CLIENT_SECRET_HERE",
                                               redirect_uri="http://localhost:8888/callback",
                                               scope="user-library-modify playlist-modify-public"))

def clean_playlist(playlist_name, username):
    explicit_songs = 0
    search_time = 0
    saved_id = ""

    # loops through the users followed playlists to check for already cleaned playlists
    for item in sp.current_user_playlists()['items']:
        if playlist_name in item['name'] and "[clean]" in item['name'] and username in item['owner']['id']:
            saved_id = item['id']  # saves id (playlist should be deleted when unfollowed, but issue with rapidly deleting and remaking playlist of same name leaves "ghost" playlist
            break

    user_id = sp.user(username)['id']
    playlist_search = sp.search(playlist_name, type='playlist')  # fetches search results for
    playlist = None  # actual playlist that will end up being passed
    for playlist_itr in playlist_search['playlists']['items']:
        if playlist_itr['id'] in saved_id:
            continue
        elif saved_id != "":
            playlist = playlist_itr
            current_playlist_tracks = sp.playlist_items(saved_id, limit=10, additional_types=['track'])['items']
            possible_new_playlist = sp.playlist_items(playlist['id'], limit=10, additional_types=['track'])['items']

            for i in range(0, len(current_playlist_tracks)):
                del current_playlist_tracks[i]['added_at']
                del current_playlist_tracks[i]['added_by']
                del possible_new_playlist[i]['added_at']
                del possible_new_playlist[i]['added_by']

            if current_playlist_tracks == possible_new_playlist:
                return saved_id
            else:
                sp.current_user_unfollow_playlist(saved_id)  # actually unfollows the playlist so it disappears from users library
                break
        else:
            playlist = playlist_itr
            break

    uri_playlist = sp.user_playlist_create(user_id, playlist['name'] + " [clean]", public=True, collaborative=False, description="clean version of " + playlist_search['playlists']['items'][0]['name'] + ". Please be reminded that any songs without clean versions were not added to the playlist.")['id']

    tracks = sp.playlist_items(playlist['uri'], additional_types=[
                          'track'])['items']

    for track in tracks:
        track = track['track']
        if track['explicit']:
            start_time = time.time()
            track_name = track['name']  # grabs track name for search
            artist = track['artists'][0]['name']  # pulls artist name to narrow down results (eliminate extraneous songs of same name)
            search = sp.search(track_name + " artist:" + artist, limit=10, type='track')  # query for all tracks with that name and by that artist

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

    return uri_playlist

def main():
    username = args.username
    playlist_name = args.playlist_name

    avg_danceability = 0.0
    avg_energy = 0.0
    avg_loudness = 0.0
    avg_speechiness = 0.0
    avg_acousticness = 0.0
    avg_instrumentalness = 0.0

    id = clean_playlist(playlist_name, username)
    tracks = sp.playlist_items(id, additional_types=['track'])['items']

    track_uri_list = []

    for track in tracks:
        track_uri_list.append(track['track']['uri'])
    track_stats = sp.audio_features(track_uri_list)
    list_length = len(track_stats)

    for i in range(0, list_length - 1):
        if track_stats[i] is None:
            print(track_uri_list[i])
        else:
            avg_danceability += float(track_stats[i]['danceability'])
            avg_energy += float(track_stats[i]['energy'])
            avg_loudness += track_stats[i]['loudness']
            avg_speechiness += float(track_stats[i]['speechiness'])
            avg_acousticness += float(track_stats[i]['acousticness'])
            avg_instrumentalness += float(track_stats[i]['instrumentalness'])

    print("This playlist has an average danceability of: " + str((avg_danceability / list_length) * 100) + "%")
    print("This playlist has an average energy of: " + str((avg_energy / list_length) * 100) + "%")
    print("This playlist has an average loudness of: " + str(avg_loudness / list_length) + " db")
    print("This playlist has an average speechiness of: " + str((avg_speechiness / list_length) * 100) + "%")
    print("This playlist has an average acousticness of: " + str((avg_acousticness / list_length) * 100) + "%")
    print("This playlist has an average instrumentalness of: " + str((avg_speechiness / list_length) * 100) + "%")


if __name__ == '__main__':
    main()
