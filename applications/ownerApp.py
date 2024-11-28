from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, Category, Product, OrderProduct, Order, ProductCategory
from sqlalchemy import func, case
from flask_jwt_extended import JWTManager
from ownerDecorator import roleCheck

application = Flask( __name__ )
application.config.from_object( Configuration )

jwt = JWTManager( application )

# Route is used to add new products
@application.route( '/update', methods=[ 'POST' ] )
@roleCheck( role='owner' )
def update( ):

    # Check the existence of the file field
    if 'file' not in request.files:
        return jsonify( message='Field file is missing.' ), 400

    # Grab the file
    file = request.files['file']
    # Empty list of products that will be updated
    products = { }
    # Make the set of existing names and categories to check with operator in
    current_iteration_products = set( )
    categories = set( )

    for i, line in enumerate( file.readlines() ):
        line = line.strip( ).decode( 'utf-8' )
        values = line.split(',')

        # Check if the line has correct number of values (It should be 3 : Name of categories, product name and product price )
        if ( len( values ) != 3 ):
            database.session.rollback( )
            return jsonify( message=f'Incorrect number of values on line { i }.' ), 400

        list_of_categories = values[0].strip( ).split( '|' )
        product_name = values[1].strip( )
        price = values[2].strip( )

        try:
            price = float( price )
            # Check if the price is negative
            if price <= 0:
                database.session.rollback( )
                return jsonify( message=f'Incorrect price on line { i }.' ), 400
        # Raise exception if the casting into float raises and error
        except ValueError:
            database.session.rollback( )
            return jsonify( message=f'Incorrect price on line { i }.' ), 400

        # Check if the product is added while we are iterating through file
        if product_name in current_iteration_products:
            database.session.rollback( )
            return jsonify( message=f'Product { product_name } already exists.' ), 400

        # Check if the product is already in the database
        product_exists_db_check = Product.query.filter_by( name=product_name ).first( )
        if product_exists_db_check:
            database.session.rollback( )
            return jsonify( message=f'Product {product_name} already exists.' ), 400

        # Save the product you are adding into the set of existing products
        current_iteration_products.add( product_name )

        # Save all the categories that product contains
        for category in list_of_categories:
            categories.add( category )

        # Save the product in current iteration into final list of products
        products [product_name] = {
            "list_of_categories": list_of_categories,
            "price": price
        }

    try:
        # Save the added categories in the database
        new_categories = [ Category( name=category_name ) for category_name in categories ]
        database.session.bulk_save_objects( new_categories )
        database.session.commit( )

        # For every product create the new object in data base
        for product_name, product_data in products.items( ):
            # Create product object
            product = Product( name=product_name, price=product_data["price"] )
            # Add the categories to the product
            product.categories = Category.query.filter( Category.name.in_( product_data["list_of_categories"] ) ).all( )
            database.session.add( product )
        database.session.commit( )
        return Response( status=200 )
    except Exception:
        database.session.rollback( )
        return jsonify( message='ERROR' ), 500


# Route is used to create statistics for products
@application.route( '/product_statistics', methods=[ 'GET' ] )
@roleCheck( role='owner' )
def product_statistics():

    # In the SELECT part of the query we have 3 columns, representing name of the product, quantity of all sold items, and quantity of all the items
    # that are waiting to be sold. Now in order to sort the products accordingly we have to join Products table with OrderProduct and Order table.
    # In the GROUP BY section we sort the products by name and grab them all.
    product_information = database.session.query( Product.name,
        func.sum( case( [( Order.status == "COMPLETE", OrderProduct.quantity )], else_=0 ) ).label("sold"),
        func.sum( case( [( Order.status != "COMPLETE", OrderProduct.quantity )], else_=0 ) ).label("waiting")
    ).join( OrderProduct, Product.id == OrderProduct.product_id ) \
        .join( Order, OrderProduct.order_id == Order.id ) \
        .group_by( Product.name ).all( )

    # Now that we have the necessary information about products we can create and format the statistics for every product
    statistics = [ ]
    for product in product_information:
        product_dict = {
            "name": product.name,
            "sold": int( product.sold ),
            "waiting": int( product.waiting )
        }
        statistics.append( product_dict )

    # Return the statistics
    return jsonify( { "statistics": statistics } ), 200

# Route is used to create statistics for the category
@application.route( '/category_statistics', methods=[ 'GET' ] )
@roleCheck( role='owner' )
def category_statistics( ):

    from sqlalchemy import func, case, desc

    # Polje statistics predstavlja niz imena svih kategorija koje se trenutno nalaze u
    # bazi. Niz je sortiran opadajuće po broju dostavljenih primeraka proizvoda koji
    # pripadaju toj kategoriji. Ukoliko se proizvod pripada više od jednoj kategoriji, računati
    # ga kao dostavljenog u svim njegovim kategorijama. Ukoliko dve kategorije imaju isti
    # broj dostavljenih proizvoda, sortirati ih rastuće po imenu.

    # Query has multiple layers. First is SELECT part where we select categories by name and perform the func.sum function where
    # we calculate the sum of product quantities sold within each category and we label it 'sold'. After that we got to join the tables using outerJoin function,
    # so we get the necessary data. After that we have GROUP BY part of query where we group by Name of the category (we are returning name
    # of the category in the statistics). ORDER BY part of the query is used to sort the categories descending by the number of sold items
    # The query itself has the condition to sort by number of sold items, and if we have 2 categories with the same number of sold items, we sort them by name
    category_info = database.session.query(
        Category.name,
        func.sum(
            case(
                [(Order.status == 'COMPLETE', OrderProduct.quantity)],
                else_=0
            )
        ).label('sold')
    ) \
        .outerjoin(ProductCategory) \
        .outerjoin(Product) \
        .outerjoin(OrderProduct) \
        .outerjoin(Order) \
        .group_by(Category.name) \
        .order_by(desc('sold'), Category.name) \
        .all()

    # We now use list comprehension mechanism to extract the names of the categories we need to return
    ret_val = [ category.name for category in category_info ]

    return jsonify( { 'statistics': ret_val } ), 200


# Start the application
if ( __name__ == "__main__" ):
    database.init_app( application )
    application.run( debug=True, host='0.0.0.0', port=5001 )