#!/usr/bin/python
"""Base Class for AJA Rest Clients
Use this class as a base for individual rest clients.
Copyright (C) 2012 AJA Video Systems, Inc.
"""

__author__ = "Support <support@aja.com>"
__version__ = "rc1"
__date__ = "Tue Mar 13 14:17:51 PDT 2012"
__copyright__ = "Copyright (C) 2009 AJA Video Systems, Inc."
__license__ = "Proprietary"

import sys
import threading
import urllib
import json
import re # "now you have two problems" -- jwz

class UnsupportedFirmwareVersionError(Exception):
    """ Raised if the target unit is running unsupported firmware. """
    pass

class BaseClient:
    __author__ = "Support <support@aja.com>"
    __version__ = "$Revision: 26 $"
    __date__ = "$Date: 2012-04-05 12:46:58 -0700 (Thu, 05 Apr 2012) $"
    __copyright__ = "Copyright (C) 2009 AJA Video Systems, Inc."
    __license__ = "Proprietary"
    __doc__ = """
This class understands the kipro REST api.
Quickstart:

$ python
>>> from aja.embedded.rest.kipro import *
>>> client = Client('http://YourKiPro')
>>> client.getFirmwareVersion()
'4.0.0.9'
>>> client.record()
>>> client.play()
>>> client.getWriteableParameters()
"""
    __success = 200

    def __init__(self, url, supportedFirmwareVersion, cacheRawParameters=True):
        self.url = url
        self.firmwareVersion = self.__getFirmwareVersion()
        if self.firmwareVersion < supportedFirmwareVersion:
            raise UnsupportedFirmwareVersionError(self.firmwareVersion + " < " + supportedFirmwareVersion)
        self.rawParametersCache = None
        if cacheRawParameters:
            self.getRawParameters()

    def setParameter(self, param, value):
        """ Set a single parameter value. """
        result = (None, "")
        f = None
        params = urllib.urlencode({'paramName':param, 'newValue' : value})
        try:
            f = urllib.urlopen(self.url + '/config', params)
            result = (f.getcode(), f.read())
            f.close()
        except:
            if f is not None:
                f.close()
            raise

        return result

    def getRawParameter(self, param_id):
        """ Returns (http error code, a json string containing all the information about the param including its current value) """
        result = (None, "")
        f = None
        try:
            f = urllib.urlopen(self.url + '/options?' + param_id)
            result = (f.getcode(), f.read())
            f.close()
        except:
            if f is not None:
                f.close()
            raise

        return result

    def getParameter(self, param_id):
        """ Returns (the http error code, the value of the param_id or an empty string if none or not found). """
        (code, response) = self.getRawParameter(param_id)
        result = (code, "")
        if code == self.__success:
            result = (code, (self.getSelected(response))['text'])
        return result

    def cleanResponse(self, response):
        """
        This deals with some historical peculiarities in Ki-Pro JSON formatting.
        """
        p = re.compile('([a-zA-Z_]+):')
        joined = "".join(response.splitlines())
        stripped = joined.strip(';')
        cleaned = p.sub(r'"\1":', stripped)
        return cleaned

    def asPython(self, response):
        """
        Convert a Ki-Pro response into a python object
        (usually an array of dictionaries depending on the json).
        """
        result = None
        try:
            result = json.loads(response)
        except:
            result = json.loads(self.cleanResponse(response))
        return result

    def getSelected(self, response):
        """
        The JSON returned is a list of all possible values for enum parameters with 
        the current value marked as selected. Integer and string parameters
        are returned in the same way with just one entry in the list.
        Return the selected value entry in the list.
        """
        result = None
        options = self.asPython(response)
        for option in options:
            if "selected" in option:
                if option["selected"] == "true":
                    result = option
                    break
        return result

    def translateVersionBits(self, versionBits):
        """
        The version is reported as a 32 bit integer.
        Returns a human readable version number decode this into four dotted octets.
        """
        version = "Error translating version bits"
        v = int(versionBits)
        version = "%d.%d.%d.%d" % ((v & 0xFF000000) >> 24, (v & 0x00FF0000) >> 16, (v & 0x0000FF00) >> 8, v & 0x000000FF)
        return version

    def waitForConfigEvents(self, connectionid=None):
        """
        This is primarily used to get timecode.
        """
        events_stream = urllib.urlopen(self.url + "/json?action=wait_for_config_events&configid=0&connectionid=%s" % connectionid)
        if (events_stream.getcode() == self.__success) :
            events_json = events_stream.read()
            events = json.loads( events_json )
            return events
        return None

    def connect(self):
        """
        This is only used for listening for event streams (primarily timecode).
        """
        result = None
        connect_stream = urllib.urlopen(self.url + "/json?action=connect&configid=0")
        if (connect_stream.getcode() == self.__success) :
            connect_json = connect_stream.read()
            result = json.loads( connect_json )
        return result['connectionid']

    def __getFirmwareVersion(self):
        """
        Internal (private) call for getting current firmware version.
        Only used by  __init__.
        """
        version = ""
        (httpcode, response) = self.getParameter("eParamID_SWVersion")
        if httpcode == self.__success:
            version = self.translateVersionBits(response)
        return version

    def getFirmwareVersion(self):
        """ Convenience method for getting the current firmware version. """
        return self.firmwareVersion

    def getRawParameters(self, cacheRawParameters=True):
        """
        Get everything the Ki-Pro knows about all parameters.
        This is list will be cached unless cacheRawParameters is set to false ("not recommended") so treat this
        as a stale list of available parameters and valid settings. Things that won't change at runtime.
        See getParameter() for current state of individual parameters.
        """
        rawParams = []
        if not self.rawParametersCache is None:
            rawParams = self.rawParametersCache
        else:
            response = []
            f = None
            try:
                f = urllib.urlopen(self.url + '/descriptors?paramid=*')
                response = (f.getcode(), f.read())
                f.close()
            except:
                if f is not None:
                    f.close()
                raise

            if response[0] == self.__success:
                try:
                    rawParams = self.asPython(response[1])
                    self.rawParametersCache = rawParams
                except:
                    print "Could not parse param list!"
                    raise
        return rawParams

    def getReadableParameters(self):
        """
        Get all parameters and their descriptions.
        This is list may be cached and so should be treated as stale.
        See getParameter() for current state
        """
        params = []
        rawParams = self.getRawParameters()
        filteredParams = []
        for param in rawParams:
            param_id = param['param_id']
            description = "description missing"
            attributes = param['string_attributes']
            for attribute in attributes:
                if 'name' in attribute and attribute['name'] == 'description':
                    description = attribute['value']
                    break
            params.append({param_id: description})
        return params

    def getWriteableParameters(self):
        """
        Returns a list of dictionaries containing all of the params which are available for writing.
        The key value is the param_id used for requests and the value is the description if any.
        This is list may be cached and so should be treated as stale.
        See getParameter() for current state
        """
        params = []
        rawParams = self.getRawParameters()

        filteredParams = []
        for param in rawParams:
            if not 'readonly' in param:
                filteredParams.append(param)

        for param in filteredParams:
            param_id = param['param_id']
            description = "description missing"
            attributes = param['string_attributes']
            for attribute in attributes:
                if 'name' in attribute and attribute['name'] == 'description':
                    description = attribute['value']
                    break
            params.append({param_id: description})
        return params

    def getValidSettingsForParameter(self, param_id):
        """
        Returns a list of
        """
        settings = []
        (code, response) = self.getRawParameter(param_id)
        if code == self.__success:
            stuff = self.asPython(response)
            for thing in stuff:
                settings.append((thing['value'],thing['text']))
        return settings

    def getSystemName(self):
        """ Returns the human readable-system name. """
        (code, response) = self.getParameter('eParamID_SysName')
        if code == self.__success:
            return response
