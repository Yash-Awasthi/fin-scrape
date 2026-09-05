from romancer.environment.object import ImprovedRomancerObject, LoggedList, LoggedSet, LoggedDict
from romancer.agent.personlikeagent import PersonLikeAgent, PersonlikeActionROMANCERMessage
from romancer.environment.location import StationaryGeographicLocation

    
def next_deterministic_action(o, m):
    '''This method sends a message to the supervisor indicating the time of the next deterministic action that the agent will take. This can be an arbitrary action. The PersonLikeAgent might invoke either its reasoner or amygdala to determine this action, but it can also represent non-cognitive processes associated with the "person."'''
    next_deliberate_action(o, m)


def next_deliberate_action(o, m):
    '''The purpose of this method is to determine whether the agent plans to execute a deliberate action before a maximum time. Deliberate actions are always deterministic, but deterministic actions are not necessarily deliberate. For example, some agents can move just as vehicles can, and some of those movements can be deterministic from a simulation standpoint while not being deliberate. E.g., if an agent represents a falling person, their physical shift to a different disposition as they fell would be deterministic (in that it can be predicted to occur ast a specific future time) but not deliberate in that the agent may not have planned to fall and may not be aware it is falling. The PersonLikeAgent might invoke either its reasoner or amygdala to determine this action.'''
    next_action_time = o.reasoner.next_deliberate_action_time
    if not next_action_time or next_action_time > m.time:
        return None
    else:
        action = o.reasoner.next_deliberate_action
        message = PersonlikeActionROMANCERMessage(uid=o.new_message_index, sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='PersonlikeActionROMANCERMessage', actions=tuple(action), time=next_action_time, most_recent_percept_time=o.most_recent_percept_time)
        o.outbox.append(message)
    

class EscalationLadderAgent(PersonLikeAgent):
    '''
    '''

    def __init__(self, environment, time, perception_filter, amygdala, reasoner, location = StationaryGeographicLocation(latitude = 0.0, longitude = 0.0, bearing=0.0), name = None):
        super().__init__(environment, time, perception_filter, amygdala, reasoner, location, name)
        self.dispatch_table = LoggedDict({'DeterministicActionsBeforeTime': next_deterministic_action, 
                                          'StochasticActionsBeforeTime': lambda o, m: None,
                                          'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                                          'NextDeliberateAction': next_deliberate_action,
                                          'UpdateAmygdalaParameters': lambda o, m: o.amygdala.update_parameters(m)}, parent = self, varname = 'dispatch_table')

    def visualise_final(self):
        super().visualise_final()
