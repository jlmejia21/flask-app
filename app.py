#importe de librerias

import json
from cgi import FieldStorage
from io import StringIO

import numpy as np
import pandas as pd
import requests
from flask import Flask, request
from flask_cors import CORS
from sklearn.cluster import KMeans

app = Flask(__name__)
CORS(app)

#api_url = "http://localhost:3000/"
api_url = "https://seashell-app-x9ubd.ondigitalocean.app/"

class JSONObject:
  def __init__( self, dict ):
      vars(self).update( dict )

def getSales():
    salesData = pd.read_csv("Ventas.csv")
    return pd.DataFrame(salesData)
#Get Stores

def getStoresCSV():
    storeData = pd.read_csv("Tiendas.csv")
    return pd.DataFrame(storeData)

def getStoresApi():
    storeResponse = requests.get("{}{}".format(api_url,'store'))
    dataStore = storeResponse.json()
    return dataStore['stores']

def getOrdersByCodes(codes):
    url = "{}{}".format(api_url,'order/find')
    storeResponse = requests.post(url, data = {"codes": codes})
    dataStore = storeResponse.json()
    return dataStore['data']


def mapOrders(idSale, ubigeoSale):
    data = []
    for i in range(idSale.size):
        ubigeo  = ubigeoSale[i].split(",")
        r = {'order': idSale[i], 
             'latitude': ubigeo[0].strip(),
             'longitude': ubigeo[1].strip() }
        data.append(r)
    return data

def main():
    dtSales = getSales()
    idSale = dtSales['id'].values.astype(str)
    latSale = dtSales['latitud'].values
    lngSale = dtSales['longitud'].values

    dtStore =  pd.DataFrame.from_dict(getStoresApi())
    # dtStore = getStoresCSV()
    idStore = dtStore['id'].values
    nameStore = dtStore['name'].values
    latStore = dtStore['latitude'].values
    lngStore = dtStore['longitude'].values

    #Zip list
    listSales = np.array(list(zip(latSale,lngSale)))
    listStores = np.array(list(zip(latStore,lngStore)))

    #Run kmeans algorithm
    n_clusters = int(listStores.size / 2)
    Kmeans = KMeans(n_clusters = n_clusters, init = listStores, n_init = 1)
    Kmeans.fit(listSales)
    centroids = Kmeans.cluster_centers_
    labels = Kmeans.labels_

    #Show Results

    results = []
    for i in range(n_clusters):
        idx = labels == i
        r = {'store':str(idStore[i]), 'customer': idSale[idx].tolist()} 
        results.append(r)
    return results

def mainPost(fileData):
    salesData = pd.read_csv(fileData.stream)
    dtSales = pd.DataFrame(salesData)
    idSale = dtSales['id'].values.astype(str)
    latSale = dtSales['latitud'].values
    lngSale = dtSales['longitud'].values

    dtStore =  pd.DataFrame.from_dict(getStoresApi())
    # dtStore = getStoresCSV()
    idStore = dtStore['id'].values
    nameStore = dtStore['name'].values
    latStore = dtStore['latitude'].values
    lngStore = dtStore['longitude'].values

    #Zip list
    listSales = np.array(list(zip(latSale,lngSale)))
    listStores = np.array(list(zip(latStore,lngStore)))

    #Run kmeans algorithm
    n_clusters = int(listStores.size / 2)
    Kmeans = KMeans(n_clusters = n_clusters, init = listStores, n_init = 1)
    Kmeans.fit(listSales)
    centroids = Kmeans.cluster_centers_
    labels = Kmeans.labels_

    #Show Results

    results = []
    for i in range(n_clusters):
        idx = labels == i
        r = {'store':str(idStore[i]), 'customer': idSale[idx].tolist()} 
        results.append(r)
    return results

def mainPostExcel(fileData):

    ordersData = pd.read_excel(fileData, engine='openpyxl')
    dtOrders = pd.DataFrame(ordersData)
    dtOrders['ID'] = dtOrders['ID'].astype(str)
    idOrders = dtOrders['ID'].values
    ubigeoOrders = dtOrders['AQUI_GEO_MANUAL'].values

    #Validate orders processed
    # idsProcessed = []
    # getOrdersProcessed  = getOrdersByCodes(idOrders)
    # for i in range(len(getOrdersProcessed)):
    #     idsProcessed.append(getOrdersProcessed[i]['code'])
    # dtOrders = dtOrders[~dtOrders['ID'].isin(idsProcessed)]
    # idOrders = dtOrders['ID'].values.astype(str)
    # ubigeoOrders = dtOrders['AQUI_GEO_MANUAL'].values
    #########

    latSale = []
    lngSale = []

    for i in range(ubigeoOrders.size):
        ubigeo  = str(ubigeoOrders[i]).split(",")
        latSale.append(float(ubigeo[0].strip()))
        lngSale.append(float(ubigeo[1].strip()))    

    dtStore =  pd.DataFrame.from_dict(getStoresApi())
    idStore = dtStore['id'].values
    nameStore = dtStore['name'].values
    latStore = dtStore['latitude'].values
    lngStore = dtStore['longitude'].values

    #Zip list

    listSales = np.array(list(zip(latSale,lngSale)))
    listStores = np.array(list(zip(latStore,lngStore)))

    #Run kmeans algorithm
    n_clusters = int(listStores.size / 2)
    Kmeans = KMeans(n_clusters = n_clusters, init = listStores, n_init = 1)
    Kmeans.fit(listSales)
    centroids = Kmeans.cluster_centers_
    labels = Kmeans.labels_

    #Show Results

    results = []
    for i in range(n_clusters):
        idx = labels == i
        storeObj = { 'id': str(idStore[i]), 'name':nameStore[i]  }

        r = {  
            # 'store':  str(idStore[i]), 
            'store': { 'id': str(idStore[i]), 
                       'name': nameStore[i], 
                       'latitude': latStore[i],
                       'longitude': lngStore[i]}, 
            'orders': mapOrders(idOrders[idx],ubigeoOrders[idx] ) , 
            # 'customer': idSale[idx].tolist() , 
            # 'ubigeo': ubigeoSale[idx].tolist()
            } 
        results.append(r)
    return results


@app.route("/", methods = ['GET','POST'] )
def getData():
    if request.method == 'GET':
        return main()
    if request.method == 'POST':
        f = request.files['file']
        return mainPostExcel(f)
