# SMART Server
## GWU implementation of an OAuth (optionally, with OIDC) server

# Local deployment
---  
---  
# ============= WARNING ==============
Local development is not possible without performing a local installation of the `oauthlib` python library. See below note about virtual environments.  
The offending line is [here](https://github.com/oauthlib/oauthlib/blob/master/oauthlib/oauth2/rfc6749/grant_types/base.py#L257). That line disallows 
local development over `http`. You must either serve through `https`, via e.g. nginx or Apache, or come up with some other workaround.

Steps required:
1. Clone the `oauthlib` library somewhere accessible, e.g. an `external-src` directory:
`git clone https://github.com/oauthlib/oauthlib.git $HOME/external-src; cd $HOME/external-src/oauthlib/`
2. Install an editable version in the Python environment:
`pip install -e .  # Note the "cd" command in step 1`
3. Edit `oauth2/rfc6749/grant_types/base.py#L257` to return `True`, regardless of `https` status. This allows CORS headers to be crafted in development.
# ====================================
---   
---   
## Install dependencies
### Python + OAuth server middleware
A virtual environment is not required, but strongly encouraged.  
Creation of a virtualenv is beyond the scope of this readme. 
Suggested references can be found e.g. [here](https://virtualenvwrapper.readthedocs.io/en/latest/).

1. Activate the python environment: `workon smart`
2. Create the Django database (contains simple user definitions for interaction)
```bash
$ # The database isn't fully commited to Git, so we first force Django to write the DB configuration files
$ python manage.py makemigrations
$ # Next, run some Django scripts to create users in the database
$ cd utilities
$ ./initialize_db.sh
...
$ # Return to the user middleware directory
$ cd -
```
3. Create a private encryption key. Even for development, it is best practice not to share this or commit it anywhere.
`$ openssl genrsa -out oidc.key 4096`

One full description of this key, and how it is created, can be found [here](https://django-oauth-toolkit.readthedocs.io/en/latest/oidc.html#creating-rsa-private-key).

4. Start the middleware server: `$ python manage.py runserver`
**NB** The server cannot interact functionally, as there is no `login` landing page running yet. The server is not configured to use the built-in Django admin user management pages.

### Node + User Interface (Single Page Application)
Installation of `nodejs` and management of the various environments is outside the scope of this documentation. See e.g. [here](https://github.com/nvm-sh/nvm) for installation and management of node.

1. Navigate to the prototype User Interface: `$ cd interface-prototype`
2. Install dependencies: `$ npm install`
3. Start the node development server: `$ npm run dev`

There should now be a login interface running at http://localhost:3000.

## Login as a user
A new user may be created using the "Register" interface, or use any of the examples from the `utilites/create_users.py` script.
**NB**: If no user is logged in when attempting to register an application, OAuth attempts to redirect the interface to a login interface (by default, http://localhost:3000/login)

## Register a new "Application" prototype
This is of course not a real App, just a shim pretending to be one.  
However, any App under development or deployment must perform these same steps.
1. Start the OAuth server: `python manage.py runserver`
2. This will result in a Django + Django OAuth server instance running on port 8000.  

There will be a bare-bones user interface present at http://localhost:8000/o/applications/.
This interface allows registration of a new client App.  
**NB** If not logged as indicated [above](#login-as-a-user), this will redirect to the login interface.  

- Click "Click here" at http://localhost:8000/o/applications/. 
- Use the following settings:
    Name: TestApp [or anything else]
    Client Type: Public [for SPA] / Confidential [for FEAST]
    Authorization grant type: Authorization Code
    Redirect uris: http://localhost:3000/callback/
    Post logout redirect uris: http://localhost:3000/login/
    Algorithm: RSA with SHA-2 256
- Copy/paste the client ID somewhere
- Click "Save"

## Direct the App UI to the OAuth server using Client ID
Update the SPA code with the client ID  in `interface-prototype/src/stores/user.js:26`:
`client_id: "[NewClientID]",`

## The full OAuth pipeline is now available
1. http://localhost:3000/login/ --> Credentials
2. After login, click "OIDC: Authorize" to view user permissions scope & authorize