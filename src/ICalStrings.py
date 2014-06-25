# -*- coding:utf-8 -*-
"""Part of iCalendar (RFC5545, RFC2445) parser/validator/generator/events enumerator :  Parse, Generate and enumerate events (support of RRULE, EXRULE, RDATE, EXDATE)

About
-----

This module is part of iCalendar parser for iCalendar file (ical or ics) defined by rfc5545
(http://tools.ietf.org/html/rfc5545), which obsoleted rfc2445
(http://www.ietf.org/rfc/rfc2445.txt), which had previously replaced vcal 1.0
(http://www.imc.org/pdi/vcal-10.txt).

The iCalendar file, once parsed, will be available as a typed structure.
Events dates can be computed (including rrule, rdate exrule and exdates).

iCalendar module and dateutils both provide some of the functionalities of this module but
do not provide it in an integrated way.

History
-------
Modified on Oct 31, 2013
@author: robdobsn

Created on Aug 4, 2011

@author: oberron
@change: to 0.4 - passes all unit test in ical_test v0.1
@change: 0.4 to 0.5 adds EXDATE support
@change: 0.5 to 0.6 adds support for no DTEND and DTEND computation from DURATION or DTSTART
@version: 0.6.x
"""

RFC5545_SCM = {
               "3": "No iCalendar loaded",
               "3.1_1":"§3.1 mandates that content lines are delimited by a line break, which is a CRLF sequence",
               "3.1_2":"§3.1 mandates that all lines follow: 'contentline   = name *(\";\" param ) \":\" value CRLF'",
               "3.1_3":"§3.1 mandates line lengths to be less than 75 octets",
               "3.1_4":"§3.1 mandates line lengths to be less than 75 octets - current line too long and ignored",
               "3.1_5":"§3.1 mandates allowable characters",
               "3.1.1_1":"§3.1.1_1 COMMA ',' character as list Separators",
               "3.3.5_1":"§3.3.5 that DATE-TIME follows ISO8601-2004 which makes dates prior to 1875/may/20 bounded to prior agreement between sender and receiver",
               "3.3.6_1": "§3.3.6 that DURATION field doesn't support the \"Y\" and \"M\" designators from ISO8601",
               "3.4_1":"§3.4 : The first line and last line of the iCalendar object MUST contain a pair of iCalendar object delimiter strings.",
               "3.6_1":"§3.6 :PRODID property of iCalendar MUST be present",
               "3.6_2":"§3.6 :VERSION property of iCalendar MUST be present",
               "3.6_3":"§3.6 :at least on object of iCalendar MUST be present",
               "3.6.1_0":"§3.6.1 says DTSTART is optional, nonetheless a value should be computable, not enough information is provided to do so",
               "3.6.1_1":"§3.6.1 specifies that \'The \"VEVENT\" calendar component cannot be nested within another calendar component.",
               "3.6.1_2":"§3.6.1 specifies DTSTAMP, UID, DTSTART, ... MUST NOT occur more than once",
               "3.6.1_3":"§3.6.1 UID is REQUIRED but cannot occur more than once",
               "3.6.1_4":"§3.6.1 Either 'dtend' or 'duration' MAY appear in a 'eventprop', but 'dtend' and 'duration' MUST NOT occur in the same 'eventprop'.",
               "3.8.2.2_1":"§3.8.2.2 on DTEND says 'its value MUST be later in time than the value of the \"DTSTART\" property.'",
               "3.8.2.4_1":"§3.8.2.4 mandates DTSTART when RRULE is set",
               '3.8.2.4_2':"§3.8.2.4 mandates DTSTART when METHOD is not set",
               "3.8.4.7_1": "§3.8.4.7 \"UID\" itself MUST be a globally unique identifier",
               "6_1":"Applications MUST generate iCalendar streams in the UTF-8 charset and MUST accept an iCalendar stream in the UTF-8 or US-ASCII charset.",
               "8.3.2_1": "§8.3.2 speficies valid properties"
               }

RFC5545_Components = {"VCALENDAR","VEVENT","VTODO","VJOURNAL","VFREEBUSY","VTIMEZONE",
                      "VALARM","STANDARD","DAYLIGHT"
                      }
RFC5545_Properties = {'CALSCALE':"TEXT", #3.7.1.  Calendar Scale
                        'METHOD':"TEXT",
                        'PRODID':"TEXT",
                        'VERSION':"TEXT", #3.7.4.  Version
                        'ATTACH':"URI", #3.8.1.1.  Attachment
                        'CATEGORIES':"TEXT", #3.8.1.2.  Categories
                        'CLASS':"TEXT", #3.8.1.3.  Classification
                        'COMMENT':"TEXT", #3.8.1.4.  Comment
                        'DESCRIPTION':"TEXT", #3.8.1.5.  Description
                        'GEO':"FLOAT", #3.8.1.6.  Geographic Position
                        'LOCATION':"TEXT", #3.8.1.7.  Location
                        'PERCENT-COMPLETE':"INTEGER",
                        'PRIORITY':"INTEGER",
                        'RESOURCES':"TEXT",
                        'STATUS':"TEXT",
                        'SUMMARY':"TEXT",
                        'COMPLETED':"DATE-TIME",
                        'DTEND':"DATE-TIME",
                        'DUE':"DATE-TIME",
                        'DTSTART':"DATE-TIME",
                        'DURATION':"DURATION",
                        'FREEBUSY':"PERIOD",
                        'TRANSP':"TEXT",
                        'TZID':"TEXT",
                        'TZNAME':"TEXT",
                        'TZOFFSETFROM':"UTC-OFFSET",
                        'TZOFFSETTO':"TZOFFSETTO",
                        'TZURL':"URI",
                        'ATTENDEE':"CAL-ADDRESS", #FIXME: this seems not very clear #3.8.4.1.  Attendee
                        'CONTACT':"TEXT",
                        'ORGANIZER':"CAL-ADDRESS",
                        'RECURRENCE-ID':"DATE-TIME",
                        'RELATED-TO':"TEXT",
                        'URL':"URI",
                        'UID':"TEXT",
                        'EXDATE':"DATE-TIME-LIST",
                        'EXRULE':"RECUR",
                        'RDATE':"DATE-TIME-LIST",
                        'RRULE':"RECUR",
                        'ACTION':"TEXT",
                        'REPEAT':"INTEGER",
                        'TRIGGER':"DURATION",
                        'CREATED':"DATE-TIME",
                        'DTSTAMP':"DATE-TIME",
                        'LAST-MODIFIED':"DATE-TIME",
                        'SEQUENCE':"INTEGER",
                        'REQUEST-STATUS':"TEXT",
                        "BEGIN":"TEXT",
                        "END":"TEXT"
            }

ESCAPEDCHAR = {"\\\\" :"\\", "\\;":";",
                "\\,":"," , "\\N":"\n" , "\\n":"\n"}
