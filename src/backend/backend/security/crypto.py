#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Asumi Kamikaze Inc.
# Licensed under the MIT License.
# Author: Alejandro M. Bernardis
# Email: alejandro (dot) bernardis (at) asumikamikaze (dot) com
# Created: 24/Sep/2014 3:57 AM

from base64 import encodestring, decodestring
from Crypto import Random
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

__all__ = (
    'generate_rsa',
    'encrypt',
    'decrypt',
    'sign',
    'verify_sign'
)


def sanitize_message(func):
    def decorator(message, *args, **kwargs):
        if not isinstance(message, basestring):
            raise TypeError('Invalid message, must be a basestring')
        if isinstance(message, unicode):
            message = message.encode()
        return func(message, *args, **kwargs)
    return decorator


def generate_rsa(bits=2048, passphrase=None, pkcs=1):
    """
    :return: tuple with private an public keys base64 encode string
    """
    rsa = RSA.generate(bits, Random.new().read)
    private = rsa.exportKey('PEM', passphrase, pkcs)
    public = rsa.publickey().exportKey('PEM', passphrase, pkcs)
    return encodestring(private), encodestring(public)


@sanitize_message
def encrypt(message, public_key, passphrase=None):
    """
    :return: base64 encode string
    """
    public_key = StringIO(decodestring(public_key)).read()
    public_key = RSA.importKey(public_key, passphrase)
    public_key = PKCS1_OAEP.new(public_key)
    return encodestring(public_key.encrypt(message))


@sanitize_message
def decrypt(message, private_key, passphrase=None):
    """
    :return: base64 decode string
    """
    private_key = StringIO(decodestring(private_key)).read()
    private_key = RSA.importKey(private_key, passphrase)
    private_key = PKCS1_OAEP.new(private_key)
    return private_key.decrypt(decodestring(message))


@sanitize_message
def sign(message, private_key, passphrase=None):
    """
    :return: base64 encode string
    """
    private_key = decodestring(StringIO(private_key).read())
    private_key = RSA.importKey(private_key, passphrase)
    return encodestring(PKCS1_v1_5.new(private_key).sign(SHA256.new(message)))


@sanitize_message
def verify_sign(message, signature, public_key, passphrase=None):
    """
    :return: boolean
    """
    message = SHA256.new(message)
    signature = decodestring(signature)
    public_key = decodestring(StringIO(public_key).read())
    public_key = RSA.importKey(public_key, passphrase)
    public_key = PKCS1_v1_5.new(public_key)
    try:
        return public_key.verify(message, signature) > 0
    except:
        return False
