import calendar
import time
from colorama import *
from ratelimit import rate_limited

import requests


def get_epoch():
    '''
    Utility function used to get the current
    epoch time. Required for some calls to
    the remote.

    :return: String representing the current epoch time.
    '''
    return calendar.timegm(time.gmtime())


def enum(**enums):
    '''
    Utility function to create a simple
    enum-like data type. Behind the scenes it
    is just an array.

    :param list enums: A list of key value pairs.
    :return: A simple list.
    '''
    return type('Enum', (), enums)


VARIANTS = enum(PERSONAL=0, SMALL=1, MEDIUM=2, LARGE=3)
PAYMENT_METHODS = enum(CASH_ON_DELIVERY=0, CARD=1, PAYPAL=2)


class Store(object):
    """
    Parses raw data returned from the API and stores it in an easy-to-use object
    :param raw_data: The raw data returned from a Local Store search
    """
    def __init__(self, raw_data):
        local_store = raw_data['localStore']
        self.id = local_store['id']
        self.name = local_store['name']
        self.collection = local_store['isCollectionAvailable']
        self.delivery = raw_data['isDeliveryAvailableFromStore']
        self.menu_version = local_store['menuVersion']


class Item(object):
    """
    Stores necessary information on menu items
    :param raw_data: The raw data from a menu search
    """
    def __init__(self, raw_data, subcategory):
        self.name = raw_data['name'].replace("®", "").replace("™", "")
        self.price = raw_data['price']
        self.id = raw_data['productId']
        self.skus = raw_data['productSkus']
        self.type = subcategory


class Menu(object):
    """
    Stores a list of Item objects retrieved from a Get Menu call
    :param raw_data: The raw data from a Get Menu call
    """
    def __init__(self, raw_data):
        self.categories = []
        self.items = []
        for category in raw_data:
            self.categories.append(category['name'])
            for subcategory in category['subcategories']:
                for item in subcategory['products']:
                    self.items.append(Item(item, subcategory['type']))

    def get_product_by_name(self, name):
        """
        Gets an Item from the Menu by name. Note that the name is not case-sensitive but
        must be spelt correctly. None will be returned if no matching name is found.
        Note that the Trademark Symbols have been removed.
        :param name: The name of the item
        :return: An item object matching the search, or None if none were found
        """

        for item in self.items:
            if item.name.lower() == name.lower():
                return item

        return None


class Client(object):
    '''
    API class for the UK version of Dominos
    pizza website.
    '''

    class ApiError(Exception):
        '''
        API exception class. It is exactly the
        same as a regular exception.
        '''
        pass

    BASE_URL = 'https://www.dominos.co.uk'

    def __init__(self):
        init()

        self.session = requests.session()

        self.reset_session()
        self.reset_store()

    @rate_limited(1)
    def reset_session(self):
        '''
        Clear out the current session on the remote
        and setup a new one.

        :return: A response object.
        '''
        response = self.session.get(self.__url('/Home/SessionExpire'))

        if response.status_code != 200:
            raise self.ApiError('Failed to clear session: {}'.format(response.status_code))

        self.session = requests.session()
        self.session.headers.update({'content-type': 'application/json; charset=utf-8'})

        return response

    @rate_limited(1)
    def reset_store(self):
        '''
        Clears out the current store and gets a cookie.
        Set the cross site request forgery token for
        each subsequent request.

        :return: A response object.
        '''
        response = self.session.get(self.__url('/Store/Reset'))

        if response.status_code != 200:
            raise self.ApiError('Cannot get cookie: {}'.format(response.status_code))

        self.session.headers.update({'X-XSRF-TOKEN': self.session.cookies['XSRF-TOKEN']})

        return response

    @rate_limited(1)
    def get_stores(self, search):
        '''
        Search for dominos pizza stores using a search
        term.

        :param search: Search term.
        :return: A response object.
        '''
        params = {'search': search}
        response = self.session.get(self.__url('/storefindermap/storenamesearch'), params=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot fetch stores: {}'.format(response.status_code))

        return response

    @rate_limited(1)
    def get_nearest_store(self, postcode):
        '''
        Search for domino pizza stores using a postcode.
        This will only search for local stores indicating
        delivery status and payment details.

        :param postcode: A postcode.
        :return: A Store object.
        '''
        params = {'SearchText': postcode}
        response = self.session.get(self.__url('/storefindermap/storesearch'), params=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot fetch nearest store for {}: {}'.format(postcode, response.status_code))

        return Store(response.json())

    @rate_limited(1)
    def set_delivery_system(self, idx, postcode):
        '''
        Set local cookies by initialising the delivery
        system on the remote. Requires a store ID and
        a delivery postcode.

        :param idx: Store id.
        :param postcode: A postcode.
        :return: A response object.
        '''
        params = {'fulfilmentmethod': 'delivery', 'postcode': postcode, 'storeid': idx}
        response = self.session.post(self.__url('/Journey/Initialize'), json=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot create cookie: {}'.format(response.status_code))

        return response

    @rate_limited(1)
    def get_menu(self, store):
        '''
        Retrieve the menu from the selected store.

        :param store: The store to retrieve menu from.
        :return: A Menu object.
        '''

        params = {
            "collectionOnly": store.delivery,
            "menuVersion": store.menu_version,
            "storeId": store.id,
        }
        response = self.session.get(self.__url('/ProductCatalog/GetStoreCatalog'), params=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot get menu: {}'.format(response.status_code))

        return Menu(response.json())

    @rate_limited(1)
    def get_basket(self):
        '''
        Retrieve the basket for the current session.

        :return: A response object.
        '''
        response = self.session.get(self.__url('/CheckoutBasket/GetBasket'))

        if response.status_code != 200:
            raise self.ApiError('Cannot get basket: {}'.format(response.status_code))

        return response

    def add_item_to_basket(self, item, variant, quantity=1):
        '''
        Add an item to the current basket.

        :param item: Item from menu.
        :param variant: Item SKU id.
        :param quantity: The quantity of item to be added
        :return: A response object, or None if an item type is not recognised.
        '''

        item_type = item.type

        if item_type == 'Pizza':
            return self.add_pizza_to_basket(item, variant, quantity)
        elif item_type == 'Side':
            return self.add_side_to_basket(item, variant, quantity)
        return None

    @rate_limited(1, 5)
    def add_pizza_to_basket(self, item, variant=VARIANTS.MEDIUM, quantity=1):
        '''
        Add a pizza to the current basket.

        :param item: Item from menu.
        :param variant: Item SKU id. Some defaults are defined in the VARIANTS enum.
        :param quantity: The quantity of pizzas to be added
        :return: A response object.
        '''

        item_variant = item.skus[variant]
        ingredients = item_variant['ingredients'].update([36, 42])

        params = {'stepId': 0, 'quantity': quantity, 'sizeId': variant, 'productId': item.id, 'ingredients': ingredients, 'productIdHalfTwo': 0, 'ingredientsHalfTwo': [], 'recipeReferrer': 0}
        response = self.session.post(self.__url('/Basket/AddPizza/'), json=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot add {} {} to basket: {}'.format(item_variant['name'], item['name'], response.status_code))

        return response

    @rate_limited(1, 5)
    def add_side_to_basket(self, item, variant=VARIANTS.PERSONAL, quantity=1):
        '''
        Add a side to the current basket.

        :param item: Item from menu.
        :param variant: Item SKU id. Some defaults are defined in the VARIANTS enum.
        :param quantity: The quantity of sides to be added
        :return: A response object.
        '''

        item_variant = item.skus[variant]

        params = {'productSkuId': item_variant['productSkuId'], 'quantity': quantity, 'ComplimentaryItems': []}
        response = self.session.post(self.__url('/Basket/AddProduct'), json=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot add {} {} to basket: {}'.format(item_variant['name'], item['name'], response.status_code))

        return response

    @rate_limited(1, 5)
    def remove_item_from_basket(self, item):
        '''
        Remove an item from the current basket.

        :param item: Basket item object.
        :return: A response object.
        '''
        params = {'basketItemId': item.id, 'wizardItemDelete': False}
        response = self.session.post(self.__url('/Basket/RemoveBasketItem'), params=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot remove {} from basket: {}'.format(item.name, response.status_code))

        return response

    @rate_limited(1)
    def get_payment_options(self):
        '''
        Retrieve a series of payment options
        alongside the card url used to
        authorise payments through mastercard
        datacash service.

        There is no guarantee the card url will
        be accepted as mastercard will likely
        reject the origin of the request.

        :return: A response object.
        '''
        response = self.session.post(self.__url('/PaymentOptions/GetPaymentDetailsData'))

        if response.status_code != 200:
            raise self.ApiError('Cannot get payment details: {}'.format(response.status_code))

        return response

    @rate_limited(1)
    def set_payment_method(self, method=PAYMENT_METHODS.PAYPAL):
        '''
        Select the payment method going to be
        used to make a purchase.

        :param method: Payment method id.
        :return: A response object.
        '''
        params = {'paymentMethod': method}
        response = self.session.post(self.__url('/PaymentOptions/SetPaymentMethod'), json=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot set payment method: {}'.format(response.status_code))

        return response

    @rate_limited(1)
    def process_payment(self):
        '''
        Proceed with payment using the payment
        method selected earlier.

        :return: A response object.
        '''
        params = {'__RequestVerificationToken': self.session.cookies, 'method': 'submit'}
        response = self.session.post(self.__url('/PaymentOptions/Proceed'), json=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot process payment: {}'.format(response.status_code))

        return response

    def __url(self, path):
        '''
        Helper method to generate fully qualified URIs
        pertaining to specific API actions.

        :param path: Relative API path to resource.
        :return: Fully qualified URI to API resource.
        '''
        return self.BASE_URL + path
