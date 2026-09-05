from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from romancer.environment.dispositiontree import GeographicDispositionStump
from romancer.commandpe.watchlist import CommandPEWatchlist as Watchlist
from romancer.commandpe.perceptionengine import CommandPEPerceptionEngine as PerceptionEngine, CommandPEPerceptionFilter as PerceptionFilter
from romancer.agent.personlikeagent import push_personlike_action
from romancer.agent.escalationladderagent import EscalationLadderAgent
from romancer.commandpe.watchlist import CommandPEWatchlistItem
from numpy import deg2rad
import random

from romancer.agent.escalationladderreasoner import EscalationLadder, EscalationLadderRung, MatchAllRung, EscalationLadderReasoner
from romancer.agent.amygdala import Amygdala, UpdateAmygdalaParameters
from romancer.agent.personlikeagent import push_personlike_action, DraftROMANCERMessage

outputfolder = inputfolder = "data/orwaca_sample"

def run(ELR):
    # run an entire simulation, feeding ELR(CB) into the ELR(R) of the simulation
    sup = SingleThreadSupervisor()

    # set dispatch function for PersonlikeActionROMANCERMessage
    sup.dispatch_table['PersonlikeActionROMANCERMessage'] = push_personlike_action
    watchlist = Watchlist(weapon_class_csv = f"{inputfolder}/weaponClass.csv", target_class_csv = f"{inputfolder}/targetClass.csv", target_unit_csv = f"{inputfolder}/targetUnitClass.csv", weapon_fired_csv = f"{outputfolder}/WeaponFired.csv", weapon_endgame_csv = f"{outputfolder}/WeaponEndgame.csv")
    start_time = 0.0 # watchlist.peek().time # time at which simulated events from CommandPE start
    sup.watchlist = watchlist # replace default SingleThreadSupervisor watchlist with populated CommandPE watchlist

    # Step 1.2: Configure logger
    # def demologger(s):
    #     print('Processed watchlist item: ', s)
    #     print()

    # sup.logger = demologger

    # Step 2: Make environment

    # Step 2.1: Make disposition stump
    min_lat = deg2rad(-180)
    max_lat = deg2rad(180)
    min_long = deg2rad(-180)
    max_long = deg2rad(180)

    stump = GeographicDispositionStump(bounds = (min_lat, max_lat, min_long, max_long)) # whole Earth

    # Step 2.2: Make perception engine
    # The CommandPEPerceptionEngine is designed to work with the percepts produced by the scheduled items in the populated CommandPEWatchlist
    # Note that this implies that the CommandPEPerceptionEngine may need to have little functionality of its own, possibly merely passing percepts to the RedAgent

    engine = PerceptionEngine()

    # Step 2.3: Make environment
    env = SingleThreadEnvironment(supervisor=sup, disposition_tree=stump, perception_engine=engine)

    sup.environment = env # set supervisor's environment attribute
    engine.environment = env # set perception engine's environment attribute

    # Step 3: create and add red agent
    # Step 3.1: Load amygdala and reasoner
    red_amygdala, red_reasoner = _generate_scenario(env)

    # Step 3.2: Create perception filter
    # The pre-processed percepts generated from the Command PE output files may require little/no filtering, so this is just a pass-through except for maybe accessing amygdala parameters
    red_perception_filter = PerceptionFilter(agent = None)

    # Step 3.3: Create and add agent
    red_reasoner.cbr = ELR
    red_nca = EscalationLadderAgent(environment = env, time = start_time, perception_filter = red_perception_filter, amygdala = red_amygdala, reasoner = red_reasoner, name="Red NCA")
    red_perception_filter.agent = red_nca
    env.register_object(red_nca)
    env.add_agent(red_nca)

    # Step 4: Run simulation
    sup.run(verbose = True)


def _generate_scenario(env):
    # randomize parameters
    red_response_threshhold = random.random()
    red_flight_weight = random.random()
    red_fight_weight = random.random()
    red_freeze_weight = random.random()
    red_initial_pbf = random.random()

    # construct scenario
    red_amygdala = Amygdala(environment = env, time = env.time, fight_weight = red_fight_weight, flight_weight = red_flight_weight, freeze_weight = red_freeze_weight, initial_fight = red_initial_fight, initial_flight = red_initial_flight, initial_freeze = red_initial_freeze, initial_pbf = red_initial_pbf, pbf_halflife = red_pbf_halflife, max_pbf = red_max_pbf, response_threshhold = red_response_threshhold)
    red_cur_rung = None # change to different rung to start above bottom of escalation ladder (implicitly rung1)
    red_planned_actions = None # change to force planned red actions, this will be heapified so it needs to be (time, action) tuples
    red_actions_taken = None # change to give Red NCA history of actions taken
    red_digested_percepts = None # change to give Red NCA history of digested percepts
    red_reasoner = EscalationLadderReasoner(environment = env, time = env.time, escalation_ladder = red_escalation_ladder, identity = 'red', current_rung = red_cur_rung, planned_actions = red_planned_actions, actions_taken = red_actions_taken, digested_percepts = red_digested_percepts)
    return red_amygdala, red_reasoner
    return red_amygdala, red_reasoner


### DEFAULT SCENARIO PARAMETERS
red_fight_weight = 1.0
red_flight_weight = 1.0
red_freeze_weight = 1.0
red_initial_fight = 0.0
red_initial_flight = 0.0
red_initial_freeze = 0.0
red_initial_pbf = 0.0001
red_pbf_halflife = 100.0
red_max_pbf = 1.0

test_action = (0.1, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), UpdateAmygdalaParameters(0, 0, 0, 0))
low_stress_params = UpdateAmygdalaParameters(0.1, 0.2, 0.3, 0.4)
low_stress_action = (0.5, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), low_stress_params)
high_stress_freeze_params = UpdateAmygdalaParameters(0.8, 0.6, 0.7, 0.8)
high_stress_freeze_action = (0.3, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), high_stress_freeze_params)
high_stress_fight_params = UpdateAmygdalaParameters(0.8, 2.0, 0.1, 0.1)
high_stress_fight_action = (0.1, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), high_stress_fight_params)
high_stress_flight_params = UpdateAmygdalaParameters(0.8, 0.2, 3.0, 0.3)
high_stress_flight_action = (20, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), high_stress_flight_params)
deescalate_params = UpdateAmygdalaParameters(-0.2, 0, 0, 0)
deescalate_action = (4, (DraftROMANCERMessage(messagetype='PersonlikeActionROMANCERMessage', time=0.0, actions=(), message_class = 'PersonlikeActionROMANCERMessage'),), deescalate_params)

rung1 = MatchAllRung(match_attributes = {'weapon': '1', 'target': 1}, # the characteristics mapped from the percepts the agent has digested that map to this rung
                                blue_actions = [], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                                red_actions = [test_action], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                                blue_deescalation_actions = [], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                                red_deescalation_actions = [deescalate_action], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                                name = "Calm")

rung2 = MatchAllRung(match_attributes = {'weapon': '2', 'target': '2'}, # the characteristics mapped from the percepts the agent has digested that map to this rung
                            blue_actions = [], # actions that agent assumes blue could or should take at this rung (can overlap with match attributes but don't have to)
                            red_actions = [low_stress_action], # actions that agent assumes red could or should take at this rung (can overlap with match attributes but don't have to)
                            blue_deescalation_actions = [], # actions that agent assumes that blue will take if it attempts to de-escalate from this rung)
                            red_deescalation_actions = [deescalate_action], # actions that agent assumes that red will take if it attempts to de-escalate from this rung
                            name = "Irritated")

rung3 = MatchAllRung(match_attributes = {'weapon': '3', 'target': '3'},
                            blue_actions = [],
                            red_actions = [high_stress_freeze_action],
                            blue_deescalation_actions = [],
                            red_deescalation_actions = [deescalate_action],
                            name = "Annoyed")

rung4 = MatchAllRung(match_attributes = {'weapon': '4', 'target': '4'},
                            blue_actions = [],
                            red_actions = [high_stress_fight_action],
                            blue_deescalation_actions = [],
                            red_deescalation_actions = [deescalate_action],
                            name = "Agitated")

rung5 = MatchAllRung(match_attributes = {'weapon': '5', 'target': '5'},
                            blue_actions = [],
                            red_actions = [high_stress_flight_action],
                            blue_deescalation_actions = [],
                            red_deescalation_actions = [deescalate_action],
                            name = "Angry")


red_escalation_ladder = EscalationLadder([rung1, rung2, rung3, rung4, rung5])
