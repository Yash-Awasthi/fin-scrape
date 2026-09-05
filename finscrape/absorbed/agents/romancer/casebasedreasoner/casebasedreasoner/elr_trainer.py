import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from casebasedreasoner.escalationladderreasoner import EscalationLadderCBR
from romancer.environment.singlethreadenvironment import SingleThreadEnvironment
from romancer.agent.escalationladderreasoner import EscalationLadderReasoner, MatchAllRung, EscalationLadder
from romancer.agent.amygdala import Amygdala, Amygdala_Fight, Amygdala_Freeze, Amygdala_Flight, Amygdala_StoneCold
from romancer.environment.percept import Percept
from casebasedreasoner.util import  export_cbr_sqlite
import random

def _get_amygdala_random(env, count):
    ### DEFAULT AMYGDALA PARAMETERS
    red_initial_fight = 0.0
    red_initial_flight = 0.0
    red_initial_freeze = 0.0
    red_pbf_halflife = 100.0
    red_max_pbf = 1.0

    def _get_random_amygdala():
        # randomize key parameters
        red_response_threshhold = random.random()
        red_flight_weight = random.random()
        red_fight_weight = random.random()
        red_freeze_weight = random.random()
        red_initial_pbf = random.random()

        # construct amygdala
        amygdala = Amygdala(environment=env, time=env.time, fight_weight=red_fight_weight,
                            flight_weight=red_flight_weight, freeze_weight=red_freeze_weight,
                            initial_fight=red_initial_fight, initial_flight=red_initial_flight,
                            initial_freeze=red_initial_freeze, initial_pbf=red_initial_pbf,
                            pbf_halflife=red_pbf_halflife, max_pbf=red_max_pbf,
                            response_threshhold=red_response_threshhold)
        return amygdala

    random_amygs = [_get_random_amygdala() for _ in range(count)]
    return random_amygs

def _get_amygdala_archetypes(env):
    archetype_amygs = [
        # Amygdala_Fight(env, env.time),
        # Amygdala_Flight(env, env.time),
        # Amygdala_Freeze(env, env.time),
        Amygdala_StoneCold(env, env.time)
    ]
    return archetype_amygs

def train():
    ### EVENT CONSTRUCTION
    weapon_classes = 5
    target_classes = 5
    hit_counts = 1

    ### ESCALATION LADDER DEFINITION
    rungs = []
    for i in range(weapon_classes):
        eventclass = i+1
        rung = MatchAllRung(match_attributes = {'weapon': str(eventclass), 'target': str(eventclass)})
        rungs.append(rung)
    escalation_ladder = EscalationLadder(rungs)

    ### TRAINING
    env = SingleThreadEnvironment(None, None, None)
    ELCBR = EscalationLadderCBR(env, env.time, verbose=True)
    ELR = EscalationLadderReasoner(env, env.time, escalation_ladder=escalation_ladder, identity='red', cbr=ELCBR)

    # inform ELCBR of ladder rungs
    match_attributes = []
    for rung in rungs:
        match_attributes.append(rung.match_attributes)

    # train on random amygdalas and systematic percepts
    amygdala_scenarios = 10
    stochastic_train_scenarios = 10 # Train on this many stochastic scenarios, in addition to the non-stochastic cross section
    percepts_per_stochastic_train = 5 # Every stochastic scenario includes this many random percepts
    items_per_stochastic_percept = 3 # Every stochastic percept includes this many items
    # amygdalas = _get_amygdala_random(env, amygdala_scenarios)
    amygdalas = _get_amygdala_archetypes(env)
    amygdala_cnt = 0
    for amygdala in amygdalas:
        amygdala_cnt += 1
        print(f"Training Amygdala {amygdala_cnt}/{len(amygdalas)} with {len(ELR.escalation_ladder)} rungs")

        print()
        for rungnum in range(len(ELR.escalation_ladder)):
            print(f"    ... Deliberate Training: rung {rungnum} with {weapon_classes * target_classes * hit_counts} percepts")
            for weapon in range(1, weapon_classes + 1):
                for target in range(1, target_classes + 1):
                    for hit_count in range(hit_counts):
                        ELR.current_rung = ELR.escalation_ladder[rungnum]
                        ELR.digested_percepts.clear()
                        ELR.reset_reasoner(rungnum)
                        percept = Percept(events_list=[{'weapon': str(weapon), 'target': str(target), 'count': str(hit_count)}])
                        ELR.enqueue_digested_percept(digested_percept=percept, percept_time=0)
                        ELR.deliberate(0, amygdala) # this will log ELRscenario memories into the attached CBR

        print()
        # for rungnum in range(len(ELR.escalation_ladder)):
        #     print(f"    ... Stochastic Training: rung {rungnum} with {percepts_per_stochastic_train} compound percepts in {stochastic_train_scenarios} scenarios")
        #     for _ in range(stochastic_train_scenarios):
        #         ELR.reset_reasoner(rungnum)
        #         for _ in range(percepts_per_stochastic_train):
        #             events_list = []
        #             for _ in range(items_per_stochastic_percept):
        #                 events_list.append({'weapon': 1+random.randint(0, weapon_classes),
        #                                            'target': 1+random.randint(0, target_classes),
        #                                            'count': random.randint(0, 3)})
        #             if 1 == len(events_list):
        #                 events_list = events_list[0]
        #             percept = Percept(events_list=events_list)
        #             ELR.enqueue_digested_percept(digested_percept=percept, percept_time=0)
        #         ELR.deliberate(0, amygdala)

        # print()
        # for depth in range(5):
        #     for breadth in range(5):
        #         print(f"Depth {depth} breath {breadth}")
        #         ELR.reset_reasoner(0)
        #         events_list = []
        #         for _ in range(depth):
        #             for _ in range(breadth):
        #                 events_list.append({'weapon': 1+random.randint(0, weapon_classes),
        #                                                'target': 1+random.randint(0, target_classes),
        #                                                'count': random.randint(0, 3)})
        #             percept = Percept(events_list=events_list)
        #             ELR.enqueue_digested_percept(digested_percept=percept, percept_time=0)
        #         ELR.deliberate(0, amygdala)


        print()

    ELCBR.display_memory(include_scenario_details=False)

    # export_cbr_sqlite(ELCBR, "trainedELCBR.sqlite")

    # serialize it
    print(f"Pickling trained ELCBR, with {len(ELCBR.mops)} mops")
    ELCBR.serialize("trainedELCBR.pkl")

    # # create a new CB-ELR and load the old one's memories into it
    # print("Verify-Loading trained ELCBR")
    # new_ELCBR = EscalationLadderCBR(env, env.time, load_memory_from="trainedELCBR.pkl")
    # print(f"Reloaded CBR has {len(new_ELCBR.mops)} mops")

if __name__ == "__main__":
    train()