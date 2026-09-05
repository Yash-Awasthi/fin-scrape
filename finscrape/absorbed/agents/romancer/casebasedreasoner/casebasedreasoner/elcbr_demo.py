import sys, os
from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from romancer.environment.percept import Percept
from casebasedreasoner.escalationladderreasoner import EscalationLadderCBR


def test_get_sibling_scenario():
    sup = SingleThreadSupervisor()
    env = SingleThreadEnvironment(sup, None, None)
    ELCBR = EscalationLadderCBR(env, env.time)
    ELCBR.add_ELRScenario([], 3, 'escalation')
    ELCBR.add_ELRScenario([], 4, 'escalation')
    ELCBR.add_ELRScenario([], 5, 'deescalation')
    scenario_slots = {'percepts': None, 'current_rung': 3}
    new_scenario = ELCBR.slots_to_mop(slots=scenario_slots, absts={'M_ELRScenario'}, mop_type='instance', must_work=True)
    old = ELCBR.get_sibling_scenario(None, new_scenario)
    print(old)
    print(old.slots)


def test_make_decision():
    sup = SingleThreadSupervisor()
    env = SingleThreadEnvironment(sup, None, None)
    ELCBR = EscalationLadderCBR(env, env.time, load_memory_from="trainedELCBR.pkl", verbose=True)
    all_scenarios = ELCBR.name_mop('M_ELRScenario').specs
    # percept_slots = {'weapon': '5', 'target': '5', 'count': '10'}
    # ELCBR.make
    # new_percept = ELCBR.create_mop_percepts_slots_r([percept_slots])
    # new_scenario_slots = {'percepts': new_percept, 'current_rung': 2}
    percepts = [Percept(events_list={'weapon': '5', 'target': '5', 'count': '2'})]
    new_scenario_slots = ELCBR.make_scenario_slots(percepts, 2)
    result = ELCBR.make_decision(new_scenario_slots)

# test_get_sibling_scenario()
test_make_decision()