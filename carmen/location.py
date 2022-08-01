"""Provides classes and functions for representing and manipulating
locations."""


import itertools
import json
import math

class Location(object):
    """Contains information about a location and how it was identified.
    """

    def __init__(self, **kwargs):
        self.latitude = 0.0
        """The latitude of this location's geographic center."""
        self.longitude = 0.0
        """The longitude of this location's geographic center."""

        # These should all be Unicode strings, not byte strings.
        self.country = None
        self.state = None
        self.county = None
        self.city = None
        """Basic location information.  A value of ``None`` for a
        particular field indicates that it does not apply for that
        specific location."""

        self.aliases = []
        """An iterable containing alternative names for this location."""

        self.resolution_method = None
        """The method used to resolve this location's data from the
        tweet that originally contained it."""

        self.known = False
        """True if this location appears in the database, False
        otherwise."""
        self.id = -1
        """For known locations, the database ID.  For other locations, a
        unique ID is arbitrarily assigned for each run."""
        self.parent_id = -1
        
        self.twitter_url = None
        """The Twitter URL corresponding to this Place."""
        self.twitter_id = None
        """The Twitter ID of this Place."""

        # Support for Python3
        try:
            iterator = kwargs.iteritems()
        except:
            iterator = kwargs.items()

        # We're all adults, right?
        for k, v in iterator:
            if hasattr(self, k):
                setattr(self, k, v)
        # print (self.id)
        if isinstance(self.id, str) and len(self.id) != 0:      
            self.id = int(self.id)
        if isinstance(self.parent_id, str) and  len(self.parent_id)!= 0:
            self.parent_id = int(self.parent_id)
        if isinstance(self.latitude, str) and  len(self.latitude)!= 0:
            self.latitude = float(self.latitude)
        if isinstance(self.longitude, str) and  len(self.longitude)!= 0:
            self.longitude = float(self.longitude)

    def __repr__(self):
        attrs = []
        for k in ('country', 'state', 'county', 'city',
                  'known', 'id'):
            attr = getattr(self, k)
            if attr:
                attrs.append('{}={}'.format(k, repr(attr)))
        return 'Location({})'.format(', '.join(attrs))

    def __unicode__(self):
        try:
            return u', '.join(itertools.ifilter(None, reversed(self.name())))
        except:
            return ', '.join(filter(None, reversed(self.name())))

    def canonical(self):
        """Return a tuple containing a canonicalized version of this
        location's country, state, county, and city names."""
        try:
            return tuple(map(lambda x: x.lower(), self.name()))
        except:
            # print ("look at me")
            # print (self.name())
            return tuple([x.lower( ) if not(isinstance(x, float) and math.isnan(x)) else None for x in self.name()])

    def name(self):
        """Return a tuple containing this location's country, state,
        county, and city names."""
        try:
            return tuple(
                getattr(self, x) if getattr(self, x) else u''
                for x in ('country', 'state', 'county', 'city'))
        except:
            return tuple(
                getattr(self, x) if getattr(self, x) else ''
                for x in ('country', 'state', 'county', 'city'))

    def parent(self):
        """Return a location representing the administrative unit above
        the one represented by this location."""
        if self.city:
            return Location(
                country=self.country, state=self.state, county=self.county)
        if self.county:
            return Location(country=self.country, state=self.state)
        if self.state:
            return Location(country=self.country)
        return Location()


EARTH = Location()
"""A location representing Earth.  This location is the ancestor of all
other locations."""


class LocationEncoder(json.JSONEncoder):
    """JSON encoder supporting `Location` objects."""
    encoding = 'utf-8'
    def default(self, obj):
        if isinstance(obj, Location):
            to_encode = {}
            for k in ('country', 'state', 'county', 'city', 'id',
                      'latitude', 'longitude', 'resolution_method'):
                      # 'author.location','geo.coordinates.coordinates', 'geo.coordinates.type', 'geo.country', 'geo.country_code', 'geo.full_name', 'geo.geo.bbox', 'geo.geo.type', 'geo.id', 'geo.name', 'geo.place_id', 'geo.place_type'):
                # We don't use hasattr here because we're checking for
                # None values; the attributes themselves always exist.
                v = getattr(obj, k)
                if v:
                    import sys
                    if sys.version_info[0] < 3:
                        if isinstance(v, unicode):
                            v = v.encode(self.encoding)
                    to_encode[k] = v
            return to_encode
        return json.JSONEncoder.default(self, obj)
