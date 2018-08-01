from __future__ import print_function
import json
import cgi
from collections import namedtuple
from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Business, BizList, ListObject
from flask import session as login_session
from yelptools import yelp_request, term_loc_search
from yelptools import get_business, query_api, render_ntuples
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response
import requests
import httplib2


app = Flask(__name__)


# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db', connect_args={'check_same_thread':False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# login as a google user + oauth2
CLIENT_ID = json.loads(
    open('google_client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase +
                    string.ascii_lowercase +
                    string.digits) for x in xrange(32))
    login_session['state'] = state
    print("\nThe current session state is %s \n" % login_session['state'])
    return render_template('login.html', STATE=state)


# GOOGLE CONNECT / from OAuth2.0 project
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code, also from the ajax code on login.html
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
                        'google_client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
        print(credentials)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token of the credentials object is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    debug_output = "\nDebug output for login:"
    debug_output += "\nAccess Token: %s" % cgi.escape(access_token)
    debug_output += "\nUser ID: %s" % cgi.escape(result['user_id'])
    debug_output += "\nIssued to: %s \n" % cgi.escape(result['issued_to'])
    print(debug_output)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    login_session['provider'] = 'google'

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't, make a new one in the db
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h6>Welcome, '
    output += login_session['username']
    output += '!</h6>'
    output += 'User ID #: %s' % login_session['user_id']
    output += '<br><img src="'
    output += login_session['picture']
    output += """ " style = "width: 150px; height: 150px;
      border-radius: 20px;-webkit-border-radius: 20px;
      -moz-border-radius: 20px;"> """
    flash("You are now logged in as: {0} ({1})".format(
            login_session['username'], login_session['email']))
    print("Login with Google done!\n")
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# GOOGLE DISCONNECT - Revoke a current user's token and reset their session
@app.route('/gdisconnect')
def gdisconnect():
    if 'access_token' in login_session:
        access_token = login_session['access_token']
    if access_token is None:
        print('\nAccess Token is None')
        response = make_response(json.dumps(
                                 'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200' or result['status'] == '400':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['state']
        del login_session['user_id']
        del login_session['provider']
        if result['status'] == '400':
            print("\nToken expired (Status 400).\n")
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# disconnect
@app.route('/disconnect')
def disconnect():
    try:
        if login_session['provider'] is not None:
            if login_session['provider'] == 'google':
                gdisconnect()
                flash("You have been successfully logged out via Google.")
                return redirect(url_for('showHome'))
        else:
            flash("You were not logged into Google.")
            return redirect(url_for('showHome'))
    except:
        flash("You were not logged in to begin with.")
        return redirect(url_for('showHome'))


@app.route('/')
def showHome():
    return render_template('index.html')


@app.route('/search')
def searchYelp():
    q_term = request.args.get('find_desc')
    q_location = request.args.get('find_loc')
    q_search_limit = request.args.get('search_limit')
    args = [q_term, q_location, q_search_limit]
    if all(a is None for a in args):
        print("\nAll args are none.")
        return render_template('yelpsearch.html')

    if q_term is not None and q_term != '':
        TERM = q_term
    else:
        TERM = 'food'
    if q_location is not None and q_location != '':
        LOCATION = q_location
    else:
        LOCATION = '10010'
    if q_search_limit is not None and q_search_limit != '':
        SEARCH_LIMIT = q_search_limit
    else:
        SEARCH_LIMIT = 10

    try:
        flash("""Here are your {0} search results for '{1}' near
              '{2}'""".format(SEARCH_LIMIT, TERM, LOCATION))
        result = query_api(TERM, LOCATION, SEARCH_LIMIT)
        ntuples = render_ntuples(result)
        return render_template('yelpsearch.html',
                               term=TERM, location=LOCATION,
                               search_limit=SEARCH_LIMIT, ntuples=ntuples)
    except:
        flash("Error with query, returning the default search...")
        result = query_api('food', '10010', SEARCH_LIMIT)
        ntuples = render_ntuples(result)
        return render_template('yelpsearch.html',
                               term='food', location='10010',
                               search_limit=SEARCH_LIMIT, ntuples=ntuples)


@app.route('/publiclists')
def publicLists():
    userlists = session.query(BizList).all()
    return render_template('publiclists.html', lists=userlists)


@app.route('/publiclists/<int:list_id>')
def showListPublic(list_id):
    userlist = session.query(BizList).filter_by(id=list_id).one()
    listobjs = session.query(ListObject).filter_by(list_id=list_id).all()
    return render_template('showListPublic.html', list=userlist, objs=listobjs)


@app.route('/userhome')
def userHome():
    if 'username' not in login_session:
        flash("Please login to go to the user homepage.")
        return redirect(url_for('showHome'))
    print(login_session)
    uid = login_session['user_id']
    userlists = session.query(BizList).filter_by(user_id=uid).all()
    return render_template('welcomeUser.html', lists=userlists)


@app.route('/user/<int:user_id>/list/new', methods=['GET', 'POST'])
def newUserList(user_id):
    if 'username' not in login_session:
        flash("Please login to create or modify a user list.")
        return redirect(url_for('showHome'))
    if request.method == 'POST':
        newList = BizList(name=request.form['name'],
                          user_id=login_session['user_id'],
                          description=request.form['description'])
        session.add(newList)
        flash('New List "%s" Successfully Created' % newList.name)
        session.commit()
        return redirect(url_for('userHome'))
    else:
        user = session.query(User).filter_by(
                    email=login_session['email']).one()
        return render_template('newUserList.html', user=user)


@app.route('/user/<int:user_id>/list/<int:list_id>', methods=['GET', 'POST'])
def showUserList(user_id, list_id):
    if 'username' not in login_session:
        flash("Please login to create or modify a user list.")
        return redirect(url_for('showHome'))
    user = session.query(User).filter_by(id=user_id).one()
    userlist = session.query(BizList).filter_by(id=list_id).one()
    listobjs = session.query(ListObject).filter_by(list_id=list_id).all()
    if login_session['user_id'] != userlist.user_id:
        flash("You are only allowed to edit your own lists.")
        return redirect(url_for('userHome'))
    if request.method == 'POST':
        obj_id_remove = request.form['id']
        obj_to_rm = session.query(ListObject).filter_by(id=obj_id_remove).one()
        session.delete(obj_to_rm)
        flash("List object '%s' removed." % obj_to_rm.name)
        session.commit()
        # can add ajax to refresh and clear cache (optional)
        return render_template('showUserList.html', user=user,
                               list=userlist, objs=listobjs)
    else:
        return render_template('showUserList.html', user=user,
                               list=userlist, objs=listobjs)


@app.route('/user/<int:user_id>/list/<int:list_id>/delete',
           methods=['GET', 'POST'])
def deleteList(user_id, list_id):
    if 'username' not in login_session:
        flash("Please login to modify or delete a user list.")
        return redirect(url_for('showHome'))
    user = session.query(User).filter_by(id=user_id).one()
    userlist = session.query(BizList).filter_by(id=list_id).one()
    if userlist.user_id != login_session['user_id']:
        flash("You are only allowed to modify or delete your own lists.")
        return redirect(url_for('showUserList',
                                user_id=user.id, list_id=userlist.id))
    if request.method == 'POST':
        session.delete(userlist)
        session.commit()
        flash("Delete list '%s'." % userlist.name)
        return redirect(url_for('userHome'))
    else:
        return render_template('deleteList.html', list=userlist)


@app.route('/user/<int:user_id>/list/<int:list_id>/addbiz',
           methods=['GET', 'POST'])
def addBizToList(user_id, list_id):
    if 'username' not in login_session:
        flash("Please login to create or modify a user list.")
        return redirect(url_for('showHome'))
    user = session.query(User).filter_by(id=user_id).one()
    userlist = session.query(BizList).filter_by(id=list_id).one()
    if userlist.user_id != login_session['user_id']:
        flash("You are only allowed to modify or delete your own lists.")
        return redirect(url_for('showUserList',
                                user_id=user.id, list_id=userlist.id))
    if request.method == 'POST':
        newBizname = request.form['id_name']
        match = session.query(Business).filter_by(id_name=newBizname).all()
        if not match:
            newBiz = Business(name=request.form['name'],
                              id_name=request.form['id_name'],
                              url=request.form['url'],
                              rating=request.form['rating'],
                              review_count=request.form['review_count'],
                              price=request.form['price'],
                              image_url=request.form['image_url'],
                              phone=request.form['phone'],
                              address=request.form['address'])
            session.add(newBiz)
            flash('New Business "%s" Added' % newBiz.name)
            newListObj = ListObject(name=newBiz.id_name,
                                    list_id=list_id)
            session.add(newListObj)
            flash('New List Object "{0}" added to list {1}'.format(
                  newListObj.name, list_id))
            session.commit()
            return redirect(url_for('showUserList', user_id=user_id,
                                    list_id=list_id))
        else:
            flash('Business "%s" already exists.' % match[0].name)
            # Add section to check if obj already in list
            newListObj = ListObject(name=match[0].id_name,
                                    list_id=list_id)
            session.add(newListObj)
            flash('New List Object "{0}" added to list {1}'.format(
                  newListObj.name, list_id))
            session.commit()
            return redirect(url_for('showUserList', user_id=user_id,
                                    list_id=list_id))
    else:
        q_term = request.args.get('find_desc')
        q_location = request.args.get('find_loc')
        q_search_limit = request.args.get('search_limit')
        args = [q_term, q_location, q_search_limit]
        if all(a is None for a in args):
            print("\nAll args are none.")
            return render_template('addBizToList.html',
                                   user=user, list=userlist)
        if q_term is not None and q_term != '':
            TERM = q_term
        else:
            TERM = 'food'
        if q_location is not None and q_location != '':
            LOCATION = q_location
        else:
            LOCATION = '10010'
        if q_search_limit is not None and q_search_limit != '':
            SEARCH_LIMIT = q_search_limit
        else:
            SEARCH_LIMIT = 5
        try:
            flash("""Here are your {0} search results for '{1}' near
                  '{2}'""".format(SEARCH_LIMIT, TERM, LOCATION))
            result = query_api(TERM, LOCATION, SEARCH_LIMIT)
            ntuples = render_ntuples(result)
            return render_template('addBizToList.html', list=userlist,
                                   term=TERM, location=LOCATION, user=user,
                                   search_limit=SEARCH_LIMIT, ntuples=ntuples)
        except:
            flash("Error with query, returning the default search...")
            result = query_api('food', '10010', SEARCH_LIMIT)
            ntuples = render_ntuples(result)
            return render_template('addBizToList.html', list=userlist,
                                   term='food', location='10010', user=user,
                                   search_limit=SEARCH_LIMIT, ntuples=ntuples)


@app.route('/user/<int:user_id>/list/<int:list_id>/edit',
           methods=['GET', 'POST'])
def editListAttr(user_id, list_id):
    if 'username' not in login_session:
        flash("Please login to create or modify a user list.")
        return redirect(url_for('showHome'))
    userlist = session.query(BizList).filter_by(id=list_id).one()
    user = session.query(User).filter_by(id=user_id).one()
    if login_session['user_id'] != userlist.user_id:
        flash("You are only allowed to edit your own lists.")
        return redirect(url_for('showUserList',
                                user_id=user.id, list_id=userlist.id))
    if request.method == 'POST':
        userlist.description = request.form['description']
        session.add(userlist)
        session.commit()
        flash("List description modified.")
        return redirect(url_for('showUserList',
                                user_id=user_id, list_id=list_id))
    else:
        return render_template('editListAttr.html', list=userlist, user=user)


# see businesses, not JSON
@app.route('/bizlist')
def bizList():
    bidnesses = session.query(Business).all()
    return render_template('new_entry.html', businesses=bidnesses)


# see objects in a given list, not JSON
@app.route('/bizlist/<int:bizlist_id>')
def bizListObjs(bizlist_id):
    blistobjs = session.query(ListObject).filter_by(list_id=bizlist_id).all()
    return render_template('b_list_objs.html', objects=blistobjs)


# show all businesses stored in db
@app.route('/JSON/businesses/all')
def showBusinessesJSON():
    businesses = session.query(Business).all()
    return jsonify(businesses=[b.serialize for b in businesses])


# show all users
@app.route('/JSON/users/all')
def showUsersJSON():
    users = session.query(User).all()
    return jsonify(users=[u.serialize for u in users])


# get all lists created by a particular user
@app.route('/JSON/users/<int:user_id>/lists')
def showUserListsJSON(user_id):
    userlists = session.query(BizList).filter_by(user_id=user_id).all()
    return jsonify(lists=[l.serialize for l in userlists])


# get all objects for a particular list
@app.route('/JSON/lists/<int:list_id>')
def showListObjectsJSON(list_id):
    listobjs = session.query(ListObject).filter_by(list_id=list_id).all()
    return jsonify(objects=[o.serialize for o in listobjs])


if __name__ == '__main__':
    app.secret_key = 'open_sesame'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
