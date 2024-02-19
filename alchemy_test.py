#import sqlalchemy
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData

engine = create_engine("sqlite:///datos_feria.db")

conn = engine.connect()

metadata = MetaData()

registro_de_visitantes = Table('registro_de_visitantes', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('empresa', String),
                 Column('nombre', String),
                 Column('cargo', String),
                 Column('documento', String),
                 Column('telefono', String),
                 Column('correo', String),
                 Column('ciudad', String),
                 Column('pais', String),
                 Column('feria', String), 
                 Column('identificador', String),

                )
                 

class RegistroDeVisitantes:
    def __init__(self, id, empresa, nombre, cargo, documento, telefono, correo, ciudad, pais, feria, identificador):
        self.id = id
        self.empresa = empresa
        self.nombre = nombre
        self.cargo = cargo
        self.documento = documento
        self.telefono = telefono
        self.correo = correo
        self.ciudad = ciudad
        self.pais = pais
        self.feria = feria
        self.identificador = identificador


with engine.connect() as connection:
    metadata.create_all(engine)

    result = connection.execute(registro_de_visitantes.select())
    for row in result:
        print(row)

#print(repr(metadata.tables['registro_de_visitantes']))


