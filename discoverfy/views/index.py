"""
Discoverfy index (main) view.

URLs include:
/
"""
import json
import flask
from flask import Flask, request, redirect, render_template, url_for
import requests
import base64
import urllib
import discoverfy


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


@discoverfy.app.route('/', methods=['GET', 'POST'])
def show_index():
    """Display / route."""
    if request.method == 'POST':
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

    # Save Discover Weekly playlist
    save_playlist(access_token, profile_data['id'])

    return redirect(url_for('show_user', user_id=profile_data['id']))


@discoverfy.app.route('/u/<user_id>/')
def show_user(user_id):
    """Display /u/<user_id> route."""
    return render_template('user.html', user=user_id)


def save_playlist(access_token, user_id):
    """Save the user's Discover Weekly playlist"""
    post_body = {
        'name': 'Discoverfy',
        'public': False
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization':'Bearer {}'.format(access_token)
    }

    # Create new playlist
    playlist_api_endpoint = '{}/users/{}/playlists'.format(SPOTIFY_API_URL, user_id)
    playlist_response_string = requests.post(playlist_api_endpoint, data=json.dumps(post_body), headers=headers)
    playlist_response_json = json.loads(playlist_response.text)
