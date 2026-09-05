# from dispositiontree import 1DimensionalDispositionTree
import threading

import numpy as np

from romancer.romancer.supervisor.supervisor import Supervisor


class Environment():
    ENVIRONMENT_ID = 2

    def __init__(self, supervisor, disposition_tree, perception_engine):
        self.inbox = list() # list of messages awaiting processing
        self.outbox = list() # list of messages that have not yet been sent
        self.uid = Environment.ENVIRONMENT_ID
        self.time = 0 # supervisor initializes to simulation time of 0
        self.supervisor = supervisor
        self.message_index = 1 # increments with each message to assign unique ids
        self.disposition_tree = disposition_tree
        self.perception_engine = perception_engine
        self.agents = list() # collection of objects (not  necessarily toplevel) in environment that possess agency
        self.contents = list() # collection of toplevel items in the simulated environment
        # As near as I can tell, the supervisor is assigned and ID of 1 and the environment has this ID of 2
        # I would strongly recommend creating a constant `SUPERVISOR_ID = 1` and using that around the code
        # rather than checking for a hard coded constant everywhere.
        self.object_count = 2 # used to assign ids to new objects
        self.message_dispatch_table = dict() # dict used to map object ids to references--used for delivering messages
        self.dispatch_table = {} # dict of functions for processing messages
        self.graveyard = list() # respository for items that have been removed from environment; used for reconstructing simulation history

        self.matplotlib_lock = threading.RLock() # Matplotlib is exceptionally stateful, which causes problems when threading.
        

    def new_message_index(self):
        '''This method is used to obtain unique integer ids for messages.'''
        cur = self.message_index
        self.message_index += 1 # increase message index
        return cur


    def new_object_index(self):
        '''This method produces unique integer ids for registering objects.'''
        self.object_count += 1
        return self.object_count

    
    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the environment's inbox. Each subclass will need a unique implementation of it. It should return functions with an (obj, message) call signature.'''
        return lambda obj, message: None


    def deliver_messages(self, messages):
        '''Place messages in the inbox of the addressed recipient objects.'''
        for message in messages:
            if message.recipient == (self.uid, self.uid): # self-addressed
                self.inbox.append(message)
            elif message.recipient[0] == self.supervisor.uid:
                self.supervisor.inbox.append(message)
            elif message.recipient == (self.uid, 0): # (environment.uid, 0)--address to broadcast message to all objects and agents in environment
                self.forward_to_all(messages)
            else: # all other messages
                self.message_dispatch_table[message.recipient[0]].inbox.append(message)

                
    def send_messages(self, messages):
        '''Send the messages in the environment's outbox to their intended recipients. Note that this does not cause either the supervisor or the environment to process any of those messages.'''
        for message in self.outbox:
            if message.recipient == (self.uid, self.uid): # self-addressed
                self.inbox.append(message)
            else:
                self.environment.append(message) # send message to environment for forwarding
        self.outbox.clear()


    # def deliver_all_messages(self):
    #     '''Recurse through the contents of the environment and deliver the messages in outbox of every subsidiary object to their intended recipients.'''

    #     def deliver_all_messages_inner(obj):
    #         self.deliver_messages(obj.outbox)
    #         obj.outbox.clear()
    #         for child in obj.contents:
    #             deliver_all_messages_inner(obj)

    #     deliver_all_messages_inner(self)
        

    def register_object(self, obj):
        '''Assign an object a unique uid and associate it with that uid in the message dispatch table. Not that this method does not set the disposition of the object--this is because some objects will lack dispositions.'''
        new_id = self.new_object_index()
        obj.uid = new_id
        self.message_dispatch_table[new_id] = obj
        return new_id


    def add_object(self, obj, parent_object=None):
        '''The purpose of this method is to place the object in its correct place in the heirarchical representation in Environment.contents as well as in the relevant disposition tree(s).'''
        if parent_object:
            parent_object.children.append(obj)
            obj.parent = parent_object
        else:
            self.contents.append(obj)
        self.disposition_tree.set_disposition(obj, obj.location, obj.resolution) 


    def add_agent(self, agent, parent_object=None):
        '''This agent places the agent object in the Environment's list of agents as well as registers it as an object.'''
        self.agents.append(agent) # add agent to agents list
        self.add_object(agent, parent_object) # agents are also objects


    def remove_object(self, obj):
        '''Remove an object from the Environment and delete its uid from the message dispatch table. Send object to environment graveyard.'''
        parent = getattr(obj, 'parent', None)
        if parent:
            parent.contents.remove(obj)
        else:
            self.contents.remove(obj)
        # self.disposition_tree.remove(obj) # need to implement remove method for disposition tree--define API for this
        self.message_dispatch_table[obj.uid] = None
        self.graveyard.append(obj)


    def remove_agent(self, agent):
        '''Remove an agent from the Environment and delete its uid from the message dispatch table.'''
        self.agents.remove(agent)
        self.remove_object(agent)
        self.graveyard.append(agent)

    def finalise(self):
        '''Called at the end to do anything that needs doing'''
        for agent in self.agents:
            agent.visualise_final()
        
