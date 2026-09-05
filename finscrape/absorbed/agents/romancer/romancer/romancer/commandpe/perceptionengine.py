from romancer.environment.perceptionengine import PerceptionEngine
from romancer.environment.percept import Percept
from romancer.agent.agent import PerceptionFilter
from numpy import inf


class CommandPEPercept(Percept):
    '''The CommandPEPercept is supposed to contain a refined version of the events_list returned by the CommandPEReader, e.g.:

    CommandPEPercept(events_list = [{'event_type': 'fired', 'weapon': '1', 'target': '1', 'count': 1}, {'event_type': 'hit', 'weapon': '4', 'target': '3', 'count': 2}])
    This class can be used to store methods for use by the EscalationLadderReasoner and other reasoners.'''

    @property
    def hit_count(self):
        count = 0
        for event in self.events_list:
            if event['event_type'] == 'hit':
                count +=1
        return count
            

    @property
    def fired_count(self):
        count = 0
        for event in self.events_list:
            if event['event_type'] == 'fired':
                count +=1
        return count


    def weighted_hits(self):
        weighted_count = 0
        for event in self.events_list:
            if event['event_type'] == 'hit':
                weighted_count += event['weapon'] * event['target']
        return weighted_count


    def weighted_fired(self):
        weighted_count = 0
        for event in self.events_list:
            if event['event_type'] == 'fired':
                weighted_count += event['weapon'] * event['target']
        return weighted_count
    

class CommandPEPerceptionEngine(PerceptionEngine):
    '''Theis PerceptionFIlter is designed not just to force percepts genetated from CommandPE or AFSIM output files, but to also coexist with percepts originating from a parallel ROMANCER simulation.'''

    def __init__(self, environment=None):
        super().__init__(environment)
        self.queued_percepts = dict() # {agent_id: [percept_list]}
        self.queued_percepts_time = inf


    def run(self, **kwargs):
        observer_percepts = super().run() # in default case where there are no observers, returns an empty dict
        # check to see if it is time for currently queued percepts
        if self.environment.time == self.queued_percepts_time: # I don't think this should ever happen under normal circumstances but we should check to be safe
            for key in self.queued_percepts.keys():
                # if it is, add queued percepts to observer_percepts
                if key in observer_percepts:
                    observer_percepts[key] += self.queued_percepts[key]
                else:
                    observer_percepts[key] = self.queued_percepts[key]
                    # now we clear the queued percepts for each key (agent_id)
                    self.queued_percepts[key] = []
        return observer_percepts
        

    def force_percept(self, time, events_list, agent_id, event_keys = ['event_type', 'weapon', 'target']):
        '''This is the key method on CommandPEPerceptionEngine. It takes an events_list stored in the WatchlistItem and converts it into one or more CommandPEPercepts that are stored in queued_percepts. When the CommandPEPerceptionEngine is run, those queued percepts are sent to the agent(s) perception filters.'''
        refined_events_list = list()
        for event in events_list:
            event_dict = dict()
            for k in event_keys:
                event_dict.update({k: getattr(event, k)})
            refined_events_list.append(event_dict)
        percept = CommandPEPercept(events_list = refined_events_list)
        if agent_id in self.queued_percepts:
            self.queued_percepts[agent_id] += [percept]
        else:
            self.queued_percepts[agent_id] = [percept]
        self.queued_percepts_time = time
           

class CommandPEPerceptionFilter(PerceptionFilter):
    '''The CommandPEPerceptioFilter is intended to be used in conjunction with a PersonLikeAgent.'''

    def digest_percept(self, percept):
        '''This method assumes a CommandPEPercept.'''
        cur_params = self.agent.amygdala.current_amygdala_parameters()
        updated_percept = CommandPEPercept(events_list = percept.events_list, amygdala_params = cur_params)
        self.agent.reasoner.enqueue_digested_percept(percept, self.agent.time)
