from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy ( )
#Table is used as connection table between User and their Roles
class UserRole ( database.Model ):
    __tablename__ = "userrole"
    id = database.Column( database.Integer, primary_key=True )
    user_id = database.Column(database.Integer, database.ForeignKey("users.id"), nullable=False)
    role_id = database.Column(database.Integer, database.ForeignKey("roles.id"), nullable=False)

class User ( database.Model ):
    __tablename__ = "users"
    id = database.Column( database.Integer, primary_key=True )
    forename = database.Column( database.String(256), nullable=False )
    surname = database.Column( database.String(256), nullable=False )
    email = database.Column( database.String(256), nullable=False, unique=True )
    password = database.Column( database.String(256), nullable=False )
    roles = database.relationship( "Role", secondary=UserRole.__table__, back_populates="users" )

class Role ( database.Model ):
    __tablename__ = "roles"
    id = database.Column( database.Integer, primary_key=True )
    name = database.Column( database.String(256), nullable=False )
    users = database.relationship( "User", secondary=UserRole.__table__, back_populates="roles" )

    def __repr__( self ):
        return self.name