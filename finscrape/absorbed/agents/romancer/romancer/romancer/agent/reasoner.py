from romancer.environment.object import ImprovedRomancerObject

class Reasoner(ImprovedRomancerObject):

    '''While the Amygdala object is supposed to represent the neuroendocrine and limbic systems, the Reasoner is supposed to represent the neocortex. Reasoner implementations can work in arbitrary ways so long as they conform to the correct API. this primarily consists of its deliberate method. Reasoner instances also need to be associated with a PerceptionFilter that may be part of or associated with the Reasoner (for instance, storing a reference to the Reasoner in a lexical closure).

    The Reasoner can use the Amygdala to adjust its cognitive strategies. For  example, the current Amygdala.pbf value can be used to determine a 'cognitive budget'. If this cognitive budget falls below a particular threshold, the Reasoner may simply match present Amygdala values to return a possibly maladaptive instinctual response (e.g., fight, flight, or freeze).'''

    def __init__(self, environment, time):
        super().__init__(environment, time)
        # Note that self.next_deliberate_action is likely to be reset regularly, often by the PerceptionFilter because it detects new stimuli that may change future planned actions
        # the Reasoner's forward_simulation method can take care of keeping these values updated


    def forward_simulation(self, time, amygdala=None):
        # bring amygdala up to time
        if amygdala:
            amygdala.forward_simulation(time)
        super().forward_simulation(time)
        # pass if time is current
        # if self.time == time:
        #     pass
        # # rewind if time is in the past
        # elif self.time > time:
        #     self.rewind(time)
        # # if some or all anticipated future is precalculated and in loglist reassert precomputed history
        # else:
        #     # check if at least some of the desired future times are already stored in loglist
        #     if self.time < self.loglist.maximum_time():
        #         reasserts = self.loglist.reassert_list(self.time, time)
        #         # reassert logpoints if needed
        #         for logpoint in reasserts:
        #             self.reassert_logpoint(logpoint)
        #     # simulate new future cognition here, if necessary
        #     self.time = time
        
    
    def deliberate(self, max_time, amygdala):
        '''This method is the main interface to the Reasoner. When it is called, the Reasoner simulates its anticipated evolution out to max_time, presuming no additional external stimuli. This simulation need not be comprehensive and can stop at the moment where the agent plans to take its next deliberate action. The Reasoner does not take this next deliberate action or send messages about it, as this is supposed to be done by the PersonLikeAgent's next_deliberate_action and/or next_deterministic_action dispatch functions. The reason for this separation is so that other parts of the Agent, such as the Amygdala, can potentially preempt the Reasoner. Those functions can use information stored in the Reasoner (e.g. its loglist) after calling the Reasoner's deliberate() method. SInce dliberation is likely to be relatively computationally intensive, it may be desirable to cache the next anticipated action in a readily retrievable way, as done by this notional implementation. The max_time parameter is useful for iteratively deepening search for the next deliberate action, as necessary.'''
        if self.next_deliberate_action_time and self.next_deliberate_action_time < max_time:
            pass # no deliberation needed
        else:
            cur_time = self.time
            self.forward_simulation(cur_time, amygdala) # amygdala needs to be passed as well as the future histories evolve jointly
            # self.rewind(cur_time)


    @property
    def next_deliberate_action(self):
        '''This returns the next deliberate action, which for the nulle default reasoner is always empty.'''
        return None


    @property
    def next_deliberate_action_time(self):
        '''This returns the time of the next deliberate action, which for the nulle default reasoner is always empty.'''
        return None
    
