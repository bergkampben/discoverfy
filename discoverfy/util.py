"""
Discoverfy index (main) view.

URLs include:
/
"""
import tempfile
import shutil
import hashlib
import os
import flask
import arrow
import discoverfy


class APIException(Exception):
    """Exception type for REST API."""

    def __init__(self, status_code=400, message='', payload=None):
        """Initialize exception."""
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Convert exception to dict for later conversion to JSON."""
        output = dict(self.payload or ())
        output["status_code"] = self.status_code
        output["message"] = self.message
        return output


@discoverfy.app.errorhandler(APIException)
def handle_api_exception(error):
    """Return JSON error messages instead of default HTML."""
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def get_following_posts(cursor, logname):
    """Get posts of the user and their followers."""
    query = '''
            SELECT a.postid AS 'postid',
                   a.filename AS 'filename',
                   a.owner AS 'owner',
                   a.created AS 'created'
            FROM posts a
            JOIN following b ON a.owner=b.username2
            WHERE b.username1="{}"
            UNION ALL
            SELECT *
            FROM posts a
            WHERE OWNER = "{}"
            ORDER BY a.created DESC,
                     a.postid DESC
            '''.format(logname, logname)
    return run_query(cursor, query)


def verify_ownership(owner):
    """Assert user has permission."""
    if 'username' not in flask.session:
        return False
    return owner == flask.session['username']


def unfollow_or_follow(cursor, context):
    """Follow or unfollow based on form."""
    if 'follow' in flask.request.form:
        follow(cursor, context['logname'],
               flask.request.form['username'])
    elif 'unfollow' in flask.request.form:
        unfollow(cursor, context['logname'],
                 flask.request.form['username'])


def run_query(cursor, query):
    """Execute given query on cursor."""
    cursor.execute(query)
    return cursor.fetchall()


def delete_file(filename):
    """Delete file from upload folder."""
    filepath = os.path.join(
        discoverfy.app.config["UPLOAD_FOLDER"],
        filename
    )
    os.remove(filepath)


def sha256sum(filename):
    """Return sha256 hash of file content, similar to UNIX sha256sum."""
    content = open(filename, 'rb').read()
    sha256_obj = hashlib.sha256(content)
    return sha256_obj.hexdigest()


def save_file():
    """Save file to database."""
    # Save POST request's file object to a temp file
    dummy, temp_filename = tempfile.mkstemp()
    new_file = flask.request.files["file"]
    new_file.save(temp_filename)

    # Compute filename
    hash_txt = sha256sum(temp_filename)
    dummy, suffix = os.path.splitext(new_file.filename)
    hash_filename_basename = hash_txt + suffix
    hash_filename = os.path.join(
        discoverfy.app.config["UPLOAD_FOLDER"],
        hash_filename_basename
    )

    # Move temp file to permanent location
    shutil.move(temp_filename, hash_filename)
    discoverfy.app.logger.debug("Saved file")
    return hash_filename_basename


def upload_file(cursor):
    """Insert new post data into database."""
    filename = save_file()
    largest_id_query = '''
                       SELECT postid
                       FROM posts
                       ORDER BY postid DESC
                       LIMIT 1
                        '''
    next_id = cursor.execute(largest_id_query).fetchall()[0]['postid'] + 1
    query = '''
            INSERT INTO posts(postid, filename, owner)
            VALUES ("{}",
                    "{}",
                    "{}")
            '''.format(next_id,
                       filename,
                       flask.session['username'])
    cursor.execute(query)


def follow(cursor, username1, username2):
    """Insert new follow relationship into database."""
    query = '''
            INSERT into following(username1, username2)
            VALUES("{}",
                   "{}")
            '''.format(
                username1,
                username2)
    cursor.execute(query)


def unfollow(cursor, username1, username2):
    """Remove follow relationship from database."""
    query = '''
            DELETE
            FROM following
            WHERE username1="{}" and username2="{}"
            '''.format(username1, username2)
    cursor.execute(query)


def humanize(time):
    """Make time humanized."""
    return arrow.Arrow.fromdatetime(arrow.get(time,
                                              'YYYY-M-D HH:mm:ss')).humanize()


def delete_comment(cursor, owner, commentid):
    """Delete a comment."""
    cursor.execute('''
                    DELETE
                    FROM comments
                    WHERE owner="{}" and commentid="{}"
                   '''.format(owner, commentid))


def delete_post(cursor, owner, postid, filename):
    """Delete a post."""
    delete_file(filename)
    cursor.execute('''
                    DELETE
                    FROM comments
                    WHERE owner="{}" and postid="{}"
                    '''.format(owner, postid))
    cursor.execute('''
                    DELETE
                    FROM posts
                    WHERE owner="{}" and postid="{}"
                    '''.format(owner, postid))


def get_user_img(cursor, username):
    """Select the user image's filename."""
    cursor.execute('''
                    SELECT filename
                    FROM users
                    WHERE username="{}"
                    '''.format(username))
    return cursor.fetchall()[0]['filename']


def get_like_status(cursor, postid, logname):
    """Get the like status."""
    query = '''
            SELECT count(1)
            FROM likes
            WHERE postid={}
              AND owner="{}"
            '''.format(postid, logname)
    return run_query(cursor, query)[0]['count(1)']


def like(cursor, owner, postid):
    """Like a post."""
    query = 'insert into likes('\
            + 'owner, postid)'\
            + ' values("{}", "{}");'.format(
                owner,
                postid)
    cursor.execute(query)


def unlike(cursor, owner, postid):
    """Unlike a post."""
    cursor.execute('''
                    DELETE
                    FROM likes
                    WHERE owner="{}" and postid="{}"
                    '''.format(owner, postid))


def add_comment(cursor, owner, postid, text):
    """Add comment to post."""
    largest_id_query = '''
                       SELECT commentid
                       FROM comments
                       ORDER BY commentid DESC
                       LIMIT 1
                        '''
    next_id = cursor.execute(largest_id_query).fetchall()[0]['commentid'] + 1
    query = '''
            INSERT INTO comments(commentid, owner, postid, text)
            VALUES("{}",
                   "{}",
                   "{}",
                   "{}")
            '''.format(next_id,
                       owner,
                       postid,
                       text)
    cursor.execute(query)


def get_owner_img_url(cursor, owner):
    """Get post owner's image."""
    query = '''
            SELECT filename
            FROM users
            WHERE username="{}"
            '''.format(owner)
    return run_query(cursor, query)[0]['filename']


def post_exists(cursor, postid):
    """Check if the provided postid is valid."""
    query = '''
            SELECT count(1)
            FROM posts
            WHERE postid={}
            '''.format(postid)
    result = run_query(cursor, query)[0]['count(1)']
    return True if result == 1 else False
