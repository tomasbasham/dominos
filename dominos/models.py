'''
Dominos Pizza API models.
'''
from dominos.utils import strip_unicode_characters

class Stores(object):
    '''
    Encapsulates a list of nearby stores returned from the API.
    '''
    def __init__(self, data):
        delivery_available = data.get('localStoreCanDeliverToAddress', False)
        collection_stores = data.get('collectionStores', [])

        self.local_store = None
        if 'localStore' in data:
            self.local_store = Store(data['localStore'], delivery_available)
        self.collection_stores = [Store(s) for s in collection_stores]

    def __getitem__(self, idx):
        return self.collection_stores[idx]

    def __len__(self):
        return len(self.collection_stores)

    def __str__(self):
        stores = ''
        for store in self.collection_stores:
            stores = stores + str(store) + '\n'
        return stores

class Store(object):
    '''
    Encapsulates a single store returned from the API.
    '''
    def __init__(self, data, delivery_available=False):
        self.store_id = data['id']
        self.name = data['name']
        self.is_open = data.get('isOpen', False)
        self.collection = data.get('isCollectionAvailable', False)
        self.delivery_available = delivery_available
        self.menu_version = data['menuVersion']

    def __eq__(self, other):
        return self.store_id == other.store_id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return 'name: {}, open: {}'.format(self.name, self.is_open)

class Menu(object):
    '''
    Encapsulates a store menu.
    '''
    def __init__(self, data):
        self.items = [Item(i) for category in data for i in category['subcategories'][0]['products']]

    def get_product_by_name(self, name):
        '''
        Gets a Item from the Menu by name. Note that the name is not
        case-sensitive but must be spelt correctly.

        :param string name: The name of the item.
        :raises StopIteration: Raises exception if no item is found.
        :return: An item object matching the search.
        :rtype: Item
        '''
        return next(i for i in self.items if i.name.lower() == name.lower())

    def __len__(self):
        return len(self.items)

    def __getitem__(self, item_id):
        return next(item for item in self.items if item.item_id == item_id)

    def __str__(self):
        menu = ''
        for item in self.items:
            menu = menu + str(item) + '\n'
        return menu

class Item(object):
    '''
    Encapsulates a sinlge menu item.
    '''
    def __init__(self, data):
        self.item_id = data['productId']
        self.name = strip_unicode_characters(data['name'])
        self.price = data['price']
        self.skus = data['productSkus']
        self.type = data['type']

    def __getitem__(self, variant):
        return self.skus[variant]

    def __eq__(self, other):
        return self.item_id == other.item_id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return 'name: {}, type: {}, base price: {}'.format(self.name, self.type, self.price)

class Basket(object):
    '''
    Encapsulates a basket.
    '''
    def __init__(self, data):
        self.items = data['items']
