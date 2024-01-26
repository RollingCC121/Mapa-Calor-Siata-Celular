from crypt import methods
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.express as px
from flask import Flask, request

#crea el servidor web
app = Flask(__name__)

fecha = [] #cremos una lista vacia
latitudes = [] #creamos una lista vacia
longitudes = [] #creamos una lista vacia
m = [] #creamos una lista vacia

#creamos una fucnion que calcula la calidad del aire 
def calculadora(m):
    polucion = 0
    #for valores in m:
    if m >= 0 and m <= 12:
        polucion = 0
    elif m >= 13 and m <= 35:
        polucion = 1
    elif m >= 36 and m <= 55:
        polucion = 2
    elif m >= 56:
        polucion = 3
    return polucion

#creamos una funciona que genere alertas de calidad de aire
def respuesta(edad,x,y):
    #creaos la interpolacion para calcular la polucion segun la posicion del celular
    c=griddata((latitudes,longitudes),m,(x,y),method="nearest") 
    mensaje=''
    newEdad = int(edad) #tranformamos los datos de edad a int

    if c >= 0 and c <= 12: #condicion que calcula la calidad
        #mensaje de retorno de calidad
        return "puedes salir sin problemas ni restricciones"
    
    elif c >= 12.1 and c <= 35.4:
        if newEdad >= 60:
            return "debes evitar la actividad al aire libre"
        else:
            return "puedes salir sin problemas ni restriccionesss"
    
    elif c >= 35.5 and c <= 55.4:
        return "Puede sufrir problemas respiratorios"
    
    elif c >= 56:
        return "Mayor probabilidad de problemas respiratorios"


#la direccion de donde se sacan los datos
url = "http://siata.gov.co:8089/estacionesAirePM25/cf7bb09b4d7d859a2840e22c3f3a9a8039917cc3/"
captura_web = pd.read_json(url,convert_dates='True') #captura los datos de la pg del siata
captura_datos_puros = captura_web.datos.values.tolist()
#captura_web.to_csv("datos-siata-json.txt")

#con el ciclo for guardamos los datos capturamos en las listas
for i in range(0,18):
  fecha.append(captura_web.datos[i]['ultimaActualizacion'])
  latitudes.append(captura_web.datos[i]['coordenadas'][0]['latitud'])
  longitudes.append(captura_web.datos[i]['coordenadas'][0]['longitud'])
  m.append(captura_web.datos[i]['valorICA'])
print(m)

m=np.array(m) #creamos un array con m
ysuperior=max(latitudes) #calculamos el valor maxino de latitud
yinferior=min(latitudes) #calculamos el valor minimo de latitud
xinferior=min(longitudes) #calculamos el valor maximo de longitudes
xsuperior=max(longitudes) #calculamos el valor minimo de longituf

#creamos una grilla o malla 
grid_x, grid_y = np.meshgrid(np.linspace(xinferior,xsuperior,100), np.linspace(yinferior,ysuperior,100))

#construyo la interpolacion
from scipy.interpolate import griddata

#predecimos los valores de m segun con los algoritmos de nearest, linear y cubic
grid_z0 = griddata((latitudes, longitudes), m, (grid_y, grid_x), method='nearest') 
grid_z1 = griddata((latitudes, longitudes), m, (grid_y, grid_x), method='linear')
grid_z2 = griddata((latitudes, longitudes), m, (grid_y, grid_x), method='cubic')

#llenar los datos NaN con el valor de nearest para completar los datos en z1 y z2
rows = grid_z0.shape[0]
cols = grid_z0.shape[1]

for x in range(0, cols):
    for y in range(0, rows):
        if np.isnan(grid_z1[x,y]):
            grid_z1[x,y]=grid_z0[x,y]
        if np.isnan(grid_z2[x,y]):
            grid_z2[x,y]=grid_z0[x,y]

#crea una lista
l_z = []
l_lat = []
l_lon = []
for x in range(0, cols - 1):
    for y in range(0, rows -1):
        l_z.append((calculadora(grid_z2[x,y]))) #calculamos la calidad del aire con la funcion calcular
        l_lat.append(grid_y[x,y])
        l_lon.append(grid_x[x,y])

data = pd.DataFrame() # creao un data frame para manejar facilmente los datos
data["dato"] = l_z
data["lat"] = l_lat
data["lon"] = l_lon
fig2 = px.scatter_mapbox(data, lat='lat', lon='lon', 
                       mapbox_style="open-street-map")


@app.route('/') #creamos la ruta principal
def home():
    return 'home'

@app.route('/capturarDatos', methods=['POST']) #creamos la ruta donde se capturan los datos
def capturarDatos():
    values = request.values #se capturan los datos 
    #se comienzan a guardar en las variables como str
    datos=str(values).split(",")[2].split("'")[1]
    edad=str(datos).split(";")[0]
    longitud=str(datos).split(";")[1].split('=')[1]
    latitud=str(datos).split(";")[2].split('=')[1]
    #imprimos los datos para verificar
    print(values)
    print("getdata","{", "edad=",edad, " longitud=", longitud, " latitud=", latitud, "}")

    #creamos una variable que guarda la respuesta de la funcion respuesta
    mensaje = respuesta(edad,longitud,latitud) 
    return mensaje

    
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=80) #inicamos la pagina
