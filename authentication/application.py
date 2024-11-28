from flask import Flask, request, Response, jsonify, make_response
from configuration import Configuration
from models import database, User, UserRole
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity
from sqlalchemy import and_
from email.utils import parseaddr

application = Flask( __name__ )
application.config.from_object( Configuration )

jwt = JWTManager( application )


import re
# The function checks the validity of email using regex
def check_email(email):
    # Regular expression pattern for a valid email address
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Use the re.match function to check if the email matches the pattern
    if re.match( pattern, email ):
        return True
    else:
        return False

# The route is used to register new courier
@application.route( "/register_courier", methods=[ "POST" ] )
def register_courier( ):
    # Grab the arguments from the body
    forename = request.json.get( "forename", "" )
    surname = request.json.get( "surname", "" )
    email = request.json.get( "email", "" )
    password = request.json.get( "password", "" )

    # Check the validity of the grabbed arguments
    forename_empty = len( forename ) == 0
    surname_empty = len( surname ) == 0
    email_empty = len( email ) == 0
    password_empty = len( password ) == 0

    # Make valid responses (with code 400 as error code) if the fields are missing
    # The checkups are done in this order so the automatic tests will pass
    if forename_empty:
        return make_response( jsonify( message='Field forename is missing.' ) ), 400
    if surname_empty:
        return make_response( jsonify( message='Field surname is missing.' ) ), 400
    if email_empty:
        return make_response( jsonify( message='Field email is missing.' ) ), 400
    if password_empty:
        return make_response( jsonify( message='Field password is missing.' ) ), 400
    if not check_email(email):
        return make_response(jsonify(message='Invalid email.')), 400
    if ( len( password ) < 8 ):
        return make_response( jsonify( message='Invalid password.') ), 400

    email_exists = User.query.filter( User.email == email ).first( )
    if email_exists:
        return make_response( jsonify( message='Email already exists.' ) ), 400

    # Create the user with given arguments
    user = User( forename=forename, surname=surname, email=email, password=password)
    database.session.add( user )
    database.session.commit( )

    # Crete the user role for a created user
    user_role = UserRole( user_id=user.id, role_id=2 )
    database.session.add( user_role )
    database.session.commit( )
    # Return succesfull response
    return Response( status=200 )


@application.route( "/register_customer", methods=[ "POST" ] )
def register_customer( ):
    # Grab the arguments from the body
    forename = request.json.get( "forename", "" )
    surname = request.json.get( "surname", "" )
    email = request.json.get( "email", "" )
    password = request.json.get( "password", "" )

    # Check the validity of the grabbed arguments
    forename_empty = len( forename ) == 0
    surname_empty = len( surname ) == 0
    email_empty = len( email ) == 0
    password_empty = len( password ) == 0

    # Make valid responses (with code 400 as error code) if the fields are missing
    # The checkups are done in this order so the automatic tests will pass
    if forename_empty:
        return make_response( jsonify( message='Field forename is missing.' ) ), 400
    if surname_empty:
        return make_response( jsonify( message='Field surname is missing.' ) ), 400
    if email_empty:
        return make_response( jsonify( message='Field email is missing.' ) ), 400
    if password_empty:
        return make_response( jsonify( message='Field password is missing.' ) ), 400
    if not check_email(email):
        return make_response(jsonify(message='Invalid email.')), 400
    if ( len( password ) < 8 ):
        return make_response( jsonify( message='Invalid password.' ) ), 400

    # Check if the user with given email already exists (email should be unique for all users)
    email_exists = User.query.filter( User.email == email ).first( )
    if email_exists:
        return make_response( jsonify( message='Email already exists.' ) ), 400

    # Create the user with given arguments
    user = User( forename=forename, surname=surname, email=email, password=password )
    database.session.add( user )
    database.session.commit( )

    # Crete the user role for a created user
    user_role = UserRole( user_id=user.id, role_id=3 )
    database.session.add( user_role )
    database.session.commit( )
    # Return succesfull response
    return Response(status=200)


@application.route( "/login", methods=[ "POST" ] )
def login( ):
    # Grab the arguments from the body
    email = request.json.get( "email", "" )
    password = request.json.get( "password", "" )

    # Check the validity of the grabbed arguments
    email_empty = len( email ) == 0
    password_empty = len( password ) == 0

    # Make valid responses (with code 400 as error code) if the fields are missing
    # The checkups are done in this order so the automatic tests will pass
    if ( email_empty ):
        return make_response( jsonify( message='Field email is missing.' ) ), 400
    if ( password_empty ):
        return make_response( jsonify( message='Field password is missing.' ) ), 400
    if not check_email(email):
        return make_response(jsonify(message='Invalid email.')), 400

    # Check the users credentials
    user = User.query.filter( and_( User.email == email, User.password == password ) ).first( )
    if not user:
        return make_response( jsonify( message="Invalid credentials." ) ), 400

    # Add additional claims to the payload of the token
    additional_claims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [ str( role ) for role in user.roles ]
    }

    # Create access and refresh token for the user in order to create session
    access_token = create_access_token( identity=user.email, additional_claims=additional_claims )
    # refresh_token = create_refresh_token( identity=user.email, additional_claims=additional_claims )
    return make_response( jsonify( accessToken=access_token ) ), 200
    # Mozda ne treba refresh token
    # return make_response( jsonify( accessToken=access_token, refreshToken=refresh_token ) ), 200

@application.route( "/delete", methods=['POST'] )
@jwt_required( )
def delete( ):
    # Check the existence of the authorization header
    # if 'Authorization' not in request.headers:
    #     return make_response( jsonify( msg='Missing Authorization header' ) ), 401
    identity_email = get_jwt_identity( )
    # Check the users identity_email
    user = User.query.filter( User.email == identity_email ).first( )
    # Make response with error code 400 if the user doesn't exist
    if not user:
        return make_response( jsonify( message="Unknown user." ) ), 400
    # Delete the user from the database and return response with code 200
    database.session.delete( user )
    database.session.commit( )
    return Response( status=200 )

# PROVERI OVOU FUNKCIJU
@application.route( "/refresh", methods=["POST"] )
@jwt_required( refresh=True )
def refresh( ):
    identity = get_jwt_identity( )
    refresh_claims = get_jwt( )

    additionalClaims = {
        "forename":refresh_claims["forename"],
        "surname":refresh_claims["surname"],
        "roles":refresh_claims["roles"]
    }
    return Response( create_access_token( identity=identity, additional_claims=additionalClaims ), status=200 )

# Start the application
if ( __name__ == "__main__" ):
    database.init_app( application )
    application.run( debug=True, host='0.0.0.0', port=5000 )