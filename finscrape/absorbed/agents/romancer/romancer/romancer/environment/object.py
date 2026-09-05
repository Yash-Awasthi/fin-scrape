from typing import NamedTuple
from romancer.environment.loglist import Loglist
from numpy import rad2deg
from matplotlib.path import Path
from matplotlib.markers import MarkerStyle
import matplotlib.patheffects as pe
import warnings
from collections import UserList, UserDict
from collections.abc import MutableSequence, MutableSet, MutableMapping
from functools import singledispatch
import copy

class MissingMethodWarning(Warning):
    pass

class RewindError(Exception):
    pass


class RomancerObject():

    '''This is the base class for objects in the ROMANCER environment.'''

    def __init__(self, environment, time, location=None):
        self.inbox = list() # list of messages awaiting processing
        self.outbox = list() # list of messages that have not yet been sent
        # self.location = location
        self.environment = environment # ROMANCEREnvironment instance containing object
        self.uid = self.environment.register_object(self) # assign unique id to object
        self.message_index = 1 # increments with each message to assign unique ids
        # objects with children also need to register those children
        self.time = time # current time of simulated object
        self.loglist = Loglist() # list of logpoints
        self.repr_list = ['inbox', 'outbox', 'uid', 'message_index', 'time', 'loglist'] # used for __repr__ with keywords

        # self.dispositions = [self.environment.disposition_tree.set_disposition(self), self.environment.perception_engine.emplace(self)... ]

        
    def new_message_index(self):
        '''This method is used to obtain unique integer ids for messages.'''
        cur = self.message_index
        self.message_index += 1 # increase message index
        return cur

    
    def deliver_messages(self, messages):
        '''Place messages in object's inbox.'''
        for message in messages:
            self.inbox.append(message)


    def send_messages(self):
        '''Pass messages from outbox to environment so they can be routed to their appropriate recipients.'''
        self.environment.deliver_messages(self.outbox) # maybe this should send self-addressed messages directly to inbox
        self.outbox.clear()


    def get_children(self):
        '''Many items will have children. This method is supposed to return all children of all subsidiary objects recursively. As this default class has no children, it returns None.'''
        return None


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the object's inbox. Each subclass will need a unique implementation of it. It should return functions with an (obj, message) call signature.'''
        return lambda obj, message: None


    def process_inbox(self):
        '''This method acts on all the messages currently in the inbox using the functions returned by the dispatcher. These functions can alter the state of the object or its children, send one or more messages to various recipients, or simply be ignored.'''
        while len(self.inbox) > 0:
            message = self.inbox.pop()
            f = self.dispatcher(message)
            f(self, message)
        self.send_messages() # send outgoing messages if necessary
    

    def rewind(self, time):
        '''This method should use the object's history to revert to its state at time. As this base object has no state to manipulate, all it does is reset the object's time.'''
        self.time = time


    def forward_simulation(self, time):
        '''This method should evolve the object's state forward in time, logging changes as logpoints if necessary. Forward simulation can also generate messages.''' 
        if self.time > time:
            self.rewind(time)
        else:
            self.time = time


    def next_anticipated_disposition_change(self):
        '''This method should use the disposition nodes referenced in self.disposition and other available object state to predict the earliest future time at which the object will leave one of those nodes. Often this information will have been computed already and stored as a logpoint.

        As this base class cannot change state, it returns None.'''
        return None

        
    def plot(self, ax, owner):
        '''
        All RomancerObjects are responsible for plotting themselves.
        They will plot themselves on the provided axis ax.
        They may want to plot something relative to their owner (eg, a disposition tree).
        '''
        warnings.warn("Plot method not implemented for base RomancerObject class", MissingMethodWarning)


    def __repr__(self):
        '''This method is designed to print representations useful in experimental programming on the repl.

        Printing the Environment is a problem as it contains recursive references. Maybe it should be defined to some convenient global name by default to make printing convenient?'''
        class_name = self.__class__.__name__
        results = {key: self.__getattribute__(key) for key in self.repr_list}
        return f"{class_name}({', '.join([f'{k}={v.__repr__()}' for k,v in results.items()])})"


class AttrSetLog(NamedTuple):
    attr_name: str
    oldval: any
    newval: any


# Needed to delete attribute if needed
class AttrAdditionLog(NamedTuple):
    attr_name: str
    val: any


class AttrRemovalLog(NamedTuple):
    attr_name: str
    val: any
    
    
# These are for use with LoggedList and LoggedSet
class CollectionAdditionLog(NamedTuple):
    collectionname: str # name of attr where collection is stored in host object
    val: any # obj to add


class CollectionRemovalLog(NamedTuple):
    collectionname: str # name of attr where collction is stored in host object
    removal: any # obj to remove


class CollectionSetItemLog(NamedTuple):
    collectionname: str
    index: int
    oldval: any
    newval : any

class CollectionReverseLog(NamedTuple):
    collectionname: str

# These are for use with LoggedDict
class DictAdditionLog(NamedTuple):
    collectionname: str # name of attr where dict is stored in host object
    keyname: any # name of key with which val should be associated 
    addition: any # obj to add


class DictRemovalLog(NamedTuple):
    collectionname: str # name of attr where dict is stored in host object
    keyname: any # name of key with which val is associated
    removal: any # obj to remove


class DictSetItemLog(NamedTuple):
    collectionname: str # name of attr where dict is stored in host object
    keyname: any # name of key with which val is associated
    oldval: any # current value
    newval: any # new value
    

class UniversalLogpoint(NamedTuple):
    time: any # can be int or float
    difs: tuple[tuple] # tuple of tuples representing changes, usually just one but can be arbitrary number that occur at same time
    

class ImprovedLoglist(UserList):
    '''ROMANCER objects need to store enough information about their evolution over time to revert back to their states at earlier times. The ImprovedLoglist is intended as a means to store that state. The ImprovedLoglist is also supposed to store available information about the foreseeable future evolution of the object.'''
    def __init__(self, time):
        self.data = [UniversalLogpoint(time=time, difs=())]


    def minimum_time(self):
        return self.data[0].time

    
    def maximum_time(self):
        return self.data[-1].time


    def last_index_before(self, time):
        if time > self.maximum_time():
            return len(self.data) - 1
        elif self.minimum_time() <= time:
            for i in range(len(self.data)):
                if self.data[i].time > time:
                    return i
        else:
            raise ValueError('Time less than minimum in ImprovedLoglist')


    def first_index_after(self, time):
        if time > self.maximum_time():
            raise ValueError(f'Time {time} greater than maximum time {self.maximum_time()} in ImprovedLoglist')
        elif time < self.minimum_time():
            return 0
        else:
            for i in range(len(self.data) - 1, 0, -1):
                if self.data[i].time <= time:
                    return i + 1

            return 0


    def truncate_to_time(self, time):
        '''This method truncates the list to remove all logpoints with time greater than time.'''
        i = self.first_index_after(time)
        self.data = self.data[0:i]


    def revert_list(self, prev_time, cur_time):
        start_i = self.first_index_after(prev_time)
        stop_i = self.last_index_before(cur_time)
        return self.data[start_i: stop_i][::-1] # reverse order of logpoints so that they can be reverted
    

    def reassert_list(self, cur_time, future_time):
        start_i = self.first_index_after(cur_time)
        stop_i = self.last_index_before(future_time)
        return self.data[start_i: stop_i]


class LoggedList(MutableSequence):
    # This is not intended to be used directly, as it violates some MutableSequence implied contracts

    def __init__(self, data, parent, varname):
        # User must not modify data themselves after passing it - we hold a reference
        self.parent = parent
        self.varname = varname
        self.data = data

   
    def append(self, x):
        loglist = self.parent.loglist
        cur_time = self.parent.time
        logpoint = UniversalLogpoint(time = cur_time, difs = tuple([CollectionAdditionLog(collectionname = self.varname, val = x)]))
        if self.parent.time < loglist.maximum_time():
            loglist.truncate_to_time(cur_time)
        self.parent.loglist.append(logpoint)
        self.data.append(x)


    def pop(self):
        loglist = self.parent.loglist
        cur_time = self.parent.time
        cur_val = self.data[-1]
        logpoint = UniversalLogpoint(time = cur_time, difs = tuple([CollectionRemovalLog(collectionname = self.varname, removal = cur_val)]))
        if self.parent.time < loglist.maximum_time():
            loglist.truncate_to_time(cur_time)
        self.parent.loglist.append(logpoint)
        self.data.pop()

    
    def insert(self, i, x):
        raise NotImplementedError("LoggedList.insert(i, x) is currently not implemented.")
    

    def reverse(self):
        logpoint = UniversalLogpoint(time = self.parent.time, difs = tuple([CollectionReverseLog(collectionname = self.varname)]))
        self.parent.loglist.append(logpoint)
        self.data.reverse()
    
    def copy(self):
        # If a user requests a copy of this object, they receive just the naked list
        return self.data.copy()
    
    def clear(self):
        while len(self.data) > 0:
            self.pop()
        # raise NotImplementedError("LoggedList.clear() not implemented.")
        # logpoint = UniversalLogpoint(time = self.parent.time, difs = tuple([AttrSetLog(attr_name = self.varname, oldval = copy.copy(self), newval = LoggedList(data=[], parent=self.parent, varname=self.varname))]))
        # self.parent.loglist.append(logpoint)
        # self.data = list()

    def __setitem__(self, i, x):
        loglist = self.parent.loglist
        cur_time = self.parent.time
        cur_val = self.data[i]
        logpoint = UniversalLogpoint(time = cur_time, difs = tuple(CollectionSetItemLog(collectionname = self.varname, index = i, oldval = cur_val, newval = x)))
        if self.parent.time < loglist.maximum_time():
            loglist.truncate_to_time(cur_time)
        self.parent.loglist.append(logpoint)
        self.data[i] = x

    def __getitem__(self, index):
        return self.data[index]

    def __delitem__(self, index):
        raise NotImplementedError("Deleting items from LoggedList at specific indices not implemented.")

    def __eq__(self, other):
        return self.data == other.data
    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return f"LoggedList({self.data})"


class LoggedSet(MutableSet):

    def __init__(self, data, parent, varname):
        # User must not modify data themselves after passing it - we hold a reference
        self.parent = parent
        self.varname = varname
        self.data = data

    def __contains__(self, value):
        return value in self.data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def add(self, x):
        if x not in self.data: # only need to log additions that result in changes
            loglist = self.parent.loglist
            cur_time = self.parent.time
            logpoint = UniversalLogpoint(time = cur_time, difs = tuple([CollectionAdditionLog(collectionname = self.varname, val = x)]))
            if self.parent.time < loglist.maximum_time():
                loglist.truncate_to_time(cur_time)
            self.parent.loglist.append(logpoint)
            self.data.add(x)

            
    def remove(self, x):
        if x not in self.data:
            raise ValueError(f'Value {x} not present in LoggedSet', x)
        else:
            loglist = self.parent.loglist
            cur_time = self.parent.time
            logpoint = UniversalLogpoint(time = cur_time, difs = tuple([CollectionRemovalLog(collectionname = self.varname, removal = x)]))
            if self.parent.time < loglist.maximum_time():
                loglist.truncate_to_time(cur_time)
            self.parent.loglist.append(logpoint)
            self.data.remove(x)

            
    def discard(self, x):
        if x in self.data:
            self.remove(x)

    def union(self, *others):
        # Leaky abstraction: After doing usual set operations [union, intersection, difference],
        #  there isn't a sensible LoggedSet variant to log, and therefore forward/rewind.
        return self.data.union(*others)
    
    def intersection(self, *others):
        return self.data.intersection(*others)
    
    def difference(self, *others):
        return self.data.difference(*others)
    
    def symmetric_difference(self, *others):
        return self.data.symmetric_difference(*others)
    
    def update(self, *others):
        logs = list()
        cur_time = self.parent.time
        for other in others:
            for item in other:
                if item not in self.data:
                    logs.append(CollectionAdditionLog(collectionname = self.varname, val = item))
        if len(logs) > 0:
            loglist = self.parent.loglist
            cur_time = self.parent.time
            logpoint = UniversalLogpoint(time = cur_time, difs = tuple(logs))
            if self.parent.time < loglist.maximum_time():
                loglist.truncate_to_time(cur_time)
            self.parent.loglist.append(logpoint)
            self.data.update(*others)


    def intersection_update(self, *others):
        i = self.data.intersection(*others) # items that are in all sets
        d = self.data - i # items that are in self.data that aren't in others
        logs = list()
        for item in d:
            logs.append(CollectionRemovalLog(collectionname = self.varname, removal = item))
        if len(logs) > 0:
            loglist = self.parent.loglist
            cur_time = self.parent.time
            logpoint = UniversalLogpoint(time = cur_time, difs = tuple(logs))
            if self.parent.time < loglist.maximum_time():
                loglist.truncate_to_time(cur_time)
            self.parent.loglist.append(logpoint)
            self.data.intersection_update(*others)


    def difference_update(self, *others):
        i = self.data.intersection(*others)
        logs = list()
        for item in i:
            logs.append(CollectionRemovalLog(collectionname = self.varname, removal = item))
        if len(logs) > 0:
            loglist = self.parent.loglist
            cur_time = self.parent.time
            logpoint = UniversalLogpoint(time = cur_time, difs = tuple(logs))
            if self.parent.time < loglist.maximum_time():
                loglist.truncate_to_time(cur_time)
            self.parent.loglist.append(logpoint)
            self.data.difference_update(*others)


    def symmetric_difference_update(self, *others):
        sd = self.data.symmetric_difference(*others)
        d = self.data - sd # items to remove from self.data
        logs = list()
        for item in d: # log the removal of all items in the intersection
            logs.append(CollectionRemovalLog(collectionname = self.varname, removal = item))
        additions = sd - self.data
        for item in additions: # log the addition of all itmes not in the intersection and not in the original set
            logs.append(CollectionAdditionLog(collectionname = self.varname, val = item))
        if len(logs) > 0:
            loglist = self.parent.loglist
            cur_time = self.parent.time
            logpoint = UniversalLogpoint(time = cur_time, difs = tuple(logs))
            if self.parent.time < loglist.maximum_time():
                loglist.truncate_to_time(cur_time)
            self.parent.loglist.append(logpoint)
            self.data.symmetric_difference_update(*others)

    def clear(self):
        raise NotImplementedError("LoggedSet.clear() not implemented.")

        # logpoint = UniversalLogpoint(time = self.parent.time, difs = tuple([AttrSetLog(attr_name = self.varname, oldval = self.data.copy(), newval = set())]))
        # self.parent.loglist.append(logpoint)
        # self.data = set()


    def __repr__(self):
        return f"LoggedSet({self.data})"


class LoggedDict(UserDict):

    def __init__(self, data, parent, varname):
        # User must not modify data themselves after passing it - we hold a reference
        self.parent = parent
        self.varname = varname
        self.data = data
        
    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __setitem__(self, key, val):
        loglist = self.parent.loglist
        cur_time = self.parent.time
        try:
            cur_val = self.data[key]
        except KeyError:
            logpoint = UniversalLogpoint(time = cur_time, difs = tuple([DictAdditionLog(collectionname = self.varname, keyname = key, addition = val)]))
        else:
            logpoint = UniversalLogpoint(time = cur_time, difs = tuple([DictSetItemLog(collectionname = self.varname, keyname = key, oldval = cur_val, newval = val)]))
        if self.parent.time < loglist.maximum_time():
            loglist.truncate_to_time(cur_time)
        self.parent.loglist.append(logpoint)
        self.data[key] = val


    def pop(self, key, *default):
        if key in self.data:
            loglist = self.parent.loglist
            cur_time = self.parent.time
            cur_val = self.data[key]
            logpoint = UniversalLogpoint(time = cur_time, difs = tuple([DictRemovalLog(collectionname = self.varname, keyname = key, removal = cur_val)]))
            if self.parent.time < loglist.maximum_time():
                loglist.truncate_to_time(cur_time)
            self.parent.loglist.append(logpoint)
            return self.data.pop(key)
        elif not key in self.data and len(default) > 0:
            return default[0]
        else:
            raise KeyError('Key not present in dict: ', key)


    def popitem(self):
        key, cur_val = self.data.popitem() # will raise KeyError if dict is empty
        loglist = self.parent.loglist
        cur_time = self.parent.time
        logpoint = UniversalLogpoint(time = cur_time, difs = tuple([DictRemovalLog(collectionname = self.varname, keyname = key, removal = cur_val)]))
        if self.parent.time < loglist.maximum_time():
            loglist.truncate_to_time(cur_time)
        self.parent.loglist.append(logpoint)
        return key, cur_val
        

    def setdefault(self, key, default = None):
        if key in self.data:
            return self.data[key]
        else:
            self[key] = default # should log via __setitem__


    def update(self, other):
        logs = list()
        loglist = self.parent.loglist
        cur_time = self.parent.time
        for key, val in other.items():
            if key in self.data:
                cur_val = self.data[key]
                if self.data[key] != val:
                    logs.append(DictSetItemLog)(collectionname = self.varname, keyname = key, oldval = cur_val, new_val = val)
            else:
                logs.append(DictAdditionLog(collectionname = self.varname, keyname = key, addition = val))
        if len(logs) > 0:
            logpoint = UniversalLogpoint(time = cur_time, difs = tuple(logs))
            if self.parent.time < loglist.maximum_time():
                loglist.truncate_to_time(cur_time)
            self.parent.loglist.append(logpoint)
            self.data.update(other)

    def clear(self):
        for key, value in self.data:
            self.pop(key)


    def __repr__(self):
        return f"LoggedDict({self.data})"


class ImprovedRomancerObject():

    def __init__(self, environment=None, time=0.0):
        super().__setattr__('unlogged_attrs', dir(self) + ['unlogged_attrs', 'inbox', 'outbox', 'environment', 'uid', 'message_index', 'time', 'loglist', 'repr_list']) # needed for object's custom __setattr__ to work correctly; will dir(self) catch all the class methods?
        self.inbox = list() # list of messages awaiting processing
        self.outbox = list() # list of messages that have not yet been sent
        self.environment = environment # ROMANCEREnvironment instance containing object
        if environment is not None:
            self.uid = self.environment.register_object(self) # assign unique id to object
        self.message_index = 0 # increments with each message to assign unique ids
        self.time = time # current time of simulated object
        self.loglist = ImprovedLoglist(time) # list of logpoints
        self.repr_list = ['inbox', 'outbox', 'uid', 'message_index', 'time', 'loglist'] # used for __repr__ with keywords

    def reset_romancer_object(self, environment, time):
        # This place is not a place of honor... no highly esteemed deed is commemorated here... nothing valued is here.
        # What is here was dangerous and repulsive to us. This message is a warning about danger.
        self.inbox = list()  # list of messages awaiting processing
        self.outbox = list()  # list of messages that have not yet been sent
        self.environment = environment  # ROMANCEREnvironment instance containing object
        self.uid = self.environment.register_object(self)  # assign unique id to object
        self.message_index = 0  # increments with each message to assign unique ids
        self.time = time  # current time of simulated object
        self.loglist = ImprovedLoglist(time)  # list of logpoints

    def __setattr__(self, attr, val):
        '''This custom __setattr__ method is key to the ImprovedRomancerObject's automatic logging behavior. Unless the attr's name is included in self.unlogged_attrs, any change to that attr is automatically logged in self.loglist.'''
        # check to see if attr is in 'unlogged_attrs'; if so, just got ahead and set it
        if attr in self.unlogged_attrs:
            super().__setattr__(attr, val)
        # check to see if object currently has this attr
        else:
            if hasattr(self, attr):
                # if attr already exists, create AttrSetLog
                logpoint = UniversalLogpoint(time = self.time, difs = tuple([AttrSetLog(attr_name=attr, oldval=getattr(self, attr), newval=val)]))
            else:
                self.repr_list.append(attr)
                # if attr doesn't currently exist, create AttrAdditionLog
                logpoint = UniversalLogpoint(time = self.time, difs = tuple([AttrAdditionLog(attr_name=attr, val=val)]))
                # check to see if this requires truncating loglist
                if self.time < self.loglist.maximum_time():
                    self.loglist.truncate_to_time(self.time)
            self.loglist.append(logpoint)
            super().__setattr__(attr, val)


    def __delattr__(self, attr):
        '''This custom __delattr__ method is key to the ImprovedRomancerObject's automatic logging behavior. Unless the attr's name is included in self.unlogged_attrs, any change to that attr is automatically logged in self.loglist.'''
        # check to see if object currently has this attr
        if hasattr(self, attr):
        # check to see if attr is in 'unlogged_attrs'; if so, just got ahead and remove it
            if attr in self.unlogged_attrs:
                super().__delattr__(attr)
                # if attr currently exists, create AttrRemovalLog
            else:
                logpoint = UniversalLogpoint(time = self.time, difs = tuple([AttrRemovalLog(attr_name=attr, val=getattr(self, attr))]))
                # check to see if this requires truncating loglist
                if self.time < self.loglist.maximum_time():
                    self.loglist.truncate_to_time(self.time)
                self.loglist.append(logpoint)
                self.repr_list.remove(attr)
                super().__delattr__(attr)

        
    def new_message_index(self):
        '''This method is used to obtain unique integer ids for messages.'''
        cur = self.message_index
        self.message_index += 1 # increase message index
        return cur


    def deliver_messages(self, messages):
        '''Place messages in object's inbox.'''
        for message in messages:
            self.inbox.append(message)


    def send_messages(self):
        '''Pass messages from outbox to environment so they can be routed to their appropriate recipients.'''
        self.environment.deliver_messages(self.outbox) # maybe this should send self-addressed messages directly to inbox
        self.outbox.clear()


    def get_children(self):
        '''Many items will have children. This method is supposed to return all children of all subsidiary objects recursively. As this default class has no children, it returns None.'''
        return None


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the object's inbox. Each subclass will need a unique implementation of it. It should return functions with an (obj, message) call signature.'''
        return lambda obj, message: None


    def process_inbox(self):
        '''This method acts on all the messages currently in the inbox using the functions returned by the dispatcher. These functions can alter the state of the object or its children, send one or more messages to various recipients, or simply be ignored.'''
        while len(self.inbox) > 0:
            message = self.inbox.pop()
            f = self.dispatcher(message)
            f(self, message)
        self.send_messages() # send outgoing messages if necessary


    def revert_logpoint(self, logpoint):

        @singledispatch
        def revert_log(log):
            pass # this should raise Exception


        @revert_log.register(AttrSetLog)
        def _(log):
            cur = getattr(self, log.attr_name)
            if cur != log.newval:
                raise ValueError(f'Mismatch between log value {log.newval} and current value {cur}')
            else:
                super(ImprovedRomancerObject, self).__setattr__(log.attr_name, log.oldval)
                

        @revert_log.register(AttrAdditionLog)
        def _(log):
            if not hasattr(self, log.attr_name):
                raise AttributeError('Mismatch between log and current value')
            else:
                self.repr_list.remove(log.attr_name)
                super(ImprovedRomancerObject, self).__delattr__(log.attr_name)


        @revert_log.register(AttrRemovalLog)
        def _(log):
            if hasattr(self, log.attr_name):
                raise AttributeError('Mismatch between log and current value')
            else:
                self.repr_list.append(log.attr_name)
                super(ImprovedRomancerObject, self).__setattr__(log.attr_name, log.val)


        @revert_log.register(CollectionAdditionLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if col.__class__.__name__ == 'LoggedList':
                cur = col.data[-1]
                if cur != log.val:
                    raise ValueError(f'Mismatch between log value {log.val} and current value {cur}')
                else:
                    col.data.pop()
            elif col.__class__.__name__ == 'LoggedSet':
                if not log.val in col.data:
                    raise ValueError(f'Mismatch between log value {log.val} and current values {col.data}')
                else:
                    col.data.remove(log.val)
            else:
                raise ValueError('Cannot revert log: unlogged collection')


        @revert_log.register(CollectionRemovalLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if col.__class__.__name__ == 'LoggedList':
                col.data.append(log.removal)
            elif col.__class__.__name__ == 'LoggedSet':
                if log.removal in col.data: # value is in set when it shouldn't be
                    raise ValueError(f'Mismatch between log value {log.removal} and current values {col.data}')
                else:
                    col.data.add(log.removal)
            else:
                raise ValueError('Cannot revert log: unlogged collection')


        @revert_log.register(CollectionSetItemLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if col.__class__.__name__ == 'LoggedList':
                cur_val = col.data[log.index]
                if cur_val != log.newval:
                    raise ValueError('Mismatch between log and current value')
                else:
                    col.data[log.index] = log.oldval
            else:
                raise ValueError('Cannot revert log: CollectionSetItem only implemented for LoggedList')

        @revert_log.register(CollectionReverseLog)
        def _(log):
            col = getattr(self, log.collectionname)
            col.data.reverse()

        @revert_log.register(DictAdditionLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if not log.keyname in col.data:
                raise KeyError('Expected key not found')
            else:
                if col.data[log.keyname] != log.addition:
                    raise ValueError('Mismatch between log and current value')
                else:
                    col.data.pop(log.keyname)

        
        @revert_log.register(DictRemovalLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if log.keyname in col.data:
                raise KeyError('Unxpected key found')
            else:
                col.data[log.keyname] = log.removal
                

        @revert_log.register(DictSetItemLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if not log.keyname in col.data:
                raise KeyError('Expected key not found')
            elif col.data[log.keyname] != log.newval:
                raise ValueError('Mismatch between log and current value')
            else:
                col.data[log.keyname] = log.oldval
            

        for log in logpoint.difs:
            revert_log(log)
        self.time = logpoint.time
        


    def reassert_logpoint(self, logpoint):

        @singledispatch
        def reassert_log(log):
            pass # should raise Exception


        @reassert_log.register(AttrSetLog)
        def _(log):
            cur = getattr(self, log.attr_name)
            if cur != log.oldval:
                raise ValueError('Mismatch between log and current value')
            else:
                super(ImprovedRomancerObject, self).__setattr__(log.attr_name, log.newval)


        @reassert_log.register(AttrAdditionLog)
        def _(log):
            if hasattr(self, log.attr_name):
                raise AttributeError('Mismatch between log and current value')
            else:
                super().__setattr__(log.attr_name, log.val)


        @reassert_log.register(AttrRemovalLog)
        def _(log):
            if not hasattr(self, log.attr_name) or getattr(self, log.attr_name) != log.val:
                raise AttributeError('Mismatch between log and current value')
            else:
                super().__delattr__(log.attr_name)


        @reassert_log.register(CollectionAdditionLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if col.__class__.__name__ == 'LoggedList':
                cur = col.data[-1]
                if cur != log.addition:
                    raise ValueError('Mismatch between log and current value')         
            elif col.__class__.__name__ == 'LoggedSet':
                if log.addition in col.data:
                    raise ValueError('Mismatch between log and current value')
                else:
                    col.data.add(log.addition)
            else:
                raise ValueError('Cannot revert log: unlogged collection')


        @reassert_log.register(CollectionRemovalLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if col.__class__.__name__ == 'LoggedList':
                cur = col.data[-1]
                if cur != log.removal:
                    raise ValueError('Mismatch between log and current value')
                else:
                    col.data.pop()
            elif col.__class__.__name__ == 'LoggedSet':
                if not log.removal in col.data: # value isn't in set when it should be
                    raise ValueError('Mismatch between log and current value')
                else:
                    col.data.remove(log.removal)
            else:
                raise ValueError('Cannot revert log: unlogged collection')


        @reassert_log.register(CollectionSetItemLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if col.__class__.__name__ == 'LoggedList':
                cur_val = col.data[log.index]
                if cur_val != log.oldval:
                    raise ValueError('Mismatch between log and current value')
                else:
                    col.data[log.index] = log.newval
            else:
                raise ValueError('Cannot reassert log: CollectionSetItem only implemented for LoggedList')

        @reassert_log.register(CollectionReverseLog)
        def _(log):
            col = getattr(self, log.collectionname)
            col.data.reverse()

        @reassert_log.register(DictAdditionLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if col.data.has_key(log.keyname):
                raise KeyError('Unexpected key found')
            else:
                col.data[log.keyname] = log.addition

        
        @reassert_log.register(DictRemovalLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if not col.data.has_key(log.keyname):
                raise KeyError('Expected key not found')
            else:
                col.data.pop(log.removal)


        @reassert_log.register(DictSetItemLog)
        def _(log):
            col = getattr(self, log.collectionname)
            if not col.data.has_key(log.keyname):
                raise KeyError('Expected key not found')
            elif col.data[log.keyname] != log.oldval:
                raise ValueError('Mismatch between log and current value')
            else:
                col.data[log.keyname] = log.newval


        for log in logpoint.difs:
            reassert_log(log)
        self.time = logpoint.time


    def forward_simulation(self, time):
        '''This method should evolve the object's state forward in time, logging changes as logpoints if necessary. Forward simulation can also generate messages.''' 
        if self.time == time:
            pass
        elif self.time > time:
            self.rewind(time)
        else:
            # check if at least some of the desired future times are already stored in loglist
            if self.time < self.loglist.maximum_time():
                reasserts = self.loglist.reassert_list(self.time, time)
                # reassert logpoints if needed
                for logpoint in reasserts:
                    self.reassert_logpoint(logpoint)
            self.time = time
            # create a logpoint that says time has changed
            empty_logpoint = UniversalLogpoint(time, difs=())
            self.loglist.append(empty_logpoint)

            
        
    def rewind(self, time):
        '''This method should use the object's history to revert to its state at time. Uses logpoints in the loglist to reset state back to most recent time before desired time, then uses forward simulation to bring object forward to time.'''
        if self.time == time:
            pass
        elif self.time < time:
            raise RewindError(f"Given time {time} is in the future of time = {self.time}.")
            self.forward_simulation(time) # this should probably throw an error
        else:
            if self.time > self.loglist.minimum_time():
                reverts = self.loglist.revert_list(prev_time=time, cur_time=self.time) # logpoints are returned in reverse order
                for logpoint in reverts:
                    self.revert_logpoint(logpoint)
            self.time = time


    def next_anticipated_disposition_change(self):
        '''This method should use the disposition nodes referenced in self.disposition and other available object state to predict the earliest future time at which the object will leave one of those nodes. Often this information will have been computed already and stored as a logpoint.

        As this base class cannot change state, it returns None.'''
        return None
    

    def __repr__(self):
        '''This method is designed to print representations useful in experimental programming on the repl.'''
        class_name = self.__class__.__name__
        results = {key: self.__getattribute__(key) for key in self.repr_list}
        return f"{class_name}({', '.join([f'{k}={v.__repr__()}' for k,v in results.items()])})"

    def visualise_final(self):
        ''' Right at the end of the scenario, this will get called'''
        pass
    id_counter = 0
