from typing import NamedTuple
from romancer.environment.object import RomancerObject
from romancer.environment.location import GeographicLocation
from romancer.environment.loglist import Logpoint
from numpy import pi, inf
from copy import copy
from scipy.optimize import root_scalar
import math
from numpy import rad2deg, deg2rad
from matplotlib.path import Path
from matplotlib.markers import MarkerStyle
import cartopy.crs as ccrs
from matplotlib.lines import Line2D


# Introducing the B-0: a plane that really, really sucks

class BZeroLogpoint(Logpoint):
    '''This logpoint is used to track the evolution of the state of the plane through time. For simplicity's sake it simply stores all plane variables that can change.'''

    def __init__(self, time, location, speed, ecm):
        self.time = time
        self.location = copy(location) # GeographicLocation is mutable so logpoints need to store copy
        self.speed = speed
        self.ecm = ecm


    def __repr__(self):
        return 'BZeroLogpoint(time={}, location={}, speed={}, ecm={})'.format(self.time, self.location, self.speed, self.ecm)


class TemporalROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    time: float # simulation time
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)


class SpeedROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    speed: float # speed (km/hr)
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)

    
class ProbabilisticROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    time: float # simulation time
    probability: float # probability of event in anticipated occurrences per second
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)


def next_deterministic_action(o, m):
    '''This method sends a message to the supervisor indicating the time of the next deterministic action that the plane will take. As the only such action the plane can take on its own is traversing into a different disposition node, it simply sends a message indicating when this is predicated to take place.'''
    t = o.dispositions[0].next_anticipated_disposition_change(o)
    if t <= m.time:
        message = TemporalROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AnticipatedDispositionChange', time=t)
        o.outbox.append(message) # This doesn't actually send message to supervisor, environment needs to do that


def stochastic_actions_before_time(o, m):
    pass

    
class BZero(RomancerObject):

    def __init__(self, environment, time, location, speed, ecm=False, resolution=0.01):
        super().__init__(environment, time) # set up standard object slots
        self.children = list() # pilot and red light go here
        self.location = location # GeographicLocation representing plane latitude, longitude, and bearing
        self.speed = speed # speed along trajectory in km/hr
        self.ecm = ecm # electronic countermeasures that can confound adversary radar; boolean
        self.resolution = resolution # used for disposition tree
        self.dispositions = [self.environment.disposition_tree.set_disposition(self, self.location, self.resolution)]
        self.dispatch_table = {'DeterministicActionsBeforeTime': next_deterministic_action, 
                               'StochasticActionsBeforeTime': lambda o, m: None,
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                               'ActivateECM': lambda o, m: o.activate_ecm(),
                               'DeactivateECM': lambda o, m: o.deactivate_ecm(),
                               'SetAircraftSpeed': lambda o, m: set_aircraft_speed(o, m.speed)
                               } # dict of functions for processing messages
        self.repr_list = self.repr_list + ['location', 'speed', 'ecm', 'resolution']
        initial_logpoint = BZeroLogpoint(time=self.time, location=self.location, speed=self.speed, ecm=self.ecm)
        self.loglist.append(initial_logpoint)


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the plane's inbox. Each subclass will need a unique implementation of it. It should return functions with an (obj, message) call signature. Raises an exception if no appropriate dispatch function is found.'''
        try:
            f = self.dispatch_table[message.messagetype]
            return f
        except KeyError:
            print('No dispatch set for ', message)


    def next_anticipated_disposition_change(self):
        '''Identify future time at which plane will leave its current disposition tree node based on its current speed and trajectory.'''
        if self.speed == 0: # disposition will never change
            5/0
            return None
        actual_speed = self.speed / 3600.0 # speed in km/s
        
        # use bearing to determine which boundaries plane will cross first
        lowlat, highlat, lowlong, highlong = self.dispositions[0].bounds
        if self.location.bearing > pi: # heading west
            longbound = lowlong
        elif self.location.bearing < pi: # heading east
            longbound = highlong
        elif self.location.bearing == 0 or self.location.bearing == pi: # heading north or south
            longbound = None
        if self.location.bearing < pi / 2 or 1.5 * pi < self.location.bearing: # heading north
            latbound = highlat
        elif  pi / 2 < self.location.bearing < 1.5 * pi: # heading south
            latbound = lowlat
        elif self.location.bearing == pi / 2 or self.location.bearing == 1.5 * pi: # heading east or west
            latbound = None

        # find the intersection of the plane and the latbound
        if latbound:
            latbound_location = GeographicLocation(latbound, self.location.longitude, pi/2)
            latbound_intersection = GeographicLocation.calculate_intersection(self.location, latbound_location)
            if math.isnan(latbound_intersection.latitude):
                time_until_latbound_intersection = inf
            else:
                # determine how far the intersection is from here
                distance_to_latbound_intersection = self.location.distance(latbound_intersection)
                # determine how long until the plane reaches that intersection
                time_until_latbound_intersection = distance_to_latbound_intersection / actual_speed
        # find the intersection of the plane and the longbound
        if longbound:
            longbound_location = GeographicLocation(self.location.latitude, longbound, 0)
            longbound_intersection = GeographicLocation.calculate_intersection(self.location, longbound_location)
            if math.isnan(longbound_intersection.latitude):
                time_until_latbound_intersection = inf
            else:
                # determine how far the intersection is from here
                distance_to_longbound_intersection = self.location.distance(longbound_intersection)
                # determine how long until the plane reaches that intersection
                time_until_longbound_intersection = distance_to_longbound_intersection / actual_speed

        # determine when the plane will touch the closest boundary
        delta_t = min(time_until_latbound_intersection, time_until_longbound_intersection)

        return self.time + delta_t


    def plot(self, ax):
        lon = rad2deg(self.location.longitude)
        lat = rad2deg(self.location.latitude)
        ber = rad2deg(self.location.bearing)
        triangle = Path([[-0.5, 0], [0.5, 0], [0, 0.5]])
        rotated_triangle = MarkerStyle(triangle).rotated(deg=-ber)
        ax.plot(lon, lat, marker=rotated_triangle, color='blue', markersize=11, linestyle='')
        traj_longs = [rad2deg(l.location.longitude) for l in self.loglist] + [lon]
        traj_lats = [rad2deg(l.location.latitude) for l in self.loglist] + [lat]
        ax.plot(traj_longs, traj_lats, color='blue', linewidth=2, transform=ccrs.Geodetic())
        leg_elms = [Line2D([0], [0], color=(0, 0, 0, 0), marker=triangle, markerfacecolor='blue', markeredgecolor='blue', markersize=15, label='bomber')]
        if len(traj_longs) > 2:
            leg_elms.append(Line2D([0], [0], color='blue', linewidth=2, label='traversed flight path'))
        return leg_elms


    def update_disposition(self):
        '''Update the disposition of the plane. This method assumes that the time of the disposition change has already been identified with self.next_anticipated_disposition_change() and that the state of the plane has been evolved forward to that time using self.forward_simulation().'''
        cur = self.dispositions[0]
        self.dispositions[0], new_peers =  self.dispositions[0].adjust_disposition(self, self.location, self.resolution)
        if self.dispositions[0] is not cur:
            new_logpoint = BZeroLogpoint(time = self.time, location = self.location, speed = self.speed , ecm = self.ecm)
            self.loglist.append(new_logpoint)
        

    def forward_simulation(self, time):
        '''Evolve the plane's state forward in time. Except when rewinding, this ought not be called on an interval that will result in a changed disposition.'''
        if time == self.time:
            pass
        delta_t = time - self.time
        actual_speed = self.speed / 3600.0 # speed in km/s
        # print(actual_speed * delta_t)
        new_location = self.location.destination_point(actual_speed * delta_t)
        self.location = new_location
        self.time = time
        for child in self.children:
            child.forward_simulation(time)

        
    def rewind(self, time):
        '''Rewind the state of the B-0 to what it was at time using information stored in loglist.'''
        if self.time == time:
            pass
        low, high = self.loglist.temporal_bounds()
        if low <= time:
            self.loglist.truncate_to_time(time) # maybe this shouldn't truncate
            latest = self.loglist[-1] # most recent logpoint < time
            self.time = latest.time # set plane time to logpoint time
            self.location = latest.location # set plane location to logpoint location
            self.speed = latest.speed # set plane speed to logpoint speed
            self.ecm = latest.ecm # set plane ecm to logpoint ecm
            self.forward_simulation(time)
            # self.update_disposition() # reset plane disposition, if necessary
            self.dispositions[0], peer_difference= self.dispositions[0].adjust_disposition(self, self.location, self.resolution) # don't add superfluous logpoint


    def activate_ecm(self):
        if self.ecm:
            pass
        else:
            self.ecm = True
            new_logpoint = BZeroLogpoint(time = self.time, location = self.location, speed = self.speed , ecm = self.ecm)
            self.loglist.append(new_logpoint)


    def deactivate_ecm(self):
        if not self.ecm:
            pass
        else:
            self.ecm = False
            new_logpoint = BZeroLogpoint(time = self.time, location = self.location, speed = self.speed, ecm = self.ecm)
            self.loglist.append(new_logpoint)
        

    def set_aircraft_speed(self, speed):
        if speed == self.speed:
            pass
        else:
            self.speed = speed
            new_logpoint = BZeroLogpoint(time = self.time, location = self.location, speed = self.speed, ecm = self.ecm)
            self.loglist.append(new_logpoint)
        

class RedLightLogpoint(Logpoint):
    def __init__(self, time, on):
        self.time = time
        self.on = on # bool

    
    def __repr__(self):
        return 'RedLightLogpoint(time={}, on={})'.format(self.time, self.on)

    
def red_light_stochastic_actions_before_time(o, m):
    
    messages = list()
    peers = list()
    for d in o.dispositions:
        for item in d.identify_peers():
            if item not in peers and item != o:
                peers.append(item)
    delta_t = 5.0 # 5 second detection interval
    # times = list(range(o.time, m.time, delta_t)) range doesn't work for floats
    times = [o.time + delta_t * i for i in range(1, int((m.time - o.time) / delta_t) + 1)]
    # print(times)
    if o.on:
        for peer in peers:
            initial_time = o.parent.time
            for t in times:
                if peer.__class__.__name__ == 'RedRadar':
                    o.parent.forward_simulation(t)
                    distance = o.location.distance(peer.location)
                    # check to see if adversary radar is now off or out of range and turn off light
                    if peer.on == False or distance > 250.0:
                        message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptRedLightOff', time=t, probability=0.95)
                        messages.append(message)
            o.parent.rewind(initial_time)
        # possibly turn off at random
        for t in times:
            message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptRedLightOff', time=t, probability=0.001)
            messages.append(message)
    else:
        # check to see if adversary radar is now on or in range and turn on light
        for peer in peers:
            initial_time = o.parent.time
            for t in times:
                if peer.__class__.__name__ == 'RedRadar':
                    o.parent.forward_simulation(t)
                    distance = o.location.distance(peer.location)
                    # print(distance)
                    # check to see if adversary radar is now on and in range and turn off light if so
                    if peer.on == True and distance < 250.0:
                        message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptRedLightOn', time=t, probability=0.95)
                        messages.append(message)
            o.parent.rewind(initial_time)
            # possibly turn on at random
        for t in times:
            message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptRedLightOn', time=t, probability=0.001)
            messages.append(message)
    for message in messages:
        o.outbox.append(message)

    
class RedLight(RomancerObject):
    '''This red light can turn on to indicate possible detection by adversary radar. It can also turn on by random chance due to stochastic malfunctions.'''
    
    def __init__(self, environment, time, location):
        super().__init__(environment, time) # set up standard object slots
        self.parent = None
        self.on = False # used to generate percept
        self.dispatch_table = {'DeterministicActionsBeforeTime': lambda o, m: None, # light generates no autonomous deterministic actions
                               'StochasticActionsBeforeTime': red_light_stochastic_actions_before_time,
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                               'RedLightOn': lambda o, m: o.red_light_on(),
                               'RedLightOff': lambda o, m: o.red_light_off()}
        self.repr_list = self.repr_list + ['parent', 'on']
        initial_logpoint = RedLightLogpoint(time=self.time, on=self.on)
        self.loglist.append(initial_logpoint)


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the plane's inbox. Each subclass will need a unique implementation of it. It should return functions with an (obj, message) call signature. Raises an exception if no appropriate dispatch function is found.'''
        try:
            f = self.dispatch_table[message.messagetype]
            return f
        except KeyError:
            print('No dispatch set for ', message)

        
    @property
    def location(self):
        '''The light is part of the plane, so its location is the same as that of the plane.'''
        return self.parent.location

    
    @property
    def resolution(self):
        '''The light is part of the plane, so its resolution is the same as that of the plane.'''
        return self.parent.resolution

    
    @property
    def dispositions(self):
        '''The light is part of the plane, so its dispositions are shared with the plane.'''
        return self.parent.dispositions


    def red_light_on(self):
        if not self.on:
            self.on = True
            new_logpoint = RedLightLogpoint(time = self.time, on = self.on)
            self.loglist.append(new_logpoint)


    def red_light_off(self):
        if self.on:
            self.on = False
            new_logpoint = RedLightLogpoint(time = self.time, on = self.on)
            self.loglist.append(new_logpoint)
