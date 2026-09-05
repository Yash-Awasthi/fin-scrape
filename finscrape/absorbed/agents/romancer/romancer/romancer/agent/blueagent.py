from romancer.agent.agent import Agent, PerceptionFilter, ActionROMANCERMessage
from romancer.environment.percept import Percept
from romancer.environment.loglist import Logpoint

# The purpose of this file is to define the Blue Agent, the percepts that it can receive, and the actions that it can take

class PerceiveRedLightOn(Percept):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            getattr(self, 'time')
        except AttributeError:
            print('RedLightOn requires time attribute.')


class BlueAgentPerceptionFilter(PerceptionFilter):
    '''This perception filter converts percepts into possible changes in the red agent's internal state.'''

    def digest_percept(self, percept):
        if not isinstance(percept, (PerceiveRedLightOn)):
            raise TypeError('Percept not recognized by perception engine')
        else:
            # alter blue agent's internal state based on believing red light is on
            if not self.agent.red_light_on:
                self.agent.red_light_on = True
                self.agent.most_recent_percept_time = percept.time
                self.agent.intended_ecm_activation_time = self.agent.most_recent_percept_time + 20 # twenty seconds to make up mind to turn on ecms
                new_logpoint = BlueAgentLogpoint(time=self.agent.time, red_light_on=self.agent.red_light_on, ecm=self.agent.ecm, intended_ecm_activation_time=self.agent.intended_ecm_activation_time)
                self.agent.loglist.append(new_logpoint)


class BlueAgentLogpoint(Logpoint):
    '''Since this agent implementation is quite simple internally, it can use logpoints that document all of the egent's internal state with the exception of the loglist itself.'''

    def __init__(self, time, red_light_on, ecm, intended_ecm_activation_time):
        super().__init__(time=time)
        self.red_light_on = red_light_on
        self.ecm = ecm
        self.intended_ecm_activation_time = intended_ecm_activation_time


    def __repr__(self):
        return 'BlueAgentLogpoint(time={}, red_light_on={}, intended_ecm_activation_time={})'.format(self.time, self.red_light_on, self.intended_ecm_activation_time)


def blue_agent_deterministic_actions_before_time(o, m):
    '''As this agent's only possible deterministic actions are deliberate, this function simply calls blue_agent_next_deliberate_action.'''
    blue_agent_next_deliberate_action(o, m)


def blue_agent_stochastic_actions_before_time(o, m):
    '''This function could account for erratic behavior by the blue agent, such as activating the ecms on a whim. In this initial version, however, the blue agent only makes deliberate, planned actions.'''
    pass


def blue_agent_next_deliberate_action(o, m):
    '''If the blue agent believes that their plane has been detected by adversary radar, they may plan to activate the ECMs at some definite point in the future (possibly immediately).'''
    if not o.ecm and o.intended_ecm_activation_time:
        if o.most_recent_percept_time:
            last_percept_time = o.most_recent_percept_time
        else:
            last_percept_time = -1.0
        new_message = ActionROMANCERMessage(uid=o.new_message_index, sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptActivateECM', action='activate ecm', time=o.intended_ecm_activation_time, most_recent_percept_time=last_percept_time)
        o.outbox.append(new_message)


class BlueAgent(Agent):

    def __init__(self, environment, time, perception_filter, ecm, red_light_on=False, intended_ecm_activation_time=None):
        super().__init__(environment, time, perception_filter)
        self.ecm = ecm # does blue agent believe that ecm is on?
        self.red_light_on = red_light_on # does blue agent believe that the red light is on?
        self.intended_ecm_activation_time = intended_ecm_activation_time # does blue agent intend to activate ecm, and if so, when?
        self.repr_list = self.repr_list + ['ecm', 'red_light_on']
        initial_logpoint = BlueAgentLogpoint(time=self.time, red_light_on=self.red_light_on, ecm=self.ecm, intended_ecm_activation_time=self.intended_ecm_activation_time)
        self.loglist.append(initial_logpoint)
        self.dispatch_table = {'DeterministicActionsBeforeTime': blue_agent_deterministic_actions_before_time,
                               'StochasticActionsBeforeTime': blue_agent_stochastic_actions_before_time,
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                               'NextDeliberateAction': blue_agent_next_deliberate_action
                               }


    def rewind(self, time):
        '''This method uses the loglist to rewind the state of the red agent to what it was at time.'''
        if self.time == time:
            pass
        low, high = self.loglist.temporal_bounds()
        if low <= time:
            self.loglist.truncate_to_time(time)
            latest = self.loglist[-1]
            self.time = latest.time
            self.red_light_on = latest.red_light_on
            self.ecm = latest.ecm
            self.forward_simulation(time)


    def deliberate(self, max_time):
        '''This method is called by the supervisor to tell the red agent to plan out its future actions and underlying mental state based upon the percepts it has received as of the current time. These planned actions are used to bound future simulation times.'''
        if self.time >= max_time: # this shouldn't happen in regular use
            pass
        else:
            cur_time = self.time
            # self.forward_simulation(max_time)
            # if blue agent believes red light is on
            if self.red_light_on and not self.ecm:
                deliberation_time = 3.0 # 3 seconds to make up mind
                self.ecm = cur_time + deliberation_time
            # possibly set/update self.intended_ecm_activation_time
            # if a new intended ecm activation time is generated, send message to supervisor reflecting it
            # self.rewind(cur_time)


    @property
    def location(self):
        '''The pilot is treated as part of the plane, so their location is the same as that of the plane.'''
        return self.parent.location
    

    @property
    def resolution(self):
        '''The pilot is treated as part of the plane, so their resolution is the same as that of the plane.'''
        return self.parent.resolution


    def believes_ecm_activated(self):
        '''Log that the agent believes that the ecm is now on.'''
        self.ecm = True
        new_logpoint = BlueAgentLogpoint(time=self.time, red_light_on=self.red_light_on, ecm=self.ecm, intended_ecm_activation_time=self.intended_ecm_activation_time)
        self.loglist.append(new_logpoint)


    def believes_ecm_deactivated(self):
        '''Log that the agent believes that the ecm is now off.'''
        self.ecm = false
        new_logpoint = BlueAgentLogpoint(time=self.time, red_light_on=self.red_light_on, ecm=self.ecm, intended_ecm_activation_time=self.intended_ecm_activation_time)
        self.loglist.append(new_logpoint)
