import markdown
import os
import json

from libs import retrieve_api_data

# Import the framework
from flask import Flask
from flask_restful import Resource, Api

# Create an instance of Flask
app = Flask(__name__)
# app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
app.config['RESTFUL_JSON'] = {'separators': (', ', ': '),
                    'indent': 2}

# Create the API
api = Api(app)

def get_db():
    # filename = "quotes-data-pro.txt"
    # with open(filename, 'r') as f:
    #     db = json.loads(f.read())
    # return db
    return retrieve_api_data.run()

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
        if identifier == "update":
            try:
                data = retrieve_api_data.run(force_update=True)
            except Exception as e:
                print(e)
                return {'message': 'Unable to update'}, 500

            return {'message': 'Refreshed data successfully'}, 200

        db = get_db()['data']
        # If the key does not exist in the data store, return a 404 error.
        if not (identifier in db):
            return {'message': 'Coin not found', 'data': {}}, 404

        return {'message': 'Coin found', 'data': db[identifier]}, 200


api.add_resource(Coin, '/coin-id/<string:identifier>')
