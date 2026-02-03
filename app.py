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

@app.route("/register")
def register():
    """ 
    Default route for the register page 
    Returns: 
    template: The register page html template
    """
    return render_template("register.html")

@app.route("/login")
def login():
    """ 
    Default route for the login page 
    Returns: 
    template: The login page html template
    """
    return render_template("login.html")

@app.route("/home")
def home():
    """ 
    Default route for the home page 
    Returns: 
    template: The home page html template
    """
    return render_template("home.html")

@app.route("/profile")
def profile():
    """ 
    Default route for the profile page 
    Returns: 
    template: The profile page html template
    """
    return render_template("profile.html")

@app.route("/forum")
def forum():
    """ 
    Default route for the forum page 
    Returns: 
    template: The forum page html template
    """
    return render_template("forum.html")

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
