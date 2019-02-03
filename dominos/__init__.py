'''
Wrapper for the Dominos Pizza UK API

This module provides
'''
from dominos.api import Client, VARIANT, PAYMENT_METHOD, FULFILMENT_METHOD
from dominos.exception import ApiError

__all__ = [
    'Client',
    'ApiError',
    'VARIANT',
    'PAYMENT_METHOD',
    'FULFILMENT_METHOD'
]

__version__ = '0.0.4'
