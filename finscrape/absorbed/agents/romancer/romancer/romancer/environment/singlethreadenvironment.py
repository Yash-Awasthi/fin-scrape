from romancer.environment.environment import Environment
from typing import NamedTuple


class TemporalROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    time: float # simulation time
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)


    
class SingleThreadEnvironment(Environment):

    def __init__(self, supervisor, disposition_tree, perception_engine):
        super().__init__(supervisor, disposition_tree, perception_engine)
        self.dispatch_table = {'DeterministicActionsBeforeTime': lambda o, m: o.deterministic_events_before_time(m.time),
                               'StochasticActionsBeforeTime': lambda o, m: o.stochastic_events_before_time(m.time),
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                               } # dict of functions for processing messages


    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the environment's inbox. It should return functions with an (obj, message) call signature. Raises an exception if no appropriate dispatch function is found.'''
        try:
            f = self.dispatch_table.get(message.messagetype)
        except KeyError:
            print('No dispatch found for message type:', message.messagetype)
        finally:
            return f


    def forward_simulation(self, time):
        '''Run forward simulation on all objects in the environment by recurising through the heirarchical representation. Objects with children are expected to advance the forward simulation of thise child items as part of their forward_simulation() method.'''
        if self.time == time:
            return None
        else:
            for item in self.contents:
                item.forward_simulation(time)
            self.time = time


    def process_all_inboxes(self):
        
        def process_all_inboxes_inner(o):
            o.process_inbox()
            # o.send_messages() # pass messages from object to environment
            self.deliver_messages(self.outbox) # forward objects either to objects in environment or to supervisor
            self.outbox.clear()
            try:
                children = o.children
            except AttributeError:
                children = []
            finally:
                for child in children:
                    process_all_inboxes_inner(child)
            
        for item in self.contents:
            process_all_inboxes_inner(item)
            

    def forward_to_all(self, messages):
        '''Send messages to every object in the envionment.'''

        def forward_to_all_inner(o):
            o.deliver_messages(messages)
            try:
                children = o.children
            except AttributeError:
                children = []
            finally:
                for child in children:
                    forward_to_all_inner(child)

        for item in self.contents:
            forward_to_all_inner(item)

        
    def deterministic_events_before_time(self, next_time):
        # (environment.uid, 0)--address to broadcast message to all objects and agents in environment
        message = TemporalROMANCERMessage(uid=self.new_message_index(), sender=(self.uid, self.uid), recipient=(self.uid, 0), messagetype='DeterministicActionsBeforeTime', time=next_time)
        self.forward_to_all([message])
        self.process_all_inboxes()


    def stochastic_events_before_time(self, next_time):
        # In principle, the environment *itself* may be a source of stochastic events, but in this implementation we assume that those events only emerge from objects within the environment
        # (environment.uid, 0)--address to broadcast message to all objects and agents in environment
        message = TemporalROMANCERMessage(uid=self.new_message_index(), sender=(self.uid, self.uid), recipient=(self.uid, 0), messagetype='StochasticActionsBeforeTime', time=next_time)
        self.forward_to_all([message])
        self.process_all_inboxes()
        

    def perceive_and_deliberate(self, max_time):
        '''This method runs the perception engine and tells those agents that receive percepts to assess whether they will take deliberate actions before the next predicted event time.'''
        percepts = self.perception_engine.run()
        for uid, agent_percepts in percepts.items():
            agent = self.message_dispatch_table[uid]
            for p in agent_percepts:
                agent.perception_filter.digest_percept(p)
            agent.deliberate(max_time)
             

    


    
