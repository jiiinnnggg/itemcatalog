#!/usr/bin/env python

from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

from stores_db import Base, Manager, Store, Product
from flask import session as login_session

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json, cgi
from flask import make_response
import requests


app = Flask(__name__)


#CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Shoe Store Sample App"


# Connect to Database and create database session
engine = create_engine('sqlite:///shoestores.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def getManager(manager_id):
    manager = session.query(Manager).filter_by(id=manager_id).one()
    return manager


# Homepage, display all stores
@app.route('/')
@app.route('/store/')
def showStores():
  stores = session.query(Store).order_by(asc(Store.name))
  print "\n"
  print login_session
  print "\n"
  if 'username' not in login_session:
      return render_template('publicstores.html', stores=stores)
  else:
      return render_template('stores.html', stores=stores)


#Show a store's inventory
@app.route('/store/<int:store_id>/')
@app.route('/store/<int:store_id>/inventory/')
def showInventory(store_id):
    store = session.query(Store).filter_by(id = store_id).one()
    products = session.query(Product).filter_by(store_id = store_id).all()
    manager = getManager(store.manager_id)
    if 'username' not in login_session or manager.id != login_session['manager_id']:
        return render_template('publicinventory.html')
    else:
        return render_template('inventory.html')


if __name__ == '__main__':
  #app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
