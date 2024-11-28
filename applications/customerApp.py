from datetime import datetime
from flask import Flask, request, Response, jsonify, make_response
from configuration import Configuration
from customerDecorator import roleCheck
from models import database, Category, Product, OrderProduct, Order
from flask_jwt_extended import JWTManager, get_jwt_identity

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route( '/search', methods=[ 'GET' ] )
@roleCheck( role='customer' )
def search( ):

    # Check the existence of the authorization header
    if 'Authorization' not in request.headers:
        return jsonify( msg='Missing Authorization header' ), 401

    product = request.args.get('name')
    category = request.args.get('category')

    # Start with a base query
    query = Product.query

    # Apply filters based on search parameters
    if product:
        query = query.filter( Product.name.ilike( f'%{ product }%' ) )
    if category:
        query = query.filter( Product.categories.any( Category.name.ilike( f'%{ category }%' ) ) )

    # Grab the results of the query
    query_result = query.all( )

    # Prepare the set and list in order to use in operator
    categories = set()
    products = []

    # Iterate through the query_result to make the formated search
    for result in query_result:
        product_categories = [category.name for category in result.categories]
        categories.update( product_categories )
        product = {
            'categories': product_categories,
            'id': result.id,
            'name': result.name,
            'price': result.price
        }
        products.append( product )

    # Grab all the categories when no search parameters are provided
    if not product and not category:
        all_categories = Category.query.all( )
        categories = [ category.name for category in all_categories ]

    # Prepare the returning data
    ret_data = {
        'categories': list( categories ),
        'products': products
    }

    # Return the ret_data
    return make_response( jsonify( ret_data ) ), 200

def calculate_total_price( requests ):
    total_price = 0.0
    for request_data in requests:
        product_id, quantity = request_data['id'], request_data['quantity']
        product = Product.query.get( product_id )
        total_price += product.price * quantity
    return total_price

def create_order_products( requests, order_id ):
    for request_data in requests:
        product_id, quantity = request_data['id'], request_data['quantity']
        order_product = OrderProduct( order_id=order_id, product_id=product_id, quantity=quantity )
        database.session.add( order_product )
    database.session.commit( )


@application.route( '/order', methods=[ 'POST' ] )
@roleCheck( role='customer' )
def order( ):
    try:
         access_token = request.headers.get('Authorization')
    except:
         return Response(status=400)

    # Check the existence of the authorization header
    if 'Authorization' not in request.headers:
        return make_response( jsonify( msg='Missing Authorization header' ) ), 401

    # Check if the request contains json
    if not request.is_json:
        return jsonify(), 400

    data = request.get_json()

    if 'requests' not in data:
        return jsonify( {'message': 'Field requests is missing.'} ), 400

    requests = data['requests']

    for i, request_data in enumerate( requests ):
        product_id, quantity = request_data.get('id'), request_data.get('quantity')

        if 'id' not in request_data:
            return jsonify( {'message': f'Product id is missing for request number { i }.'} ), 400
        if 'quantity' not in request_data:
            return jsonify( {'message': f'Product quantity is missing for request number { i }.'} ), 400

        if not isinstance( product_id, int ) or product_id <= 0:
            return jsonify( {'message': f'Invalid product id for request number { i }.'} ), 400

        product = Product.query.get( product_id )
        if not product:
            return jsonify( {'message': f'Invalid product for request number { i }.'} ), 400

        if not isinstance( quantity, int ) or quantity <= 0:
            return jsonify( {'message': f'Invalid product quantity for request number { i }.'} ), 400

    total_price = calculate_total_price( requests )

    # Create the order with given parameters
    order = Order( total_price=total_price, status="CREATED", timestamp=datetime.now(), user=get_jwt_identity())
    database.session.add( order )
    database.session.commit( )

    create_order_products( requests, order.id )
    return jsonify( {'id': order.id } ), 200


@application.route( '/status', methods=[ 'GET' ] )
@roleCheck( role='customer' )
def get_order_status( ):
    try:
        access_token = request.headers.get('Authorization')
    except:
        return Response(status=400)
    if not access_token:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    # Check the existence of the authorization header
    if 'Authorization' not in request.headers:
        return make_response( jsonify( msg='Missing Authorization header' ) ), 401

    # Grab the current user-s orders
    orders = Order.query.filter_by( user=get_jwt_identity( ) ).all( )

    # Format the list_of_orders
    list_of_orders = []
    for order in orders:
        order_data = {
            "products": [],
            "price": order.total_price,
            "status": order.status,
            "timestamp": order.timestamp
        }
        for product in order.order_products:
            product_data = {
                "categories": [ category.name for category in product.product.categories ],
                "name": product.product.name,
                "price": product.product.price,
                "quantity": product.quantity
            }
            order_data["products"].append( product_data )
        list_of_orders.append( order_data )


    return make_response( jsonify( { "orders": list_of_orders } ) ), 200


@application.route( '/delivered' , methods=[ 'POST' ] )
@roleCheck( role='customer' )
def delivered():
    # Check the existence of the authorization header
    if 'Authorization' not in request.headers:
        return make_response( jsonify( msg='Missing Authorization header' ) ), 401

    # Grab the id of the order passed through request
    id_order = request.json.get('id', None)

    # Check if the id is passed
    if not id_order:
        return make_response( jsonify( { 'message': 'Missing order id.' } ) ), 400

    # Casting might raise ValueError
    try:
        id_order = int( id_order )
    except ValueError:
        return make_response( jsonify( { "message": "Invalid order id." } ) ), 400

    # Check the validity of id
    if (id_order <= 0):
        return make_response( jsonify( { 'message': 'Invalid order id.' } ) ), 400

    # Find order
    order = Order.query.filter( Order.id == id_order ).first( )

    # Check if the order id is valid
    if ( ( not order ) or ( order.status != 'PENDING' ) ):
        return make_response( jsonify({'message': 'Invalid order id.'}) ), 400

    # Mark order as complete
    order.status = 'COMPLETE'
    database.session.add( order )
    database.session.commit( )
    return Response(status=200)

# Start the application
if ( __name__ == "__main__" ):
    database.init_app( application )
    application.run( debug=True, host='0.0.0.0', port=5002)