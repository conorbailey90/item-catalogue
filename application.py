import os
from flask import Flask, render_template, url_for, request, redirect, flash
from flask import session as login_session
from flask import make_response

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item 

from google.oauth2 import id_token
from google.auth.transport import requests

import httplib2
import json
import random, string


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


# Connect to the Database
engine = create_engine('sqlite:///itemcatalogue.db')
Base.metadata.bind = engine

# Create database session
DBSession = sessionmaker(bind=engine)
session = DBSession()

def processGoogleButton():
    token_id = request.form['idtoken']
    print(token_id)
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(token_id,
                                              requests.Request(), CLIENT_ID)

        # Or, if multiple clients access the backend server:
        # idinfo = id_token.verify_oauth2_token(token, requests.Request())
        # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
        #     raise ValueError('Could not verify audience.')

        if idinfo['iss'] not in ['accounts.google.com',
                                 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # If auth request is from a G Suite domain:
        # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
        #     raise ValueError('Wrong hosted domain.')

        # ID token is valid. Get the user's Google
        # Account ID from the decoded token.

        userid = idinfo['sub']
    except ValueError:
        # Invalid token
        print(ValueError)
        pass

    login_session['username'] = idinfo['name']
    login_session['picture'] = idinfo['picture']
    login_session['email'] = idinfo['email']


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('CCCCCCCCCUUUUUUUUUNNNNNNNNNNNNNNTNTTTTTTTTTTTTTT')
    processGoogleButton()

    return ""

@app.route('/gdisconnect', methods=['POST'])
def gdisconnect():
    if request.args.get('state') == login_session['state']:
        username = login_session.get('username')
        if username is not None:
            del login_session['username']
            del login_session['email']
            del login_session['picture']

    return ""

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/loginsuccess')
def showLoginSuccess():
    return render_template('loginsuccess.html')

@app.route('/')
@app.route('/catalogue/')

def home():
    session = DBSession()
    categories = session.query(Category).all()
    items = session.query(Item).all()
    getState = login_session.get("state")
    if getState is None:
        generatedState = ''.join(random.choice(
            string.ascii_uppercase + string.digits)
                        for x in range(32))
        login_session['state'] = generatedState

    state = login_session['state']
    
    return render_template('cataloguehome.html', categories=categories, items=items, STATE=state)


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
        flash('Please sign in to add a new category.')
        return redirect(url_for('showLogin'))

    if request.method == 'POST':
        if request.form['name'] == '':
            flash('Please add a category name.')
            return render_template('addcategory.html')
        
        newUser = User(name=request.form['name'])
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