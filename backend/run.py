from app import create_app, db, socketio
from app.models import MenuItem, Order

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True)
