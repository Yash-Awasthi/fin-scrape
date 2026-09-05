from casebasedreasoner.cbr import CaseBasedReasoner, MOP
from casebasedreasoner.MOP_comparer_sorter import ELRPerceptMOPComparer
from dill import dump, load
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import copy

from romancer.environment.object import LoggedDict


class EscalationLadderCBR(CaseBasedReasoner):
    def __init__(self, env, time, load_memory_from = None, verbose = False, comparer_sorter = None, name="EscalationLadderCBR", parent_elr=None):
        super().__init__(env, time)
        self.duplicate_scenario_cnt = 0
        self.scenario_cnt = 0

        self.name = name
        self.parent_elr = parent_elr
        self.upper_threshold = 5  # how many net deviations from a known case are required to think the new case is more severe
        self.lower_threshold = -5 # how many net deviations from a known case are required to think the new case is less severe
        self.too_distant_threshold = 400 
        self.distant_threshold = 200
        self.verbose = verbose
        self.decision_making_ability = 1.0
        if comparer_sorter:
            self.mop_comparer_sorter = comparer_sorter
        else:
            self.mop_comparer_sorter = ELRPerceptMOPComparer()
        if load_memory_from:
            self.load(load_memory_from)
        else:
            self.add_mop(mop_name='M-CALC', mop_type='mop', is_default_mop=True)
            self.add_mop(mop_name='M_percept', absts={'M-EVENT'}, mop_type = 'mop', is_default_mop=True)
            self.add_mop(mop_name='M_percept_group', absts={'M-GROUP'}, slots={1: self.name_mop('M_percept')}, is_default_mop=True)
            ## potential outcomes
            self.add_mop(mop_name="M_rung", absts={'M-EVENT'}, mop_type='mop', is_default_mop=True)
            self.add_mop(mop_name='M_ELRScenario_outcome', absts={'M-EVENT'}, mop_type = 'mop', is_default_mop=True)
            self.add_mop(mop_name='I_M_escalate_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance', is_default_mop=True)
            self.add_mop(mop_name='I_M_deescalate_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance', is_default_mop=True)
            self.add_mop(mop_name='I_M_no_change_outcome', absts={'M_ELRScenario_outcome'}, mop_type='instance', is_default_mop=True)
            ## ELRScenario
            self.add_mop(mop_name='M_ELRScenario',
                        absts={'M-CASE'},
                        mop_type='mop',
                        slots={ 'old': self.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': self.get_sibling_scenario}, is_default_mop=True),
                               'percepts': self.name_mop('M_percept_group'),
                                'current_rung': 0,
                                'next_rung': self.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': self.decide_next_rung}, is_default_mop=True),
                                # 'outcome': self.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': self.adapt_outcome}, is_default_mop=True)
                                },
                         is_default_mop=True
            )

    def get_rung_mop(self, rung_num):
        ''' Returns the mop associated with this rung, creating it if necessary'''
        mop_name = f"I_M_rung_{rung_num}"
        if mop_name not in self.mops:
            slots = {'rung_num': rung_num}
            # Include a name if we can find one
            if self.parent_elr is not None:
                elrung = self.parent_elr.escalation_ladder[rung_num]
                if elrung is not None and elrung.name is not None:
                    slots['rung_name'] = elrung.name

            self.add_mop(mop_name=mop_name, absts={'M_rung'}, slots=slots, mop_type='instance', is_default_mop=True)
        return self.name_mop(mop_name)

    def get_sibling_scenario(self, pattern, mop):
        '''Finds a sibling of MOP. It is only defined for instance MOPs.'''
        if self.decision_making_ability is not None:
            # Use an intelligent/stochastic degrade algorithm if possible
            mop_name = mop.mop_name
            compare_mops = [sibling for sibling in self.get_all_siblings(mop) if sibling != mop]
            sorted_mops = self.mop_comparer_sorter.compare_mops_and_sort(self, mop_name, compare_mops)
            if len(sorted_mops) > 0:
                best_sibling = self.name_mop(sorted_mops[0])
                for sibling_name in sorted_mops:
                    sibling = self.name_mop(sibling_name)
                    if "next_rung" not in sibling.slots.keys():
                        print(f"MOP {sibling_name} does not have a next_rung associated with it, moving on")
                        continue
                    # sibling_rung = sibling.slots['current_rung']
                    # current_rung = mop.slots['current_rung']
                    if sibling != mop: # and sibling_rung == current_rung:
                        return sibling
                return best_sibling
        # Fall through to get_sibling per Schank
        for abst in mop.absts: # goes up one layer in abstraction
            for spec in abst.specs: # looks at all specializations
                if isinstance(spec, MOP) and \
                    spec.is_instance_mop() and \
                    spec != mop and not spec.is_abstraction(self.name_mop('M-FAILED-SOLUTION')) and \
                    spec.slots['current_rung'] == mop.slots['current_rung']:
                                    sibling = spec
        return sibling


    def make_decision(self, scenario_slots): # like judge.judge_case
        # this function is called whenever the ELR tries to fill the outcome slot
        # print ("---------------------------")
        instance = self.slots_to_mop(slots=scenario_slots, absts={'M_ELRScenario'}, mop_type='instance', must_work=True)
        # print(f"Deciding outcome in {instance}...")
        # outcome = instance.get_filler('outcome')
        next_rung = instance.get_filler('next_rung')
        if self.verbose:
            print(f"Next rung in {instance} is {next_rung}.")
        return next_rung


    def decide_next_rung(self, pattern, mop):
        old_mop = mop.get_filler('old') # calls get_sibling_scenario
        old_current_rung = old_mop.slots['current_rung']
        old_next_rung = old_mop.slots['next_rung']
        current_rung = mop.get_filler('current_rung')
        output = f"Comparing new scenario {mop} (current_rung={current_rung}) to old scenario {old_mop} (current_rung={old_current_rung}, next_rung={old_next_rung})...\n"
        old_outcome = old_mop.slots['outcome']
        # calculate difference between percepts
        distance = self.mop_comparer_sorter.compare_two_percept_groups(mop.slots['percepts'], old_mop.slots['percepts'])
        # print("---------------------------")
        if distance > self.too_distant_threshold:
            next_rung = current_rung
            output += f"New and old scenarios too distant (distance={distance}), maintaining: "
        elif distance > self.distant_threshold:
            rung_change = old_mop.get_filler('next_rung') - old_mop.get_filler('current_rung')
            if abs(rung_change) == 1 or rung_change == 0:
                next_rung = current_rung
            elif rung_change > 1:
                next_rung = current_rung + 1
            else:
                next_rung = current_rung - 1
            output += f"New and old scenarios somewhat distant (distance={distance}), moving one step in direction of old: "
        else:
            next_rung = old_next_rung
            output += f"New and old scenarios not distant at all (distance={distance}), copying outcome: "
        if (current_rung - next_rung) > 0:
            outcome = self.name_mop('I_M_deescalate_outcome')
        elif (current_rung - next_rung) < 0:
            outcome = self.name_mop('I_M_escalate_outcome')
        else:
            outcome = self.name_mop('I_M_no_change_outcome')
        mop.slots['outcome'] = outcome
        output += f"{outcome} from {current_rung} to {next_rung}\n"
        output += "---------------------------"
        if self.verbose:
            print(output)
        mop.absts.add(old_mop.mop_name)
        return next_rung
    

    def mop_calc(self, slots):
        instance = self.slots_to_mop(slots=slots, absts={'M-CALC'}, mop_type='instance')
        if instance:
            return instance.get_filler('value')
        return None


    def serialize(self, path):
        filepath = Path.cwd() / path
        with open(filepath, 'wb') as f:
            dump(self.mops, f)
   

    def load(self, path):
        filepath = Path.cwd() / path
        with open(filepath, 'rb') as f:
            self.mops = load(f)


    ''' Given some percepts, recursively create groups for as long as some of the things are lists or dicts.
     Eventually return a mop'''
    def create_mop_percepts_slots_r(self, percepts):
        slots_dict = {}
        if isinstance(percepts, dict):
            for k, v in percepts.items():
                if isinstance(v, dict) or isinstance(v, list):
                    slots_dict[k] = self.create_mop_percepts_slots_r(v)
                else:
                    slots_dict[k] = v
        elif isinstance(percepts, list):
            if 0 == len(percepts):
                return None
            elif 1 == len(percepts):
                return self.create_mop_percepts_slots_r(percepts[0])
            else:
                group_slots = {}
                for i in range(len(percepts)):
                    group_slots[i] = self.create_mop_percepts_slots_r(percepts[i])
                return self.add_mop(absts={'M_percept_group'}, mop_type='instance', slots=group_slots)
        else:
            print("Percepts is neither dict nor list")
            slots_dict["percept"] = percepts
        return self.add_mop(mop_type='instance', absts={'M_percept'}, slots=slots_dict)
    
    '''Assume percepts is a list of Percept objects'''
    def create_percept_group(self, percepts):
        slots = {}
        counter = 1
        for percept in percepts:
            slots[counter] = self.create_percept_mop(percept)
            counter+=1
        return self.add_mop(absts={'M_percept_group'}, slots=slots, mop_type='instance')
    
    '''Percept has attribute param_names'''
    def create_percept_mop(self, percept):
        slots = {}
        for param in percept.param_names:
            slots[param] = getattr(percept, param)
        return self.add_mop(absts={'M_percept'}, slots=slots, mop_type='instance')

    def find_existing_percept_mop(self, percepts, percept_match_keys):
        ''' Given the percepts here, find a MOP that is precisely the same as this set of percepts, if it exists
        percept_match_keys is a List of keys, that, if the percepts align on these, then that is sufficient for "sameness"
        '''

        # Base to compare against
        this_percept_set = set()
        for percept in percepts:
            percept_dict = {k: getattr(percept, k, None) for k in percept_match_keys}
            this_percept_set.add(frozenset(percept_dict.items()))

        percept_group_mop = self.mops['M_percept_group']
        for mopname in self.mops:
            thismop = self.mops[mopname]
            # Set of dictionaries
            mop_props = set()
            if percept_group_mop.is_abstraction(thismop) and percept_group_mop.mop_name != thismop.mop_name:
                for percept_mop in thismop.slots.values():
                    this_map = { k: percept_mop.slots.get(k, None) for k in percept_match_keys}
                    item = frozenset(this_map.items())
                    # Early out if possible
                    if item not in this_percept_set:
                        break
                    mop_props.add(item)
            if mop_props == this_percept_set:
                return thismop
        return None

    # For now, this code assumes that percepts is a list of objects.
    #  In future, will want to work with arbitrary structures handled by create_mop_percepts_slots_r
    #  But will then also need to make more complex find_existing_percept_mop, etc, to account for this
    def make_scenario_slots(self, percepts, current_rung, next_rung=None):
        percept_group = self.create_percept_group(percepts)
        # outcome
        if next_rung is None: # we don't know the outcome yet
            outcome = None
        elif next_rung < current_rung: # we went down the ladder
            outcome = self.name_mop('I_M_deescalate_outcome')
        elif current_rung < next_rung: # we went up the ladder
            outcome = self.name_mop('I_M_escalate_outcome')
        else: # we stayed on the same rung
            outcome = self.name_mop('I_M_no_change_outcome')
        slots = {'percepts': percept_group, 'current_rung': current_rung}
        if next_rung:
            slots['next_rung'] = next_rung
            slots['matched_rung'] = self.get_rung_mop(next_rung)
        if outcome:
            slots['outcome'] = outcome
        return slots
    
    # This function is only used during "training"; during rollout, normal CBR behaviour is followed
    def add_ELRScenario(self, percepts, current_rung, next_rung):
        existing_mop = self.find_existing_percept_mop(percepts, ["actor", "action_taken", "messages"])
        if None != existing_mop:
            self.duplicate_scenario_cnt += 1
            return
        self.scenario_cnt += 1

        # print(f"Scenario/dup: {self.scenario_cnt}/{self.duplicate_scenario_cnt}")

        slots = self.make_scenario_slots(percepts, current_rung, next_rung)
        ## create the new scenario
        self.add_mop(absts={'M_ELRScenario'},
                     mop_type='instance',
                     slots=slots)


    def display_memory(self, include_scenario_details=False):
        print("------------------")
        print("ELRScenarios:")
        outcome_totals = {}
        for spec in self.name_mop("M_ELRScenario").specs:
            outcome = spec.slots['outcome']
            outcome_totals[outcome] = outcome_totals.get(outcome, 0) + 1
        print("Outcomes: " + str(outcome_totals))
        print()

        if include_scenario_details:
            ## show known ELRScenarios
            for spec in self.name_mop("M_ELRScenario").specs:
                print(spec.mop_name)
                print(spec.slots['percepts'])
                print(spec.slots['outcome'])
                print()

    def __repr__(self):
        # This needs to be replaced with something more useful
        return f"{self.name}(EscalationLadderCBR)"