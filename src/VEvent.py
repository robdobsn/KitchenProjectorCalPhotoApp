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

import datetime
from ICalStrings import RFC5545_SCM, ESCAPEDCHAR,RFC5545_Properties

CRLF= "\r\n"

class VEvent:

    def __init__(self, parent):
        self.parent = parent

    """ Parses a vevent (object from vcalendar as defined by the iCalendar standard (RFC5545)
    """
#    vevent_load = { "uid": self.string_load}
    def _icalindex_to_pythonindex(self,indexes):
        ret_val = []
        for index in indexes:
            index = int(index)
            if index > 0:
                #ical sees the first as a 1 whereas python sees the 0 as the first index for positives
                index = index -0
            ret_val.append(index)
        return ret_val

    def line_wrap(self,newline):
        if len(newline)<75:
            ret_val = newline
        else:
            #FIXME: about the utf-8 and mid-octet splitting
            NnewLine = int(len(newline)/73.0)
            ret_val = newline[0:74]+CRLF
            for i in range(1,NnewLine):
                ret_val+=" "+newline[i*73+1:(i+1)*73+1]+CRLF
            ret_val+=" "+newline[(NnewLine)*73+1:]

        return ret_val

    def string_write(self,string):
        for esc in ESCAPEDCHAR:
            string = string.replace(ESCAPEDCHAR[esc],esc)
        return string

    def string_load(self,propval,param="",LineNumber = 0):
        #TODO add here escaped characters
        ret_val = propval
        for esc in ESCAPEDCHAR:
            ret_val= ret_val.replace(esc,ESCAPEDCHAR[esc])

        return ret_val

    def date_write(self,date2w,param=""):
        """ takes date or datetime and returns icalendar date or datetime"""
        dt = datetime.datetime(year=2013,month=1,day=26)

        if type(dt)==type(date2w):
            datestring = self.string_write(date2w.strftime("%Y%m%dT%H%M%S").upper())
        else :
            datestring = self.string_write(date2w.strftime("%Y%m%d").upper())
        return datestring

    def date_load(self,propval,param="",LineNumber = 0):
        """ loads the date-time or date value + optional TZID into UTC date-time or date"""

        #DTSTART, DTEND, DTSTAMP, UNTIL,
        #self.mycal4log = ics()
        #TODO: handle params properly http://www.kanzaki.com/docs/ical/dtstart.html

        retdate=datetime.datetime(1970,1,1) #FIXME: this is temporary
        yeardate = int(propval[0:4])

        if yeardate<1970:
            self.parent.Validator("3.3.5_1", line_count = LineNumber,line = propval,alttxt="1970 however is often a computer epoch limit prior validation should be undertaken before keeping such a past date", show = True)
        elif yeardate<1875:
            self.parent.Validator("3.3.5_1", line_count = LineNumber,line = propval,show= True)
        elif yeardate<1582: #retdate<datetime.datetime(year=1582,month=10,day=15):
            self.parent.Validator("3.3.5_1", line_count = LineNumber,line = propval,alttext = "dates prior to 1582/oct/15 might be in julian calendar, prior validation should be undertaken", show = True,prio=1)
        else:
            if len(propval)>8:
                retdate = datetime.datetime.strptime(propval[:15],"%Y%m%dT%H%M%S")
            else:
                retdate = datetime.datetime.strptime(propval,"%Y%m%d")

        return retdate

    def duration_write(self,duration):
        return duration

    def duration_load(self,duration,param="",conformance=False,LineNumber = 0):
        self.mycal4log = ics()
        #FIXME: check that datetime.timdelta supports timeoffsets
        """
        FIXME: get below addressed and fixed when adding datetime
        The duration of a week or a day depends on its position in the
      calendar.  In the case of discontinuities in the time scale, such
      as the change from standard time to daylight time and back, the
      computation of the exact duration requires the subtraction or
      addition of the change of duration of the discontinuity.  Leap
      seconds MUST NOT be considered when computing an exact duration.
      When computing an exact duration, the greatest order time
      components MUST be added first, that is, the number of days MUST
      be added first, followed by the number of hours, number of
      minutes, and number of seconds.
        """
#        print "line 79",duration
        if duration[0]=="P":
            duration = duration[1:]
        tdelta = datetime.timedelta()
        years =0
        months =0
        sign =1
        if duration[0:1]=="-":
            duration = duration[1:]
            sign = -1
#            print "sign",sign
        if duration.find("T")>=0:
            [date,time]=duration.split("T")
#            print "line 89, date time", date,time
#            date = date[1:]
        else:
            [date , time] = [duration,""]
        pos = date.find("W")
        if pos>0:
            tdelta += datetime.timedelta(weeks= sign*int(date[:pos]))
        pos = date.find("Y")
        if (pos)>0:
            years = sign*int(date[:pos])
            date = date[pos+1:]
            if conformance:
                self.mycal4log.Validator("3.3.6_1",level=1) #raise Exception("VEVENT VALIDATOR","encountered a Y parameter in a DURATION field which is prohibited by RFC5545")
            else:
                self.mycal4log.Validator("3.3.6_1",level=0)
        pos = date.find("M")
        if pos>0:
            months = sign*int(date[:pos])
            date = date[pos+1:]
#            if conformance: raise Exception("VEVENT VALIDATOR","encountered a M parameter in a DURATION field which is prohibited by RFC5545")
            if conformance:
                self.mycal4log.Validator("3.3.6_1",level=1)
            else:
                self.mycal4log.Validator("3.3.6_1",level=0)

        pos = date.find("D")
        if (pos)>0:
            tdelta += datetime.timedelta(days = sign*int(date[:pos]))
        pos = time.find("H")
        if (pos)>0:
            tdelta += datetime.timedelta(hours = sign*int(time[:pos]))
            time = time[pos+1:]
        pos = time.find("M")
        if (pos)>0:
            tdelta += datetime.timedelta(minutes = sign*int(time[:pos]))
#            print "line 129 tdelta minute",tdelta
            time = time[pos+1:]
        pos = time.find("S")
        if (pos)>0:
            tdelta += datetime.timedelta(seconds = sign*int(time[:pos]))
        return [years,months,tdelta]

    def datelist_write(self,dtlist):
        return  dtlist

    def datelist_load(self,sDatelist,param="",LineNumber = 0):
#        if sDatelist.find(",")>=0:
        sDatelist=sDatelist.split(",")
        lDatelist = []
        for value in sDatelist:
            lDatelist.append(self.date_load(value,LineNumber = LineNumber))
#        else:
#            raise Exception("ICALENDAR WARNING", RFC5545_SCM["3.1.1_1"] + "\nline information: %s - %s"%("NA",sDatelist))
        return lDatelist

    def rrule_load(self,sRrule,param="",LineNumber = 0):
        #FIXME: add logs
        rules = {}
#        self._log("rrule is:",[line])
        rrule = sRrule.split(";")
        for rule in rrule:
#            self._log("120 rule out rules is:",[rule])
            if len(rule)>0:
                #FIXME: this is to cater for line ending with ; which is probably not valid
                [param, value] = rule.split("=")
                if (param == "FREQ"):
                    rules[param] = value
                elif (param == "UNTIL"):
                    rules[param] = self.date_load(value)
                    #TODO: check if that no "COUNT" is defined
                elif (param == "COUNT"):
                    rules[param] = int(value)
                    #TODO: check if that no "UNTIL" is defined
                elif (param == "INTERVAL"):
                    #( ";" "INTERVAL" "=" 1*DIGIT )          /
                    rules[param] = int(value)
                elif (param == "BYSECOND"):
                    #( ";" "BYSECOND" "=" byseclist )        /
                    #byseclist  = seconds / ( seconds *("," seconds) )
                    #seconds    = 1DIGIT / 2DIGIT       ;0 to 59
                    byseclist = value.split(",")
                    rules[param]=[]
                    for seconds in byseclist:
                        rules[param].append(int(seconds))
                elif (param == "BYMINUTE"):
                    rules[param] = value
                elif (param == "BYHOUR"):
                    rules[param] = value
                elif (param == "BYDAY"):
                    #( ";" "BYDAY" "=" bywdaylist )          /
                    #bywdaylist = weekdaynum / ( weekdaynum *("," weekdaynum) )
                    #weekdaynum = [([plus] ordwk / minus ordwk)] weekday
                    #plus       = "+"
                    #  minus      = "-"
                    #  ordwk      = 1DIGIT / 2DIGIT       ;1 to 53
                    #  weekday    = "SU" / "MO" / "TU" / "WE" / "TH" / "FR" / "SA"
                    #;Corresponding to SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY,
                    #;FRIDAY, SATURDAY and SUNDAY days of the week.
                    #bywdaylist = split(value,",")
                    #for weekdaynum in bywdaylist:
                    rules[param] = {}
                    ldow = {}   #dictionnary with dow and list of index
                    #{'MO': [0], 'TU': [1], 'WE': [-1]} means every monday, first tuesday
                    # last wednesday, ..
                    bywdaylist = value.split(",")
                    dow = ["MO","TU","WE","TH","FR","SA","SU"]
                    for weekdaynum in bywdaylist:
                        #get the position of the DOW
                        #weekdaynum of type: MO , 1MO, 2TU or -2WE
                        for d in dow:
                            if weekdaynum.find(d) >=0:
                                pos_dow = weekdaynum.find(d)
                        #extract position of dow to split its index from it.
                        if pos_dow == 0:
                            index = 0
                        else:
                            index = int(weekdaynum[0:pos_dow])
                        ddow = weekdaynum[pos_dow:]
                        if ddow in ldow:
                            ldow[ddow].append(index)
#                                    print "238"
                        else:
#                                    print "240", ldow, ddow, index
                            ldow[ddow] = [index]
#                                print "ldow is now:",ldow
                    rules[param] = ldow
#                    self._log("175",[rules[param],param])
                elif (param == "BYMONTHDAY"):
                    # ( ";" "BYMONTHDAY" "=" bymodaylist )    /
                    # bymodaylist = monthdaynum / ( monthdaynum *("," monthdaynum) )
                    # monthdaynum = ([plus] ordmoday) / (minus ordmoday)
                    # ordmoday   = 1DIGIT / 2DIGIT       ;1 to 31
                    bymodaylist = value.split(",")
                    rules[param] = self._icalindex_to_pythonindex(bymodaylist)
                elif (param == "BYYEARDAY"):
                    byyeardaylist = value.split(",")
                    rules[param] = self._icalindex_to_pythonindex(byyeardaylist)
                elif (param == "BYWEEKNO"):
                    bywklist = value.split(",")
                    rules[param] = self._icalindex_to_pythonindex(bywklist)
                elif (param == "BYMONTH"):
                    #";" "BYMONTH" "=" bymolist )
                    #bymolist   = monthnum / ( monthnum *("," monthnum) )
                    #monthnum   = 1DIGIT / 2DIGIT       ;1 to 12
                    bymolist = value.split(",")
                    rules[param] = self._icalindex_to_pythonindex(bymolist)
                elif (param == "BYSETPOS"):
                    #( ";" "BYSETPOS" "=" bysplist )         /
                    # bysplist   = setposday / ( setposday *("," setposday) )
                    # setposday  = yeardaynum
                    bysplist = value.split(",")
                    rules[param] = self._icalindex_to_pythonindex(bysplist)
                elif (param == "WKST"):
                    rules[param] = value
                else:
                    rules[param] = value
        return rules

    def rrule_write(self,sRRULE):
        return sRRULE

    def validate_event(self,event):
#        self._log("193 validate_event", event, 0)
#        print "line 71",event
        #self.mycal4log = ics()
        addsummary = ""
        adduid = ""
        if "SUMMARY" in event:
            addsummary = " event summary:"+event["SUMMARY"]["val"]
        if "UID" not in event:
#            print (event["UID"])
            self.parent.Validator("3.6.1_3",alttxt = addsummary) #raise Exception("VEVENT VALIDATOR","mandatory property UID not set"+addsummary)
        else:
            adduid = " event UID:"+event["UID"]["val"]
#        if "DTSTART" not in event:
#            #FIXME no DTSTART is valid, but should raise a warning
#            raise Exception("VEVENT VALIDATOR","mandatory property DTSTART not set"+adduid+addsummary)
        if "DTEND" in event:
            if "DURATION" in event:
                self.parent.Validator("3.6.1_4",alttxt = adduid+addsummary)
            if event["DTSTART"]["val"] > event["DTEND"]["val"]:
                self.parent.Validator("3.8.2.2_1",level=1,alttxt=adduid+addsummary)#raise Exception("VEVENT VALIDATOR","DTSTART > DTEND"+adduid+addsummary)
