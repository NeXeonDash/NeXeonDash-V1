import os
from src.app import app, socketio

if __name__ == '__main__':
    port = int(os.getenv('PORT', 80))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
