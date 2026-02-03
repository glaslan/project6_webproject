""" This module is the main entry point for the Flask app """

from flask import Flask, jsonify, render_template

app = Flask(__name__)


@app.route("/")
def index():
    """ 
    Default route for the index page 
    Returns: 
    template: The index page html template
    """
    return render_template("index.html")


@app.route("/health")
def health():
    """ 
    Default route for checking that the website is up and reachable
    Returns: 
    json: A json object indicating whether the website is healthy
    """
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
