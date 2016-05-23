dominos
=======
.. image:: https://travis-ci.org/tomasbasham/dominos.svg?branch=master
    :target: https://travis-ci.org/tomasbasham/dominos

Dominos Pizza remains today a closed system, not officially offering a public API from which to order delicious baked pizzas. However with the invent of their multiple mobile applications and their own website having been reimplemented in AngularJS it was apparent these all used some undocumented public API.

This packages implements an abstract layer to the Dominos Pizza (UK) API, returning raw response objects from which JSON payloads can be read.

Installation
------------

PyPi
~~~~

To install dominos, simply:

.. code:: bash

    $ pip install dominos

GitHub
~~~~~~

Installing the latest version from Github:

.. code:: bash

    $ git clone https://github.com/tomasbasham/dominos
    $ cd dominos
    $ python setup.py install

Usage
-----

To use this package you simply have to instantiate a Dominos object:

.. code:: python

    from dominos.api import Client
    api = Client()
    response = api.get_nearest_store('AB12 000')
    print(response.json())

This returns the nearest store to the supplied postcode. There are many other methods implemented in this package to return store menus, add items to a basket and checkout.

Contributing
------------

1. Fork it ( https://github.com/tomasbasham/dominos/fork )
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create a new Pull Request
