from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy( )
#Table is used as connection table between Product and their Categories
class ProductCategory ( database.Model ):
    __tablename__ = "product_categories"
    id = database.Column( database.Integer, primary_key=True )
    thread_id = database.Column( database.Integer, database.ForeignKey( "products.id" ), nullable=False )
    tag_id = database.Column( database.Integer, database.ForeignKey( "categories.id" ), nullable=False )

#Table is used as connection table between Order and their Products
class OrderProduct ( database.Model ):
    __tablename__ = "order_products"
    order_id = database.Column( database.Integer, database.ForeignKey( "orders.id" ), primary_key=True )
    product_id = database.Column( database.Integer, database.ForeignKey( "products.id" ), primary_key=True )
    quantity = database.Column( database.Integer, nullable=False )
    order = database.relationship( "Order", back_populates="order_products" )
    product = database.relationship( "Product", backref="order_products" )

class Product ( database.Model ):
    __tablename__ = "products"
    id = database.Column( database.Integer, primary_key=True )
    name = database.Column( database.String(256), nullable=False )
    price = database.Column( database.Float, nullable=False )
    categories = database.relationship( "Category", secondary=ProductCategory.__table__, back_populates="products" )

    def __repr__( self ):
        return f"({ str( self.categories ) }, {str( self.id ) }, { str( self.name ) }, { str( self.price ) })"

class Category ( database.Model ):
    __tablename__ = "categories"
    id = database.Column( database.Integer, primary_key=True)
    name = database.Column( database.String(256), nullable=False)
    products = database.relationship( "Product", secondary=ProductCategory.__table__, back_populates="categories" )

    def __repr__( self ):
        return f"({ self.name })"

class Order(database.Model):
    __tablename__ = "orders"
    id = database.Column( database.Integer, primary_key=True )
    total_price = database.Column( database.Float, nullable=False )
    status = database.Column( database.String(50), nullable=False )
    timestamp = database.Column( database.DateTime, nullable=False )
    user = database.Column( database.String(256), nullable=False )
    order_products = database.relationship( "OrderProduct", back_populates="order" )

    def __repr__(self):
        return f'id: {self.id} status: {self.status} date: {self.timestamp} user: {self.user}'

