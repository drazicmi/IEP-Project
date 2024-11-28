from flask import Flask, request, Response, jsonify, make_response
from configuration import Configuration
from models import database, Order
from flask_jwt_extended import JWTManager
from courierDecorator import roleCheck

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route( '/pick_up_order', methods=[ 'POST' ] )
@roleCheck( role='courier')
def pick_up_order( ):
    # Check the existence of the authorization header
    if 'Authorization' not in request.headers:
        return make_response( jsonify( msg='Missing Authorization header' ) ), 401

    # Check if the request contains json
    if not request.is_json:
        return jsonify( ), 400

    # Grab the id of the order passed through request
    id_order = request.json.get( 'id', None )

    # Check if the id is passed
    if not id_order:
        return jsonify( { "message": "Missing order id." } ), 400

    # Casting might raise ValueError
    try:
        id_order = int( id_order )
    except ValueError:
        return jsonify( { "message": "Invalid order id." } ), 400

    if (id_order <= 0):
        return jsonify({"message": "Invalid order id."}), 400

    # Grab te order and pick it up
    order = Order.query.filter( Order.id == id_order ).first( )
    if ( ( not order ) or ( order.status != 'CREATED' ) ):
        return jsonify( { "message": "Invalid order id." } ), 400

    # Mark the order as picked up
    order.status = "PENDING"
    database.session.add( order )
    database.session.commit( )
    return Response( status=200 )


@application.route( '/orders_to_deliver', methods=[ 'GET' ])
@roleCheck( role='courier')
def orders_to_deliver( ):
    # Check the existence of the authorization header
    if 'Authorization' not in request.headers:
        return make_response( jsonify( msg='Missing Authorization header' ) ), 401
    
    # Grab all the undelivered orders
    orders = Order.query.filter( Order.status == "CREATED" )
    
    # Create the list of dictionaries that is returned as response
    ret_value = [ { "id": order.id, "email": order.user } for order in orders]

    return jsonify( { "orders": ret_value } ), 200

# Start the application
if ( __name__ == "__main__" ):
    database.init_app( application )
    application.run( debug=True, host='0.0.0.0', port=5003)