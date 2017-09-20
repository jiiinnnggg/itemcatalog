#!/usr/bin/env python

from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

from stores_db import Base, Manager, Store, ShoeItem
from flask import session as login_session

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json, cgi
from flask import make_response
import requests


app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///shoestores.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()




if __name__ == '__main__':
  #app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
