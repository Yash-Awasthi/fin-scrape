from romancer.environment.percept import Percept
from operator import ne

def make_observer(obj, attr, value):
    '''This function provides an example of how to generate observers: functions that take no arguments that use current state to determine whether to generate a Percept object that is then passed to agents. This simple observer simply checks if a specific attribute of the object has a particular value and generates a Percept if so.'''

    def observer():
        if getattr(obj, attr) == value:
            return Percept(uid=obj.uid, attr=attr, value=value)
        
    return observer


def make_change_observer(obj, attr, percept_class=Percept):
    '''This function makes an observer that produces a Percept if a particular attribute has changed since the last time it was run.'''

    val = getattr(obj, attr)

    def change_observer():
        nonlocal val
        cur_val = getattr(obj, attr)
        if val != cur_val:
            percept = percept_class(uid=obj.uid, attr=attr, val=val, new_val=cur_val, time=obj.time)
        else:
            return None
        val = cur_val
        return percept

    return change_observer


def make_threshold_rate_observer(obj, attr, threshold_rate):
    '''This function makes an observer that produces a Percept if a particular attribute has changed since the last time it was run at a rate exceeding a particular threshhold rate. Note that this observer will only work correctly on a scalar attribute.'''
    
    val_time = obj.time
    val = get(obj, attr)

    def threshold_rate_observer():
        delta_t = obj.time - val_time
        cur_val = get(obj, attr)
        delta_v = cur_val - val
        rate = delta_v / delta_t
        if rate >  threshold_rate:
            percept = Percept(uid=obj.uid, attr=attr, val=val, new_val=new_va, rate=rate, threshhold_rate=threshhold_rate)
        else:
            percept = None
        val.time = obj.time
        val = cur_val
        return percept

    return threshold_rate_observer

# Possibly make observers that capture attribute of both an agent's ontology and the outside environment--e.g., that fire when some aspect of the external environment is different than an agent expects


def make_surprise_observer(obj1, attr1, obj2, attr2, test_fn = ne):

    def surprise_observer():
        if test_fn(get(obj1, attr1), get(obj1, attr1)):
            return Percept(uid=obj1.uid, attr1=attr1)

    return surprise_observer
    
class PerceptionEngine():
    '''The purpose of the perception engine is to generate percepts that are sent to agents based on the state of the simulated environment.

    Future iterations of the perception engine may add features such as mechanisms to calculate which subset of the observers is potentially relevant and run only that subset, rather than simply running all of them as this initial version does.'''
    
    def __init__(self, environment=None):
        self.environment = environment # used to access environmental state if necessary
        self.observers = dict() # a dictionary in which the keys are the uids of agents and the vaules are lists of observers (callables)

        
    def run(self, **kwargs): # kwargs accounts for addition of future functionality 
        new_percepts = dict()
        for agent in self.observers.keys():
            agent_percepts = list()
            for observer in self.observers[agent]:
                possible_percept = observer()
                if possible_percept:
                    agent_percepts.append(possible_percept)
            if len(agent_percepts) > 0:
                new_percepts[agent] = agent_percepts
        return new_percepts


    def add_observer(self, agent_id, observer):
        if self.observers.get(agent_id, None):
            self.observers[agent_id].append(observer)
        else:
            self.observers[agent_id] = list()
            self.observers[agent_id].append(observer)


    def remove_observer(self, agent_id, observer):
        if observer in self.observers[agent_id]:
            self.observers[agent_id].remove(observer)
        else:
            raise ValueError("Observer not found in perception engine: ", observer)


    
