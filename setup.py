from setuptools import setup

import dominos

def readme():
    '''Read README file'''
    with open('README.rst') as infile:
        return infile.read()

setup(
    name='dominos',
    version=dominos.__version__,
    description='Dominos Pizza UK API wrapper',
    long_description=readme().strip(),
    author='Tomas Basham',
    author_email='me@tomasbasham.co.uk',
    url='https://github.com/tomasbasham/dominos',
    license='MIT',
    packages=['dominos'],
    install_requires=[
        'ratelimit',
        'requests'
    ],
    keywords=[
        'dominos',
        'pizza',
        'api'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Topic :: Software Development'
    ],
    include_package_data=True,
    zip_safe=False
)
