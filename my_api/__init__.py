import markdown
import os
import json

# Import the framework
from flask import Flask
from flask_restful import Resource, Api

# Create an instance of Flask
app = Flask(__name__)

# Create the API
api = Api(app)

def get_db():
    filename = "quotes-data-pro.txt"
    with open(filename, 'r') as f:
        db = json.loads(f.read())
    return db

@app.route("/")
def index():
    """Present some documentation"""

    # Open the README file
    with open(os.path.dirname(app.root_path) + '/README.md', 'r') as markdown_file:

        # Read the content of the file
        content = markdown_file.read()

        # Convert to HTML
        return markdown.markdown(content)


class Coin(Resource):
    def get(self, identifier):
        shelf = get_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (identifier in shelf):
            return {'message': 'Coin not found', 'data': {}}, 404

        return {'message': 'Coin found', 'data': shelf[identifier]}, 200


api.add_resource(Coin, '/coinid/<string:identifier>')
