import time

from romancer.supervisor.supervisor import Supervisor
from romancer.supervisor.watchlist import WatchlistItem


# define WatchlistItems
# For this SingleThreadSupervisor, we can skip sending unnecessary methods and just call methods
# on environmental objects directly

# Stop

class Stop(WatchlistItem):
    '''This WatchlistItem halts the supervisor once simulation is complete. It defines the simulated time at which simulation will be terminated.'''

    def process(self, supervisor):
        supervisor.watchlist.data=[(self.time, self)] # ensure that stop is sole item on watchlist after executed.
        print('Simulation terminated at time = ', supervisor.environment.time)


    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={})'.format(self.__class__.__name__, self.time)

    
    def __gt__(self, item):
        '''Needed to ensure that Stop will always be last item on the Watchlist.'''
        return True

# Pause

class Pause(WatchlistItem):
    '''This WatchlistItem pauses the supervisor in a way that permits it to be restarted.'''

    def process(self, supervisor):
        supervisor.paused = True

    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={})'.format(self.__class__.__name__, self.time)

# AnticipatedDispositionChange

class AnticipatedDispositionChange(WatchlistItem):
    '''This WatchlistItem flags that a specific object in the environment is anticipated to change dispositions at a particular time.

    While it is unnecessary for this simple demo, an imporant application for this kind of watchlist item is to reconfigure agents' perception engines to reflect altered dispositions. For example, if an object moves into an agent's possible visible field, the AnticipatedDispositionChange could alter that agent's perception engine accordingly.'''

    def __init__(self, time, object_uid, granularity=None):
        super().__init__(time)
        self.object_uid = object_uid
        self.granularity = granularity


    def process(self, supervisor):
        obj = supervisor.environment.message_dispatch_table[self.object_uid]
        if not self.granularity:
            self.granularity = obj.granularity
        for disposition in obj.dispositions:
            disposition.adjust_disposition(obj, obj.location, self.granularity)
        supervisor.check_for_percepts = True # disposition changes are assumed to possibly generate percepts


    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={}, object_uid={}, granularity={})'.format(self.__class__.__name__, self.time, self.object_uid, self.granularity)


class RedLightOn(WatchlistItem):

    def __init__(self, time, red_light_uid):
        super().__init__(time)
        self.red_light_uid = red_light_uid
        

    def process(self, supervisor):
        red_light = supervisor.environment.message_dispatch_table[self.red_light_uid]
        red_light.red_light_on()
        supervisor.check_for_percepts = True # red light likely to generate percepts


    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={}, red_light_uid={})'.format(self.__class__.__name__, self.time, self.red_light_uid)


class RedLightOff(WatchlistItem):

    def __init__(self, time, red_light_uid):
        super().__init__(time)
        self.red_light_uid = red_light_uid

        
    def process(self, supervisor):
        red_light = supervisor.environment.message_dispatch_table[self.red_light_uid]
        red_light.red_light_off()
        supervisor.check_for_percepts = True # red light likely to generate percepts


    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={}, red_light_uid={})'.format(self.__class__.__name__, self.time, self.red_light_uid)


class ActivateECM(WatchlistItem):

    def __init__(self, time, bomber_uid, agent_uid):
        super().__init__(time)
        self.bomber_uid = bomber_uid
        self.agent_uid = agent_uid


    def process(self, supervisor):
        bomber = supervisor.environment.message_dispatch_table[self.bomber_uid]
        agent = supervisor.environment.message_dispatch_table[self.agent_uid]
        bomber.activate_ecm()
        agent.believes_ecm_activated() # agent believes ECM is now on


    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={}, bomber_uid={})'.format(self.__class__.__name__, self.time, self.bomber_uid)


class DeactivateECM(WatchlistItem):

    def __init__(self, time, bomber_uid, agent_uid):
        super().__init__(time)
        self.bomber_uid = bomber_uid
        self.agent_uid = agent_uid

    def process(self, supervisor):
        bomber = supervisor.environment.message_dispatch_table[self.bomber_uid]
        agent = supervisor.environment.message_dispatch_table[self.agent_uid]
        bomber.deactivate_ecm()
        agent.believes_ecm_deactivated() # agent believes ECM is now off
        

    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={}, bomber_uid={})'.format(self.__class__.__name__, self.time, self.bomber_uid)
    

class DisplayBlip(WatchlistItem):

    def __init__(self, time, screen_uid):
        super().__init__(time)
        self.screen_uid = screen_uid
        

    def process(self, supervisor):
        screen = supervisor.environment.message_dispatch_table[self.screen_uid]
        screen.display_blip()
        if screen.blip_to_display: # ensure there is still a blip on the screen
            supervisor.check_for_percepts = True

    
    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={}, screen_uid={})'.format(self.__class__.__name__, self.time, self.screen_uid)


class ActivateRadar(WatchlistItem):

    def __init__(self, time, radar_uid):
        super().__init__(time)
        self.radar_uid = radar_uid


    def process(self, supervisor):
        radar = supervisor.environment.message_dispatch_table[self.radar_uid]
        radar.activate_radar()
        # the radar takes a nonzero amount of time to generate a percept, so supervisor.check_for_percepts need not be set here


    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={}, radar_uid={})'.format(self.__class__.__name__, self.time, self.radar_uid)


class DeactivateRadar(WatchlistItem):

    def __init__(self, time, radar_uid):
        super().__init__(time)
        self.radar_uid = radar_uid


    def process(self, supervisor):
        radar = supervisor.environment.message_dispatch_table[radar_uid]
        radar.deactivate_radar()
        screen = [s for s in radar.children if s.__class__.__name__ == 'RadarScreen'][0]
        # TODO: add method to radar screen to log this correctly
        if screen.blip_to_display:
            screen.blip_to_display = False # radar screen goes blank when radar is deactivated


    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={}, radar_uid={})'.format(self.__class__.__name__, self.time, self.radar_uid)
        

class SetAircraftSpeed(WatchlistItem):

    def __init__(self, time, plane_uid, speed):
        super().__init__(time)
        plane_uid = plane_uid
        self.speed = speed


    def process(self, supervisor):
        plane = supervisor.environment.message_dispatch_table[plane_uid]
        if plane.speed != self.speed:
            plane.set_aircraft_speed(self.speed)


    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={}, plane_uid={}, speed={})'.format(self.__class__.__name__, self.time, self.plane_uid, self.speed)


class ContactSuperior(WatchlistItem):

    def __init__(self, time):
        super().__init__(time)
        

    def process(self, supervisor):
        print('Radar operator attempted to contact superior at time = ', supervisor.environment.time)
        

    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return '{}(time={})'.format(self.__class__.__name__, self.time)

    
# define functions used by SingleThreadSupervisor's dispatch table
# note that these are allowed to make side effects on the supervisor, return an object, or both

def attempt_activate_ecm(sup, message):
    '''This function is used to act on messages sent by the blue agent that reflect attempts to activate the bomber's ECMs.'''
    item = ActivateECM(time = message.time, bomber_uid = sup.environment.message_dispatch_table[message.sender[1]].parent.uid, agent_uid = message.sender[1])
    return item


def attempt_deactivate_ecm(sup, message):
    '''This function is used to act on messages sent by the blue agent that reflect attempts to deactivate the bomber's ECMs.'''
    item = DeactivateECM(time = message.time, bomber_uid = sup.environment.message_dispatch_table[message.sender[1]].parent.uid, agent_uid = message.sender[1])
    return item


def attempt_red_light_on(sup, message):
    '''This function is used to act on messages sent by the bomber's red light reflecting attempts to turn the red warning light on.'''
    item = RedLightOn(time = message.time, red_light_uid = message.sender[1])
    return item


def attempt_red_light_off(sup, message):
    item = RedLightOff(time = message.time, red_light_uid = message.sender[1])
    return item

    
def attempt_activate_radar(sup, message):
    '''This function is used to act on messages sent by the red agent that reflect attempts to turn the radar on.'''
    item = ActivateRadar(time = message.time, radar_uid = sup.environment.message_dispatch_table[message.sender[1]].parent.uid)
    return item


def attempt_deactivate_radar(sup, message):
    '''This function is used to act on messages sent by the red agent that reflect attempts to turn the radar off.'''
    item = DectivateRadar(time = message.time, radar_uid = sup.environment.message_dispatch_table[message.sender[1]].parent.uid)
    return item


def attempt_display_blip(sup, message):
    '''This function is used to act on messages sent by the radar screen that reflect attempts to display a radar blip.'''
    screen_uid = [child for child in sup.environment.message_dispatch_table[message.sender[1]].children if child.__class__.__name__ == 'RadarScreen'][0].uid
    item = DisplayBlip(time = message.time, screen_uid = screen_uid)
    return item


def attempt_set_speed(sup, message):
    '''This function is used to act on messages sent by the blue agent that reflect attempts to adjust the bomber's speed.'''
    item = SetAircraftSpeed(time = message.time, speed=message.speed, bomber_uid = message.sender[1])
    return item


def attempt_contact_superior(sup, message):
    '''This function is used to act on messages sent by the red agent that reflect attempts to contact his superiors.'''
    item = ContactSuperior(time = message.time)
    return item


def attempt_anticipated_disposition_change(sup, message):
    '''This function is used to act on messages sent by the blue agent that reflect attempts to activate the bomber's ECM's.'''
    item = AnticipatedDispositionChange(time = message.time, object_uid =sup.environment.message_dispatch_table[message.sender[1]].uid, granularity = None)
    return item


class SingleThreadSupervisor(Supervisor):


    def __init__(self, environment=None, random_seed=12345, time_cb=None):
        super().__init__(environment, random_seed, time_cb=time_cb)
        self.paused = False # is supervisor currently paused?
        self.check_for_percepts = False # flag indicating whether percept-generating event may have occured
        self.dispatch_table = {'AttemptActivateECM': attempt_activate_ecm,
                               'AttemptDectivateECM': attempt_deactivate_ecm,
                               'AttemptRedLightOn': attempt_red_light_on,
                               'AttemptRedLightOff': attempt_red_light_off,
                               'AttemptActivateRadar': attempt_activate_radar,
                               'AttemptDectivateRadar': attempt_deactivate_radar,
                               'AttemptDisplayBlip': attempt_display_blip,
                               'AttemptSetSpeed': attempt_set_speed,
                               'AttemptContactSuperior': attempt_contact_superior,
                               'AttemptAnticipatedDispositionChange': attempt_anticipated_disposition_change,
                               } # dict of functions for processing messages


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the supervisor's inbox. It should return functions with an (supervisor, message) call signature. Raises an exception if no appropriate dispatch function is found.'''
        try:
            f = self.dispatch_table[message.messagetype]
            return f
        except KeyError:
            print('No dispatch found for message type:', message.messagetype, " on ", self)


    def deterministic_events_process_inbox(self, max_time):
        '''The purpose of this method is to process a set of messages sent by environmental objects in response to a query from the supervisor for the next deterministic event those objects envision making. It identifies which of those events is earliest and returns it as the candidate next event.'''
        candidate_next_item, new_max_time = None, max_time
        if len(self.inbox) > 0:
            # By shuffling and sorting, we gaurantee that we've implemented a randomly-unstable sort,
            #   no matter how the .sort() is implemented in future
            self.rng.shuffle(self.inbox)
            self.inbox.sort(key=lambda m: m.time) # sort watchlist by time in ascending order
            f = self.dispatcher(self.inbox[0])
            candidate_next_item = f(self, self.inbox[0])
            new_max_time = candidate_next_item.time
        self.inbox.clear()
        return candidate_next_item, new_max_time
    

    def stochastic_events_process_inbox(self, candidate_next_item, max_time):
        '''The purpose of this method is to process a set of messages sent by environmental objects in response to a query from the supervisor about possible stochastic events that those objects might make before max_time. Each of these messages is assumed to have a probability attribute that the supervisor uses to assess whether the event happens. This method goes through the messages in chronological order and assesses whether each possible event occurs. If one is assessed positively, then it becomes the candidate next item and its time become the new max time. Otherwise, the candidate_next_item and max_time passed into the method are returned unchanged.'''
        candidate_next_item, new_max_time = candidate_next_item, max_time
        if len(self.inbox) > 0:
            self.rng.shuffle(self.inbox)
            self.inbox.sort(key=lambda m: m.time) # sort watchlist by time in ascending order
            # print(self.inbox)
            for message in self.inbox:
                # assess whether possible event described by message occurs and if so when
                if self.rng.random() <= message.probability:
                    f = self.dispatcher(message)
                    candidate_next_item = f(self, message)
                    new_max_time = candidate_next_item.time
                    break
        self.inbox.clear()
        return candidate_next_item, new_max_time
       

    def bring_watchlist_up_to_date(self, verbose=False):
        '''This method ensures that the lead item on the watchlist is in fact the next one that should be executed. It should work by checking the simulated time of the lead item on the watchlist and then asking relevant objects in the environment (agents, etc.) whether they will or might cause an event of interest in that timeframe.'''
        # check if already at watchlist item time
        next_time = self.watchlist.peek().time
        if self.environment.time == next_time: # no opportunity for next event not to be correct
            return None # nothing to do, watchlist is up to date
        # deterministic events?
        self.environment.deterministic_events_before_time(next_time) # SingleThreadSupervisor can simply tell environment to do this rather than sending message
        # this method should send messages regarding the next deterministic event(s) to the supervisor
        # if multiple deterministic events are scheduled for the same time, send them all
        # examine inbox to see if new deterministic events have been identified prior to next_time
        # if so, store them as possible_next_events, next_time == new_next_time
        candidate_next_item, next_time = self.deterministic_events_process_inbox(next_time)
        # stochastic events?
        self.environment.stochastic_events_before_time(next_time) # SingleThreadSupervisor can simply tell environment to do this rather than sending message
        # this method should send messages regarding possible stochastic event(s) to the supervisor
        # sort possible stochastic events by time
        # use rng to test whether each possible stochastic event turns into a watchlist item
        # if so, this event becomes next watchlist item, next_time=that item's time
        # if no stochastic event has occured, then push the deterministic events in possible_next_events onto watchlist
        candidate_next_item, next_time = self.stochastic_events_process_inbox(candidate_next_item, next_time)
        
        if candidate_next_item:
            self.watchlist.push(candidate_next_item)
        # advance simulation time to next_time
        next_time = max(0, next_time)
        self.environment.forward_simulation(next_time)
        

    def process_next_watchlist_item(self, verbose=False):
        '''This method processes the next item on the watchlist. It assumes that the watchlist is up to date and that enviornment state is synchronized to the same time as that event.'''
        item = self.watchlist.peek()
        item.process(self) # run code associated with WatchlistItem; this can cause arbitrary changes to environment and supervisor state
        self.logger(self.watchlist.pop()) # pop the just-processed item off of the watchlist and log it if desired
        if self.check_for_percepts and len(self.watchlist) > 0:
            next_time = self.watchlist.peek().time
            self.perceive_and_deliberate(next_time)
            self.check_for_percepts = False



    def perceive_and_deliberate(self, max_time, verbose=False):
        '''This method is supposed to be called as part of process_next_watchlist_item(), in cases where new percepts have been generated and agents need to deliberate about those percepts. It tells the environment to run the perception engine and command those agents that receive percepts to assess whether they will take deliberate actions before the next predicted event time. If such actions are planned, they will be messaged to the supervisor when bring_watchlist_up_to_date is next called.'''
        self.environment.perceive_and_deliberate(max_time)
        

    def send_messages(self):
        '''Send the messages in the supervisor's outbox to their intended recipients. Note that this does not cause either the supervisor or the environment to process any of those messages.'''
        for message in self.outbox:
            # recipient isn't defined in this function
            if message.recipient[0] == self.uid: # self-addressed
                self.inbox.append(message)
            else:
                self.environment.deliver_messages([message]) # environment forwards messages directly to inboxes by default


    def run(self, verbose=False):
        while len(self.watchlist) > 0 and not self.paused: # loop as long as watchlist items remain and self.paused is False
            self.bring_watchlist_up_to_date() # ensure current head of watchlist is actual next event
            self.process_next_watchlist_item() # process next watchlist event
            if self.time_cb is not None:
                self.time_cb(self.environment.time)
            time.sleep(0.001) # Let other threads have a bite of the CPU [eg a GUI that needs updating]
        if self.time_cb is not None:
            self.time_cb(None)
        self.environment.finalise()
