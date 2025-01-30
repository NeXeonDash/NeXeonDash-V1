import os
from dotenv import load_dotenv
from flask import Flask, url_for, render_template
from flask_socketio import SocketIO
from .database import init_db
from .endpoints import register_endpoints

load_dotenv()  # Load variables from .env

app = Flask(
    __name__,
    static_url_path='/static',
    static_folder='../static',
    template_folder='../templates'
)
app.secret_key = os.getenv('SECRET_KEY', 'NeXeonDash')
socketio = SocketIO(app)

# Add custom error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Initialize the database
init_db(app)

# Register Flask endpoints/routes
register_endpoints(app)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 80))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
