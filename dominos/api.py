import calendar
import time

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
        :return: A response object.
        '''
        params = {'SearchText': postcode}
        response = self.session.get(self.__url('/storefindermap/storesearch'), params=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot fetch nearest store for {}: {}'.format(postcode, response.status_code))

        return response

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
    def get_store_context(self):
        '''
        Get the required context for the store. This must
        be called at some point after initialising the
        delivery system.

        :return: A response object.
        '''
        params = {'_': get_epoch()}
        response = self.session.get(self.__url('/ProductCatalog/GetStoreContext'), params=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot fetch store context: {}'.format(response.status_code))

        return response

    @rate_limited(1)
    def get_categories(self, context):
        '''
        Retrieve the menu categories from the selected store.

        :param context: The store context.
        :return: A response object.
        '''
        session_context = context['sessionContext']
        response = self.session.get(self.__url('/ProductCatalog/GetStoreCatalogCategories'), params=session_context)

        if response.status_code != 200:
            raise self.ApiError('Cannot get menu: {}'.format(response.status_code))

        return response

    @rate_limited(1)
    def get_menu(self, context):
        '''
        Retrieve the menu from the selected store.

        :param context: The store context.
        :return: A response object.
        '''
        session_context = context['sessionContext']
        response = self.session.get(self.__url('/ProductCatalog/GetStoreCatalog'), params=session_context)

        if response.status_code != 200:
            raise self.ApiError('Cannot get menu: {}'.format(response.status_code))

        return response

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

    def add_item_to_basket(self, item, variant, options=None):
        '''
        Add an item to the current basket.

        :param item: Item from menu.
        :param variant: Item SKU id.
        :param options: Additional options, such as quantity.
        :return: A response object, or None if an item type is not recognised.
        '''
        if options is None:
            options = {}

        item_type = item['type']

        if item_type == 'Pizza':
            return self.add_pizza_to_basket(item, variant, options)
        elif item_type == 'Side':
            return self.add_side_to_basket(item, variant, options)
        return None

    @rate_limited(1)
    def add_pizza_to_basket(self, item, variant=VARIANTS.MEDIUM, options=None):
        '''
        Add a pizza to the current basket.

        :param item: Item from menu.
        :param variant: Item SKU id. Some defaults are defined in the VARIANTS enum.
        :param options: Additional options, such as quantity.
        :return: A response object.
        '''
        if options is None:
            options = {}

        quantity = options.get('quantity', 1)
        item_variant = item['productSkus'][variant]
        ingredients = item_variant['ingredients'].update([36, 42])

        params = {'stepId': 0, 'quantity': quantity, 'sizeId': variant, 'productId': item['productId'], 'ingredients': ingredients, 'productIdHalfTwo': 0, 'ingredientsHalfTwo': [], 'recipeReferrer': 0}
        response = self.session.post(self.__url('/Basket/AddPizza/'), json=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot add {} {} to basket: {}'.format(item_variant['name'], item['name'], response.status_code))

        return response

    @rate_limited(1)
    def add_side_to_basket(self, item, variant=VARIANTS.PERSONAL, options=None):
        '''
        Add a side to the current basket.

        :param item: Item from menu.
        :param variant: Item SKU id. Some defaults are defined in the VARIANTS enum.
        :param options: Additional options, such as quantity.
        :return: A response object.
        '''
        if options is None:
            options = {}

        quantity = options.get('quantity', 1)
        item_variant = item['productSkus'][variant]

        params = {'ProductSkuId': item_variant['productSkuId'], 'Quantity': quantity, 'ComplimentaryItems': []}
        response = self.session.post(self.__url('/Basket/AddProduct'), json=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot add {} {} to basket: {}'.format(item_variant['name'], item['name'], response.status_code))

        return response

    @rate_limited(1)
    def remove_item_from_basket(self, idx):
        '''
        Remove an item from the current basket.

        :param idx: Basket item id.
        :return: A response object.
        '''
        params = {'basketItemId': idx, 'wizardItemDelete': False}
        response = self.session.post(self.__url('/Basket/RemoveBasketItem'), params=params)

        if response.status_code != 200:
            raise self.ApiError('Cannot remove {} from basket: {}'.format(idx, response.status_code))

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
        response = self.session.post(self.__url('/paymentoptions/proceed'), json=params)

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
