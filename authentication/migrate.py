from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate, init, migrate, upgrade
from models import database, Role, UserRole, User
from sqlalchemy_utils import database_exists, create_database

application = Flask( __name__ )
application.config.from_object( Configuration )

# Create object used in migration
migrate_object = Migrate( application, database )

# Create database
if not database_exists( application.config["SQLALCHEMY_DATABASE_URI"] ):
    create_database( application.config["SQLALCHEMY_DATABASE_URI"] )

# Initialize database with application object
database.init_app( application )

with application.app_context( ) as context:
    # Make initial migration on the database
    init( )
    migrate( message='Initial migration' )
    upgrade( )

    # Initialize the roles of the company
    store_owner_role = Role( name='owner' )
    courier_role = Role( name='courier' )
    customer_role = Role( name='customer' )

    # Add all the roles
    database.session.add( store_owner_role )
    database.session.add( courier_role )
    database.session.add( customer_role )
    database.session.commit( )

    # Create the user who is store_owner
    store_owner = User ( forename='Scrooge', surname='McDuck', email='onlymoney@gmail.com', password='evenmoremoney' )
    database.session.add( store_owner )
    database.session.commit( )

    # Give him the role
    user_role = UserRole( user_id=store_owner.id, role_id=store_owner_role.id )
    database.session.add( user_role )
    database.session.commit( )