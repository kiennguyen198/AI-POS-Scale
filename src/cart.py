def calculate_item_total(price_per_kg,weight_g):
    item_total=round(price_per_kg*weight_g/1000)
    return item_total

def add_item(cart,fruit_name,weight_g,price_per_kg):
    item_total=calculate_item_total(price_per_kg,weight_g)
    item={  
        "fruit_name":fruit_name,
        "weight_g":weight_g,
        "price_per_kg":price_per_kg,
        "item_total":item_total
    }
    cart.append(item)

def calculate_cart_total(cart):
    cart_total=0
    for item in cart:
        cart_total+=item["item_total"]
    return cart_total

def remove_item(cart,item_index):
    removed_item=cart.pop(item_index)
    return removed_item

def clear_cart(cart):
    cart.clear()