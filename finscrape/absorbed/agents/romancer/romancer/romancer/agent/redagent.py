from romancer.agent.agent import Agent, PerceptionFilter, ActionROMANCERMessage
from romancer.environment.percept import Percept
from romancer.environment.loglist import Logpoint
from romancer.radar import ProbabilisticROMANCERMessage

# The purpose of this file is to define the Red Agent, the percepts that it can receive, and the actions that it can take

class BlipOnRadarScreen(Percept):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            getattr(self, 'time')
        except AttributeError:
            print('BlipOnRadarScreen requires time attribute.')
            

class RedAgentPerceptionFilter(PerceptionFilter):
    '''This perception filter converts percepts into possible changes in the red agent's internal state.'''

    def digest_percept(self, percept):
        if not isinstance(percept, (BlipOnRadarScreen)):
            raise TypeError('Percept not recognized by perception engine')
        else:
            # alter red agent's internal state based on the additional radar blip
            self.agent.blip_count += 1
            self.agent.most_recent_percept_time = percept.time
            new_logpoint = RedAgentLogpoint(time=self.agent.time, intended_radar_activation_time=self.agent.intended_radar_activation_time, blip_count=self.agent.blip_count, believed_radar_state=self.agent.believed_radar_state)
            self.agent.loglist.append(new_logpoint)


class RedAgentLogpoint(Logpoint):
    '''Since this agent implementation is quite simple internally, it can use logpoints that document all of the egent's internal state with the exception of the loglist itself.'''

    def __init__(self, time, intended_radar_activation_time, blip_count, believed_radar_state=False):
        super().__init__(time=time)
        self.intended_radar_activation_time = intended_radar_activation_time
        self.blip_count = blip_count
        self.believed_radar_state = believed_radar_state


    def __repr__(self):
        return 'RedAgentLogpoint(time={}, intended_radar_activation_time={}, blip_count={}, believed_radar_state={})'.format(self.time, self.intended_radar_activation_time, self.blip_count, self.believed_radar_state)


def red_agent_deterministic_actions_before_time(o, m):
    '''As this agent's only possible deterministic actions are deliberate, this function simply calls red_agent_next_deliberate_action.'''
    red_agent_next_deliberate_action(o, m)


def red_agent_stochastic_actions_before_time(o, m):
    '''This function could account for random behavior by the red agent--for example, turning on the radar before the appointed time on a whim. For the initial demo, however, its sole purpose is to possibly attempt to report a possible attack from Blue based on the number of radar blips the Red Agent has perceived.'''
    delta_t = 7.0 # 7 second detection interval
    times = [o.time + delta_t * i for i in range(1, int((m.time - o.time) / delta_t) + 1)]
    # print(times)
    reporting_probability = min(o.blip_count / 50.0, 1.0)
    for t in times:
            message = ProbabilisticROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptContactSuperior', time=t, probability=reporting_probability)
            o.outbox.append(message)


def red_agent_next_deliberate_action(o, m):
    '''The red agent plans to activate the radar at a certain time. If the agent believes that the radar is off, it plans to activate the radar at that time.'''
    if m.time > o.intended_radar_activation_time and o.believed_radar_state == False:
        if o.most_recent_percept_time:
            last_percept_time = o.most_recent_percept_time
        else:
            last_percept_time = -1.0
        new_message = ActionROMANCERMessage(uid=o.new_message_index(), sender=(o.environment.uid, o.uid), recipient=(1, 1), messagetype='AttemptActivateRadar', action='activate radar', time=o.intended_radar_activation_time, most_recent_percept_time=last_percept_time)
        o.believed_radar_state = True
        new_logpoint = RedAgentLogpoint(time=o.time, intended_radar_activation_time=o.intended_radar_activation_time, blip_count=o.blip_count, believed_radar_state=o.believed_radar_state)
        o.loglist.append(new_logpoint)
        o.outbox.append(new_message)
    

class RedAgent(Agent):

    def __init__(self, environment, time, perception_filter, intended_radar_activation_time, blip_count, believed_radar_state=False):
        super().__init__(environment, time, perception_filter)
        self.intended_radar_activation_time = intended_radar_activation_time # planned time to activate radar
        self.believed_radar_state = believed_radar_state # state that agent believes radar is in (may not be correct)
        self.blip_count = blip_count # number of radar screen blips that the agent has perceived
        self.repr_list = self.repr_list + ['intended_radar_activation_time', 'believed_radar_state']
        initial_logpoint = RedAgentLogpoint(time=self.time, intended_radar_activation_time=self.intended_radar_activation_time, blip_count=self.blip_count, believed_radar_state=self.believed_radar_state)
        self.loglist.append(initial_logpoint)
        self.dispatch_table = {'DeterministicActionsBeforeTime': red_agent_deterministic_actions_before_time,
                               'StochasticActionsBeforeTime': red_agent_stochastic_actions_before_time,
                               'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                               'NextDeliberateAction': red_agent_next_deliberate_action
                               }


    def rewind(self, time):
        '''This method uses the loglist to rewind the state of the red agent to what it was at time.'''
        if self.time == time:
            pass
        low, high = self.loglist.temporal_bounds()
        if low <= time < high:
            self.loglist.truncate_to_time(time)
        latest = self.loglist[-1]
        self.time = latest.time
        self.intended_radar_activation_time = latest.intended_radar_activation_time
        self.believed_radar_state = latest.believed_radar_state 
        self.blip_count = latest.blip_count
        self.forward_simulation(time)


    def deliberate(self, max_time):
        '''This method is called by the supervisor to tell the red agent to plan out its future actions and underlying mental state based upon the percepts it has received as of the current time. These planned actions are used to bound future simulation times.'''
        if self.time >= max_time: # this shouldn't happen in regular use
            pass
        else:
            self.forward_simulation(max_time)
            # if red agent believes radar is currently off:
            # possibly update self.intended_radar_activation_time
            # if a new intended radar activation time is generated, send message to supervisor reflecting it
            # if agent believes radar is on and has perceived radar blips:
            # possibly update state polled by red_agent_stochastic_actions_before_time
            

    @property
    def location(self):
        '''The operator is treated as part of the radar, so their location is the same as that of the radar.'''
        return self.parent.location
    

    @property
    def resolution(self):
        '''The operator is treated as part of the radar, so their resolution is the same as that of the radar.'''
        return self.parent.resolution
