import os
from flask import Flask, render_template, url_for, request, redirect, flash, Markup, jsonify
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

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']


# Connect to the Database
engine = create_engine('sqlite:///itemcatalogue.db')
Base.metadata.bind = engine

# Create database session
DBSession = sessionmaker(bind=engine)
session = DBSession()


# JSON API End Points

@app.route('/catalogue/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[i.serialize for i in categories])

@app.route('/catalogue/categories/<int:category_id>/JSON')
def itemsJSON(category_id):
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])

@app.route('/catalogue/items/<int:item_id>/JSON')
def itemJSON(item_id):
    item = session.query(Item).filter_by(
        id=item_id).one()
    return jsonify(Item=item.serialize)


# Flask Application Routing

@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
        for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate anti-forgery state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # (Receive token by HTTPS POST)
    # ...
    token = request.form['idtoken']
    print(token)
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

        # Or, if multiple clients access the backend server:
        # idinfo = id_token.verify_oauth2_token(token, requests.Request())
        # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
        #     raise ValueError('Could not verify audience.')

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # If auth request is from a G Suite domain:
        # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
        #     raise ValueError('Wrong hosted domain.')

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
    except ValueError:
        # Invalid token
        pass
    
    login_session['username'] = idinfo['name']
    login_session['picture'] = idinfo['picture']
    login_session['email'] = idinfo['email']

    return ''

   
@app.route('/gdisconnect', methods = ['POST'])
def gdisconnect():
    if request.args.get('state') == login_session['state']:
        username = login_session.get('username')
        if username != None:
            del login_session['username']
            del login_session['email']
            del login_session['picture']

    return ""

def get_state():
    getState = login_session.get("state")
    if getState is None:
        generatedState = ''.join(random.choice(
            string.ascii_uppercase + string.digits)
                        for x in range(32))
        login_session['state'] = generatedState

    state = login_session['state']
    return state


@app.route('/')
@app.route('/catalogue/')
def home():
    session = DBSession()
    categories = session.query(Category).all()
    items = session.query(Item).all()

    state = get_state()

    # Register a new user to the database
    user = login_session.get('username')
    if user != None:
        user_email = session.query(User).filter_by(email=login_session['email']).one_or_none()
        if user_email == None:
            new_user = User(name=login_session['username'], email=login_session['email'])
            session.add(new_user)
            session.commit()
    current_user = session.query(User).filter_by(email = login_session.get('email')).one_or_none()
   
    return render_template('cataloguehome.html', categories=categories, items=items, 
                                STATE=state, user=user, current_user=current_user)


@app.route('/catalogue/members')
def members():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    members = session.query(User).all()
    state = get_state()
    return render_template('members.html', members = members, STATE=state)

@app.route('/catalogue/users/<int:user_id>/')
def user_profile(user_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    if 'username' not in login_session:
        flash('Please sign in.', 'error')
        return redirect(url_for('login'))
    
    state = get_state()

    member = session.query(User).filter_by(id=user_id).one()
    user_categories = session.query(Category).filter_by(user_id = user_id).all()
    user_items = session.query(Item).filter_by(user_id = user_id).all()
    return render_template('profile.html', member = member, categories = user_categories, 
                                    items = user_items, STATE=state)

    

# View Item list per category
@app.route('/catalogue/<int:category_id>/')
@app.route('/catalogue/<int:category_id>/items/')
def item_list(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    category = session.query(Category).filter_by(id = category_id).one_or_none()

    owner_id = category.user_id
    owner = session.query(User).filter_by(id=owner_id).one()

    state = get_state()
    user = login_session.get('username')

    # IF statement used to prevent an error when the browser Back button is clicked after category deletion.
    if category == None:
        return redirect(url_for('home'))
    items = session.query(Item).filter_by(category_id=category_id).all()
    if items == []:
        flash(Markup('There are no items listed under this category. Add an item <a href="/catalogue/items/add/">here</a>'),'error')
    return render_template('categorylist.html',user = user, category = category, 
                                    items=items, owner = owner, STATE=state)


# View individual item details
@app.route('/catalogue/<int:category_id>/<int:item_id>/')
def item(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    state = get_state()
    user = login_session.get('username')

    category = session.query(Category).filter_by(id = category_id).one()
    item = session.query(Item).filter_by(category_id= category_id, id=item_id).one()

    owner_id = item.user_id
    owner = session.query(User).filter_by(id=owner_id).one()
    return render_template('listitem.html', user = user, category_id = category_id, 
                item_id=item_id, category = category, item = item, owner=owner, STATE=state)

# Add new category
@app.route('/catalogue/categories/add/', methods = ['GET', 'POST'])
def add_category():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    state = get_state()
    user = login_session.get('username')

    if 'username' not in login_session:
        flash('Please sign in to add a new category.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Check the text input is not blank.
        if request.form['name'] == '':
            flash('Please add a category name.', 'error')
            return render_template('addcategory.html')
        
        # Check to see if the logged in users details are stored in the database
        currentUser = session.query(User).filter_by(email=login_session['email']).first()
        if currentUser == None:
            # Add new user to datbase
            newUser = User(name = login_session['username'], email = login_session['email'])
            session.add(newUser)
            session.commit()

        # Add new category with a link to the User ID
        currentUser = session.query(User).filter_by(email=login_session['email']).first()
        new_category = Category(name = request.form['name'], user_id=currentUser.id)
        session.add(new_category)
        session.commit()
        flash('New category created: %s' % new_category.name, 'success') 
        return redirect(url_for('home'))
    else:
        return render_template('addcategory.html',user = user, STATE=state)

# Edit category
@app.route('/catalogue/categories/<int:category_id>/edit/', methods = ['GET', 'POST'])
def edit_category(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    state = get_state()
    user = login_session.get('username')

    category = session.query(Category).filter_by(id = category_id).one()

    owner_id = category.user_id
    owner = session.query(User).filter_by(id=owner_id).one()

    if 'username' not in login_session:
        flash('Please sign in to edit an item.', 'error')
        return redirect(url_for('login'))

    if owner.email != login_session['email']:
        flash('You are not authorised to edit this category.', 'error')
        return redirect(url_for('item_list', category_id = category.id))


    if request.method == 'POST':
        category.name = request.form['name']
        session.add(category)
        session.commit()
        flash('Category name updated', 'success') 
        return redirect(url_for('item_list', category_id = category_id))
    else:
        return render_template('editcategory.html',user = user, 
                    category_id = category_id, category = category, STATE=state)

# Delete category
@app.route('/catalogue/categories/<int:category_id>/delete/', methods = ['GET', 'POST'])
def delete_category(category_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    state = get_state()
    user = login_session.get('username')

    category = session.query(Category).filter_by(id = category_id).one_or_none()

    owner_id = category.user_id
    owner = session.query(User).filter_by(id=owner_id).one()

    if 'username' not in login_session:
        flash('Please sign in to delete an item.', 'error')
        return redirect(url_for('login'))

    if owner.email != login_session['email']:
        flash('You are not authorised to delete this category.', 'error')
        return redirect(url_for('item_list', category_id = category.id))

    if category == None:
        return redirect(url_for('home'))
    elif request.method == 'POST':
        session.delete(category)
        session.commit()
        flash('Deleted category: %s' % category.name, 'success') 
        return redirect(url_for('home'))
    else:
        return render_template('deletecategory.html',user = user, 
                    category_id = category_id, category = category, STATE=state)

# Add Item
@app.route('/catalogue/items/add/', methods = ['GET', 'POST'])
def add_item():
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    state = get_state()
    user = login_session.get('username')

    categories = session.query(Category).all()

    if categories == []: # No categories stored in Database. Redirect to add a category.
        flash('Please create a category for your new item first.', 'error')
        return redirect(url_for('add_category'))

    if 'username' not in login_session:
        flash('Please sign in to add a new item.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Check the text input is not blank.
        if request.form['name'] == '':
            flash('Please add an item name.', 'error')
            return render_template('additem.html', categories = categories)
        
        # Check to see if the logged in users details are stored in the database
        currentUser = session.query(User).filter_by(email=login_session['email']).first()
        if currentUser == None:
            # Add new user to datbase
            newUser = User(name = login_session['username'], email = login_session['email'])
            session.add(newUser)
            session.commit()
        
        # Add new category with a link to the User ID
        currentUser = session.query(User).filter_by(email=login_session['email']).first()
        new_item = Item(
            name = request.form['name'], 
            category = session.query(Category).filter_by(name = request.form['category']).one(),
            description = request.form['description'],
            user_id = currentUser.id)
        session.add(new_item)
        session.commit()
        flash('%s added to to the %s category.' %(new_item.name, new_item.category.name), 'success' )
        return redirect(url_for('home'))
    else:
        return render_template('additem.html', user = user, categories=categories, STATE=state)

# Edit Item
@app.route('/catalogue/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    state = get_state()
    user = login_session.get('username')

    categories = session.query(Category).all()

    editItem = session.query(Item).filter_by(id =item_id).one()

    owner_id = editItem.user_id
    owner = session.query(User).filter_by(id=owner_id).one()

    if 'username' not in login_session:
        flash('Please sign in to edit an item.', 'error')
        return redirect(url_for('login'))

    if owner.email != login_session['email']:
        flash('You are not authorised to edit this item.', 'error')
        return redirect(url_for('item', category_id=category_id, item_id=item_id))
    
    if request.method == 'POST':
        # Check the text input is not blank.
        if request.form['name'] == '':
            flash('Please add an item name.', 'error')
            return render_template('additem.html', categories = categories)
        
        # Check to see if the logged in users details are stored in the database
        currentUser = session.query(User).filter_by(email=login_session['email']).first()
        if currentUser == None:
            # Add new user to datbase
            newUser = User(name = login_session['username'], email = login_session['email'])
            session.add(newUser)
            session.commit()

        editItem.name = request.form['name']
        editItem.category = session.query(Category).filter_by(name = request.form['category']).one()
        editItem.description = request.form['description']
        session.add(editItem)
        session.commit()
        flash('%s updated' %editItem.name, 'success') 
        return redirect(url_for('item', category_id=editItem.category.id, item_id=item_id, owner=owner))
    else:
        return render_template('edititem.html',user = user, category_id = category_id, 
                    item_id = item_id, categories=categories, item=editItem, STATE=state)

# Delete item
@app.route('/catalogue/<int:category_id>/<int:item_id>/delete/', methods = ['GET', 'POST'])
def delete_item(category_id, item_id):
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    state = get_state()
    user = login_session.get('username')

    deleteItem = session.query(Item).filter_by(id =item_id).one_or_none()

    owner_id = deleteItem.user_id
    owner = session.query(User).filter_by(id=owner_id).one()

    if 'username' not in login_session:
        flash('Please sign in to delete an item.', 'error')
        return redirect(url_for('login'))

    if owner.email != login_session['email']:
        flash('You are not authorised to delete this item.', 'error')
        return redirect(url_for('item', category_id=category_id, item_id=item_id))

    if deleteItem == None:
        return redirect(url_for('home'))
    elif request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash('%s deleted' %deleteItem.name, 'success') 
        return redirect(url_for('item_list', category_id = category_id))
    else:
        return render_template('deleteitem.html',user = user, category_id = category_id, 
                                            item = deleteItem, STATE=state)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)