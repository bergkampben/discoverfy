"""
Discoverfy index (main) view.

URLs include:
/
"""
import json
import flask
from flask import Flask, request, redirect, render_template, url_for, session
import requests
import base64
import urllib
import discoverfy
import sqlite3
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import apscheduler

#  Client Keys
CLIENT_ID = '15b472bff56a463781420db9f55bcf7d'
CLIENT_SECRET = '100bf466b477416883f8f581f179cd43'

# Spotify URLS
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com'
API_VERSION = 'v1'
SPOTIFY_API_URL = '{}/{}'.format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = 'http://localhost'
PORT = 8000
REDIRECT_URI = '{}:{}/callback'.format(CLIENT_SIDE_URL, PORT)
SCOPE = 'playlist-modify-public playlist-modify-private playlist-read-private user-top-read'


auth_query_parameters = {
    'response_type': 'code',
    'redirect_uri': REDIRECT_URI,
    'scope': SCOPE,
    'client_id': CLIENT_ID
}

def weekly_task():
    with discoverfy.app.app_context():
    #add_user_to_db('wef','12e2')
        database = discoverfy.model.get_db()
        cursor = database.cursor()
        cursor.execute('''
                   SELECT *
                   FROM users
                   ''')
        result = cursor.fetchall()

        # Weekly work for each user
        for i in result:
            print(i)

            # Get new access token using refresh token

            # Create new playlist for user (do_the_thing)

    print ("debug")

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=weekly_task,
    trigger=IntervalTrigger(seconds=5),
    id='main_task',
    name='weekly_task',
    replace_existing=True)
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


@discoverfy.app.route('/', methods=['GET', 'POST'])
def show_index():
    """Display / route."""
    if 'username' in session:
        return redirect(url_for('show_user', user_id=session['username']))
    elif request.method == 'POST':
        url_args = ''
        for key, val in auth_query_parameters.items():
            url_args += '{}={}&'.format(key, val)
        auth_url = '{}?{}'.format(SPOTIFY_AUTH_URL, url_args)
        return redirect(auth_url)
    return render_template('index.html')


def add_user_to_db(user_id, refresh_token):
    database = discoverfy.model.get_db()
    cursor = database.cursor()
    """Add new user to database."""
    cursor.execute('''
                   INSERT INTO users(user_id, refresh_token)
                   VALUES("{}",
                          "{}")
                   '''.format(user_id, refresh_token))


@discoverfy.app.route('/callback/')
def callback():
    """Get authentication tokens."""
    # Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        'grant_type': 'authorization_code',
        'code': str(auth_token),
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    # Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data['access_token']
    refresh_token = response_data['refresh_token']
    token_type = response_data['token_type']
    expires_in = response_data['expires_in']

    # Use the access token to access Spotify API
    authorization_header = {'Authorization':'Bearer {}'.format(access_token)}

    # Get profile data
    user_profile_api_endpoint = '{}/me/'.format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # Get user playlist data
    playlist_api_endpoint = '{}/playlists/'.format(profile_data['href'])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)

    # Add user to database
    try:
        add_user_to_db(profile_data['id'], refresh_token)
        # Save Discover Weekly playlist
        do_the_thing(access_token, profile_data['id'])
    except(sqlite3.IntegrityError) as e:
        print(e)

    return redirect(url_for('show_user', user_id=profile_data['id']))


@discoverfy.app.route('/u/<user_id>/')
def show_user(user_id):
    """Display /u/<user_id> route."""
    return render_template('user.html', user=user_id)


def do_the_thing(playlist_data, access_token, user_id):
    """Save the user's Discover Weekly playlist"""
    post_body = {
        'name': 'Discoverfy',
        'public': False
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization':'Bearer {}'.format(access_token)
    }

    discover_weekly_tracks_link = ''
    discover_weekly_found = False
    while not discover_weekly_found:
        for playlist in playlist_data['items']:
            if playlist['name'] == 'Discover Weekly' and playlist['owner']['id'] == 'spotify':
                discover_weekly_tracks_link = playlist['tracks']['href']
                discover_weekly_found = True
                break

        if playlist_data['next']:
            next_playlist_link = playlist_data['next']
            playlists_response = requests.get(next_playlist_link, headers=headers)
            playlist_data = json.loads(playlists_response.text)


    tracks_response = requests.get(discover_weekly_tracks_link, headers=headers)
    tracks_data = json.loads(tracks_response.text)

    track_uris = []
    for track in tracks_data['items']:
        track_uris.append(track['track']['uri'])

    # Get current Discover Weekly tracks
    # tracks_api_endpoint = '{}/users/{}/playlists/{}/tracks'.format(SPOTIFY_API_URL, user_id, playlist_id)

    # Save tracks to a new playlist
    playlist_api_endpoint = '{}/users/{}/playlists'.format(SPOTIFY_API_URL, user_id)
    playlist_response = requests.post(playlist_api_endpoint, data=json.dumps(post_body), headers=headers)
    playlist_data = json.loads(playlist_response.text)

    new_playlist_id = playlist_data['id']

    post_body = {
        'uris': track_uris
    }

    playlist_tracks_api_endpoint = '{}/users/{}/playlists/{}/tracks'.format(SPOTIFY_API_URL, user_id, new_playlist_id)
    playlist_response = requests.post(playlist_tracks_api_endpoint, data=json.dumps(post_body), headers=headers)
