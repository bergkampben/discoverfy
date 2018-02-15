"""
Discoverfy uploads view.

URLs include:
/uploads/
"""
import flask
import discoverfy


@discoverfy.app.route('/uploads/<path:filename>')
def download_file(filename):
    """Display pictures when filepath present."""
    return flask.send_from_directory(discoverfy.app.config['UPLOAD_FOLDER'],
                                     filename,
                                     as_attachment=True)
