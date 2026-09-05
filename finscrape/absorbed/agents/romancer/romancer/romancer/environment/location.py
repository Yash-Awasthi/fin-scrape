from dataclasses import dataclass
from numpy import sin, cos, arctan2, arcsin, arccos, pi, sqrt, rad2deg, deg2rad
import math

def decdegrees_to_degrees(decdegrees):
    '''Converts decimal degrees into a (degrees, minutes, seconds) tuple.'''
    # We need to remember if it was positive or negative so we can round in the correct direction
    is_positive = decdegrees >= 0
    # Then turn it into an int so it rounds toward 0
    degrees = abs(decdegrees)
    whole_degrees, minutes = divmod(degrees * 60, 60)
    whole_minutes, seconds = divmod(minutes * 60, 60)
    if is_positive:
        return whole_degrees, whole_minutes, seconds
    else:
        return -1 * whole_degrees, whole_minutes, seconds

    
def degrees_to_decdegrees(degrees, minutes, seconds):
    '''Converts degrees, minutes, seconds location into unitary decimal degrees.'''
    is_positive = degrees >= 0
    ans = abs(degrees) + (minutes / 60.0) + (seconds / 3600.0)
    if not is_positive:
        return -1 * ans
    return ans

    
# Formulas adapted from https://www.movable-type.co.uk/scripts/latlong.html

def bearing(lat1, long1, lat2, long2):
    '''Return the bearing, in radians, from lat1, long1 to lat2, long2. The bearing is from 0-2pi with 0 being N.'''
    delta_long = long2 - long1
    y = sin(delta_long) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_long)
    theta = arctan2(y, x)
    return (theta + 2 * pi) % (2 * pi) # compass bearing


@dataclass
class GeographicLocation:
    latitude: float # in radians, -pi ... pi, equator = 0
    longitude: float # in radians, -pi ... pi, Prime Meridian = 0
    bearing: float # in radians, 0 ... 2 pi, compass bearing


    def distance(self, location):
        '''Return the distnace, in kilometers, between self and location, using the haversine formula.'''
        delta_lat = location.latitude - self.latitude
        delta_long = location.longitude - self.longitude
        a = sin(delta_lat / 2)**2 + cos(self.latitude) * cos(location.latitude) * sin(delta_long / 2)**2
        c = 2 * arctan2(sqrt(a), sqrt(1 - a))
        d = c * 6371.0
        return d
    

    def bearing_to(self, location):
        '''Return the bearing, in radians, from self to location. The bearing is from 0-2pi with 0 being N.'''
        return bearing(self.latitude, self.longitude, location.latitude, location.longitude)
        

    def destination_point(self, distance):
        '''Calculate the destination point and final bearing traveling distance from location along a (shortest distance) great circle arc. Returns a new GeographicLocation object representing that point.'''
        if distance == 0.0:
            return self
        delta = distance / 6371.0 # kilometers
        lat2 = arcsin(sin(self.latitude) * cos(delta) + cos(self.latitude) * sin(delta) * cos(self.bearing))
        long2 = self.longitude + arctan2(sin(self.bearing) * sin(delta) * cos(self.latitude), cos(delta) - sin(self.latitude) * sin(lat2))
        long2 = (long2 + 3 * pi) % (2 * pi) - pi # normalize longitude to -pi ... pi
        final_bearing = (bearing(lat2, long2, self.latitude, self.longitude) + pi) % (2 * pi) # reverse bearing from endpoint to starting point
        return GeographicLocation(latitude = lat2, longitude = long2, bearing = final_bearing)


    def to_decimal_degrees(self):
        '''This method returns a (latitude, longitude, bearing) tuple with the location given in decimal degrees rather than radians.'''
        decimal_latitude = rad2deg(self.latitude)
        decimal_longitude = rad2deg(self.longitude)
        decimal_bearing = rad2deg(self.bearing)
        return decimal_latitude, decimal_longitude, decimal_bearing


    @staticmethod
    def calculate_intersection(location_1, location_2):
        if location_1.latitude == location_2.latitude and location_1.longitude == location_2.longitude:
            return GeographicLocation(location_1.latitude, location_1.longitude, 0)
        if location_1.bearing == location_2.bearing:
            return GeographicLocation(math.nan, math.nan, 0)

        lat1, lon1, bearing1 = location_1.latitude, location_1.longitude, location_1.bearing
        lat2, lon2, bearing2 = location_2.latitude, location_2.longitude, location_2.bearing

        dLat = lat2 - lat1
        dLon = lon2 - lon1

        delta12 = 2 * arcsin( sqrt( sin(dLat/2)**2 + cos(lat1) * cos(lat2) * sin(dLon/2)**2 ) )
        # print("in calculate_intersection: ", delta12)
        # print(sin(delta12), cos(lat1))
        # round the arguments to eliminate floating-point calculations resulting in out-of-domain errors
        arg1 = ( sin(lat2) - sin(lat1) * cos(delta12) ) / ( sin(delta12) * cos(lat1) )
        if arg1 < -1 or arg1 > 1:
            return GeographicLocation(math.nan, math.nan, 0)
        arg2 = ( sin(lat1) - sin(lat2) * cos(delta12) ) / ( sin(delta12) * cos(lat2) )
        if arg2 < -1 or arg2 > 1:
            return GeographicLocation(math.nan, math.nan, 0)

        thetaA = arccos( arg1 )
        thetaB = arccos( arg2 )

        if sin(lon2 - lon1) > 0:
            theta12 = thetaA
            theta21 = 2 * pi - thetaB
        else:
            theta12 = 2 * pi - thetaA
            theta21 = thetaB

        alpha1 = bearing1 - theta12
        alpha2 = theta21 - bearing2

        alpha3 = arccos( -cos(alpha1) * cos(alpha2) + sin(alpha1) * sin(alpha2) * cos(delta12) )
        delta13 = arctan2( sin(delta12) * sin(alpha1) * sin(alpha2) , cos(alpha2) + cos(alpha1) * cos(alpha3) )
        lat3 = arcsin( sin(lat1) * cos(delta13) + cos(lat1) * sin(delta13) * cos(bearing1) )
        dLon13 = arctan2( sin(bearing1) * sin(delta13) * cos(lat1) , cos(delta13) - sin(lat1) * sin(lat3) )
        lon3 = lon1 + dLon13

        return GeographicLocation(lat3, lon3, 0)

    @staticmethod
    def coords(lat, lon):
        x = cos(deg2rad(lon)) * cos(deg2rad(lat))
        y = sin(deg2rad(lon)) * cos(deg2rad(lat))
        z = sin(deg2rad(lat))
        return {'x': x, 'y': y, 'z': z}

    @staticmethod
    def vec_cross(V1, V2):
        if len(V1) != 3 or len(V2) != 3:
            raise ValueError("Wrong vector size")

        x = V1['y'] * V2['z'] - V2['y'] * V1['z']
        y = V1['z'] * V2['x'] - V2['z'] * V1['x']
        z = V1['x'] * V2['y'] - V2['x'] * V1['y']

        return {'x': x, 'y': y, 'z': z}

    @staticmethod
    def lat_intersect(lat1, lon1, lat2, lon2, LonIntercept):
        # takes two points on a great circle path (eg, path of an object)
        # calculates the arc angle along the great circle path until
        # the path intersects with LonIntercept
        Start = GeographicLocation.coords(lat=lat1, lon=lon1)
        End = GeographicLocation.coords(lat=lat2, lon=lon2)

        GC = GeographicLocation.vec_cross(Start, End)
        N = sum([value**2 for value in GC.values()])
        GC = {k: v / sqrt(N) for k, v in GC.items()}

        zProj = sin(deg2rad(LonIntercept))

        a = Start['z']
        b = Start['y'] * GC['x'] - Start['x'] * GC['y']
        c = zProj

        arc = arctan2(b, a) - arccos(c / sqrt(a**2 + b**2))

        return arc

    def __round__(self, precision):
        return (round(self.latitude, precision), round(self.longitude, precision), round(self.bearing, precision))

    # def __repr__():
    #     return "(" + str(round(latitude, 2)) + ", " + str(round(longitude, 2)) + ", " + str(round(bearing, 2)) + ")"

@dataclass
class StationaryGeographicLocation(GeographicLocation):
    latitude: float # in radians, -pi ... pi, equator = 0
    longitude: float # in radians, -pi ... pi, Prime Meridian = 0
    bearing: None # stationary location lacks bearing
    
    def destination_point(self, distance):
        '''Throws an error as StationaryGeographicLocation cannot move and lacks a bearing.'''
        raise RuntimeError('StationaryGeographicLocation lacks bearing and cannot move')


    def to_decimal_degrees(self):
        '''This method returns a (latitude, longitude, bearing) tuple with the location given in decimal degrees rather than radians.'''
        decimal_latitude = (self.latitude / pi) * 180.0
        decimal_longitude = (self.longitude / pi) * 180.0
        return decimal_latitude, decimal_longitude, self.bearing

    
