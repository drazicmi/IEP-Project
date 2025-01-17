from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

# Decorator is used to check the permissions of the user by checking their role in the system
def roleCheck( role ):
    def innerRole( function ):
        @wraps( function )
        def decorator( *arguments, **keywordArguments ):
            verify_jwt_in_request( )
            claims = get_jwt( )
            if ( ( "roles" in claims ) and ( role in claims["roles"] ) ):
                return function( *arguments, **keywordArguments )
            else:
                return jsonify( msg='Missing Authorization Header' ), 401
        return decorator
    return innerRole


