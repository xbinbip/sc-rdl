from flask import Flask, render_template, request, redirect, url_for, make_response, abort
import time
from multiprocessing import Process
from spic_soap import login as spic_login, spic_status, get_unit_list, logout as spic_logout
from datetime import datetime, timedelta
from contextlib import contextmanager
import sqlite3


# хелперы

def dt_from_isoformat(date: str) -> datetime:
    return datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f%z")

#конец хелперов

#db
@contextmanager
def db_con(db_name = 'rdl.db'):

    connection = sqlite3.connect(db_name)
    try:
        cursor = connection.cursor()
        yield cursor
    except Exception as e:
        connection.rollback()
        print(f"An error occurred: {str(e)}")
        raise(e)
    else:
        connection.commit()
    finally:
        connection.close()



connection = sqlite3.connect('rdl.db')
cursor = connection.cursor()


    # Create table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS unit_list (
        brand TEXT,
        color TEXT,
        company_id INTEGER,
        description TEXT,
        garage_number TEXT,
        model TEXT,
        name TEXT,
        olson_id TEXT,
        owner TEXT,
        power REAL,
        registration TEXT,
        state_number TEXT,
        unit_id INTEGER PRIMARY KEY UNIQUE NOT NULL,
        unit_type_id INTEGER,
        vin_number TEXT,
        year INTEGER
    )
''')

connection.commit()
connection.close()

def insert_units(units):
    with db_con() as cursor:
        # Prepare the insert statement
        query = '''
            INSERT or REPLACE INTO unit_list (
                brand,
                color,
                company_id,
                description,
                garage_number,
                model,
                name,
                olson_id,
                owner,
                power,
                registration,
                state_number,
                unit_id,
                unit_type_id,
                vin_number,
                year
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        # Execute the insert statement for each unit
        for unit in units:
            cursor.execute(query, (
                unit.get('Brand', None),
                unit.get('Color', None),
                unit.get('CompanyId', None),
                unit.get('Description', None),
                unit.get('GarageNumber', None),
                unit.get('Model', None),
                unit.get('Name', None),
                unit.get('OlsonId', None),
                unit.get('Owner', None),
                unit.get('Power', None),
                unit.get('Registration', None),
                unit.get('StateNumber', None),
                unit.get('UnitId', None),
                unit.get('UnitTypeId', None),
                unit.get('VinNumber', None),
                unit.get('Year', None)
            ))
    return True

#конец db

app = Flask(__name__)

server_status = {
    'message_log' : []
}

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/logout", methods=["GET"])
def logout():
    spic_logout()
    return redirect(url_for('status'))

@app.route("/units", methods=["GET", "POST"])
def units():
    units = get_unit_list()
    return render_template("unit_list.html", units=units)

@app.route("/status", methods=["GET", "POST"])
def status():
    return render_template("status.html", spic_status=spic_status)

@app.route("/update", methods=["POST"])
def update():
    #TODO
    pass

@app.route("/success", methods=["GET"])
def success(message):
    return render_template("success.html", message=message)

@app.route("/update/unitlist", methods=["GET"])
def update_unit_list():
    units = get_unit_list()
    insert_units(units)
    return render_template("success.html", message='Units updated successfully')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', status_code=404, message='Page not found'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', status_code=500, message='Internal server error'), 500

@app.route("/login", methods=["GET"])
def login():
    try:
        print(spic_status)
        if spic_status['logged_in']:
            redirect(url_for('success', message='Already logged in'))
            pass
        resp = spic_login()
        spic_status['logged_in'] = True if resp['ExpireDate'] else False
        session_id = resp['SessionId']
        expire_date = resp['ExpireDate']
        spic_status['session_info'] = {'SessionId': session_id, 'Expiring': expire_date}
    except Exception as e:
        # Handle the exception appropriately
        print(f"An error occurred: {str(e)}")
        return abort(500)
    
    return redirect(url_for('status'))

#test  
def main_loop() -> None:
    pass

if __name__ == "__main__":
    #p = Process(target=main_loop)
    #p.start() 
    app.run()
    #p.join()
        