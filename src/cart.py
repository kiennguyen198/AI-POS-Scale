def calculate_item_total(price_per_kg,weight_g):
    item_total=round(price_per_kg*weight_g/1000)
    return item_total

def add_item(
    cart,
    fruit_name,
    weight_g,
    price_per_kg,
    label_id=None
):
    item_total=calculate_item_total(price_per_kg,weight_g)
    item={  
        "fruit_name":fruit_name,
        "weight_g":weight_g,
        "price_per_kg":price_per_kg,
        "item_total":item_total
    }

    if label_id is not None:
        item["label_id"]=label_id

    cart.append(item)

def calculate_cart_total(cart):
    cart_total=0
    for item in cart:
        cart_total+=item["item_total"]
    return cart_total

def remove_item(cart,item_index):
    removed_item=cart.pop(item_index)
    return removed_item

def has_label_id(cart,label_id):
    for item in cart:
        if item.get("label_id")==label_id:
            return True
    return False

def add_scanned_product(cart,product,should_add):
    if not should_add:
        return False

    if has_label_id(cart,product["label_id"]):
        return False

    add_item(
        cart,
        product["fruit_name"],
        product["weight_g"],
        product["price_per_kg"],
        product["label_id"]
    )

    return True

def clear_cart(cart):
    cart.clear()
