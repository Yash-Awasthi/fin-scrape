from romancer.environment.object import ImprovedRomancerObject, LoggedList, LoggedSet, LoggedDict
from romancer.supervisor.watchlist import WatchlistItem
from romancer.environment.location import StationaryGeographicLocation
from typing import NamedTuple

def next_deterministic_action(o, m):
    '''This method sends a message to the supervisor indicating the time of the next deterministic action that the agent will take. This can be an arbitrary action. The PersonLikeAgent might invoke either its reasoner or amygdala to determine this action, but it can also represent non-cognitive processes associated with the "person."'''
    pass


def next_deliberate_action(o, m):
    '''The purpose of this method is to determine whether the agent plans to execute a deliberate action before a maximum time. Deliberate actions are always deterministic, but deterministic actions are not necessarily deliberate. For example, some agents can move just as vehicles can, and some of those movements can be deterministic from a simulation standpoint while not being deliberate. E.g., if an agent represents a falling person, their physical shift to a different disposition as they fell would be deterministic (in that it can be predicted to occur ast a specific future time) but not deliberate in that the agent may not have planned to fall and may not be aware it is falling. The PersonLikeAgent might invoke either its reasoner or amygdala to determine this action.'''
    pass


class PersonLikeAgent(ImprovedRomancerObject):
    '''Person-like agents are intended to represent human cognitive processes in at least modest fidelity. They incorporate an object approximately representing neuroendocrine and limbic systems (a ) and another representing higher-level reasoning functions (i.e., neocortex).'''

    def __init__(self, environment, time, perception_filter, amygdala, reasoner, location = StationaryGeographicLocation(latitude = 0.0, longitude = 0.0, bearing=0.0), name=None):
        super().__init__(environment, time)
        self.perception_filter = perception_filter # this should probably log by default
        self.most_recent_percept_time = None # this should definitely log
        self.amygdala = amygdala
        self.reasoner = reasoner
        self.location = location # fixed location
        self.resolution = 1.0 # fixed resolution, should this be very large?
        self.name = name
        self.dispatch_table = LoggedDict({'DeterministicActionBeforeTime': next_deterministic_action,
                                          'StochasticActionsBeforeTime': lambda o, m: None,
                                          'AdvanceToTime': lambda o, m: o.forward_simulation(m.time),
                                          'NextDeliberateAction': next_deliberate_action,
                                          'UpdateAmygdalaParameters': lambda o, m: o.amygdala.update_parameters(m)}, parent = self, varname = 'dispatch_table')
        

    def dispatcher(self, message):
        '''This is the function that decides how to process messages in the agent's inbox. It should return functions with an (supervisor, message) call signature. Raises an exception if no appropriate dispatch function is found.'''
        try:
            f = self.dispatch_table[message.messagetype]
            return f
        except KeyError:
            print('No dispatch found for message type:', message.messagetype)


    def forward_simulation(self, time):
        '''The forward_simulation method for the PersonLikeAgent works by calling the forward_simulation method of the agent's reasoner, which in turn advances the simulation of the amygdala as needed.'''
        self.reasoner.forward_simulation(time, self.amygdala)
        if self.time < time:
            self.time = time      
            
    def perceive(self, percept):
        '''This method updates the agent's internal state based on percept. This is delegated to the PerceptionFilter, which may contain closures over the agent's amyygdala and reasoner.'''
        self.perception_filter.digest_percept(percept)


    def deliberate(self, max_time):
        '''This method causes the agent to cogitate and predict how its mental state and intentions will evolve up until max_time in the future, presuming that it receives no additional percepts after the current time. One of the purposes of this method is to establish the evolution of the internal mental state of the agent. These changes can be stored on the loglist and then used to account for how a new percept can interrupt the agent's 'chain of thought.'

        The PersonLikeAgent delegates deliberation to its reasoner.'''
        self.reasoner.deliberate(max_time, self.amygdala)

    # def visualise_final(self):
    #     super().visualise_final()
    #     self.reasoner.visualise_final()
    #     self.amygdala.export_plot(title=f"Amygdala {self.name}", filename="amygdala_{self.name}.png")



class PersonLikeAgentAction(WatchlistItem):
    '''This WatchlistItem takes the next action on the associated PersonLikeAgent's action queue and updates its amygdala parameters.'''

    def __init__(self, time, agent_uid):
        super().__init__(time)
        self.agent_uid = agent_uid
        self.amygdala_update_parameters = None


    def process(self, supervisor):
        agent = supervisor.environment.message_dispatch_table[self.agent_uid]
        # take next action on agent's reasoner's action queue
        params = agent.reasoner.take_next_action() # take_next_action() method returns amygdala update parameters
        # it also is permitted to send arbitrary numbers of arbitrary messsages to the supervisor which can then trigger changes in supervisor and environment state (e.g., enqueing future WatchlistItems)
        # use returned params to update agent's amygdala state
        self.amygdala_update_parameters = params

        agent.amygdala.update_parameters(params)
        if not self.agent_uid:
            if len(supervisor.environment.agents) == 1: # only one possible agent to receive percept
                agent_uid = supervisor.environment.agents[0].uid
        else: 
            agent_uid = self.agent_uid
        supervisor.environment.perception_engine.force_percept(self.time, [], agent_uid) # this method should generate the percept from events_list and have it queued for delivery when the perceptionengine is run
        supervisor.check_for_percepts = True

        
    def __repr__(self):
        return '{}(time={}, agent_uid={}, amygdala_params={})'.format(self.__class__.__name__, self.time, self.agent_uid, self.amygdala_update_parameters)


class PersonlikeActionROMANCERMessage(NamedTuple):
    uid: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    time: float # simulation time
    actions: tuple # sequence (possibly empty) or action messages sent to supervisor when action is executed
    amygdala_params: dict = {'delta_pbf': 0.0, 'delta_fight': 0.0, 'delta_flight': 0.0, 'delta_freeze': 0.0}
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)
    most_recent_percept_time: float = -1.0 # negative value means 'None'
    target_uid: int = 0 # target object if needed, 0 means 'none'

    
def push_personlike_action(sup, message):
    '''This method is supposed to be used with the SingleThreadSupervisor's dispatch table in response to a PersonlikeActionROMANCERMessage.'''
    item = PersonLikeAgentAction(message.time, agent_uid = message.sender[1])
    return item


class DraftROMANCERMessage():
    '''The purpose of this class is to provide a means of generating arbitrary ROMANCER messages, which are by definition immutable objects, at runtime. It is used by initializing with kwargs that include all the slots of the message in addition to an argument 'message_class' which indicates the class name of the message. The same DraftROMANCERMessage object can be mutated to create many different immutable messages as desired. The generate a message based on the current state of the object, use the coerce_to_message method.'''

    def __init__(self, **kwargs):
        default_kwargs = dict({'confirmReceipt': False})
        default_kwargs.update(kwargs)
        default_kwargs.pop('message_class')
        self.class_obj = globals()[kwargs['message_class']]
        self.constructor_args = default_kwargs


    def coerce_to_message(self, **substitute_kwargs):
        current_args = self.constructor_args | substitute_kwargs
        message = self.class_obj(**current_args)
        return message


    def __repr__(self):
        print_args = self.constructor_args | {'message_class': self.class_obj.__name__}
        return 'DraftROMANCERMessage(**{})'.format(print_args)
