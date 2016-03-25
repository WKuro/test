import sqlite3
from flask import Flask, abort, request, url_for, render_template, jsonify, g , session, redirect
import os
from flask_googlemaps import GoogleMaps, Map
import json
from contextlib import closing

# Server Configuration
DEBUG = True
DATABASE = "congestion_data.db"
SECRET_KEY = 'development key'
USERNAME = "admin"
PASSWORD = "18349275"


app = Flask(__name__)
app.config.from_object(__name__)
port = int(os.getenv('VCAP_APP_PORT', '8080'))

GoogleMaps(app)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
            db.execute('insert into entries (lat, lng, degree) values (?, ? ,?)', [0, 0 ,0])
        db.commit()


@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()

@app.route('/')
def view_map():
    cur = g.db.execute('select lat, lng, degree, moment from entries order by id desc')
    history = [dict(lat=row[0], lng=row[1], degree=row[2], moment=row[3]) for row in cur.fetchall()]
    congestion_map = Map(
        identifier = "place1",
        lat=10.7500,
        lng=106.6667,
        markers=[(10.4500, 106.6600)],
        infobox=["Do ket xe={degree} %, thoi diem={moment}".format(**history[0])],
        style="height:1000px;width=1000px;margin:0;"
    )
    return render_template("show_map.html", congestion_map=congestion_map, history=history)

@app.route('/login', methods=['POST'])
def admin_login():
    input_admin=request.get_json(force=True)
    if input_admin["username"] == app.config["USERNAME"] and input_admin["password"] == app.config["PASSWORD"]:
        session["logged_in"] = True
        return jsonify({"res": "Admin has susscessfully logged in"})
    else:
        return jsonify({"res": "Incorrect username or password"})

@app.route('/data_stream', methods=['POST'])
def data_in():
    input_admin=request.get_json(force=True)
    if input_admin["username"] == app.config["USERNAME"] and input_admin["password"] == app.config["PASSWORD"]:
        data = request.get_json(force=True)
        g.db.execute('insert into entries (lat, lng, degree) values (?, ? ,?)', [data["lat"], data["lng"], data["degree"]])
        g.db.commit()
        return jsonify({"res": "Succesfully insert entry to database"})
    else:
        return jsonify({"res": "You have no permission to access database"})

@app.route('/logout')
def admin_logout():
    session.pop("logged_in", None)
    return jsonify({"res": "Admin logged out"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
