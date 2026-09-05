from casebasedreasoner.casebasedreasoner import cbr
from casebasedreasoner.mop import MOP
from casebasedreasoner.util import make_graphviz_graph, export_cbr_sqlite, load_cbr_sqlite
import networkx as nx
import matplotlib.pyplot as plt
import random
import os
import subprocess

class Judge(cbr.CaseBasedReasoner):
    def judge(self, case_slots): # in book, this takes slots, turns them into a mop, and installs it
        instance = self.slots_to_mop(slots=case_slots, absts={'M-CRIME'}, mop_type='instance', must_work=True)
        defendant = instance.role_filler('defendant')
        print(f"Sentencing {defendant} in {instance}...")
        instance.get_filler('sentence') 
        
        return instance
    

    def judge_case(self, case_slots): # in book, this takes in slot_forms, turns them into slots
        print("---------------------------")
        instance = self.judge(case_slots)
        sentence = instance.role_filler('sentence')
        print(f"Sentence in {instance} is {sentence}.")


    def calculate_escalations(self, pattern, mop):
        print("---------------------------")
        print(f"Calculating escalations in {mop}")
        previous_severity = 0
        counter = 1
        escalations = {}
        for event in mop.get_filler('events').group_to_list():
#            severity = event.path_filler('action', 'severity')
            severity = event.path_filler(('action', 'severity'))
            escalation = severity - previous_severity
            previous_severity = severity
            escalations[counter] = escalation
            counter += 1
        escalations_mop = self.slots_to_mop(slots=escalations, absts={'M-ESCALATION-GROUP'}, mop_type='instance')
        return escalations_mop
    

    def calculate_motives(self, pattern, mop):
        print("---------------------------")
        print(f"Calculating motives in {mop}")
        prev_motive = 0
        motives = {}
        counter = 1
        escalations = mop.get_filler('escalations').group_to_list()
        for escalation in escalations:
            prev_motive = self.mop_calc({'role': motive, 'escalation': escalation, 'prev_motive': prev_motive})
            motives[counter] = prev_motive
            counter += 1
        motives_mop = self.slots_to_mop(slots=motives, absts={'M-MOTIVE-GROUP'}, mop_type='instance')
        return motives_mop

    def adapt_sentence(self, pattern, mop): # compares each event in the new and old crimes, adjusting sentence if it can 
        old_mop = mop.get_filler('old')
        old_size = old_mop.get_filler('events').group_size()
        old_sentence = old_mop.get_filler('sentence')
        size = mop.get_filler('events').group_size()
        print("---------------------------")
        print(f"Adapting sentence in {old_mop}")
        for pos in range(0, min(old_size, size)):
            old_index = old_size - pos
            index = size - pos
            slots = {'role': sentence, 'index': pos, 'old_sentence': old_sentence}
            slots.update(judge.crime_compare_slots(old_mop, old_index, ['old_action', 'old_motive', 'old_severity']))
            slots.update(judge.crime_compare_slots(mop, index, ['this_action', 'this_motive', 'this_severity']))
            result = judge.mop_calc(slots)
            if result is not None:
                return result
        print("---------------------------")
        print("No major difference found")
        print("Using old sentence")
        return old_sentence


    def mop_calc(self, slots):
        instance = self.slots_to_mop(slots=slots, absts={'M-CALC'}, mop_type='instance')
        if instance:
            return instance.get_filler('value')
        return None

    def crime_compare_slots(self, mop, n, roles):
        paths = [('events', n, 'action'), ('motives', n), ('outcomes', n, 'state', 'severity')]
        assert len(roles) == len(paths), "Length of roles and paths must be equal"
        slots = {}
        for role, path in zip(roles, paths):
            slots[role] = mop.path_filler(path)
        return slots


    def adjust_sentence(self, mop):
        print("~---------------------------~")
        print(f"{mop} applied, {mop.get_filler('index')} events from the end")
        old_sentence = mop.get_filler('old_sentence')
        weight = mop.get_filler('weight')
        index = mop.get_filler('index')
        direction = mop.get_filler('direction')
        return self.adjust_function(old_sentence, weight, index, direction)
    
    def compare_constraint(self, constraint, filler, slots):
        compare_fn = constraint.get_filler('compare_fn')
        to = self.indirect_filler('to', constraint, slots)
        return compare_fn(filler, to)

    def indirect_filler(self, role, mop, slots):
        filler = mop.get_filler(role)
        return slots.get_filler(filler)

    def adjust_function(self, sentence, weight, index, direction):
        closeness = 0.25 if index <= 1 else 0
        adjusted_sentence = sentence + (sentence * (weight + closeness) * direction)
        return adjusted_sentence

    
    def range_constraint(self, constraint, filler, slots):
        '''Assume filler is number that can be compared against the constraint.'''
        below = constraint.role_filler('below')
        above = constraint.role_filler('above')
        if below is not None:
            return filler < below
        if above is not None:
            return filler > above
        return False
    
    def check_for_mops_not_in_specs(self):
        calc_mops_missing_from_specs = []
        calc_mops_in_specs = []
        print()
        print("Checking for MOPs missing from specs...")
        for mop in self.mops:
            in_some_spec = False
            for candidate_mop in self.mops:
                candidate_specs = self.name_mop(candidate_mop).specs
                if self.name_mop(mop) in candidate_specs:
                    in_some_spec = True
            if not in_some_spec and "CALC" in mop:
                calc_mops_missing_from_specs.append(self.name_mop(mop))
            if in_some_spec and "CALC" in mop:
                calc_mops_in_specs.append(self.name_mop(mop))

        print("CALC MOPs missing from specs:")
        print(calc_mops_missing_from_specs)
        print("CALC MOPs in specs:")
        print(calc_mops_in_specs)



judge = Judge()

# create different mops
al = judge.add_mop(mop_name='I-M-AL', absts={'M-ACTOR'}, mop_type='instance', is_default_mop=True)
chuck = judge.add_mop(mop_name='I-M-CHUCK', absts={'M-ACTOR'}, mop_type='instance', is_default_mop=True)
david = judge.add_mop(mop_name='I-M-DAVID', absts={'M-ACTOR'}, mop_type='instance', is_default_mop=True)
randy = judge.add_mop(mop_name='I-M-RANDY', absts={'M-ACTOR'}, mop_type='instance', is_default_mop=True)
ted = judge.add_mop(mop_name='I-M-TED', absts={'M-ACTOR'}, mop_type='instance', is_default_mop=True)
tim = judge.add_mop(mop_name='I-M-TIM', absts={'M-ACTOR'}, mop_type='instance', is_default_mop=True)

# some of these are mops with roles/fillers (aka slots)
# (DEFMOP M-FREQUENCY (M-ROOT) (SEVERITY NIL)) NIL is None
frequency = judge.add_mop(mop_name='M-FREQUENCY', absts={'M-ROOT'}, mop_type='mop', slots={'severity': None}, is_default_mop=True)
# (DEFMOP I-M-ONCE (M-FREQUENCY) (SEVERITY 0))
once = judge.add_mop(mop_name='I-M-ONCE', absts={'M-FREQUENCY'}, mop_type='instance', slots={'severity': 0}, is_default_mop=True)
# (DEFMOP I-M-SEVERAL-TIMES (M-FREQUENCY) (SEVERITY 1)) (DEFMOP I-M-REPEATEDLY (M-FREQUENCY) (SEVERITY 2))
several_times = judge.add_mop(mop_name='I-M-SEVERAL-TIMES', absts={'M-FREQUENCY'}, mop_type='instance', slots={'severity': 1}, is_default_mop=True)
repeatedly = judge.add_mop(mop_name='I-M-REPEATEDLY', absts={'M-FREQUENCY'}, mop_type='instance', slots={'severity': 2}, is_default_mop=True)

# (DEFMOP M-MOTIVE (M-ROOT))
judge.add_mop(mop_name='M-MOTIVE', absts={'M-ROOT'}, mop_type='mop', is_default_mop=True)
# (DEFMOP M-JUSTIFIED (M-MOTIVE))
justified = judge.add_mop(mop_name='M-JUSTIFIED', absts={'M-MOTIVE'}, mop_type='mop', is_default_mop=True)
# (DEFMOP M-UNJUSTIFIED (M-MOTIVE))
unjustified = judge.add_mop(mop_name='M-UNJUSTIFIED', absts={'M-MOTIVE'}, mop_type='mop', is_default_mop=True)
# (DEFMOP I-M-SELF-DEFENSE (M-JUSTIFIED) INSTANCE) 
self_defense = judge.add_mop(mop_name='I-M-SELF-DEFENSE', absts={'M-JUSTIFIED'}, mop_type='instance')
# (DEFMOP I-M-RETALIATION (M-UNJUSTIFIED) INSTANCE) 
retaliation = judge.add_mop(mop_name='I-M-RETALIATION', absts={'M-UNJUSTIFIED'}, mop_type='instance', is_default_mop=True)
# (DEFMOP I-M-UNPROVOKED (M-UNJUSTIFIED) INSTANCE)
unprovoked = judge.add_mop(mop_name='I-M-UNPROVOKED', absts={'M-UNJUSTIFIED'}, mop_type='instance', is_default_mop=True)
# (DEFMOP M-CRIME-TYPE (M-ROOT))
crime_type = judge.add_mop(mop_name='M-CRIME-TYPE', absts={'M-ROOT'}, mop_type='mop', is_default_mop=True)
# (DEFMOP I-M-HOMICIDE (M-CRIME-TYPE) INSTANCE)
homicide = judge.add_mop(mop_name='I-M-HOMICIDE', absts={'M-CRIME-TYPE'}, mop_type='instance', is_default_mop=True)

# (DEFMOP M-FIGHT-ACT (M-ACT) (SEVERITY NIL))
fight_act = judge.add_mop(mop_name='M-FIGHT-ACT', absts={'M-ACT'}, mop_type='mop', slots={'severity': None}, is_default_mop=True)
# (DEFMOP M-HURT-ACT (M-FIGHT-ACT) (SEVERITY M-RANGE (BELOW 5)))
m_range = judge.add_mop(mop_name='M-RANGE', absts={'M-PATTERN'}, mop_type='mop', slots={'abst_fn':judge.range_constraint}, is_default_mop=True)
hurt_act = judge.add_mop(mop_name='M-HURT-ACT', absts={'M-FIGHT-ACT'}, mop_type='mop', slots={'severity': judge.add_mop(absts={'M-RANGE'}, slots={'below': 5}, is_default_mop=True)}, is_default_mop=True)
# (DEFMOP I-M-SLAP (M-HURT-ACT) (SEVERITY 1))
slap = judge.add_mop(mop_name='I-M-SLAP', absts={'M-HURT-ACT'}, mop_type='instance', slots={'severity': 1}, is_default_mop=True)
# (DEFMOP I-M-HIT (M-HURT-ACT) (SEVERITY 1))
hit = judge.add_mop(mop_name='I-M-HIT', absts={'M-HURT-ACT'}, mop_type='instance', slots={'severity': 1}, is_default_mop=True)
# (DEFMOP I-M-STRIKE (M-HURT-ACT) (SEVERITY 2))
strike = judge.add_mop(mop_name='I-M-STRIKE', absts={'M-HURT-ACT'}, mop_type='instance', slots={'severity': 2}, is_default_mop=True)
# (DEFMOP I-M-KNOCK-DOWN (M-HURT-ACT) (SEVERITY 3)) 
knock_down = judge.add_mop(mop_name='I-M-KNOCK-DOWN', absts={'M-HURT-ACT'}, mop_type='instance', slots={'severity': 3}, is_default_mop=True)
# (DEFMOP I-M-SLASH (M-HURT-ACT) (SEVERITY 4))
slash = judge.add_mop(mop_name='I-M-SLASH', absts={'M-HURT-ACT'}, mop_type='instance', slots={'severity': 4}, is_default_mop=True)
# (DEFMOP M-WOUND-ACT (M-FIGHT-ACT) (SEVERITY M-RANGE (ABOVE 4)))
wound_act = judge.add_mop(mop_name='M-WOUND-ACT', absts={'M-FIGHT-ACT'}, mop_type='mop', slots={'severity': judge.add_mop(absts={'M-RANGE'}, slots={'above': 4}, is_default_mop=True)}, is_default_mop=True)
# (DEFMOP I-M-STAB (M-WOUND-ACT) (SEVERITY 5))
stab = judge.add_mop(mop_name='I-M-STAB', absts={'M-WOUND-ACT'}, mop_type='instance', slots={'severity': 5}, is_default_mop=True)
# (DEFMOP I-M-SHOOT (M-WOUND-ACT) (SEVERITY 5))
shoot = judge.add_mop(mop_name='I-M-SHOOT', absts={'M-WOUND-ACT'}, mop_type='instance', slots={'severity': 5}, is_default_mop=True)
# (DEFMOP I-M-BREAK-SKULL (M-WOUND-ACT) (SEVERITY 5))
break_skull = judge.add_mop(mop_name='I-M-BREAK-SKULL', absts={'M-WOUND-ACT'}, mop_type='instance', slots={'severity': 5}, is_default_mop=True)
# (DEFMOP M-PHYS-STATE (M-STATE) (SEVERITY NIL))
phys_state = judge.add_mop(mop_name='M-PHYS-STATE', absts={'M-STATE'}, mop_type='mop', slots={'severity': None}, is_default_mop=True)
# (DEFMOP I-M-BRUISED (M-PHYS-STATE) (SEVERITY 1)) 
bruised = judge.add_mop(mop_name='I-M-BRUISED', absts={'M-PHYS-STATE'}, mop_type='instance', slots={'severity': 1}, is_default_mop=True)
# (DEFMOP I-M-KNOCKED-DOWN (M-PHYS-STATE) (SEVERITY 2)) 
knocked_down = judge.add_mop(mop_name='I-M-KNOCKED-DOWN', absts={'M-PHYS-STATE'}, mop_type='instance', slots={'severity': 2}, is_default_mop=True)
# (DEFMOP I-M-CUT (M-PHYS-STATE) (SEVERITY 3))
cut = judge.add_mop(mop_name='I-M-CUT', absts={'M-PHYS-STATE'}, mop_type='instance', slots={'severity': 3}, is_default_mop=True)
# (DEFMOP I-M-DEAD (M-PHYS-STATE) (SEVERITY 5))
dead = judge.add_mop(mop_name='I-M-DEAD', absts={'M-PHYS-STATE'}, mop_type='instance', slots={'severity': 5}, is_default_mop=True)
# (DEFMOP M-OUTCOME (M-ROOT))
outcome = judge.add_mop(mop_name='M-OUTCOME', absts={'M-ROOT'}, mop_type='mop', is_default_mop=True)
# (DEFMOP M-FIGHT-OUTCOME (M-OUTCOME) (STATE M-PHYS-STATE) (ACTOR M-ACTOR))
fight_outcome = judge.add_mop(mop_name='M-FIGHT-OUTCOME', absts={'M-OUTCOME'}, mop_type='mop', slots={'state': phys_state, 'actor': judge.name_mop('M-ACTOR')}, is_default_mop=True)
# (DEFMOP M-FIGHT-EVENT (M-EVENT) (ACTION M-FIGHT-ACT)
fight_event = judge.add_mop(mop_name='M-FIGHT-EVENT', absts={'M-EVENT'}, mop_type='mop', slots={'action': fight_act}, is_default_mop=True)

# (DEFMOP M-EVENT-GROUP (M-GROUP) (1 M-EVENT))
judge.add_mop(mop_name='M-EVENT-GROUP', absts={'M-GROUP'}, slots={1: judge.name_mop('M-EVENT')}, is_default_mop=True)
# (DEFMOP M-OUTCOME-GROUP (M-GROUP) (1 M-OUTCOME))
judge.add_mop(mop_name='M-OUTCOME-GROUP', absts={'M-GROUP'}, slots={1: judge.name_mop('M-OUTCOME')}, is_default_mop=True)
# (DEFMOP M-ESCALATION-GROUP (M-GROUP) (1 M-RANGE))
judge.add_mop(mop_name='M-ESCALATION-GROUP', absts={'M-GROUP'}, slots={1: judge.name_mop('M-RANGE')}, is_default_mop=True)
# (DEFMOP M-MOTIVE-GROUP (M-GROUP) (1 M-MOTIVE))
judge.add_mop(mop_name='M-MOTIVE-GROUP', absts={'M-GROUP'}, slots={1: judge.name_mop('M-MOTIVE')}, is_default_mop=True)
# (DEFMOP CALC-ESCALATIONS (M-FUNCTION))
calc_escalations = judge.add_mop(mop_name='CALC-ESCALATIONS', absts={'M-FUNCTION'}, mop_type='mop', is_default_mop=True)
# (DEFMOP CALC-MOTIVES (M-FUNCTION))
calc_motives = judge.add_mop(mop_name='CALC-MOTIVES', absts={'M-FUNCTION'}, mop_type='mop', is_default_mop=True)
# (DEFMOP ADAPT-SENTENCE (M-FUNCTION))
adapt_sentence = judge.add_mop(mop_name='ADAPT-SENTENCE', absts={'M-FUNCTION'}, mop_type='mop', is_default_mop=True)
# (DEFMOP CALC-SENTENCE (M-FUNCTION))
calc_sentence = judge.add_mop(mop_name='CALC-SENTENCE', absts={'M-FUNCTION'}, mop_type='mop', is_default_mop=True)

crime = judge.add_mop(mop_name="M-CRIME", 
                      absts={'M-CASE'}, 
                      mop_type='mop', 
                      slots={'crime_type': crime_type, 
                            'defendant': judge.name_mop('M-ACTOR'), 
                            'victim': judge.name_mop('M-ACTOR'), 
                            'events': judge.name_mop('M-EVENT-GROUP'), 
                            'outcomes': judge.name_mop('M-OUTCOME-GROUP'), 
                            'escalations': judge.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': judge.calculate_escalations}, is_default_mop=True),
                            'motives': judge.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': judge.calculate_motives}, is_default_mop=True),
                            'sentence': judge.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': judge.adapt_sentence}, is_default_mop=True)}, is_default_mop=True)
# (DEFMOP M-CRIME (M-CASE)
    # (CRIME-TYPE M-CRIME-TYPE)
    # (DEFENDANT M-ACTOR)
    # (VICTIM M-ACTOR)
    # (EVENTS M-EVENT-GROUP)
    # (OUTCOMES M-OUTCOME-GROUP)
    # (ESCALATIONS M-PATTERN (CALC-FN CALC-ESCALATIONS)) 
    # (MOTIVES M-PATTERN (CALC-FN CALC-MOTIVES)) 
    # (SENTENCE M-PATTERN (CALC-FN ADAPT-SENTENCE)))

# (DEFMOP MOTIVE (M-ROLE) INSTANCE)
motive = judge.add_mop(mop_name='MOTIVE', absts={'M-ROLE'}, mop_type='instance', is_default_mop=True)
# (DEFMOP M-CALC (M-ROOT))
judge.add_mop(mop_name='M-CALC', mop_type='mop', is_default_mop=True)
# (DEFMOP M-CALC-MOTIVE (M-CALC)
    # (ROLE MOTIVE) (VALUE NIL))
judge.add_mop(mop_name='M-CALC-MOTIVE', absts={'M-CALC'}, slots={'role': motive, 'value': None}, mop_type='mop', is_default_mop=True)
# (DEFMOP M-CALC-ESCALATION-MOTIVE (M-CALC-MOTIVE) (ESCALATION M-RANGE (ABOVE 0))
    # (VALUE I-M-RETALIATION))
judge.add_mop(mop_name='M-CALC-ESCALATION-MOTIVE',
              absts={'M-CALC-MOTIVE'},
              slots={'escalation': judge.add_mop(absts={"M-RANGE"}, slots={'above': 0}, is_default_mop=True) ,
                     'value': retaliation},
              mop_type='mop',
              is_default_mop=True)
# (DEFMOP M-CALC-SELF-DEFENSE-MOTIVE (M-CALC-MOTIVE) (ESCALATION M-RANGE (BELOW 1))
    # (PREV-MOTIVE M-UNJUSTIFIED)
    # (VALUE I-M-SELF-DEFENSE))
judge.add_mop(mop_name='M-CALC-SELF-DEFENSE-MOTIVE',
              absts={'M-CALC-MOTIVE'},
              slots={'escalation': judge.add_mop(absts={"M-RANGE"}, slots={'below': 1}, is_default_mop=True),
                     'prev_motive': unjustified,
                     'value': self_defense},
              mop_type='mop',
              is_default_mop=True)
# (DEFMOP M-CALC-RETALIATION-MOTIVE (M-CALC-MOTIVE) (ESCALATION M-RANGE (BELOW 1))
    # (PREV-MOTIVE M-JUSTIFIED)
    # (VALUE I-M-RETALIATION))
judge.add_mop(mop_name='M-CALC-RETALIATION-MOTIVE',
              absts={'M-CALC-MOTIVE'},
              slots={'escalation': judge.add_mop(absts={"M-RANGE"}, slots={'below': 1}, is_default_mop=True),
                     'prev_motive': justified,
                     'value': retaliation},
              mop_type='mop',
              is_default_mop=True)

judge.add_mop(mop_name='M-COMPARE', absts={'M-PATTERN'}, mop_type='mop', slots={'abst_fn': judge.compare_constraint, 'to': 
            judge.name_mop('M-ROLE'), 'compare_fn': judge.name_mop('M-FUNCTION')}, is_default_mop=True)
judge.add_mop(mop_name='M-EQUAL', absts={'M-COMPARE'}, mop_type='mop', slots={'compare_fn': MOP.equals}, is_default_mop=True)
judge.add_mop(mop_name='M-LESS-THAN', absts={'M-COMPARE'}, mop_type='mop', slots={'compare_fn': MOP.less_than}, is_default_mop=True)
sentence = judge.add_mop(mop_name='SENTENCE', absts={'M-ROLE'}, mop_type='instance', is_default_mop=True)
judge.add_mop(mop_name='OLD-SEVERITY', absts={'M-ROLE'}, mop_type='instance', is_default_mop=True)


# (DEFMOP M-ADAPT-SENTENCE (M-CALC)
    # (ROLE SENTENCE)
    # (VALUE M-PATTERN (CALC-FN ADJUST-SENTENCE)))
judge.add_mop(mop_name='M-ADAPT-SENTENCE', 
              absts={'M-CALC'}, 
              mop_type='mop', slots={'role': sentence, 
                                     'value': judge.add_mop(absts={'M-PATTERN'}, slots={'calc_fn': judge.adjust_sentence}, is_default_mop=True)}, is_default_mop=True)

### need to finish these ADAPT MOPS that should look very similar to this
# (DEFMOP M-CALC-RETALIATION-MOTIVE (M-CALC-MOTIVE) (ESCALATION M-RANGE (BELOW 1))
    # (PREV-MOTIVE M-JUSTIFIED)
    # (VALUE I-M-RETALIATION))
# judge.add_mop(mop_name='M-CALC-RETALIATION-MOTIVE', absts={'M-CALC-MOTIVE'}, slots={'escalation': judge.add_mop(absts={"M-RANGE"}, slots={'below': 1}), 'prev_motive': justified, 'value': retaliation}, mop_type='mop')

# (DEFMOP M-ADAPT-EXTREME-FORCE-OLD (M-ADAPT-SENTENCE) (OLD-ACTION M-WOUND-ACT)
    # (THIS-ACTION M-NOT (OBJECT M-WOUND-ACT)) 
    # (OLD-MOTIVE M-UNJUSTIFIED)
    # (THIS-MOTIVE M-UNJUSTIFIED)
    # (WEIGHT 0.50) (DIRECTION -l))
# still need to fill in the THIS-ACTION slot and all the other slots
# judge.add_mop(mop_name='M-ADAPT-EXTREME-FORCE-OLD', absts={'M-ADAPT-SENTENCE'}, slots={'old_action': wound_act, 'this_action': judge.add_mop()})
###
judge.add_mop(mop_name='M-ADAPT-EXTREME-FORCE-OLD',
              absts={'M-ADAPT-SENTENCE'},
              slots={'old_action': wound_act,
                     'this_action': judge.add_mop(absts={'M-NOT'}, slots={'object': wound_act}, is_default_mop=True), #checking if the action is not true and this is our constraint.
                     'old_motive': unjustified,
                     'this_motive': unjustified,
                     'weight': 0.5,
                     'direction': -1}, is_default_mop=True)

# (DEFMOP M-ADAPT-EXTREME-FORCE-NEW (M-ADAPT-SENTENCE) (OLD-ACTION M-NOT (OBJECT M-WOUND-ACT)) (THIS-ACTION M-WOUND-ACT)
# (OLD-MOTIVE M-UNJUSTIFIED)
# (THIS-MOTIVE M-UNJUSTIFIED)
# (WEIGHT 0.50) (DIRECTION 1))
judge.add_mop(mop_name='M-ADAPT-EXTREME-FORCE-NEW',
              absts={'M-ADAPT-SENTENCE'},
              slots={'old_action': judge.add_mop(absts={'M-NOT'}, slots={'object': wound_act}, is_default_mop=True),
                     'this_action': wound_act,
                     'old_motive': unjustified,
                     'this_motive': unjustified,
                     'weight': 0.5,
                     'direction': 1}, is_default_mop=True)
# (DEFMOP M-ADAPT-WORSE-MOTIVE-OLD (M-ADAPT-SENTENCE) (OLD-SEVERITY NIL)
# (THIS-SEVERITY M-EQUAL (TO OLD-SEVERITY)) (OLD-MOTIVE M-UNJUSTIFIED)
# (THIS-MOTIVE M-JUSTIFIED)
# (WEIGHT 0.25) (DIRECTION -1))
judge.add_mop(mop_name='M-ADAPT-WORSE-MOTIVE-OLD',
              absts={'M-ADAPT-SENTENCE'},
              slots={'old_severity': None,
                     'this_severity': judge.add_mop(absts={'M-EQUAL'}, slots={'to': 'old_severity'}, is_default_mop=True),
                     'old_motive': unjustified,
                     'this_motive': justified,
                     'weight': 0.25,
                     'direction': -1}, is_default_mop=True)

# (DEFMOP M-ADAPT-WORSE-MOTIVE-NEW (M-ADAPT-SENTENCE) (OLD-SEVERITY NIL)
# (THIS-SEVERITY M-EQUAL (TO OLD-SEVERITY)) (OLD-MOTIVE M-JUSTIFIED)
# (THIS-MOTIVE M-UNJUSTIFIED)
# (WEIGHT 0.25) (DIRECTION 1))
judge.add_mop(mop_name='M-ADAPT-WORSE-MOTIVE-NEW',
              absts={'M-ADAPT-SENTENCE'},
              slots={'old_severity': None,
                     'this_severity': judge.add_mop(absts={'M-EQUAL'}, slots={'to': 'old_severity'}, is_default_mop=True),
                     'old_motive': justified,
                     'this_motive': unjustified,
                     'weight': 0.25,
                     'direction': 1}, is_default_mop=True)

# (DEFMOP M-ADAPT-MIXED-OLD (M-ADAPT-SENTENCE) (OLD-SEVERITY NIL)
# (THIS-SEVERITY M-LESS-THAN (TO OLD-SEVERITY)) (OLD-MOTIVE M-JUSTIFIED)
# (THIS-MOTIVE M-UNJUSTIFIED)
# (WEIGHT O.OO) (DIRECTION -1))
judge.add_mop(mop_name='M-ADAPT-MIXED-OLD',
              absts={'M-ADAPT-SENTENCE'},
              slots={'old_severity': None,
                     'this_severity': judge.add_mop(absts={'M-LESS-THAN'}, slots={'to': 'old_severity'}, is_default_mop=True),
                     'old_motive': justified,
                     'this_motive': unjustified,
                     'weight': 0.0,
                     'direction': -1}, is_default_mop=True)

# (DEFMOP M-ADAPT-MIXED-NEW (M-ADAPT-SENTENCE) (THIS-SEVERITY NIL)
# (OLD-SEVERITY M-LESS-THAN (TO OLD-SEVERITY)) (OLD-MOTIVE M-UNJUSTIFIED)
# (THIS-MOTIVE M-JUSTIFIED)
# (WEIGHT 0.00) (DIRECTION 1))
judge.add_mop(mop_name='M-ADAPT-MIXED-NEW',
              absts={'M-ADAPT-SENTENCE'},
              slots={'this_severity': None,
                     'old_severity': judge.add_mop(absts={'M-LESS-THAN'}, slots={'to': 'old_severity'}, is_default_mop=True),
                     'old_motive': unjustified,
                     'this_motive': justified,
                     'weight': 0.0,
                     'direction': 1}, is_default_mop=True)
###

event_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': ted, 'object': al, 'freq': once})
event_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': al, 'object': ted, 'freq': once})
event_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': stab, 'actor': ted, 'object': al, 'freq': repeatedly})
case_1_events = judge.add_mop(absts={'M-EVENT-GROUP'}, mop_type='instance', slots={1: event_1, 2: event_2, 3: event_3})
outcome_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': al})
outcome_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': ted})
outcome_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': dead, 'actor': al})
case_1_outcomes = judge.add_mop(absts={'M-OUTCOME-GROUP'}, mop_type='instance', slots={1: outcome_1, 2: outcome_2, 3: outcome_3})
case_1_slots = {'crime_type': homicide, 'defendant': ted, 'victim': al, 'events': case_1_events, 'outcomes': case_1_outcomes, 'sentence': 40}


# Define the events
event_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': strike, 'actor': randy, 'object': chuck, 'freq': repeatedly})
event_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': strike, 'actor': chuck, 'object': randy, 'freq': repeatedly})
event_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': randy, 'object': chuck, 'freq': once})
event_4 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': slash, 'actor': chuck, 'object': randy, 'freq': once})
event_5 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': stab, 'actor': randy, 'object': chuck, 'freq': repeatedly})
# Combine the events into a list
case_2_events = judge.add_mop(absts={'M-EVENT-GROUP'}, mop_type='instance', slots={1: event_1, 2: event_2, 3: event_3, 4: event_4, 5: event_5})
# Define the outcomes
outcome_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': chuck})
outcome_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': randy})
outcome_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': chuck})
outcome_4 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': cut, 'actor': randy})
outcome_5 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': dead, 'actor': chuck})
# Combine the outcomes into a list
case_2_outcomes = judge.add_mop(absts={'M-OUTCOME-GROUP'}, mop_type='instance', slots={1: outcome_1, 2: outcome_2, 3: outcome_3, 4: outcome_4, 5: outcome_5})
# Define the slots for the case
case_2_slots = {
    'crime_type': homicide,
    'defendant': randy,
    'victim': chuck,
    'events': case_2_events,
    'outcomes': case_2_outcomes,
    'sentence': 40
}
# Create the case MOP instance
# Judge the case
judge.judge_case(case_1_slots)
judge.judge_case(case_2_slots)

# Define the events
event_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': slap, 'actor': david, 'object': tim, 'freq': several_times})
event_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': strike, 'actor': tim, 'object': david, 'freq': several_times})
event_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': knock_down, 'actor': david, 'object': tim, 'freq': once})
event_4 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-EVENT'}, slots={'action': stab, 'actor': tim, 'object': david, 'freq': several_times})
# Combine the events into a list
case_3_events = judge.add_mop(absts={'M-EVENT-GROUP'}, mop_type='instance', slots={1: event_1, 2: event_2, 3: event_3, 4: event_4})
# Define the outcomes
outcome_1 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': tim})
outcome_2 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': bruised, 'actor': david})
outcome_3 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': knocked_down, 'actor': tim})
outcome_4 = judge.add_mop(mop_type='instance', absts={'M-FIGHT-OUTCOME'}, slots={'state': dead, 'actor': david})
# Combine the outcomes into a list
case_3_outcomes = judge.add_mop(absts={'M-OUTCOME-GROUP'}, mop_type='instance', slots={1: outcome_1, 2: outcome_2, 3: outcome_3, 4: outcome_4})
# Define the slots for the case
case_3_slots = {
    'crime_type': homicide,
    'defendant': tim,
    'victim': david,
    'events': case_3_events,
    'outcomes': case_3_outcomes,
}
# Create the case MOP instance
# Judge the case

# judge.judge_case(case_3_slots)
judge.set_stochastic_decision_making(0.0)
judge.judge_case(case_3_slots)

judge.check_for_mops_not_in_specs()
# for q in range(11):
#     judge.set_stochastic_intelligence(q / 10.0)
#     tests = []
#     for test in range(10):
#         sibling = judge.get_sibling(None, 'I-M-FIGHT-EVENT.102')
#         tests.append(sibling.mop_name)
#     print(f"Decision Making={q}, results={tests}")

sqlite3_db = "judge.sqlite"
export_cbr_sqlite(judge, sqlite3_db)

# Print the current working directory
print(f"Current working directory: {os.getcwd()}")

# Verify that the file has been created
dot = make_graphviz_graph(judge, include_slot_edges=False)
with open("judge.dot", "w") as out_dot:
    out_dot.write(dot)


fmt = "svg"
dot_command = f"dot -Kfdp -T{fmt} -ojudge.{fmt} judge.dot"
print(f"Running command: {dot_command}")
os.system(dot_command)

# Open the generated SVG file
svg_file = f"judge.{fmt}"
if os.path.exists(svg_file):
    print(f"Opening file: {svg_file}")
    subprocess.run(f"start {svg_file}", shell=True, check=True)
else:
    print(f"Failed to create SVG file: {svg_file}")

# Export the CBR data to the SQLite database
# export_cbr_sqlite(judge, sqlite3_db, ['judge', 'judge_case'])
#
# newsup = romancer.supervisor.singlethreadsupervisor.SingleThreadSupervisor()
# newenv = romancer.environment.singlethreadenvironment.SingleThreadEnvironment(sup, None, None)
# reloaded_judge = load_cbr_sqlite(sqlite3_db, newenv, cbr.CaseBasedReasoner)
#
# reload_case_slots = {
#     'crime_type': reloaded_judge.mops['I-M-HOMICIDE'],
#     'defendant': reloaded_judge.mops['I-M-TIM'],
#     'victim': reloaded_judge.mops['I-M-DAVID'],
#     'events': reloaded_judge.mops['I-M-EVENT-GROUP.128'],
#     'outcomes': reloaded_judge.mops['I-M-OUTCOME-GROUP.133'],
#     'escalations': reloaded_judge.mops['I-M-ESCALATION-GROUP.140'],
#     'motives': reloaded_judge.mops['I-M-MOTIVE-GROUP.145'],
#     'old': reloaded_judge.mops['I-M-CRIME.123'],
#     'sentence': 30
# }
#
# print("Judge me judge me judge me")
# reloaded_judge.judge_case(reload_case_slots)

# dot = make_graphviz_graph(judge, include_slot_edges=False)
# with open("judge.dot", "w") as out_dot:
#     out_dot.write(dot)
# fmt = "svg"
# os.system(f"dot -Kfdp -T{fmt} -ojudge.{fmt} judge.dot 2>/dev/null && xdg-open judge.{fmt}")
 #the aggressor is the one that is killed so sentence is less bad and 30 years