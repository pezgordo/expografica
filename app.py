from flask import Flask, redirect, render_template, request, session, send_file, abort, jsonify
import sqlite3
import random
import segno
import os
from PIL import Image
from flask_session import Session
from helpers import apology
from functools import wraps
import datetime
from datetime import date
import pandas as pd

#---Imports WHATSAPP BOT---#

import requests
import json

# Function to fetch data from SQLite database and export to Excel
def export_to_excel():
    conn = sqlite3.connect('datos_feria.db')  # SQLite database file
    query = "SELECT * FROM registro_de_visitantes"  # Replace 'your_table' with the name of your table
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    today = date.today().strftime("%Y-%m-%d")
    excel_file = f"lista_de_visitantes_{today}.xlsx"
    df.to_excel(excel_file, index=False)
    return excel_file

#---Imports WHATSAPP BOT END ---#
#basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# Set DEBUG mode
app.debug = False  # Set to True for development, False for production

# Set allowed hosts
ALLOWED_HOSTS = ['*']  # Accept requests from any host/domain


#app.secret_key = 'clave_secreta'

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# SQLite3 Conectar a base de datos
conn = sqlite3.connect('datos_feria.db', check_same_thread=False)

# Create a cursor Object
db = conn.cursor()


# Listado de Ferias
FERIAS = [
    "TEXTIL",
    "GRAFICA"
]


### login required func
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# AFTER REQUEST
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



# INDEX
@app.route("/")
def index():

    referring_site = request.headers.get('Referer')
    print(referring_site)

    if referring_site and 'https://expograficabolivia.com.bo/' in referring_site:
        var_feria = 'GRAFICA'
    elif referring_site and 'https://boliviatextil.com.bo/' in referring_site:
        var_feria = 'TEXTIL'
    else:
        var_feria = 'GRAFICA'

    return render_template("index.html", var_feria=var_feria)
  


# FLASK GRID
#### for table route - flask-grid ###

DB_FILE = 'datos_feria.db'

def execute_query(query, args=None):
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()
    if args:
        cursor.execute(query, args)
    else:
        cursor.execute(query)
    result = cursor.fetchall()
    connection.commit()
    connection.close()
    return result


# EXCEL EXPORT ROUTE
@app.route('/export', methods=['GET'])
def export():
    excel_file = export_to_excel()
    return send_file(excel_file, as_attachment=True)


# SERVER FOR LISTA DE VISITANTES TABLE
@app.route('/api/data')
def data():
    query = "SELECT * FROM registro_de_visitantes"

    # Search filter
    search = request.args.get('search')
    if search:
        query += " WHERE nombre LIKE ? OR documento LIKE ? OR identificador LIKE ?"
        search_term = f"%{search}%"
        args = (search_term, search_term, search_term)
        query_result = execute_query(query, args)
    else:
        query_result = execute_query(query)

    total = len(query_result)

    # Sorting
    sort = request.args.get('sort')
    if sort:
        order = []
        for s in sort.split(','):
            if len(s) < 2:
                continue # Skip if sorting parameter is invalid
            direction = s[0] # Direction: '+' (ascending) or '-' (descending)
            column_name = s[1:] # Column name to sort by
            if column_name in ['id', 'nombre', 'documento', 'pais', 'feria', 'identificador', 'fecha_de_registro']:
                order.append((column_name, direction))
        if order:
            print("ORDER IS: ")
            print(order[0])

            column_indices = {'id': 0, 'nombre': 2, 'documento': 4, 'pais': 8, 'feria': 9, 'identificador': 10, 'fecha_de_registro': 11}

            query_result.sort(key=lambda x: x[column_indices[order[0][0]]] if x[column_indices[order[0][0]]] is not None else "", reverse=(order[0][1] == '-'))





    # Pagination
    start = request.args.get('start', type=int, default=-1)
    length = request.args.get('length', type=int, default=-1)
    if start != -1 and length != -1:
        query_result = query_result[start:start+length]

    # Response
    data = [{'id': row[0], 'empresa': row[1], 'nombre': row[2], 'cargo': row[3], 'documento': row[4], 'telefono': row[5], 'correo': row[6], 'ciudad': row[7],  'pais': row[8], 'feria': row[9], 'identificador': row[10], 'fecha_de_registro': row[11]} for row in query_result]
    return {'data': data, 'total': total}


@app.route('/api/data', methods=['POST'])
def update():
    data = request.get_json()
    if 'id' not in data:
        abort(400)

    query = "SELECT * FROM registro_de_visitantes WHERE id = ?"
    user_id = data['id']
    user_data = execute_query(query, (user_id,))
    if not user_data:
        abort(404)

    # Update fields
    update_query = "UPDATE registro_de_visitantes SET "
    update_fields = []
    update_values = []
    for field in ['empresa', 'nombre', 'cargo', 'documento', 'telefono', 'correo', 'ciudad', 'pais', 'feria', 'identificador', 'fecha_de_registro']:
        if field in data:
            update_fields.append(f"{field} = ?")
            update_values.append(data[field])

    update_query += ", ".join(update_fields)
    update_query += " WHERE id = ?"
    update_values.append(user_id)

    execute_query(update_query, tuple(update_values))

    return '', 204
#####


# SERVER FOR LISTA DE EMPRESAS REGISTRADAS TABLE
@app.route('/api/data_empresas')
def data_empresas():
    query = "SELECT * FROM registro_de_empresas"

    # Search filter
    search = request.args.get('search')
    if search:
        query += " WHERE empresa LIKE ? OR pais LIKE ? OR identificador LIKE ?"
        search_term = f"%{search}%"
        args = (search_term, search_term, search_term)
        query_result = execute_query(query, args)
    else:
        query_result = execute_query(query)

    total = len(query_result)

    # Sorting
    sort = request.args.get('sort')
    if sort:
        order = []
        for s in sort.split(','):
            direction = s[0]
            column_name = s[1:]
            if column_name in ['id', 'empresa','feria', 'pais', 'identificador', 'habilitado']:
                order.append((column_name, direction))
        if order:
            print("ORDER IS: ")
            print(order[0])
            # Sort query_result based on the sorting parameters
            #query_result.sort(key=lambda x: x[0][order[0][0]], reverse=(order[0][1] == '-'))
            column_indices = {'id': 0, 'empresa': 1, 'feria': 2, 'pais': 3, 'identificador': 4, 'habilitado': 5}
            #query_result.sort(key=lambda x: x[order[0][0]], reverse=(order[0][1] == '-'))
            query_result.sort(key=lambda x: x[column_indices[order[0][0]]], reverse=(order[0][1] == '-'))


    # Pagination
    start = request.args.get('start', type=int, default=-1)
    length = request.args.get('length', type=int, default=-1)
    if start != -1 and length != -1:
        query_result = query_result[start:start+length]

    # Response
    data = [{'id': row[0], 'empresa': row[1], 'feria': row[2], 'telefono': row[3], 'correo': row[4], 'pais': row[5], 'password': row[6], 'identificador': row[7], 'habilitado': row[8]} for row in query_result]
    return {'data': data, 'total': total}


@app.route('/api/data_empresas', methods=['POST'])
def update_empresas():
    data = request.get_json()
    if 'id' not in data:
        abort(400)

    query = "SELECT * FROM registro_de_empresas WHERE id = ?"
    user_id = data['id']
    user_data = execute_query(query, (user_id,))
    if not user_data:
        abort(404)

    # Update fields
    update_query = "UPDATE registro_de_empresas SET "
    update_fields = []
    update_values = []
    for field in ['empresa', 'feria', 'telefono', 'correo', 'pais', 'password', 'identificador', 'pais', 'feria', 'identificador', 'habilitado']:
        if field in data:
            update_fields.append(f"{field} = ?")
            update_values.append(data[field])

    update_query += ", ".join(update_fields)
    update_query += " WHERE id = ?"
    update_values.append(user_id)

    execute_query(update_query, tuple(update_values))

    return '', 204
#### End - for table route


# DESREGISTRAR VISITANTES
@app.route("/desregistrarse", methods=["POST"])
def desregistrarse():
    # Olvidar registrante
    id = request.form.get("id")
    print(f"id: {id}")  # Add this line for debugging
    if id:
        print(f"DELETE FROM registro_de_visitantes WHERE id = {id}")
        db.execute("DELETE FROM registro_de_visitantes WHERE id = ?", (id,))
        conn.commit()

    return redirect("/registrantes")


# REGISTRO DE VISITANTES
@app.route("/registro", methods=["POST"])
def register():

    #generate random number
    def generate_random_number():
        return random.randint(100000, 999999)
    
    # Validar submision
    empresa = request.form.get("empresa")
    nombre = request.form.get("nombre")
    cargo = request.form.get("cargo")
    documento = request.form.get("documento")
    telefono = request.form.get("telefono")
    correo = request.form.get("correo")
    ciudad = request.form.get("ciudad")
    pais = request.form.get("pais")
    feria = request.form.get("feria")
    fecha = date.today()
    
    
    while True:
        # generate a random 6 digit number
        random_number = generate_random_number()
        identificador = random_number

        #check if the identificador number exists in the table
        db.execute('SELECT * FROM registro_de_visitantes WHERE identificador = ?', (random_number,))
        existing_row = db.fetchone()

        if existing_row is None:
            if not nombre or feria not in FERIAS:
                return render_template("failure.html", message="Casilla de nombre vacia")

            try:

                # Recordar registrante
                db.execute("INSERT INTO registro_de_visitantes (empresa, nombre, cargo, documento, telefono, correo, ciudad, pais, feria, identificador, fecha_de_registro) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (empresa, nombre, cargo, documento, telefono, correo, ciudad, pais, feria, random_number, fecha))
                conn.commit()
            except Exception as e:
                print(f"Error insertando en base de datos: {e}")
                return render_template("failure.html", message=f"Error: {e}")




            ###-------Generar QR--------------


            # Assuming your data_to_encode is a tuple
            vcard_data = f"BEGIN:VCARD\nVERSION:3.0\nN:{nombre}\nORG:{empresa}\nROLE:{cargo}\nTEL:{telefono}\nEMAIL:{correo}\nNOTE:{documento}\nCATEGORIES:{feria}\nUID:{random_number}\nEND:VCARD"

            #print(vcard_data)

            
            # Create a QR code with Segno
            qr = segno.make(vcard_data)

    
            # Save the QR code as a temporary file
            filename_png = os.path.join('static/qr', f'temp_qr_{identificador}.png')

            qr.save(filename_png, scale=5)

            # Open the PNG file with Pillow and save it as JPG
            image = Image.open(filename_png)

            filename_jpg = os.path.join('static/qr', f'temp_qr_{identificador}.jpg')

            image.convert("RGB").save(filename_jpg)


            ###---------------WHATSAPP BOT------------####

            
            if telefono and telefono.startswith("+"):
                telefono = telefono[1:]  # Remove the leading '+'


            url = "https://graph.facebook.com/v18.0/169273282946153/messages"

            payload = json.dumps({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            #"to": f"591{telefono}",
            #"to": "59169830657",
            "to": f"{telefono}",
            "type": "template",
            "template": {
                "name": "envio_qr",
                "language": {
                "code": "en"
                },
                "components": [
                {
                    "type": "header",
                    "parameters": [
                    {
                        "type": "image",
                        "image": {
                        "link": f"https://webapp.expograficabolivia.com.bo/static/qr/temp_qr_{identificador}.jpg"
                        #"link": "https://webapp.expograficabolivia.com.bo/static/qr/temp_qr_123858.jpg"

                        }
                    }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                    {
                        "type": "text",
                        "text": nombre
                    },
                    {
                        "type": "text",
                        "text": cargo
                    },
                    {
                        "type": "text",
                        "text": empresa
                    },
                    {
                        "type": "text",
                        "text": ciudad
                    },
                    {
                        "type": "text",
                        "text": pais
                    },
                    {
                        "type": "text",
                        "text": identificador
                    }
                    ]
                }
                ]
            }
            })
            headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer EAAExyzOF11QBOwtZAJ1gOjVxPhlmuE6UxgxKfn0xR8Aqr1oadeS2GQTl1m2DZC4xUfmFoaAd0udaOOvKqDjgIZAnV7S91bHFWJPEzrywL61NWdmnZAoEYsjG1AgFaaiZAMkHKQb8KlK0LQToK5ZA4PYDZBzN2Wv0DxR76U0OJeFuXUfgZCzGDbUa9cIhJYcSKBsp'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            print(response.text)
            
            message = '''
                En un momento llegará a su número de whatsapp un QR e información que deberá presentar en el ingreso principal<br><br>
                <strong>Día del evento:</strong> 02, 03 y 04 de Agosto 2024<br>
                <strong>Lugar del evento:</strong> Pabellón Guarayo, FexpoCruz Santa Cruz, Bolivia. (Av. Roca y Coronado entre 3er y 4to anillo, lado del parqueo principal)
                '''



            ###############################
            # Confirm registration
            return render_template('success.html', message=message)


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("debe introducir nombre de usuario", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("debe introducir contraseña", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        )

        # Fetch a single row
        user = rows.fetchone()
        
        # Ensure username exists and password is correct
        #if len(rows) != 1 or rows[0]["password"] != request.form.get("password"):
        if user is None or user[2] != request.form.get("password"):
            return apology("usuario y/o contraseña invalido", 403)

        # Remember which user has logged in
        session["user_id"] = user[0]

        # Redirect user to registrantes page
        return redirect("/administracion")
        
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# ADMINISTRACION
@app.route("/administracion")
@login_required
def administracion():
    return render_template('administracion.html')


# ADMINISTRACION - ADMINISTRACION DE VISITANTES  
# LISTA DE VISITANTES REGISTRADOS
@app.route("/registrantes")
@login_required
def registrantes():

    query = "SELECT * FROM registro_de_visitantes"
    visitantes = execute_query(query)

    #visitantes = RegistroDeVisitantes.query
    #query_1 = RegistroDeVisitantes.query.get(1)
    print("QUEIRYYYYYY")
    print(query)
    return render_template('registrantes.html', visitantes=visitantes)


# ADMINISTRACION - ADMINISTRACION DE VISITANTES - LISTA DE VISITANTES REGISTRADOS 
# REENVIAR CODIGO QR
@app.route("/reenviar_qr", methods=["GET", "POST"])
def reenviar_qr():
        if request.method == "POST":
            # Olvidar registrante
            id = request.form.get("id")
            print(f"id: {id}")  # Add this line for debugging
            if id:
                #print(f"SELECT * FROM registro_de_visitantes WHERE id = ?", (id,))
                
                # Retrieve data from the database
                data_to_encode = db.execute("SELECT * FROM registro_de_visitantes WHERE id = ?", (id,)).fetchone()

                if data_to_encode is None:
                    return render_template('failure.html', message='Data not found')

                # Convert the tuple to a string
                data_str = ', '.join(map(str, data_to_encode))


                # Convert the tuple to a string with line breaks
                #data_str = '\n'.join(map(str, data_to_encode))
                #data_str = '\n'.join([f"{column}: {value}" for column, value in zip(data_to_encode.keys(), data_to_encode)])

                # Column names (replace these with your actual column names)
                column_names = ['id', 'Empresa', 'Nombre', 'Cargo', 'Documento','Telefono', 'Correo', 'Ciudad', 'Pais', 'Feria', 'Identificador']

                # Convert the tuple to a string with line breaks
                data_str = '\n'.join([f"{column}: {value}" for column, value in zip(column_names[1:], data_to_encode[1:])])
                ###print(data_str)

                # Display data with line breaks in HTML
                data_str_html = data_str.replace('\n', '<br>')

                # Assuming your data_to_encode is a tuple
                #vcard_data = f"BEGIN:VCARD\nVERSION:3.0\nN:{data_to_encode[column_names.index('Nombre')]}\nORG:{data_to_encode[column_names.index('Empresa')]}\nROLE:{data_to_encode[column_names.index('Cargo')]}\nTEL:{data_to_encode[column_names.index('Telefono')]}\nEMAIL:{data_to_encode[column_names.index('Correo')]}\nEND:VCARD"
                ###vcard_data = f"BEGIN:VCARD\nVERSION:3.0\nN:{data_to_encode[column_names.index('Nombre')]}\nORG:{data_to_encode[column_names.index('Empresa')]}\nROLE:{data_to_encode[column_names.index('Cargo')]}\nTEL:{data_to_encode[column_names.index('Telefono')]}\nEMAIL:{data_to_encode[column_names.index('Correo')]}\nNOTE:{data_to_encode[column_names.index('Documento')]}\nTITLE:{data_to_encode[column_names.index('Rubro')]}\nCATEGORIES:{data_to_encode[column_names.index('Feria')]}\nUID:{data_to_encode[column_names.index('Identificador')]}\nEND:VCARD"

                ###print(vcard_data)

                
                # Create a QR code with Segno
                #qr = segno.make(data_str)
                ###qr = segno.make(vcard_data)



                # ---- parametros de envio whatsapp -----
                # 2.Nombre 3.Cargo 1.Empresa 8.Ciudad 9.Pais  11.Identificador
                nombre = data_to_encode[2]
                cargo = data_to_encode[3]
                empresa = data_to_encode[1]
                ciudad = data_to_encode[8]
                pais = data_to_encode[9]
                identificador = data_to_encode[10] 

                #------ telefono de envio ------

                telefono = data_to_encode[5]

                #---------------------------------------        
                

                print("reenvio nombre: " + nombre)
                print("reenvio telefono: " + telefono)
                print("reenvio identificador: " + identificador)
            
                # Save the QR code as a temporary file
                ###filename_png = os.path.join('static/qr', f'temp_qr_{identificador}.png')

                ###qr.save(filename_png, scale=5)

                # Open the PNG file with Pillow and save it as JPG
                ###image = Image.open(filename_png)

                #filename_jpg = os.path.join('static', 'temp_qr.jpg')

                ###filename_jpg = os.path.join('static/qr', f'temp_qr_{identificador}.jpg')



                ###image.convert("RGB").save(filename_jpg)
                
                ### TEST IMAGE QR

                qr_path = f"static/qr/temp_qr_{identificador}.jpg"
                



                ###---------------WHATSAPP BOT------------####
                if telefono and telefono.startswith("+"):
                    telefono = telefono[1:]  # Remove the leading '+'

                print("reenvio telefono: " + telefono)




                url = "https://graph.facebook.com/v18.0/169273282946153/messages"

                payload = json.dumps({
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": f"{telefono}",
                "type": "template",
                "template": {
                    "name": "envio_qr",
                    "language": {
                    "code": "en"
                    },
                    "components": [
                    {
                        "type": "header",
                        "parameters": [
                        {
                            "type": "image",
                            "image": {
                            "link": f"https://webapp.expograficabolivia.com.bo/static/qr/temp_qr_{identificador}.jpg"
                            }
                        }
                        ]
                    },
                    {
                        "type": "body",
                        "parameters": [
                        {
                            "type": "text",
                            "text": nombre
                        },
                        {
                            "type": "text",
                            "text": cargo
                        },
                        {
                            "type": "text",
                            "text": empresa
                        },
                        {
                            "type": "text",
                            "text": ciudad
                        },
                        {
                            "type": "text",
                            "text": pais
                        },
                        {
                            "type": "text",
                            "text": identificador
                        }
                        ]
                    }
                    ]
                }
                })
                headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer EAAExyzOF11QBOwtZAJ1gOjVxPhlmuE6UxgxKfn0xR8Aqr1oadeS2GQTl1m2DZC4xUfmFoaAd0udaOOvKqDjgIZAnV7S91bHFWJPEzrywL61NWdmnZAoEYsjG1AgFaaiZAMkHKQb8KlK0LQToK5ZA4PYDZBzN2Wv0DxR76U0OJeFuXUfgZCzGDbUa9cIhJYcSKBsp'
                }

                response = requests.request("POST", url, headers=headers, data=payload)

                print(response.text)


                





            ####-----------------------####





                # Render the HTML template with the QR code data
                return render_template('success.html', message='Codigo QR enviado exitosamente')

        else:
            return redirect("/")

# ADMINISTRACION - ADMINISTRACION DE VISITANTES - LISTA DE VISITANTES REGISTRADOS - 
# GENERATE ETIQUETA
@app.route('/generate_qr', methods=["GET", "POST"])
def generate_qr():
    if request.method == "POST":
        # Olvidar registrante
        id = request.form.get("id")
        print(f"id: {id}")  # Add this line for debugging
        if id:
            #print(f"SELECT * FROM registro_de_visitantes WHERE id = ?", (id,))
            
            # Retrieve data from the database
            data_to_encode = db.execute("SELECT * FROM registro_de_visitantes WHERE id = ?", (id,)).fetchone()

            if data_to_encode is None:
                return render_template('failure.html', message='Data not found')

            # Convert the tuple to a string
            data_str = ', '.join(map(str, data_to_encode))


            # Convert the tuple to a string with line breaks
            #data_str = '\n'.join(map(str, data_to_encode))
            #data_str = '\n'.join([f"{column}: {value}" for column, value in zip(data_to_encode.keys(), data_to_encode)])

            # Column names (replace these with your actual column names)
            column_names = ['id', 'Empresa', 'Nombre', 'Cargo', 'Documento','Telefono', 'Correo', 'Ciudad', 'Pais', 'Feria', 'Identificador']

            # Convert the tuple to a string with line breaks
            data_str = '\n'.join([f"{column}: {value}" for column, value in zip(column_names[1:], data_to_encode[1:])])
            ###print(data_str)

            # Display data with line breaks in HTML
            data_str_html = data_str.replace('\n', '<br>')

            # Assuming your data_to_encode is a tuple
            #vcard_data = f"BEGIN:VCARD\nVERSION:3.0\nN:{data_to_encode[column_names.index('Nombre')]}\nORG:{data_to_encode[column_names.index('Empresa')]}\nROLE:{data_to_encode[column_names.index('Cargo')]}\nTEL:{data_to_encode[column_names.index('Telefono')]}\nEMAIL:{data_to_encode[column_names.index('Correo')]}\nEND:VCARD"
            ###vcard_data = f"BEGIN:VCARD\nVERSION:3.0\nN:{data_to_encode[column_names.index('Nombre')]}\nORG:{data_to_encode[column_names.index('Empresa')]}\nROLE:{data_to_encode[column_names.index('Cargo')]}\nTEL:{data_to_encode[column_names.index('Telefono')]}\nEMAIL:{data_to_encode[column_names.index('Correo')]}\nNOTE:{data_to_encode[column_names.index('Documento')]}\nTITLE:{data_to_encode[column_names.index('Rubro')]}\nCATEGORIES:{data_to_encode[column_names.index('Feria')]}\nUID:{data_to_encode[column_names.index('Identificador')]}\nEND:VCARD"

            ###print(vcard_data)

            
            # Create a QR code with Segno
            #qr = segno.make(data_str)
            ###qr = segno.make(vcard_data)



            # ---- parametros de envio whatsapp -----
            # 2.Nombre 3.Cargo 1.Empresa 8.Ciudad 9.Pais  11.Identificador
            nombre = data_to_encode[2]
            cargo = data_to_encode[3]
            empresa = data_to_encode[1]
            ciudad = data_to_encode[8]
            pais = data_to_encode[9]
            identificador = data_to_encode[10] 

            #------ telefono de envio ------

            telefono = data_to_encode[5]

            #---------------------------------------        
            


        
            # Save the QR code as a temporary file
            ###filename_png = os.path.join('static/qr', f'temp_qr_{identificador}.png')

            ###qr.save(filename_png, scale=5)

            # Open the PNG file with Pillow and save it as JPG
            ###image = Image.open(filename_png)

            #filename_jpg = os.path.join('static', 'temp_qr.jpg')

            ###filename_jpg = os.path.join('static/qr', f'temp_qr_{identificador}.jpg')



            ###image.convert("RGB").save(filename_jpg)
            
            ### TEST IMAGE QR

            qr_path = f"static/qr/temp_qr_{identificador}.jpg"
            



            ###---------------WHATSAPP BOT------------####


            """url = "https://graph.facebook.com/v18.0/169273282946153/messages"

            payload = json.dumps({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"591{telefono}",
            #"to": "59169830657",
            "type": "template",
            "template": {
                "name": "envio_qr",
                "language": {
                "code": "en"
                },
                "components": [
                {
                    "type": "header",
                    "parameters": [
                    {
                        "type": "image",
                        "image": {
                        "link": f"https://webapp.expograficabolivia.com.bo/static/qr/temp_qr_{identificador}.jpg"
                        }
                    }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                    {
                        "type": "text",
                        "text": nombre
                    },
                    {
                        "type": "text",
                        "text": cargo
                    },
                    {
                        "type": "text",
                        "text": empresa
                    },
                    {
                        "type": "text",
                        "text": ciudad
                    },
                    {
                        "type": "text",
                        "text": pais
                    },
                    {
                        "type": "text",
                        "text": identificador
                    }
                    ]
                }
                ]
            }
            })
            headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer EAAExyzOF11QBOwtZAJ1gOjVxPhlmuE6UxgxKfn0xR8Aqr1oadeS2GQTl1m2DZC4xUfmFoaAd0udaOOvKqDjgIZAnV7S91bHFWJPEzrywL61NWdmnZAoEYsjG1AgFaaiZAMkHKQb8KlK0LQToK5ZA4PYDZBzN2Wv0DxR76U0OJeFuXUfgZCzGDbUa9cIhJYcSKBsp'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            print(response.text)"""


            





        ####-----------------------####





            # Render the HTML template with the QR code data
            return render_template('qr_template.html', data=data_str_html, qr_path=qr_path)

    else:
        return redirect("/")


# ADMINISTRACION - ADMINISTRACION DE EXPOSITORES - VER LISTA DE EXPOSITORES
@app.route("/administracion_expositores")
@login_required
def administracion_expositores():

    query = "SELECT * FROM registro_de_empresas"
    empresas_registradas = execute_query(query)

    return render_template("administracion_expositores.html", empresas_registradas=empresas_registradas)



# HABILITAR EXPOSITORES (***NOT USED***)
@app.route("/habilitar_expositor", methods=["POST"])
def habilitar_expositor():
    id = request.form.get("id")
    print(f"id: {id}")  # Add this line for debugging
    if id:
        #print(f"DELETE FROM registro_de_empresas WHERE id = {id}")
        
        db.execute("UPDATE registro_de_empresas SET habilitado = 'SI' WHERE id = ?", (id,))
        conn.commit()

    return redirect("/administracion_expositores")


# ADMINISTRAR EXPOSITOR INDIVIDUAL (***REVISAR!!***)
@app.route("/administrar_expositor_individual", methods=["POST"])
def administrar_expositor():

    return render_template("administrar_expositor_individual.html")


# DESREGISTRAR EXPOSITORES
@app.route("/desregistrar_expositor", methods=["POST"])
def desregistrar_expositor():
        # Olvidar empresa
    id = request.form.get("id")
    print(f"id: {id}")  # Add this line for debugging
    if id:
        print(f"DELETE FROM registro_de_empresas WHERE id = {id}")
        db.execute("DELETE FROM registro_de_empresas WHERE id = ?", (id,))
        conn.commit()

    return redirect("/administracion_expositores")


# ADMINISTRACION - ADMINISTRACION DE EXPOSITORES
# FORMULARIO DE REGISTRO EXPOSITORES - PARA AGREGAR NUEVO EXPOSITOR
@app.route("/formulario_registro_expositores")
def formulario_registro_expositores():

    return render_template("formulario_registro_expositores.html")


# ADMINISTRACION - ADMINISTRACION DE EXPOSITORES - FORMULARIO DE REGISTRO EXPOSITORES
# CONFIRMACION REGISTRO DE EXPOSITORES - GUARDAR INFORMACION
@app.route("/registro_expositores", methods=["POST"])
#@login_required
def registro_expositores():

    #generate random number
    def generate_random_number():
        return random.randint(100000, 999999)
    
    # Validar submision
    empresa = request.form.get("nombre_empresa")
    feria = request.form.get("tipo_feria")
    telefono = request.form.get("telefono_empresa")
    correo = request.form.get("correo_empresa")
    pais = request.form.get("pais_empresa")
    password = request.form.get("password")
    habilitado = "NO"

    while True:
        # Generate random 6 digit number
        random_number = generate_random_number()
        identificador = random_number

        # Check if the number exists in the table
        db.execute('SELECT * FROM registro_de_empresas WHERE identificador = ?', (random_number,))
        existing_row = db.fetchone()
        print(existing_row)
        print(empresa)
        print(feria)

        # Ensure POST Method
        if request.method == "POST":

            if existing_row is None:
                if not empresa or feria not in FERIAS:
                    return render_template("failure.html", message="Error de registro")
                
                # Check if username already exists
                existing_user = db.execute("SELECT * FROM registro_de_empresas WHERE empresa = ?", (empresa,)).fetchall()
                if existing_user:
                    #print(existing_user)
                    return apology("Ya existe una empresa registrada con ese nombre!", 400)

                # Ensure password submit
                elif not request.form.get("password"):
                    return apology ("Debe ingresar una contraseña para registrar", 400)
                
                # Ensure passwords confirmation
                elif not request.form.get("confirmation"):
                    return apology("Debe confirmar su contraseña", 400)
                
                # Ensure passwords match
                elif request.form.get("password") != request.form.get("confirmation"):
                    return apology("La contraseña no coincide", 400)

                try:
                    # Registrar empresa
                    db.execute("INSERT INTO registro_de_empresas (empresa, feria, telefono, correo, pais, password, identificador, habilitado) VALUES(?,?,?,?,?,?,?,?)", (empresa, feria, telefono, correo, pais, password, identificador, habilitado))
                    conn.commit()
                except Exception as e:
                    # Debug
                    print(f"Error insertando en base de datos: {e}")
                    # Error message
                    return render_template("failure.html", message=f"Error: {e}")
                
                message = 'Registro de Expositor Exitoso!'

                return render_template("success.html", message=message)



# PRE REGISTRO DE EXPOSITORES (NO ESTA USADO!!!)
@app.route("/pre_registro_expositores")
def pre_registro_expositores():

    referring_site = request.headers.get('Referer')
    print(referring_site)

    if referring_site and 'https://expograficabolivia.com.bo/' in referring_site:
        var_feria = 'GRAFICA'
    elif referring_site and 'https://boliviatextil.com.bo/' in referring_site:
        var_feria = 'TEXTIL'
    else:
        var_feria = 'GRAFICA'

    return render_template("pre_registro_expositores.html", var_feria=var_feria)
  


# MODULO ADMINISTRACION DE EMPRESAS
# MANEJO INDIVIDUAL DE EMPRESAS

# EMPRESA LOGIN
@app.route("/empresa_login", methods=["GET", "POST"])
#@app.route('/manejar_empresa/<int:empresa_id>', methods=['GET', 'POST'])
def empresa_login():

    # Forget any user_id
    session.clear()

    # Reached via POST
    if request.method == "POST":

        #DEBUG
        #print("empresa name: " + request.form.get("nombre_empresa"))
        #print("empresa password: " + request.form.get("password"))

        # Asegurar nombre de empresa
        if not request.form.get("nombre_empresa"):
            return apology("nombre de empresa no valido / Invalid company name", 403)
        # Asegurar contraseña de empresa
        elif not request.form.get("password"):
            return apology("Debe introducir la contraseña / Must provide password", 403)
        # Query base de datos por nombre de empresa
        rows = db.execute("SELECT * FROM registro_de_empresas WHERE empresa = ?", (request.form.get("nombre_empresa"),))

        #DEBUG
        #print(rows)
        #print(rows.fetchone())
        row = rows.fetchone()
        
        #print(len(rows))
        
        # Asegurar que la empresa existe y la contraseña es la correcta
        
        # Check if any rows were fetched
        if not row:
            return apology("Nombre de Empresa invalida / Invalid company name", 403)
            
        else:
            # Check password
            if row[6] == request.form.get("password"):

                # Recordar que usuario a loggeado 
                session["user_id"] = row[0]

                # Redirect user to manejar_empresa.html
                #return redirect("/") 
                return redirect("/manejar_empresa")
            else:
                return apology("Contraseña invalida / Invalid Password")

    # Reached via GET
    else:
        return render_template("pre_registro_expositores.html")


# MANEJAR EMPRESA
@app.route("/manejar_empresa", methods=["GET", "POST"])
@login_required
def manejar_empresa():
    user_id = session.get("user_id")

        #generate random number
    def generate_random_number():
        return random.randint(100000, 999999)
    #telefono = db.execute("SELECT DISTINCT telefono FROM registro_de_empresas WHERE id = ?", (user_id,)).fetchall()
    #telefono = db.execute("SELECT telefono FROM registro_de_empresas WHERE id = ?", (user_id,)).fetchone()
    #if telefono:
    #    telefono = telefono[0]
    #    print(telefono)

    informacion = db.execute("SELECT * FROM registro_de_empresas WHERE id = ?", (user_id,)).fetchone()
    print (informacion)
    print("id: " + str(informacion[0]))
    print("empresa: " + str(informacion[1]))
    print("feria: " + str(informacion[2]))
    print("telefono: " + str(informacion[3]))
    print("correo: " + str(informacion[4]))
    print("pais:" + str(informacion[5]))
    print("password: " + str(informacion[6]))
    print("identificador: " + str(informacion[7]))
    print("habilitado: " + str(informacion[8]))

    id = informacion[0]
    empresa = informacion[1]
    feria = informacion[2]
    telefono = informacion[3]
    correo = informacion[4]
    pais = informacion[5]
    password = informacion[6]
    identificador = informacion[7]
    habilitado = informacion[8]

    
    nombre_empleado = request.form.get("nombre_empleado")
    empresa_empleado = request.form.get("empresa_empleado")
    cargo_empleado = request.form.get("cargo_empleado")
    telefono_empleado = request.form.get("telefono_empleado")
    correo_empleado = request.form.get("correo_empleado")
    
    if request.method == "POST":
    
        while True:
            # Generar codigo aleatorio
            random_number = generate_random_number()
            identificador = random_number

            #check if the number exists in the table
            db.execute('SELECT * FROM registro_de_empleados WHERE identificador = ?', (random_number,))
            existing_row = db.fetchone()

            if existing_row is None:

                try:
                    # Recordar registrante
                    db.execute("INSERT INTO registro_de_empleados (nombre_empleado, empresa, cargo, telefono, correo, identificador) VALUES(?, ?, ?, ?, ?, ?)", (nombre_empleado, empresa_empleado, cargo_empleado, telefono_empleado, correo_empleado, identificador))
                    conn.commit()
                except Exception as e:
                    print(f"Error insertando en base de datos: {e}")
                    return render_template("failure.html", message=f"Error: {e}")

    else:
        return render_template("manejar_empresa.html", id=id, empresa=empresa, feria=feria, telefono=telefono, correo=correo, pais=pais, password=password, identificador=identificador, habilitado=habilitado)


# MANEJAR EMPRESA
# REGISTRAR NUEVO EMPLEADO
@app.route("/registrar_empleado", methods=["GET", "POST"])
@login_required
def registrar_empleado():
    user_id=session.get("user_id")
    informacion = db.execute("SELECT * FROM registro_de_empresas WHERE id = ?", (user_id,)).fetchone()

    # Generate random number
    def generate_random_number():
        return random.randint(100000, 999999)
    
    # Validar submision
    nombre_empleado = request.form.get("nombre_empleado")
    empresa_empleado = informacion[1]
    cargo_empleado = request.form.get("cargo_empleado")
    telefono_empleado = request.form.get("telefono_empleado")
    correo_empleado = request.form.get("correo_empleado")
    
    fecha_de_registro_empleado = date.today()

    # If user reached via POST
    if request.method == "POST":

        while True:
            # Generar codigo aleatorio
            identificador_empleado = generate_random_number()

            #check if the identificador number exists in the table
            db.execute('SELECT * FROM registro_de_visitantes WHERE identificador = ?', (identificador_empleado,))
            existing_row_empleado = db.fetchone()

            empleado_existente = db.execute("SELECT * FROM registro_de_empleados WHERE empresa = ? AND nombre_empleado = ?", (empresa_empleado, nombre_empleado,)).fetchone()

            if empleado_existente:
                return render_template("failure.html", message=f"El empleado {nombre_empleado} ya existe.")
            # Si el identificador de empleado no existe en la base de datos
            elif existing_row_empleado is None:
                try:

                    # Registrar empleado
                    db.execute("INSERT INTO registro_de_empleados (nombre_empleado, empresa, cargo, telefono, correo, identificador, fecha_de_registro_empleado) VALUES(?, ?, ?, ?, ?, ?, ?)", (nombre_empleado, empresa_empleado, cargo_empleado, telefono_empleado, correo_empleado, identificador_empleado, fecha_de_registro_empleado))
                    conn.commit()
                # Verificar errores
                except Exception as e:
                    print(f"Error registrando empleado en base de datos: {e}")
                    return render_template("failure.html", message=f"Error: {e}")
                
                # Si no existen errores reportar registro correcto
                return render_template("success.html", message=f"Registro de Empleado {nombre_empleado} de la empresa {empresa_empleado} Exitoso!")

    # If user reached via GET
    else:
        return render_template("registrar_empleado.html", empresa_empleado=empresa_empleado)


# MANEJAR EMPRESA
# VER EMPLEADOS REGISTRADOS
@app.route("/ver_empleados_registrados", methods=["GET", "POST"])
@login_required
def ver_empleados_registrados():
    user_id=session.get("user_id")

    informacion_empresa = db.execute("SELECT * FROM registro_de_empresas WHERE id = ?", (user_id,)).fetchone()

    empresa = informacion_empresa[1]

    db.execute("SELECT * FROM registro_de_empleados WHERE empresa = ?", (empresa,))
    empleados_registrados=db.fetchall()
    return render_template("ver_empleados_registrados.html", empleados_registrados=empleados_registrados, empresa=empresa)


# MANEJAR EMPRESA
# LECTOR QR
@app.route("/lector_qr")
@login_required
def lector_qr():
    
    return render_template('lector_qr.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
