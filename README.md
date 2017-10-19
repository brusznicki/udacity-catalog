# Udacity - item catalog app
This app is a prototype of a Film Item Catalog built for the Udacity [FSND Course](#).

## About
This app is a RESTful web app built using [Flask](http://flask.pocoo.org/), [python 2.7.12](https://www.python.org/downloads/release/python-2712/), and [SQLite](https://www.sqlite.org/). [OAuth2](https://github.com/joestump/python-oauth2) is used to provide authentication via popular web services such as [Google OAuth](https://developers.google.com/identity/protocols/OAuth2). It can be extended to provide authentication via [Facebook](https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow/), [Github](https://developer.github.com/apps/building-integrations/setting-up-and-registering-oauth-apps/), and [Amazon OAuth](http://login.amazon.com/).

## Project Organization
> The main Python module runs the Flask application via `project.py`.
> Flask configurations are in the `config.py` module.
> A SQL database is created and populated using the `database_setup.py` module.
> Film data is provided by calls to the Movie DB API in `database_setup.py`.
> Views are rendered from stored HTML templates in the `templates` folder
> Static assets such as CSS, Javascript, and Images are stored in the static directory.


## Quickstart
1. Download or clone the [fullstack-nanodegree-vm repository](https://github.com/udacity/fullstack-nanodegree-vm).

2. Replace the *catalog* subfolder with the contents of this repository - [Github Link](https://github.com/brusznicki/udacity-catalog).

## Dependencies
This app is built according to the VirtualBox / Vagrant guidelines provided in the FSDN Crud final project. Access to the Udacity vagrant file is required to quickly build out dependencies. I have forked the Vagrantfile to include other modules such as Faker TODO
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
- [Vagrant](https://www.vagrantup.com/)
- [Udacity Vagrantfile](https://github.com/udacity/fullstack-nanodegree-vm)

## Step by Step Installation

Launch the Vagrant VM from inside the *vagrant* folder with:

`vagrant up`

`vagrant ssh`

Change directory to the catalog folder

`cd /vagrant/catalog`

Run the data_importer

`python data_importer.py`

Launch the application
`python project.py`

Navigate to the application in your browser

`http://localhost:5000/`

*IMPORTANT* Use *localhost* and not *0.0.0.0* or else Oauth will ot operate as intended.

If all is good you'll see
[img](https://i.imgur.com/trSmtqi.png)


## Google OAuth instructions

1. Go to [Google Dev Console](https://console.developers.google.com)
2. Sign up or Login if prompted
3. Go to Credentials
4. Select Create Crendentials > OAuth Client ID
5. Select Web application
6. Enter name 'Item-Catalog'
7. Authorized JavaScript origins = 'http://localhost:5000'
8. Authorized redirect URIs = 'http://localhost:5000/login' && 'http://localhost:5000/gconnect'
9. Select Create
10. Copy the Client ID and paste it into the `data-clientid` in login.html
11. On the Dev Console Select Download JSON
12. Rename JSON file to client_secrets.json
13. Place JSON file in item-catalog directory that you cloned from here
14. Run application using `python project.py`

## API endpoints
The following are open to the public:

GET Catalog: `/catalog/JSON`
    - Displays the full catalog

GET Catalog: `/catalog/<string:category_name>/JSON`
    - Displays catalog category data

GET Item: `/catalog/<string:category_name>/<int:item_id>/JSON`
    - Displays all categories for a specific catalog
