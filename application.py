from flask import Flask, render_template, url_for, request, redirect, flash
from flask import session as login_session
app = Flask(__name__)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item 
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


# Connect to the Database
engine = create_engine('sqlite:///itemcatalogue.db')
Base.metadata.bind = engine

# Create database session
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    print('THE CODE IS: ' + code)

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
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
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if the user is already logged in
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']


    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output

# Disconnect the Google connection

@app.route('/gdisconnect/')
def gdisconnect():
    # Only disconnect a connected user

    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the users session
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(json.dumps('Failed to revoke token for given user'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/')
@app.route('/catalogue/')
def home():
    session = DBSession()
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return render_template('cataloguehome.html', categories=categories, items=items)


# View Item list per category
@app.route('/catalogue/<int:category_id>/')
@app.route('/catalogue/<int:category_id>/items/')
def item_list(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id = category_id).one_or_none()
    if category == None:
        return redirect(url_for('home'))
    items = session.query(Item).filter_by(category_id=category_id).all()
    return render_template('categorylist.html', category = category, items=items)


# View individual item details
@app.route('/catalogue/<int:category_id>/<int:item_id>/')
def item(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id = category_id).one()
    item = session.query(Item).filter_by(category_id= category_id, id=item_id).one()
    return render_template('listitem.html', category_id = category_id, item_id=item_id, category = category, item = item)

# Add new category
@app.route('/catalogue/categories/add/', methods = ['GET', 'POST'])
def add_category():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        if request.form['name'] == '':
            return render_template('addcategory.html')
        new_category = Category(name = request.form['name'])
        session.add(new_category)
        session.commit()
        flash('New category created: %s' % new_category.name) 
        return redirect(url_for('home'))
    else:
        return render_template('addcategory.html')

# Edit category
@app.route('/catalogue/categories/<int:category_id>/edit/', methods = ['GET', 'POST'])
def edit_category(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        category.name = request.form['name']
        session.add(category)
        session.commit()
        flash('Category name updated') 
        return redirect(url_for('item_list', category_id = category_id))
    else:
        return render_template('editcategory.html', category_id = category_id, category = category)

# Delete category
@app.route('/catalogue/categories/<int:category_id>/delete/', methods = ['GET', 'POST'])
def delete_category(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id = category_id).one_or_none()
    if category == None:
        return redirect(url_for('home'))
    elif request.method == 'POST':
        session.delete(category)
        session.commit()
        flash('Deleted: %s' % category.name) 
        return redirect(url_for('home'))
    else:
        return render_template('deletecategory.html', category_id = category_id, category = category)

# Add Item
@app.route('/catalogue/items/add/', methods = ['GET', 'POST'])
def add_item():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    categories = session.query(Category).all()
    if categories == []: # No categories stored in Database. Redirect to add a category.
        flash('Please create a category for your new item first') 
        return redirect(url_for('add_category'))
    if request.method == 'POST':
        if request.form['name'] == '':
            flash('Please enter an item name') 
            return render_template('additem.html', categories=categories)
        new_item = Item(
            name = request.form['name'], 
            category = session.query(Category).filter_by(name = request.form['category']).one(),
            description = request.form['description'])
        session.add(new_item)
        session.commit()
        flash('%s added!' %new_item.name) 
        return redirect(url_for('home'))
    else:
        return render_template('additem.html', categories=categories)

# Edit Item
@app.route('/catalogue/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    categories = session.query(Category).all()
    item = session.query(Item).filter_by(id=item_id).one()
    editItem = session.query(Item).filter_by(id =item_id).one()
    if request.method == 'POST':
        editItem.name = request.form['name']
        editItem.category = session.query(Category).filter_by(name = request.form['category']).one()
        editItem.description = request.form['description']
        session.add(editItem)
        session.commit()
        flash('%s updated' %editItem.name) 
        return redirect(url_for('home'))
    else:
        return render_template('edititem.html', category_id = category_id, item_id = item_id, categories=categories, item=item)

# Delete item
@app.route('/catalogue/<int:category_id>/<int:item_id>/delete/', methods = ['GET', 'POST'])
def delete_item(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    deleteItem = session.query(Item).filter_by(id =item_id).one_or_none()
    if deleteItem == None:
        return redirect(url_for('home'))
    elif request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash('%s deleted' %deleteItem.name) 
        return redirect(url_for('item_list', category_id = category_id))
    else:
        return render_template('deleteitem.html', category_id = category_id, item = deleteItem)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)