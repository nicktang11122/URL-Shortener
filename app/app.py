from flask import Flask, render_template, request, jsonify, redirect
from flask_cors import CORS
from models import LongURL, ShortUrl, engine
from sqlalchemy.orm import sessionmaker
import string, random

app = Flask(__name__, template_folder="templates")
CORS(app) # Enable CORS for all routes

# Set up the DB session
Session = sessionmaker(bind=engine)
session = Session()

# Generate unique short URL key
def generate_key(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        key = ''.join(random.choices(chars, k=length))
        ## Check if the key already exists in the database
        ## If it doesn't exist, return the key
        if not session.query(ShortUrl).filter_by(url=key).first():
            return key

# Home page (basic HTML form for quick testing)
@app.route('/')
def index():
    return render_template("page.html")  

# Create / shorten URL
@app.route('/shorten', methods=['POST'])
def shorten():
    ## Get the Original URL from the frontend
    data = request.get_json()
    original_url = data.get("longURL")
    
    #If the URL is not valid, return an error message
    if not original_url or not original_url.startswith("http"):
        return jsonify({"error": "Invalid or missing URL"}), 400

    # Check if the long URL already exists
    existing_long = session.query(LongURL).filter_by(url=original_url).first()
    
    # If it exists, use the existing entry; otherwise, create a new one
    # This avoids creating duplicate long URL entries in the database
    if existing_long:
        long_entry = existing_long
    else:
        long_entry = LongURL(url=original_url)
        session.add(long_entry)
        session.commit()

    #check if a short URL already exists for this long URL
    # If it exists, delete the old short URL entry
    existing_short = session.query(ShortUrl).filter_by(longURL_id=long_entry.id).first()
    if existing_short:
        session.delete(existing_short)
        session.commit()

    # Generate short key and create new short URL
    key = generate_key()
    short_entry = ShortUrl(url=key, longURL_id=long_entry.id)
    session.add(short_entry)
    session.commit()

    ## Return the short URL
    return jsonify({"shortURL": f"{key}"}), 201

# Get original URL from short URL
@app.route('/lookup', methods=['POST'])
def getOriginalURL():
    ## Get the Original URL from the frontend
    data = request.get_json()
    short_url = data.get("shortURL")

    #check if the short URL is valid
    if not short_url:
        return jsonify({"error": "missing URL"}), 400

    ## If the short URL is valid, check if it exists in the database
    existing_short = session.query(ShortUrl).filter_by(url=short_url).first()
    if existing_short:
        # If it exists, get the associated long URL
        long_entry = session.query(LongURL).filter_by(id=existing_short.longURL_id).first()
        if long_entry: #If the long URL exists, return it
            return jsonify({"longURL": long_entry.url}), 200
        else: #Else, return an error message
            return jsonify({"error": "Long URL not found"}), 404
    else: #If the short URL doesn't exist, return an error message
        return jsonify({"error": "Short URL not found"}), 404 
    

### Get short URL from original URL
@app.route('/find', methods=['POST'])
def getShortURL():
    ## Get the Original URL from the frontend
    data = request.get_json()
    long_url = data.get("longURL")

    ##Check if the URL is valid
    if not long_url or not long_url.startswith("http"):
        return jsonify({"error": "Invalid or missing URL"}), 400
    ## Check if the long URL already exists in the database
    existing_long = session.query(LongURL).filter_by(url=long_url).first()
    if existing_long:
        short_url = session.query(ShortUrl).filter_by(url=existing_long.shortUrl.url).first()
        if short_url:
            # If it exists, check if the short URL exists and return it if does
            return jsonify({"shortURL": short_url.url}), 200
        else: #else, return an error message
            return jsonify({"error": "Short URL not found"}), 404
    else:
        return jsonify({"error": "Long URL not found"}), 404 
        
# Delete URL
@app.route('/delete', methods=['DELETE'])
def deleteURL():
    ##Get the URL from the frontend
    data = request.get_json()
    original_url = data.get("longURL")

    ##Check if the URL is valid
    if not original_url or not original_url.startswith("http"):
        return jsonify({"error": "Invalid or missing URL"}), 400

    # Check if the long URL already exists in the database
    existing_long = session.query(LongURL).filter_by(url=original_url).first()

    ## If it exists, delete the long URL entry and its associated short URL
    ## If it doesn't exist, return an error message
    if existing_long:
        existing_short = session.query(ShortUrl).filter_by(longURL_id=existing_long.id).first()
        if existing_short:
            session.delete(existing_short)
        session.delete(existing_long)
        session.commit()
        return jsonify({"message": "URL deleted successfully."}), 200
    else:
        return jsonify({"error": "URL does not exist"}), 400


# Takes GET request from user when link is clicked and redirects short URL to original URL
@app.route('/<string:key>')
def redirect_to_long(key):
    short = session.query(ShortUrl).filter_by(url=key).first()
    if short: #redirect the short URL to the long URL if it exists
        return redirect(short.longURLs.url, code=302)
    return jsonify({"error": "Short URL not found"}), 404


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
