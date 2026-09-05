from romancer.supervisor.watchlist import Watchlist
import numpy as np
import time

class Supervisor():
    '''This base class defines the interface that implementations of the supervisor should follow.'''
    SUPERVISOR_ID = 1

    def __init__(self, environment=None, random_seed=12345, time_cb=None):
        self.rng = np.random.default_rng(random_seed) # random number generator permits reproducible model runs
        self.environment = environment
        self.time_cb = time_cb  # a callback to call anytime the time changes
        self.inbox = list() # list of messages awaiting processing
        self.outbox = list() # list of messages that have not yet been sent
        self.uid = Supervisor.SUPERVISOR_ID # supervisor always has id of 1
        self.time = 0 # supervisor initializes to simulation time of 0
        self.watchlist = Watchlist()
        self.message_index = 1 # increments with each message to assign unique ids
        self.logger = lambda s: None # function used to write logfile, if desired


    def bring_watchlist_up_to_date(self):
        '''This method ensures that the lead item on the watchlist is in fact the next one that should be executed. It should work by checking the simulated time of the lead item on the watchlist and then asking relevant objects in the environment (agents, etc.) whether they will or might cause an event of interest in that timeframe.'''
        next_time = self.watchlist.peek.time
        if self.environment.time == next_time: # no opportunity for next event not to be correct
            return None 
        # STEP 1
        self.outbox.append('message deterministic event between self.time and next_time:') # send message to environment telling it to identify soonest deterministic event (if any) between self.time and next_time
        # deterministic events are, for example, disposition changes based on current trajectories
        self.send_messages()
        self.environment.process_inbox() # environment generates events
        self.environment.send_messages() # environments sends resulting events back to supervisor
        # Check messages received from children of environment and set next_time to that of the next deterministic event, if it is eceived
        # STEP 2
        self.outbox.append('message possible stochastic events between self.time and next_time') # send message to environment telling it to identify possible stochastic events between self.time and next_time
        self.environment.process_inbox() # envioronment generates events
        self.environment.send_messages() # environments sends resulting events back to supervisor
        # sort possible stochastic events by time from soonest to last
        # process possible events and determine using their probability and self.rng whether they become a deterministic event
        # if deterministic event is added to watchlist, set next_time to the time of that event; break
        # if full list is processed without a stochastic event being promoted to a deterministic event, push the soonest deterministic event onto the watchlist
        self.environment.forward_simulation(next_time) # make sure environment state is advanced to t = next_time


    def process_next_watchlist_item(self):
        '''This method processes the next item on the watchlist. It assumes that the watchlist is up to date and that enviornment state is synchronized to the same time as that event.'''
        item = self.watchlist.peek()
        item.process(self) # run code associated with WatchlistItem; this can cause arbitrary changes to environment and supervisor state
        self.logger(self.watchlist.pop()) # pop the just-processed item off of the watchlist and log it if desired
        # if processing item has resulted in environment state changes that could maken events currently in watchlist impossible, remove or edit those items--these state changes should result in messages sent to supervisor inbox
        self.process_inbox() # calls methods that clean up watchlist to remove items depending on dispositions that no longer exist, and possibly to add some that are now possible
        # check for contradictions in environment, if necessary, and fix them if possible--hopefully not necessary when using single thread?
        # PERHAPS BREAK THIS INTO DISTINCT METHOD?
        new_percepts = self.environment.perception_engine.run() # check to see if processing the event resulted in percept generation
        # Percepts can be arbitarily complex objects that stay in the environment--not immuntable or hashable
        if new_percepts: # if there are new percepts, these  may result in cogitation leading to future actions
            for percept in new_percepts:
                agent = percept.agent
                self.environment.deliver_messages(['message to agent: return time of its next intended action based on current percepts']) # presuming no additional messages, when will agent act next?
            self.environment.process_inbox() # environment runs agent simulations as necessary based on delivered messages
            self.process_inbox() # the methods invoked by the referred messages should result in new watchlist items
            # These watchlist items can either be added by deleting previous intended actions from the watchlist and pushing new ones, or by editing existing ones in place
            # For the initial implementation it's probably better to just find and remove existing actions and regenerate Watchlist items, even if this is duplicitive
        
        
    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the supervisor's inbox. Each subclass will need a unique implementation of it. It should return functions with an (obj, message) call signature.'''
        return lambda obj, message: None


    def deliver_messages(self, messages):
        '''Place messages in supervisor's inbox. This method should be called by the environment and agents, primarily.'''
        if not isinstance(messages, list):
            messages = [messages]
        for message in messages:
            self.inbox.append(message)


    def send_messages(self):
        '''Send the messages in the supervisor's outbox to their intended recipients. Note that this does not cause either the supervisor or the environment to process any of those messages.'''
        for message in self.outbox:
            if recipient[0] == self.uid: # self-addressed
                self.inbox.append(message)
            else:
                self.environment.inbox.append(message) # send message to environment for forwarding
                # Tell environment to send messages?


    def new_message_index(self):
        '''This method is used to obtain unique integer ids for messages.'''
        cur = self.message_index
        self.message_index += 1 # increase message index
        return cur


    def process_inbox(self):
        '''This method acts on all the messages currently in the inbox using the functions returned by the dispatcher. These functions can alter the state of the object or its children, send one or more messages to various recipients, or simply be ignored.'''
        # It may be desirable to include some sort of sorting and/or pruning mechanism here--possibly check for presence of certain messages and sort/prune accordingly?
        while len(self.inbox) > 0:
            message = self.inbox.pop()
            f = self.dispatcher(message)
            f(self, message)
        self.send_messages() # send outgoing messages if necessary


    def run(self):
        while len(self.watchlist) > 0: # loop as long as watchlist items remain
            if self.time_cb is not None:
                self.time_cb(self.environment.time)
            time.sleep(0.0) # Threading yield
            self.process_inbox() # carry out housekeeping tasks if necessary
            self.bring_watchlist_up_to_date() # ensure current head of watchlist is actual next event
            self.process_inbox() # carry out housekeeping tasks if necessary
            self.process_next_watchlist_item() # process next watchlist event
        if self.time_cb is not None:
            self.time_cb(None)
