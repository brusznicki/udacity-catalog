from flask import Flask, jsonify, redirect, render_template, request, \
                  url_for, flash
from flask import session as login_session
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item, User
from config import configure_app
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response
import datetime
import httplib2
import json
import random
import requests
import string
# Initiate Flask and load configuration
app = Flask(__name__)
configure_app(app)  # see config.py for configuraiton

# Connect to Database and create database session
engine = create_engine('sqlite:///catalogapp.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# GConnect CLIENT_ID
CLIENT_ID = json.loads(
                 open('google_client_secrets.json', 'r')
                 .read())['web']['client_id']
APPLICATION_NAME = "Udacity Catalog App"

DEFAULT_IMAGE = "http://www.reelviews.net/resources/img/default_poster.jpg"


# Login Routing
# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    '''Google OAuth2 connection Handler'''
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('google_client_secrets.json',
                                             scope='')
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                                'Current user is already connected.'),
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
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;\
                -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'], "success")
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    '''Helper method to create a new user'''
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserID(email):
    '''Helper method to get a user id given an email'''
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    '''Handler for disconnect from google oauth2'''
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
                                'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    '''Abstract disconnect handler'''
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.", "success")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in", "success")
        return redirect(url_for('showCatalog'))

# ===================
# Application routing
# ===================


# Homepage
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    '''Show Handler for Catalog / Index Page'''
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).order_by(desc(Item.date_updated)).limit(10)
    return render_template('catalog.html',
                           categories=categories,
                           items=items)


# Category / All Items
@app.route('/catalog/<string:category_name>')
@app.route('/catalog/<string:category_name>/items/')
def showCategory(category_name):
    '''Show Handler for an individual Category'''
    category = session.query(Category).filter_by(name=category_name).one()
    category_id = category.id
    items = session.query(Item).filter_by(category_id=category_id)
    show_crud = False
    if category.user_id == login_session['user_id']:
        show_crud = True
    return render_template('category.html',
                           category=category,
                           items=items,
                           show_crud=show_crud)


# Categories
@app.route('/catalog/categories')
def showCategories():
    '''Show Handler for all Categories'''
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('categories.html',
                           categories=categories)


# New Category
@app.route('/catalog/category/new/', methods=['GET', 'POST'])
def newCategory():
    '''Create Handler for Category'''
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        user_id = login_session['user_id']
        print user_id
        newCategory = Category(name=request.form['name'],
                               user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name,
              'success')
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newcategory.html')


# Edit Category
@app.route('/catalog/<string:category_name>/edit/', methods=['GET', 'POST'])
def editCategory(category_name):
    '''Edit Handler for Category'''
    editedCategory = session.query(
        Category).filter_by(name=category_name).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedCategory.user_id != login_session['user_id']:
        flash("You are not allowed to edit this Category", "danger")
        return redirect(url_for('showCategory',
                                category_name=editedCategory.name))
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            session.add(editedCategory)
            session.commit()
            flash('Category Successfully Edited %s' % editedCategory.name)
            return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html', category=editedCategory)


# Delete Category
@app.route('/catalog/<string:category_name>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_name):
    '''Delete Handler for Category'''
    deletedCategory = session.query(
        Category).filter_by(name=category_name).one()
    if 'username' not in login_session:
        return redirect('/login')
    if deletedCategory.user_id != login_session['user_id']:
        flash("You are not allowed to delete this Category", "danger")
        return redirect(url_for('showCategory',
                                category_name=deletedCategory.name))
    if request.method == 'POST':
        session.delete(deletedCategory)
        session.commit()
        flash('Category Successfully Deleted %s' % deletedCategory.name)
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html', category=deletedCategory)


# Item
@app.route('/catalog/<string:category_name>/<int:item_id>/')
def showItem(category_name, item_id):
    '''Show Handler for Items'''
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(id=item_id).one()
    show_crud = False
    if item.user_id == login_session['user_id']:
        show_crud = True
    return render_template('item.html',
                           category=category,
                           item=item,
                           show_crud=show_crud)


# New Item
@app.route('/catalog/<string:category_name>/newItem/', methods=['GET', 'POST'])
def newItem(category_name):
    '''Create Handler for Items'''
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        print "attempting to save the new item"
        category = session.query(Category).filter_by(name=category_name).one()
        image_path = request.form['image_path']
        if not image_path:
            image_path = DEFAULT_IMAGE
        print image_path
        newItem = Item(title=request.form['title'],
                       description=request.form['description'],
                       date_updated=datetime.datetime.now(),
                       image_path=image_path,
                       user_id=login_session['user_id'],
                       category_id=category.id)
        session.add(newItem)
        flash('New Item %s Successfully Created' % newItem.title,
              'success')
        session.commit()
        print "saving film"
        return redirect(url_for('showCategory',
                                category_name=category.name))
    else:
        category = session.query(Category).filter_by(name=category_name).one()
        print "rendering newItem.hml with category %s" % category.name
        return render_template('newItem.html', category=category)


# Edit Item
@app.route('/catalog/<string:category_name>/<int:item_id>/edit/',
           methods=['GET', 'POST'])
def editItem(category_name, item_id):
    '''Edit Handler for Items'''
    category = session.query(Category).filter_by(name=category_name).one()
    editedItem = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return redirect('/login')
    if editedItem.user_id != login_session['user_id']:
        flash("You are not allowed to edit this Item", "danger")
        return redirect(url_for('showItem',
                                category_name=category_name,
                                item_id=editedItem.id))
    if request.method == 'POST':
        print "attempting to post"
        if request.form['title']:
            editedItem.title = request.form['title']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['image_path']:
            editedItem.image_path = request.form['image_path']
        print "attempting to get category from form"
        # print request.form['category']
        if request.form['category']:
            category = session.query(Category).filter_by(
                       name=request.form['category']).one()
            editedItem.category = category
        time_updated = datetime.datetime.now()
        editedItem.date_updated = time_updated
        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited %s' % editedItem.title)
        return redirect(url_for('showItem',
                                category_name=category_name,
                                item_id=editedItem.id))
    else:
        return render_template('editItem.html',
                               category=category,
                               categories=categories,
                               item=editedItem)


# Delete Item
@app.route('/catalog/<string:category_name>/<int:item_id>/delete/',
           methods=['GET', 'POST'])
def deleteItem(category_name, item_id):
    '''Delete Handler for Items'''
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(name=category_name).one()
    if 'username' not in login_session:
        return redirect('/login')
    if itemToDelete.user_id != login_session['user_id']:
        flash("You are not allowed to delete this Item", "danger")
        return redirect(url_for('showItem',
                                category_name=category_name,
                                item_id=item_id))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Category Successfully Deleted %s' % itemToDelete.title)
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteItem.html',
                               category=category,
                               item=itemToDelete)


# ================
# JSON APIs
# ================


# Full Catalog
@app.route('/catalog/JSON')
def catalogJSON():
    '''JSON Show for Catalog'''
    categories = session.query(Category).order_by(asc(Category.name))
    return jsonify(categories=[c.serialize for c in categories])


# Category
@app.route('/catalog/<string:category_name>/JSON')
def categoryJSON(category_name):
    '''JSON Show for Category'''
    category = session.query(Category).filter_by(name=category_name).one()
    return jsonify(category.serialize)


# Item
@app.route('/catalog/<string:category_name>/<int:item_id>/JSON')
def itemJSON(category_name, item_id):
    '''JSON Show for Item'''
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item.serialize)


if __name__ == '__main__':
    app.run(host='localhost', port=5000)
