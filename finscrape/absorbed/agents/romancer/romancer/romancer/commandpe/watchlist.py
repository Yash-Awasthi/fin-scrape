from romancer.supervisor.watchlist import Watchlist, WatchlistItem
from romancer.commandpe.CPEReader import CPEWeaponFiredReader
from heapq import heapify, heappop, heappush
from copy import copy

# The purpose of the CommandPEWatchlist is to provide a watchlist designed to be initialized from CommandPE output files like those provided by AFGSC


def default_aggregator_fn(events_list, cur_time, inevitable_events):
    '''The purpose of the aggregator function is to convert events returned by the CPEWeaponFiredReader used by CommandPEWatchlist's __init__ method into WatchlistItems that are then used to populated the CommandPEWatchlist's inevitable_events attribute. In order to generate different WatchlistItems from the same set of CommandPE files, pass a differet version of this function.'''
    # convert events into WatchlistItem(s)
    item = CommandPEWatchlistItem(cur_time, events_list) 
    # push WatchlistItem(s) onto inevitable_events
    inevitable_events.append(item)


class CommandPEWatchlist():

    def __init__(self, data = None, inevitable_events = None, weapon_class_csv = None, target_class_csv = None, target_unit_csv = None, weapon_fired_csv = None, weapon_endgame_csv = None, shooter_side='BLUE', temporal_resolution = 600.0, aggregator_fn = default_aggregator_fn, time = 0.0):
        '''Annoyingly, this cannot directly subclass romancer.supervisor.watchlist as UserList expects an initialization form of 0 or 1 arguments. The CommandPEWatchlist is meant to be initialized either from a set of CommandPE output CSV files, or from a pre-populated CommandPEWatchlist.'''
        if not inevitable_events:
            self.inevitable_events = list()
        else:
            self.inevitable_events = inevitable_events
        if not data:
            self.data = list()
        else:
            self.data = data
        if weapon_class_csv and target_class_csv and target_unit_csv and weapon_fired_csv and weapon_endgame_csv and shooter_side:
            reader = CPEWeaponFiredReader(weapon_class_csv, target_class_csv, target_unit_csv, weapon_fired_csv, weapon_endgame_csv, shooter_side)
            while not reader.is_scenario_complete():
                events_list = reader.read_next_weapons_events(temporal_resolution)
                cur_time = reader.get_current_time_s()
                aggregator_fn(events_list, cur_time, self.inevitable_events)
        # ensure inevitable_events is sorted by time
        self.inevitable_events.sort() # note that inevitable_events is a sorted list, not a heap
        # push copies of WatchlistItems in inevitable_events onto self.data
        if len(self.data) == 0: 
            for event in self.inevitable_events:
                self.push(copy(event))
        if time == 0.0:
            self.time = time # time is time of most recently popped event
        else:
            self.rewind(time) # set watchlist to correct subset of inevitable_events
            

    def __repr__(self):
        return 'CommandPEWatchlist(data = {}, inevitable_events = {})'.format(self.data.__repr__(), self.inevitable_events)

    
    def push(self, item):
        '''Add a new item to the Watchlist associated with time.'''
        heappush(self.data, (item.time, item))


    def pop(self):
        '''Remove the item with the lowest time from the Watchlist while keeping the Watchlist ordered by time from lowest to highest. Returns the removed item.'''
        item = heappop(self.data)[1]
        self.time = item.time
        return item


    def peek(self):
        '''Return a reference to the item with the lowest time on the Watchlist without changing its contents.'''
        return self.data[0][1]


    def remove(self, items):
        '''Remove items from Watchlist and return a properly ordered Watchlist. Raises an exception if one of the items is not in Watchlist.'''
        for item in items:
            try:
                index = [self.data[1] for i in self.data].index(item)
            except ValueError:
                print('item not in Watchlist:', item)
            self.data.pop(index)
        heapify(self.data)


    def remove_if(self, test_fn):
        '''Removes items from Watchlist that test True for test_fn. Returns properly sorted Watchlist.'''
        survivors = [entry for entry in self.data if not test_fn(entry[1])]
        self.data = survivors
        heapify(self.data)


    def find_if(self, test_fn):
        '''Returns a list of the items in the Watchlist that return True for test_fn, permitting them to be modified in place if desired.'''
        return [entry[1] for entry in self.data if test_fn(entry[1])]


    def rewind(self, time):
        '''This method rewinds the CommandPEWatchlist, repopulating with copies of the WatchlistItems stored in self.inevitable_events as needed.'''
        if time <= self.time: # should this be <?
            # push items from inevitable_events back onto Watchlist as needed
            for item in self.inevitable_events:
                if time <= item.time <= self.time:
                    self.push(copy(event))
                elif item.time >= self.time:
                    break
        elif time > self.time:
            # pop items from Watchlist as needed
            while self.peek().time > time:
                self.pop()
        # else: # time == self.time
        #     pass # is this right? There may be multiple items on Watchlist for simultaneous time


    def __len__(self):
        '''This is needed as the supervisor uses len() on the watchlist.'''
        return len(self.data)
        

class CommandPEWatchlistItem(WatchlistItem):
    '''The CommandPEWatchlistItem is basically a container for the list of events returned by the CPEREader's read_next_weapons_events method, which also provides the process method expected by the supervisor.'''

    def __init__(self, time, events_list, agent_uid = None):
        self.time = time
        self.events_list = events_list
        self._agent_uid = agent_uid # programmed recipient for percept(s), automatically determined if only one agent exists in environment


    def process(self, supervisor):
        '''When processed, the CommandPEWatchlistItem is supposed to call the PerceptionEngine to convert the contents of self.events_list into a percept, which is then passed to the agent(s) perception filter(s).'''
        if not self._agent_uid:
            if len(supervisor.environment.agents) == 1: # only one possible agent to receive percept
                agent_uid = supervisor.environment.agents[0].uid
        else:
             agent_uid = self._agent_uid
        supervisor.environment.perception_engine.force_percept(self.time, self.events_list, agent_uid) # this method should generate the percept from events_list and have it queued for delivery when the perceptionengine is run
        supervisor.check_for_percepts = True # this tells the supervisor to run the perception engine


    def __repr__(self):
        return 'WatchlistItem(time={}, events_list={})'.format(self.time, self.events_list)
