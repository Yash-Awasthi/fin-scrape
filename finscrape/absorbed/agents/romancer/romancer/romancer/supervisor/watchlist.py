from collections import UserList
from heapq import heapify, heappop, heappush

class Watchlist(UserList):
    '''This basic Watchlist implementation is likely to be inefficient when it grows too long but has the advantage of simplicity.'''

    def push(self, item):
        '''Add a new item to the Watchlist associated with time.'''
        heappush(self.data, (item.time, item))


    def pop(self):
        '''Remove the item with the lowest time from the Watchlist while keeping the Watchlist ordered by time from lowest to highest. Returns the removed item.'''
        item = heappop(self.data)[1]
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


class WatchlistItem():
    '''Unlike ROMANCERMessages, which are intended to handle events with respect to CPU time, WatchlistItems are intended to address simulated time. WatchlistItems are only intended to be used within the supervisor, so they need not be passed between processes and can be mutable.

    Messages can tell the supervisor to add WatchlistItems, but decisions about how the simulated state evolves should be made by code associated with or triggered by WatchlistItems. This code is permitted, in principle, to modify state existing anywhere, in the environment or the supervisor itself.

    WatchlistItems are supposed to be subclassed in order to reuse code where possible. Much simulator code should be encapsulated within WatchlistItem subclasses. WatchlistItem subclasses can have an arbitrary number of attributes and methods, but they should always implement those given below.'''
    
    def __init__(self, time):
        self.time = time # The simulation time associated with the item. "Administrative" WatchlistItems can be assigned negative time to ensure they are prioritized before all regular WatchlistItems.


    def __repr__(self):
        '''It is desirable to have a __repr__ method for WatchlistItems that allows them to be reconstituted and interpreted by humans.'''
        return 'WatchlistItem(time={})'.format(self.time)


    def __gt__(self, item):
        '''This is necessary for resolving ties in priority queue insertions.'''
        return False


    def __lt__(self, item):
        '''This is necessary for resolving ties in priority queue insertions.'''
        return False


    def process(self, supervisor):
        '''The code that runs when a WatchlistItem is processed is triggered by running this method.'''
        pass        
