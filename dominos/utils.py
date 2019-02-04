'''
Dominos Pizza API utility functions.
'''
import re

def enum(**enums):
    '''
    Utility function to create a simple enum-like data type. Behind the scenes
    it is just a list.

    :param list enums: A list of key value pairs.
    :return: A simple list.
    :rtype: list
    '''
    return type('Enum', (), enums)

def strip_unicode_characters(text):
    '''
    Remove the unicode symbols from the given string.

    :param string text: The text containing the trademark symbol.
    :return: Text with the unicode symbols removed.
    :rtype: string
    '''
    return re.sub(r'[^\x00-\x7F]+', '', text)

def update_session_headers(session):
    '''
    Add content type header to the session.

    :param: requests.sessions.Session session: A session.
    :return: A session with modified headers.
    :rtype: requests.sessions.Session
    '''
    session.headers.update({
        'Content-Type': 'application/json; charset=utf-8',
        'Host': 'www.dominos.co.uk'
    })

    return session
