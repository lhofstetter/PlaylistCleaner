import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("username")
parser.add_argument("playlist_name")

args = parser.parse_args()

def main():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="INSERT_CLIENT_ID", client_secret="INSERT_CLIENT_SECRET", redirect_uri="http://localhost:8888/callback", scope="user-library-read user-library-modify playlist-modify-private playlist-modify-public playlist-read-private playlist-modify-public"))
    track_list = []
    playlist_name = args.playlist_name


    user_id = sp.user(args.username)['id']
    playlist_search = sp.search(playlist_name, type='playlist')
    result = playlist_search['playlists']['items'][0]
    playlist_length = int(result['tracks']['total'])
    uri_playlist = sp.user_playlist_create(user_id, playlist_name + " [clean]", public=True, collaborative=False, description="clean version of " + playlist_name)['id']

    tracks_left = playlist_length
    count = 0
    while tracks_left > 0:
        for track in sp.playlist_tracks(result['uri'], offset=(100*count))['items']:
            track_list.append(track['track'])
            tracks_left -= 1

        count += 1

    final_playlist_uris = []

    for track in track_list:
        if track['explicit'] == True:
            track_name = track['name'] # grabs specific track name for new search
            artist = track['artists'][0]['name'] # pulls artist name to narrow down results (eliminate extraneous songs of same name)

            search = sp.search(track_name + " " + artist, type='track') # query for all tracks with that name
            for new_track in search['tracks']['items']:
                if new_track['explicit'] == False: # checks each track in the search results for a clean version
                    final_playlist_uris.append(new_track['uri']) # adds that track to a list with all the tracks that are added to the new playlist
                    break
                else:
                    continue
        else:
            final_playlist_uris.append(track['uri'])

    print(len(final_playlist_uris))

    count = 0
    tracks_left = len(final_playlist_uris)

    while tracks_left > 100:
        sp.user_playlist_add_tracks(user_id, uri_playlist, final_playlist_uris[0+(100*count):100+(100*count)])
        count += 1
        tracks_left -= 100

    sp.user_playlist_add_tracks(user_id, uri_playlist, final_playlist_uris[0+(100*count):100+(100*count)])

if __name__ == '__main__':
    main()
