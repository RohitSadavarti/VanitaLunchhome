from app import create_app, db
from app.models import MenuItem, Order
import os

app = create_app()

# For Vercel serverless functions
def handler(event, context):
    return app

# For local development
if __name__ == '__main__':
    app.run(debug=True)

# This is what Vercel will use
app = create_app()
