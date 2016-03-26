#!/usr/bin/env python

"""
Subrequest for ETag validation checks.
"""


from redbot.resource.active_check.base import SubRequest
import redbot.speak as rs

class ETagValidate(SubRequest):
    "If an ETag is present, see if it will validate."

    def modify_req_hdrs(self, req_hdrs):
        if self.base.response.parsed_headers.has_key('etag'):
            weak, etag = self.base.response.parsed_headers['etag']
            if weak:
                weak_str = u"W/"
                # #65: note on weak etag
            else:
                weak_str = u""
            etag_str = u'%s"%s"' % (weak_str, etag)
            req_hdrs += [
                (u'If-None-Match', etag_str),
            ]
        return req_hdrs
            
    def preflight(self):
        if self.base.response.parsed_headers.has_key('etag'):
            return True
        else:
            self.base.test_state.inm_support = False
            return False

    def done(self):
        if not self.response.complete:
            self.add_note('', rs.ETAG_SUBREQ_PROBLEM,
                problem=self.response.http_error.desc
            )
            return
            
        if self.response.status_code == '304':
            self.base.test_state.inm_support = True
            self.add_note('header-etag', rs.INM_304)
            self.check_missing_hdrs([
                    'cache-control', 'content-location', 'etag', 
                    'expires', 'vary'
                ], rs.MISSING_HDRS_304, 'If-None-Match'
            )
        elif self.response.status_code \
          == self.base.response.status_code:
            if self.response.payload_md5 \
              == self.base.response.payload_md5:
                self.base.test_state.inm_support = False
                self.add_note('header-etag', rs.INM_FULL)
            else: # bodies are different
                if self.base.response.parsed_headers['etag'] == \
                  self.response.parsed_headers.get('etag', 1):
                    if self.base.response.parsed_headers['etag'][0]: # weak
                        self.add_note('header-etag', rs.INM_DUP_ETAG_WEAK)
                    else: # strong
                        self.add_note('header-etag',
                            rs.INM_DUP_ETAG_STRONG,
                            etag=self.base.response.parsed_headers['etag']
                        )
                else:
                    self.add_note('header-etag', rs.INM_UNKNOWN)
        else:
            self.add_note('header-etag', 
                rs.INM_STATUS, 
                inm_status = self.response.status_code,
                enc_inm_status = self.response.status_code \
                  or '(unknown)'
            )
        # TODO: check entity headers