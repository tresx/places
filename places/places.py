import json

import googlemaps
from flask import (Blueprint, current_app, flash, g, redirect,
                   render_template, request, session, url_for)

from places.auth import login_required
from places.db import get_db

bp = Blueprint('places', __name__)


@bp.route('/')
def index():
    if (request.referrer and
        'login' in request.referrer and
        session.get('user_id')):
            flash('You are now logged in.')
    api_key = current_app.config.get('API_KEY')
    return render_template('places/index.html',
                           api_key=api_key)


@bp.route('/locations')
def locations():
    """AJAX endpoint, return locations within 1 degree lat/lng as JSON."""
    cur = get_db().cursor()
    lat = request.args.get('lat')
    min_lat = float(lat) - 1
    max_lat = float(lat) + 1
    lng = request.args.get('lng')
    min_lng = float(lng) - 1
    max_lng = float(lng) + 1

    cur.execute("""
        SELECT *
        FROM locations
        WHERE lat > %s AND lat < %s AND lng > %s AND lng < %s""",
        (min_lat, max_lat, min_lng, max_lng))
    locations = cur.fetchall()
    results = [{
        'id': row['id'],
        'name': row['name'],
        'description': row['description'],
        'postcode': row['postcode']} for row in locations]
    for result in results:
        cur.execute("""
            SELECT rating FROM reviews
            WHERE location_id = %s""", str(result['id']))
        ratings = cur.fetchall()
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
        name = request.form['name'].strip()
        description = request.form['description'].strip()
        postcode = request.form['postcode'].strip().upper()
        error = None
        if not name or not description or not postcode:
            error = 'Name, description and postcode are required.'
        # Calculate lat and lng from postcode
        geocode_result = gmaps.geocode('components=postal_code:' + postcode)
        if not geocode_result:
            error = 'Error geocoding postcode.'
        else:
            lat = geocode_result[0]['geometry']['location']['lat']
            lng = geocode_result[0]['geometry']['location']['lng']

        if error is not None:
            flash(error)
        else:
            # Format postcode correctly for database
            postcode = postcode.replace(' ', '')  # Remove all spaces
            incode = postcode[len(postcode)-3:] # Last 3 characters
            outcode = postcode[0:len(postcode)-3]  # Rest of postcode
            postcode = f'{outcode} {incode}'
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO locations (name, description, postcode,
                                       user_id, lat, lng)
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
            cur.execute("""
                SELECT *
                FROM locations
                WHERE name LIKE %s
                    AND description LIKE %s
                    AND postcode LIKE %s""",
                (f'%{name}%', f'%{description}%', f'%{postcode}%'))
            results = cur.fetchall()
            if not results:
                flash('Sorry, no results found.')
                return render_template('places/search.html')
            results = [dict(result) for result in results]
            for result in results:
                cur.execute("""
                    SELECT rating FROM reviews
                    WHERE location_id = %s""", str(result['id']))
                ratings = cur.fetchall()
                if ratings:
                    result['average_rating'] = sum(
                        rating['rating'] for rating in ratings)/len(ratings)
        return render_template('places/search.html', results=results)

    return render_template('places/search.html')


@bp.route('/place/<place_id>', methods=('GET', 'POST'))
def place(place_id):
    """Details page for a single place."""
    api_key = current_app.config.get('API_KEY')
    conn = get_db()
    cur = conn.cursor()
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
            cur.execute("""
                INSERT INTO reviews (user_id, location_id, rating, review)
                VALUES (%s, %s, %s, %s)""",
                (g.user['id'], place_id, rating, review))
            conn.commit()
            flash('Review added!')
            return redirect(url_for('places.place', place_id=place_id))
    # Render place page
    cur.execute("""
        SELECT locations.name, locations.description, locations.postcode,
               locations.lat, locations.lng, users.email
        FROM locations
            JOIN users ON locations.user_id=users.id
        WHERE locations.id = %s""", (place_id,))
    location = cur.fetchone()
    if not location:
        flash('Sorry, that location page was not found.')
        return redirect(url_for('places.index'))

    cur.execute("""
        SELECT reviews.rating, reviews.review, users.email
        FROM reviews
            JOIN users ON reviews.user_id=users.id
        WHERE location_id = %s""", place_id)
    reviews = cur.fetchall()
    average_rating = (
        sum(review['rating'] for review in reviews)/len(reviews)
        if reviews else 'None')

    return render_template('places/place.html', location=dict(location),
                           reviews=reviews, average_rating=average_rating,
                           api_key=api_key)
