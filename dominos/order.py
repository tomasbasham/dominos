from dominos import Client, VARIANT, FULFILMENT_METHOD

api = Client()
store = api.get_nearest_store("NW1 2AS")
print(store.name)

api.set_delivery_system(store, 'NW1 2AS', fulfilment_method= FULFILMENT_METHOD.COLLECTION)

menu = api.get_menu(store)
print(menu)
potato = menu.get_product_by_name("Potato Wedges")
api.add_item_to_basket(potato, variant=VARIANT.LARGE, quantity=2)
basket = api.get_basket()
print(basket.items)
