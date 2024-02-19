from flask import Flask, redirect, render_template, request, session, send_file
import sqlite3
import random
import segno
import os
from PIL import Image
from flask_session import Session
from helpers import apology


app = Flask(__name__)
#app.secret_key = 'clave_secreta'

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Conectar a base de datos
conn = sqlite3.connect('datos_feria.db', check_same_thread=False)

# Create a cursor Object
db = conn.cursor()


# Listado de Ferias
FERIAS = [
    "TEXTIL",
    "GRAFICA"
]




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
    return render_template("index.html", ferias=FERIAS)
    #return render_template("login.html")
    



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


    ### DEVELOPER SWITCH###
        
    # -----FOR SERVER-----
    #return redirect("/webapp/registrantes")

    # -----LOCAL-----
    return redirect("/registrantes")





# REGISTRO
@app.route("/registro", methods=["POST"])
def register():

    #generate random number
    def generate_random_number():
        return random.randint(100000, 999999)
    
    # Validar submision
    nombre = request.form.get("nombre")
    direccion = request.form.get("direccion")
    empresa = request.form.get("empresa")
    cargo = request.form.get("cargo")
    rubro = request.form.get("rubro")
    telefono = request.form.get("telefono")
    correo = request.form.get("correo")
    feria = request.form.get("feria")
    
    while True:
    # generate a random 6 digit number
        random_number = generate_random_number()

        #check if the number exists in the table
        db.execute('SELECT * FROM registro_de_visitantes WHERE identificador = ?', (random_number,))
        existing_row = db.fetchone()

        if existing_row is None:

            if not nombre or feria not in FERIAS:
                return render_template("failure.html", message="Casilla de nombre vacia")


            # Recordar registrante
            db.execute("INSERT INTO registro_de_visitantes (nombre, direccion, empresa, cargo, rubro, telefono, correo, feria, identificador) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (nombre, direccion, empresa, cargo, rubro, telefono, correo, feria, random_number))
            conn.commit()


        # Confirm registration
        return render_template("success.html")




# REGISTRANTES
@app.route("/registrantes")
#@login_required
def registrantes():
    db.execute("SELECT * FROM registro_de_visitantes")
    registrantes=db.fetchall()
    return render_template("registrantes.html", registrantes=registrantes)



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





# GENERATE QR
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
            #data_str = ', '.join(map(str, data_to_encode))


            # Convert the tuple to a string with line breaks
            #data_str = '\n'.join(map(str, data_to_encode))
            #data_str = '\n'.join([f"{column}: {value}" for column, value in zip(data_to_encode.keys(), data_to_encode)])

            # Column names (replace these with your actual column names)
            column_names = ['id', 'Nombre', 'Direccion', 'Empresa', 'Cargo', 'Rubro', 'Telefono', 'Correo', 'Feria', 'Identificador']

            # Convert the tuple to a string with line breaks
            data_str = '\n'.join([f"{column}: {value}" for column, value in zip(column_names[1:], data_to_encode[1:])])
            print(data_str)

            # Display data with line breaks in HTML
            data_str_html = data_str.replace('\n', '<br>')

            # Assuming your data_to_encode is a tuple
            vcard_data = f"BEGIN:VCARD\nVERSION:3.0\nN:{data_to_encode[column_names.index('Nombre')]}\nORG:{data_to_encode[column_names.index('Empresa')]}\nROLE:{data_to_encode[column_names.index('Cargo')]}\nTEL:{data_to_encode[column_names.index('Telefono')]}\nEMAIL:{data_to_encode[column_names.index('Correo')]}\nEND:VCARD"
            print(vcard_data)

            
            # Create a QR code with Segno
            #qr = segno.make(data_str)
            qr = segno.make(vcard_data)


            
        
            # Save the QR code as a temporary file
            filename_png = os.path.join('static', 'temp_qr.png')

            qr.save(filename_png, scale=5)

            # Open the PNG file with Pillow and save it as JPG
            image = Image.open(filename_png)
            filename_jpg = os.path.join('static', 'temp_qr.jpg')
            image.convert("RGB").save(filename_jpg)

            # Render the HTML template with the QR code data
            return render_template('qr_template.html', data=data_str_html, qr=qr)

    else:
        return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)