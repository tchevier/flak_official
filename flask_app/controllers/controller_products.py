from math import prod
from statistics import quantiles
from flask import Flask, render_template, redirect, session, request, url_for
from flask_app import app

from flask_app.models.model_users import User
from flask_app.models.model_products import Product
from flask_app.models.model_carts import Cart

import stripe

app.config['STRIPE_PUBLIC_KEY'] = "pk_test_51LZfwfBpdBqI2NGfTcsVuhYX7cGryM01JYho5soGOJZUc631Toshd5bjjxFNmhqRV70E9rDw1XDdOd0VmpYyajNX003T3MoQAW"
app.config['STRIPE_SECRET_KEY'] = "sk_test_51LZfwfBpdBqI2NGfeg0WCAbt76TgguncRH6nL6KtvErDSgmoSEkjTcOeRJFUZdAaPBaTReS4XoGIRUlC4qZyHntV00vJ7CMz5a"

stripe.api_key = "sk_test_51LZfwfBpdBqI2NGfeg0WCAbt76TgguncRH6nL6KtvErDSgmoSEkjTcOeRJFUZdAaPBaTReS4XoGIRUlC4qZyHntV00vJ7CMz5a"

    
#CART PROCESS
@app.route('/cart/<int:id>/process', methods=['POST'])
def cart_process(id):
    if 'user_id' in session:
        relation_data = {
            'cart_id': session['cart_id'],
            'product_id': session['product_id'],
            'quantity': request.form['quantity'],
            'size': request.form['size'],
        }
        if Cart.validate_relation(relation_data):
            Cart.relate_product_to_cart(relation_data)
            Cart.update_cart(relation_data)
            return redirect(f'/cart/{id}')
        return redirect(f'/shop/{session["product_id"]}/view')
    return redirect('/login')

#CART UPDATE
@app.route('/cart/<int:id>/update', methods=['POST'])
def cart_update(id):
    if 'user_id' in session:
        data = {
        'cart_id': id,
        'size': request.form['size'],   
        'product_id': request.form['product_id'],
        'quantity': request.form['quantity'],
        
        }
        relation_id = Cart.get_relation(data)
        data = {
        'id': relation_id,
        'cart_id': id,
        'size': request.form['size'],   
        'product_id': request.form['product_id'],
        'quantity': request.form['quantity'],
        }
        Cart.update_cart(data)

        return redirect(f'/cart/{id}')
    return redirect('/login')

#DELETE ITEM FROM CART
@app.route('/cart/<int:cart_id>/<int:product_id>/<string:size>/delete')
def cart_delete_product(cart_id, product_id, size):
    if 'user_id' in session:
        data = {
            'cart_id': cart_id,
            'product_id' : product_id,
            'size': size,
        }
        Cart.delete_product_from_cart(data)
        print("empieed")
        return redirect(f'/cart/{cart_id}')
    return redirect('/login')

#CART CHECKOUT
@app.route('/cart/<int:id>')
def cart(id):
    if 'user_id' in session:
        cart = Cart.get_cart({'user_id': session['user_id']})
        user = User.get_one({'id': session['user_id']})
        Cart.get_products_from_cart({'id': session['cart_id']}, cart)
        is_empty = True
        for product in cart.products:
            if product.quantity != 0:
                is_empty = False
        if not is_empty:      
            subtotal = 0
            #TAX
            # tax = round(total_price * 0.083, 2)
            # session['total_price'] = total_price + tax
            line_items_actual = []
            for product in cart.products:
                dict = {
                'price' : product.stripe_id, 
                'quantity': product.quantity
                }
                line_items_actual.append(dict)
                subtotal += (product.price * product.quantity)

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items= line_items_actual,
                mode='payment',
                success_url= url_for('success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url = url_for('cancel', _external=True),
            )
            return render_template('cart.html', cart = cart , subtotal = subtotal, user = user, checkout_session_id = checkout_session['id'], checkout_public_key = app.config['STRIPE_PUBLIC_KEY'])

        return render_template('cart.html', cart = cart, user = user)
    return redirect('/login')

#CHECKOUT SUCCESS
@app.route('/checkout-session/success')
def success():
    #EMPTY CART
    Cart.empty_cart({'cart_id': session['cart_id']})

    return render_template('success.html')

#CHECKOUT FAIL
@app.route('/checkout-session/cancel')
def cancel():
    return redirect('/')


