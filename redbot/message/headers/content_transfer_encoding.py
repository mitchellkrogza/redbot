#!/usr/bin/env python




import redbot.speak as rs
from redbot.message import headers as rh
from redbot.message import http_syntax as syntax


def parse(subject, value, red):
    red.exchange_state.add_note(subject, rs.CONTENT_TRANSFER_ENCODING)
    return value
    
def join(subject, values, red):
    return values