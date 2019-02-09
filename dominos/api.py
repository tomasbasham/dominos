'''
Dominos Pizza API public interface.

This module includes the client object used to make requests to the Dominos
Pizza UK API. Additionally it provides some global constants that may be used
as configuration optons to some API methods.
'''
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo

from dominos.exception import ApiError
from dominos.models import Stores, Menu, Basket
from dominos.utils import enum, update_session_headers

import requests

VARIANT = enum(PERSONAL=0, SMALL=1, MEDIUM=2, LARGE=3)
PAYMENT_METHOD = enum(CASH_ON_DELIVERY=0, CARD=1, PAYPAL=2, VISA_CHECKOUT=4)
FULFILMENT_METHOD = enum(COLLECTION=0, DELIVERY=1)

class Client(object):
    '''
    API class for the UK version of Dominos pizza website.
    '''
    BASE_URL = 'https://www.dominos.co.uk'

    def __init__(self, session=requests.session()):
        self.session = update_session_headers(session)
        self.reset_store()

    def new_session(self, session):
        '''
        Clear out the current session on the remote and setup a new one.

        :return: A response from having expired the current session.
        :rtype: requests.Response
        '''
        response = self.__get('/Home/SessionExpire')
        self.session = update_session_headers(session)

        return response

    def reset_store(self):
        '''
        Clears out the current store and gets a cookie. Set the cross site
        request forgery token for each subsequent request.

        :return: A response having cleared the current store.
        :rtype: requests.Response
        '''
        response = self.__get('/Store/Reset')

        token = self.session.cookies['XSRF-TOKEN']
        self.session.headers.update({'X-XSRF-TOKEN': token})

        return response

    def get_stores(self, search_term):
        '''
        Search for dominos pizza stores using a search term.

        :param string search: Search term.
        :return: A list of nearby stores matching the search term.
        :rtype: list
        '''
        params = {'SearchText': search_term}
        response = self.__get('/storefindermap/storesearch', params=params)

        return Stores(response.json())

    def get_nearest_store(self, postcode):
        '''
        Search for domino pizza stores using a postcode. This will only search
        for local stores indicating delivery status and payment details.

        :param string postcode: A postcode.
        :return: A response containing stores matching the postcode.
        :rtype: requests.Response
        '''
        return self.get_stores(postcode).local_store

    def set_delivery_system(self, store, postcode, fulfilment_method=FULFILMENT_METHOD.DELIVERY):
        '''
        Set local cookies by initialising the delivery system on the remote.
        Requires a store ID and a delivery postcode.

        :param Store store: Store id.
        :param string postcode: A postcode.
        :return: A response having initialised the delivery system.
        :rtype: requests.Response
        '''
        method = 'delivery' if fulfilment_method == FULFILMENT_METHOD.DELIVERY else 'collection'

        params = {
            'fulfilmentMethod': method,
            'postcode': postcode,
            'storeid': store.store_id
        }

        return self.__post('/Journey/Initialize', json=params)

    def get_menu(self, store):
        '''
        Retrieve the menu from the selected store.

        :param Store store: A store.
        :return: The store menu.
        :rtype: Menu
        '''
        params = {
            'collectionOnly': not store.delivery_available,
            'menuVersion': store.menu_version,
            'storeId': store.store_id,
        }

        response = self.__get('/ProductCatalog/GetStoreCatalog', params=params)
        return Menu(response.json())

    def get_basket(self):
        '''
        Retrieve the basket for the current session.

        :return: A response containing the basket for the current session.
        :rtype: requests.Response
        '''
        response = self.__get('/CheckoutBasket/GetBasket')
        return Basket(response.json())

    def add_item_to_basket(self, item, variant=VARIANT.MEDIUM, options={'quantity': 1}):
        '''
        Add an item to the current basket.

        :param Item item: Item from menu.
        :param int variant: Item SKU id. Ignored if the item is a side.
        :param dict options: Dictionary of options like quantity and an ingredients list
        :return: A response having added an item to the current basket.
        :rtype: requests.Response
        '''
        item_type = item.type

        if item_type == 'Pizza':
            return self.add_pizza_to_basket(item, variant, options)
        elif item_type == 'Side':
            return self.add_side_to_basket(item, options['quantity'])
        return None

    def add_pizza_to_basket(self, item, variant=VARIANT.MEDIUM, options={}):
        '''
        Add a pizza to the current basket.

        :param Item item: Item from menu.
        :param int variant: Item SKU id. Some defaults are defined in the VARIANT enum.
        :param dict options: Dictionary of options like quantity and an ingredients list. If nothing is
        specified then a default quantity of 1 and the default ingredients for the pizza will be used.
        :return: A response having added a pizza to the current basket.
        :rtype: requests.Response
        '''
        item_variant = item[variant]
        ingredients = [42, 36] + item_variant['ingredients'] + options.get("ingredients", [])

        params = {
            'stepId': 0,
            'quantity': options['quantity'],
            'sizeId': variant,
            'productId': item.item_id,
            'ingredients': ingredients,
            'productIdHalfTwo': 0,
            'ingredientsHalfTwo': [],
            'recipeReferrer': 0
        }

        return self.__post('/Basket/AddPizza', json=params)

    def add_side_to_basket(self, item, quantity=1):
        '''
        Add a side to the current basket.

        :param Item item: Item from menu.
        :param int quantity: The quantity of side to be added.
        :return: A response having added a side to the current basket.
        :rtype: requests.Response
        '''
        item_variant = item[VARIANT.PERSONAL]

        params = {
            'productSkuId': item_variant['productSkuId'],
            'quantity': quantity,
            'ComplimentaryItems': []
        }

        return self.__post('/Basket/AddProduct', json=params)

    def remove_item_from_basket(self, idx):
        '''
        Remove an item from the current basket.

        :param int idx: Basket item id.
        :return: A response having removed an item from the current basket.
        :rtype: requests.Response
        '''
        params = {
            'basketItemId': idx,
            'wizardItemDelete': False
        }

        return self.__post('/Basket/RemoveBasketItem', json=params)

    def set_payment_method(self, method=PAYMENT_METHOD.CASH_ON_DELIVERY):
        '''
        Select the payment method going to be used to make a purchase.

        :param int method: Payment method id.
        :return: A response having set the payment option.
        :rtype: requests.Response
        '''
        params = {'paymentMethod': method}
        return self.__post('/PaymentOptions/SetPaymentMethod', json=params)

    def set_delivery_address(self):
        '''
        Set the delivery address for the order.
        '''
        pass

    def process_payment(self):
        '''
        Proceed with payment using the payment method selected earlier.

        :return: A response having processes the payment.
        :rtype: requests.Response
        '''
        params = {
            '__RequestVerificationToken': self.session.cookies,
            'method': 'submit'
        }

        return self.__post('/PaymentOptions/Proceed', json=params)

    def __get(self, path, **kargs):
        '''
        Make a HTTP GET request to the Dominos UK API with the given parameters
        for the current session.

        :param string path: The API endpoint path.
        :params list kargs: A list of arguments.
        :return: A response from the Dominos UK API.
        :rtype: response.Response
        '''
        return self.__call_api(self.session.get, path, **kargs)

    def __post(self, path, **kargs):
        '''
        Make a HTTP POST request to the Dominos UK API with the given
        parameters for the current session.

        :param string path: The API endpoint path.
        :params list kargs: A list of arguments.
        :return: A response from the Dominos UK API.
        :rtype: response.Response
        '''
        return self.__call_api(self.session.post, path, **kargs)

    @on_exception(expo, (ApiError, RateLimitException), max_tries=10)
    @limits(calls=5, period=1)
    def __call_api(self, verb, path, **kargs):
        '''
        Make a HTTP request to the Dominos UK API with the given parameters for
        the current session.

        :param verb func: HTTP method on the session.
        :param string path: The API endpoint path.
        :params list kargs: A list of arguments.
        :return: A response from the Dominos UK API.
        :rtype: response.Response
        '''
        response = verb(self.__url(path), **kargs)

        if response.status_code != 200:
            raise ApiError('{}: {}'.format(response.status_code, response))

        return response

    def __url(self, path):
        '''
        Helper method to generate fully qualified URIs pertaining to specific
        API actions.

        :param string path: Relative API path to resource.
        :return: Fully qualified URI to API resource.
        :rtype: string
        '''
        return self.BASE_URL + path
