from flask import Flask, redirect, render_template, request, session, send_file, abort, jsonify
import sqlite3
import random
import segno
import os
from PIL import Image
from flask_session import Session
from helpers import apology
from flask_sqlalchemy import SQLAlchemy





#---WHATSAPP BOT---#

import requests
import json

#---WHATSAPP BOT ---#

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
#app.secret_key = 'clave_secreta'

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SQLALCHEMY_ECHO'] = False
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

###---FOR DATABASE TABLE
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'datos_feria.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SQLA_db = SQLAlchemy(app)


class RegistroDeVisitantes(SQLA_db.Model):
    __tablename__ = 'registro_de_visitantes'
    id = SQLA_db.Column(SQLA_db.Integer, primary_key=True)
    empresa = SQLA_db.Column(SQLA_db.Text)
    nombre = SQLA_db.Column(SQLA_db.Text)
    cargo = SQLA_db.Column(SQLA_db.Text)
    documento = SQLA_db.Column(SQLA_db.Text)
    telefono = SQLA_db.Column(SQLA_db.Text)
    correo = SQLA_db.Column(SQLA_db.Text)
    ciudad = SQLA_db.Column(SQLA_db.Text)
    pais = SQLA_db.Column(SQLA_db.Text)
    feria = SQLA_db.Column(SQLA_db.Text)
    identificador= SQLA_db.Column(SQLA_db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'empresa': self.empresa,
            'nombre': self.nombre,
            'cargo': self.cargo,
            'documento': self.documento,
            'telefono': self.telefono,
            'correo': self.correo,
            'ciudad': self.ciudad,
            'pais': self.pais,
            'feria': self.feria,
            'identificador': self.identificador
        }

#with app.app_context():
#    SQLA_db.create_all()



"""
    def to_dict(self):
        return {
            'id': self.id,
            'empresa': self.empresa,
            'nombre': self.nombre,
            'cargo': self.cargo,
            'documento': self.documento,
            'telefono': self.telefono,
            'correo': self.correo,
            'ciudad': self.ciudad,
            'pais': self.pais,
            'feria': self.feria,
            'identificador': self.identificador
        }
    


def get_users(search=None, start=None, length=None, sort=None):
    query = "SELECT * FROM registro_de_visitantes"
    if search:
        query += f" WHERE nombre LIKE '%{search}%' OR documento LIKE '%{search}%' OR identificador LIKE '%{search}%'"
    if sort:
        query += f" ORDER BY {sort.replace('-', ' DESC,')}"

    if start is not None and length is not None:
        query += f" LIMIT {length} OFFSET {start}"

    db.execute(query)
    users = db.fetchall()
    return [User(*user).to_dict() for user in users]

def count_users(search=None):
    query = "SELECT COUNT(*) FROM users"
    if search:
        query += f"WHERE name LIKE '%{search}%' OR email LIKE '%{search}%'"

    db.execute(query)
    return db.fetchone()[0]

def update_user(user_id, data):
    if 'id' not in data or int(data['id']) != user_id:
        abort(400)

    for field in ['name', 'age', 'address', 'phone', 'email']:
        if field in data:
            db.execute(f"UPDATE users SET {field} = ? WHERE id = ?",
                            (data[field], user_id))
    conn.commit()


#### END FOR TABLE DB CONNECT #######
"""



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


    #return render_template("index.html", ferias=FERIAS)
    return render_template("index.html", var_feria=var_feria)
    #return render_template("login.html")
    


#### for table route
@app.route('/api/data')
def data():
    query = RegistroDeVisitantes.query

    # search filter
    search = request.args.get('search')
    if search:
        query = query.filter(SQLA_db.or_(
            RegistroDeVisitantes.nombre.like(f'%{search}%'),
            RegistroDeVisitantes.documento.like(f'%{search}%'),
            RegistroDeVisitantes.identificador.like(f'%{search}%'),
        ))
    total = query.count()

    # sorting
    sort = request.args.get('sort')
    if sort:
        order = []
        for s in sort.split(','):
            direction = s[0]
            column_name = s[1:]
            #if column_name not in ['id', 'nombre', 'documento', 'pais', 'feria', 'identificador']:
            if column_name in ['id', 'nombre', 'documento', 'pais', 'feria', 'identificador']:
                col = getattr(RegistroDeVisitantes, column_name)
                #nombre = 'nombre'
            #col = getattr(RegistroDeVisitantes, nombre)
            else:
                col = RegistroDeVisitantes.nombre

            if direction == '-':
                col = col.desc()
            order.append(col)
        if order:
            query = query.order_by(*order)

    # pagination
    start = request.args.get('start', type=int, default=-1)
    length = request.args.get('length', type=int, default=-1)
    if start != -1 and length != -1:
        query = query.offset(start).limit(length)

    # response
    return {
        'data': [user.to_dict() for user in query],
        'total': total,
    }

@app.route('/api/data', methods=['POST'])
def update():
    data = request.get_json()
    if 'id' not in data:
        abort(400)
    user = RegistroDeVisitantes.query.get(data['id'])
    for field in ['id', 'empresa', 'nombre', 'cargo', 'documento', 'telefono', 'correo', 'ciudad', 'pais', 'feria', 'identificador']:
        if field in data:
            setattr(user, field, data[field])
    SQLA_db.session.commit()
    return '', 204

####



# DESREGISTRARSE
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





# REGISTRO
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
    
    
    while True:
        # generate a random 6 digit number
        random_number = generate_random_number()
        identificador = random_number

        #check if the number exists in the table
        db.execute('SELECT * FROM registro_de_visitantes WHERE identificador = ?', (random_number,))
        existing_row = db.fetchone()

        if existing_row is None:
            if not nombre or feria not in FERIAS:
                return render_template("failure.html", message="Casilla de nombre vacia")

            try:

                # Recordar registrante
                db.execute("INSERT INTO registro_de_visitantes (empresa, nombre, cargo, documento, telefono, correo, ciudad, pais, feria, identificador) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (empresa, nombre, cargo, documento, telefono, correo, ciudad, pais, feria, random_number))
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
            'Authorization': 'Bearer EAAExyzOF11QBO22RcOKLdbkokOE54IMxQXG3pFJ5ske4JFdH3U3amwM4xachVJPQO5ADayLk4rk55eM9dgLIqCCpyFHKZBcsRBj9bhtCLgySrkVI7NGD2IZBkGW6Mqy54JTfHuLm5Crg7zNdDHrVyhI7IyicNk8R4eoKe7mBpp7gNxqN6O6mZBCbjZBlzre5jFybHCzDVVIZBWzm5'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            print(response.text)
            
            ###############################
            # Confirm registration
            return render_template("success.html")




# REGISTRANTES
@app.route("/registrantes")



#@login_required
###def registrantes():
###    db.execute("SELECT * FROM registro_de_visitantes")
###    registrantes=db.fetchall()
###    return render_template("registrantes.html", registrantes=registrantes)


def registrantes():

    visitantes = RegistroDeVisitantes.query
    query_1 = RegistroDeVisitantes.query.get(1)
    print("QUEIRYYYYYY")
    print(query_1)
    return render_template('registrantes.html', visitantes=visitantes)



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
        #session["user_id"] = user[0]

        # Redirect user to home page

        ###---DEVELOPER SWITCH---###
        
        ###---REMOTE---###
        #return redirect("/webapp/registrantes")
    
        ###---LOCAL---###
        return redirect("/registrantes")
        
        

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

    ### DEVELOPER SWITCH ###

    ###--- REMOTE ---###
    #return redirect("/webapp/")
    ###--- LOCAL ---###
    return redirect("/")





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
            'Authorization': 'Bearer EAAExyzOF11QBOzr7kZClWzXJ628XhdkgxvZBb9K9f8cVYyzBNq6GfGn3StolJ3mifBaPdGZA45AvKyJwDOFMInuaHplCek9BUhZA5HABrwJms8UUZAdQs7iw2AI34lfyWS8FowZC1FizvDLdezVpwgezGyLamU4sRPqrsiv3Ba194kdO925Vl4r2ZCooUZCOzp2JuCa0KsGiixRVp1tw'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            print(response.text)"""


            





        ####-----------------------####





            # Render the HTML template with the QR code data
            return render_template('qr_template.html', data=data_str_html, qr_path=qr_path)

    else:
        return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)