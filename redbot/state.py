#!/usr/bin/env python

"""
The Resource Expert Droid state container.

Holds all test-related state that's useful for analysis; ephemeral
objects (e.g., the HTTP client machinery) are kept elsewhere.
"""

import types

import redbot.speak as rs

class RedState(object):
    "All of the state we want to record about a test."

    def __init__(self):
        self.exchanges = {}
        self.transfer_in = 0
        self.transfer_out = 0
        self.linked = []    # list of linked RedStates (if descend=True)
        self.links = {}          # {type: set(link...)}
        self.partial_support = None
        self.inm_support = None
        self.ims_support = None
        self.gzip_support = None
        self.gzip_savings = 0

    def __repr__(self):
        status = [self.__class__.__module__ + "." + self.__class__.__name__]
        return "<%s at %#x>" % (", ".join(status), id(self))

    def add_exchange(self, exchange_name, request, response):
        "Add an exchange."
        self.exchanges[exchange_name] = ExchangeState(exchange_name, request, response)
        exchange_state = self.exchanges[exchange_name]
        request.set_exchange_state(exchange_state)
        response.set_exchange_state(exchange_state)
        return exchange_state
        
    def get_exchange(self, exchange_name):
        "Get an exchange by its name."
        return self.exchanges.get(exchange_name, self.exchanges[None])


class ExchangeState(object):
    "Holder for the state specific to a message exchange."
    
    def __init__(self, exchange_name=None, request=None, response=None):
        self.exchange_name = exchange_name
        self.notes = []
        self.request = request
        self.response = response
        self._context = {}

    def set_context(self, **kw):
        "Set the note variable context."
        self._context = kw
        
    def add_note(self, subject, note, subreq=None, **kw):
        "Set a note."
        kw.update(self._context)
        kw['response'] = rs.response.get(
            self.exchange_name, rs.response['this']
        )
        kw['status'] = self.response.status_code
        self.notes.append(note(subject, subreq, kw))
