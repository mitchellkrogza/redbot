#!/usr/bin/env python


import redbot.speak as rs
from redbot.message import headers as rh
from redbot.message import http_syntax as syntax

description = u"""\
The `Age` header conveys the sender's estimate of the amount of time since the response (or its
validation) was generated at the origin server."""

reference = u"%s#header.age" % rs.rfc7234

@rh.GenericHeaderSyntax
@rh.ResponseHeader
def parse(subject, value, red):
    try:
        age = int(value)
    except ValueError:
        red.exchange_state.add_note(subject, rs.AGE_NOT_INT)
        return None
    if age < 0:
        red.exchange_state.add_note(subject, rs.AGE_NEGATIVE)
        return None
    return age

@rh.SingleFieldValue
def join(subject, values, red):
    return values[-1]
    
    
class AgeTest(rh.HeaderTest):
    name = 'Age'
    inputs = ['10']
    expected_out = 10
    expected_err = []

class MultipleAgeTest(rh.HeaderTest):
    name = 'Age'
    inputs = ['20', '10']
    expected_out = 10
    expected_err = [rs.SINGLE_HEADER_REPEAT]

class CharAgeTest(rh.HeaderTest):
    name = 'Age'
    inputs = ['foo']
    expected_out = None
    expected_err = [rs.AGE_NOT_INT]

class NegAgeTest(rh.HeaderTest):
    name = "Age"
    inputs = ["-20"]
    expected_out = None
    expected_err = [rs.AGE_NEGATIVE]
