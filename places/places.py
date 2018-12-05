import googlemaps
import json
from flask import (Blueprint, current_app, flash, g, redirect,
                   render_template, request, url_for)
from werkzeug.exceptions import abort

from places.auth import login_required
from places.db import get_db

bp = Blueprint('places', __name__)


@bp.route('/')
def index():
    api_key = current_app.config.get('API_KEY')
    print(api_key)
    return render_template('places/index.html',
                           api_key=api_key)


@bp.route('/locations')
def locations():
    """AJAX endpoint, return locations within 1 degree lat/lng as JSON."""
    conn = get_db()
    cur = conn.cursor()

    lat = request.args.get('lat')
    min_lat = float(lat) - 1
    max_lat = float(lat) + 1
    lng = request.args.get('lng')
    min_lng = float(lng) - 1
    max_lng = float(lng) + 1

    locations = cur.execute("""
        SELECT *
        FROM location
        WHERE lat > %s AND lat < %s AND lng > %s AND lng < %s""",
        (min_lat, max_lat, min_lng, max_lng)).fetchall()
    results = [{
        'id': row['id'],
        'name': row['name'],
        'description': row['description'],
        'postcode': row['postcode']} for row in locations]
    for result in results:
        ratings = cur.execute("""
            SELECT rating FROM review
            WHERE location_id = %s""", str(result['id'])).fetchall()
        if ratings:
            result['average_rating'] = round(
                sum(rating['rating'] for rating in ratings)/len(ratings), 1)
        else:
            result['average_rating'] = 'None'

    return json.dumps(results)


@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    api_key = current_app.config.get('API_KEY')
    gmaps = googlemaps.Client(key=api_key)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        postcode = request.form['postcode']

        # Calculate lat and lng from postcode and insert into database as well
        geocode_result = gmaps.geocode(postcode)
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']

        error = None
        if not name or not description or not postcode:
            error = 'Name, description and postcode are required.'
        elif not geocode_result:
            error = 'Error geocoding postcode.'
        if error is not None:
            flash(error)
        else:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO location (
                    name,
                    description,
                    postcode,
                    user_id,
                    lat,
                    lng
                )
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (name, description, postcode, g.user['id'], lat, lng))
            conn.commit()
            flash('Location added!')
            return redirect(url_for('places.index'))
    return render_template('places/add.html')


@bp.route('/search', methods=('GET', 'POST'))
def search():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        postcode = request.form['postcode']
        error = None
        results = []
        if not name and not description and not postcode:
            error = 'Please enter a name, description or postcode.'
        if error is not None:
            flash(error)
        else:
            conn = get_db()
            cur = conn.cursor()
            results = cur.execute("""
                SELECT *
                FROM location
                WHERE name LIKE %s
                    AND description LIKE %s
                    AND postcode LIKE %s""",
                (f'%{name}%', f'%{description}%', f'%{postcode}%')).fetchall()
            results = [dict(result) for result in results]
            for result in results:
                ratings = db.execute("""
                    SELECT rating FROM review
                    WHERE location_id = %s""", str(result['id'])).fetchall()
                if ratings:
                    result['average_rating'] = sum(
                        rating['rating'] for rating in ratings)/len(ratings)
        return render_template('places/search.html', results=results)

    # TODO: Should not display 'Sorry, no results found' on initial render
    return render_template('places/search.html')


@bp.route('/place/<place_id>', methods=('GET', 'POST'))
def place(place_id):
    """Details page for a single place."""
    api_key = current_app.config.get('API_KEY')
    if request.method == 'POST':
        # Add review to the database
        rating = request.form['rating']
        review = request.form['review']
        error = None
        if not rating or not review:
            error = 'Rating and review are required.'
        if not g.user['id']:
            error = 'Sorry, you must be logged in to post a review.'
        if error is not None:
            flash(error)
        else:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO review (user_id, location_id, rating, review)
                VALUES (%s, %s, %s, %s)"""
                (g.user['id'], place_id, rating, review))
            conn.commit()
            flash('Review added!')
            return redirect(url_for('places.place', place_id=place_id))
    # Render place page
    conn = get_db()
    cur = conn.cursor()
    location = cur.execute("""
        SELECT location.name, location.description, location.postcode,
               location.lat, location.lng, user.username
        FROM location
            JOIN user ON location.user_id=user.id
        WHERE location.id = %s""", (place_id,)).fetchone()
    if not location:
        flash('Sorry, that location page was not found.')
        return redirect(url_for('places.index'))

    reviews = cur.execute("""
        SELECT review.rating, review.review, user.username
        FROM review
            JOIN user ON review.user_id=user.id
        WHERE location_id = %s""", place_id).fetchall()
    average_rating = (
        sum(review['rating'] for review in reviews)/len(reviews)
        if reviews else 'None')

    return render_template('places/place.html', location=dict(location),
                           reviews=reviews, average_rating=average_rating,
                           api_key=api_key)
