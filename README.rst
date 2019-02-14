dominos |build| |maintainability|
=================================

Dominos Pizza remains today a closed system, not officially offering a public
API from which to order delicious baked pizzas. However with the invent of
their multiple mobile applications and their own website having been
reimplemented in AngularJS it was apparent these all used some undocumented
API.

This package implements an abstract layer on top the Dominos Pizza (UK) API,
returning objects from which data can be read.

Installation
------------

PyPi
~~~~

Add this line to your application's requirements.txt:

.. code:: python

    dominos

And then execute:

.. code:: bash

    $ pip install -r requirements.txt

Or install it yourself:

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

To use this package simply instantiate a ``Client`` object:

.. code:: python

    from dominos import Client, VARIANT

    api = Client()
    store = api.get_nearest_store('AB12 000')
    print(store.name)

This returns the nearest store for the supplied postcode and prints the name
returned from the API. Additionally it sets the necessary ``XSRF-TOKEN``
required to perform some actions later in the process. These include adding an
item to the basket and processing payments.

To grab the store menu:

.. code:: python

    menu = api.get_menu(store)
    potato_wedges = menu.get_product_by_name('Potato Wedges')
    print(potato_wedges.price)
    
``get_product_by_name`` is not case sensitive.

**Note**: Never call more than one api function in the same line! This causes
issues with the API that may result in data being incorrectly processed.

.. code:: python

    api.add_item_to_basket(item=menu.get_item_by_name("Original Cheese & Tomato"), variant=VARIANTS.MEDIUM)

This code calls two api functions - ``api.add_item_to_basket`` and
``menu.get_item_by_name``. Instead it is recommended to store intermediate
values into separate variables:

.. code:: python

    pizza = menu.get_item_by_name('Original Cheese & Tomato')
    api.add_item_to_basket(item=pizza, vairant=VARIANT.MEDIUM)

Full Usage Example
~~~~~~~~~~~~~~~~~~

Having instantiated an API ``Client`` a ``Store`` is needed from which to
retrieve the full list of available items. This can be obtained through
``get_nearest_store``:

.. code:: python

    from dominos import Client, FULFILMENT_METHOD, VARIANT

    api = Client(session)
    store = api.get_nearest_store('AB12 000')

The nearest store will be returned if and only if one can be found for the
given postcode. It is also possible to pass a more generic search term to
``get_nearest_store``, i.e. Cardiff, that will return only stores from which
one may collect. In this instance ``get_nearest_store`` will return ``None``.

If instead it is more appropriate to return a list of stores use ``get_stores``
which also takes a generic search term and is indexed numerically.

At this point the delivery system should be initialised for the fulfilment
method to be processed. This determines if the order will be for collection or
delivery.

.. code:: python

    api.set_delivery_system(store, 'AB12 000', fulfilment_method=FULFILMENT_METHOD.COLLECTION)

In addition to ``COLLECTION`` this method will also accept ``DELIVERY``
indicating the order should be delivered. The default value for this method is
for delivery and may be omitted.

Now that a ``Store`` object has been obtained through either of the above
methods, its menu may be retrieved with ``get_menu``, taking the store as an
argument.

.. code:: python

    menu = api.get_menu(store)

This will return a ``Menu`` object that can be search by item name or
alternatively indexed by item ID. The menu item name must be spelled correctly
but is not cases-sensitive. If the item is found in the menu then an ``Item``
object will be returned which may be added to the basket:

.. code:: python

    pizza = menu.get_product_by_name('Original Cheese & Tomato')
    api.add_item_to_basket(pizza, variant=VARIANT.LARGE)

There are four available variants: ``PERSONAL``, ``SMALL``, ``MEDIUM`` and
``LARGE``. Note that the variant is ignored if adding a side since it must
always be ``PERSONAL``.

By defaut ``add_item_to_basket`` will add only 1 item to the basket at a time
but this may be changed by using a dictionary of ``options``.

.. code:: python

    options = {
        'quantity': 2,
    }
    api.add_item_to_basket(pizza, variant=VARIANT.LARGE, options=options)
    
It is also possible to add extra toppings. In it's current state, the library
offers two ways to add ingredients. You can add by ingredient IDs or names.
To add ingredients by ID, use the ``add_ingredients`` function.

.. code:: python

    pizza.add_ingredients(124, 8, 8)

Note that having the same ID twice will give 'Extra' of the topping.
To remove any toppings, simple pass use the ``remove_ingredient`` function
the same way.

To search for toppings by name, you need an ``IngredientList``. This can be
retrieved as follows:

.. code:: python

    ingredients = api.get_available_ingredients(pizza, VARIANT.MEDIUM, store)
    
To search for an ID by the ingredient's name, use ``get_by_name``.

.. code:: python

    beef = ingredients.get_by_name("Ground Beef")
    
To add any number of ingredients by name, you can use a function from
``IngredientList`` called ``add_to_pizza``.

.. code:: python

    ingredients.add_to_pizza(cheese_tomato, "Ground Beef", "Domino's Stuffed Crust", "Burger Sauce")

None of the ``IngredientList`` functions are case sensitive.

At this time, the Dominos library does not support order placement, although it
should be entirely possible to accept orders that are marked for cash upon
delivery (not all stores allow for this). For now the basket information can be
printed:

.. code:: python

    basket = api.get_basket()
    print(basket.items)

License
-------

This project is licensed under the `MIT License <LICENSE.txt>`_.

.. |build| image:: https://travis-ci.com/tomasbasham/dominos.svg?branch=master
    :target: https://travis-ci.com/tomasbasham/dominos

.. |maintainability| image:: https://api.codeclimate.com/v1/badges/77198135c362816e5d78/maintainability
    :target: https://codeclimate.com/github/tomasbasham/dominos/maintainability
    :alt: Maintainability
