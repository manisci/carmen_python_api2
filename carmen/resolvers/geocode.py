"""Resolvers based on geocodes."""


from collections import defaultdict
import warnings

from geopy import Point
from geopy.distance import distance as geopy_distance

from ..location import EARTH
from ..resolver import AbstractResolver, register


@register('geocode')
class GeocodeResolver(AbstractResolver):
    """A resolver that locates a tweet by finding the known location
    with the shortest geographic distance from the tweet's coordinates.
    """

    cell_size = 100.0

    def __init__(self, max_distance=25):
        self.max_distance = float(max_distance)
        self.location_map = defaultdict(list)

    def _cells_for(self, latitude, longitude):
        """Return a list of cells containing the location at *latitude*
        and *longitude*."""
        latitude = latitude * self.cell_size
        longitude = longitude * self.cell_size
        shift_size = self.cell_size / 2
        for latitude_cell in (latitude - shift_size,
                              latitude, latitude + shift_size):
            for longitude_cell in (longitude - shift_size,
                                   longitude, longitude + shift_size):
                yield (int(latitude_cell / self.cell_size),
                       int(longitude_cell / self.cell_size))

    def add_location(self, location):
        if not location.latitude and location.longitude:
            return
        for cell in self._cells_for(location.latitude, location.longitude):
            self.location_map[cell].append(location)

    def resolve_tweet(self, tweet):
        # 
        # Update for APIv2: the coordinates are in the field
        #       data->geo->coordinates->coordinates
        # if they exist. The coordinates is a list with size 2.
        # 
        # The Twitter API allows tweet['coordinates'] to both be absent
        # and None, such that the key exists but has a None value.
        # "tweet.get('coordinates', {})" would return None in the latter
        # case, with None.get() in turn causing an AttributeError. (None
        # or {}), on the other hand, is {}, and {}.get() is okay.
        data = tweet.get('data')
        geo = data.get('geo') or {}
        tweet_coordinates = (geo.get('coordinates') or {}).get('coordinates')

        # Enhancement (Jack 09/15/21): another way to get coordinates is from 
        #       includes->places->[0]->geo->bbox
        # the bbox is a list of four coordinates. 
        # Avg 0 and 2 to get 1st coord, and avg 1 & 3 to get the 2nd 
        if not tweet_coordinates:
            places = tweet.get('includes', {}).get('places', None)
            if not places:
                return None
            place = places[0]
            bbox = place.get('geo', {}).get('bbox')
            if not bbox:
                return None
            float_coords = [
                (float(bbox[0])+float(bbox[2]))/2,
                (float(bbox[1])+float(bbox[3]))/2
            ]
            tweet_coordinates = [
                float(f"{float_coords[0]:.7f}"), 
                float(f"{float_coords[1]:.7f}")
            ]
        tweet_coordinates = Point(longitude=tweet_coordinates[0],
                                  latitude=tweet_coordinates[1])
        closest_candidate = None
        closest_distance = float('inf')
        for cell in self._cells_for(tweet_coordinates.latitude,
                                    tweet_coordinates.longitude):
            for candidate in self.location_map[cell]:
                candidate_coordinates = Point(
                    candidate.latitude, candidate.longitude)
                distance = geopy_distance(
                    tweet_coordinates, candidate_coordinates).miles
                if closest_distance > distance:
                    closest_candidate = candidate
                    closest_distance = distance
        if closest_distance < self.max_distance:
            return (False, closest_candidate)
        return None
