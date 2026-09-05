from romancer.environment.object import ImprovedRomancerObject, LoggedList, LoggedSet, LoggedDict
import networkx as nx

# class MOPSlot(ImprovedRomancerObject):
#     '''A structure to contain role, filler information. The reason that MOPs are not implemented with ordinary Python slots is that they can be dynamically updated and their slots have associated filler MOPs.'''

#     def __init__(self, environment, time, role, filler):
#         super().__init__(environment, time)
#         self.unlogged_attrs.append('role')
#         self.role = role # e.g., 'actor', 'object'
#         self.filler = filler # can be any MOP

class MOPError(Exception):
    pass


def is_satisfied(constraint, filler, slots):
    '''Returns True if filler satisfies the conditions specified by constraint. A constraint is satisfied if:
 
    1. The contraint is False or None.
    2. The constraint is a Pattern MOP whose abstraction function returns True when called with constraint, filler, and slots.
    3. The constraint is an abstraction of the filler.
    4. The constraint is an instance MOP and the filler is empty. The slot source can inherit the instance when needed.
    5. The constraint has at least one slot, the filler is not empty, and all of the slots are satisfied by the slots of the filler.
 
    Slotless abstractions are treated specially, because they have no slots to constrain what can go under them.''' # What should we return in this case?
 
    g = constraint is None
    if g:
        return g 
    if isinstance(constraint, MOP) and constraint.is_pattern():
        fn = constraint.inherit_filler('abst_fn')
        return fn(constraint, filler, slots)
    a = isinstance(constraint, MOP) and isinstance(filler, MOP) and constraint.is_abstraction(filler)
    if a:
        return a
    if isinstance(constraint, MOP) and constraint.is_instance_mop() and filler is None: # now this condition matches more closelt the description
        return True
    if isinstance(constraint, MOP) and len(constraint.slots) > 0 and filler is not None:
        if constraint.slots_satisfied_by(filler): #this is new
            return True
    if not isinstance(constraint, MOP) and filler is None:
        return True
    return False # default: return None or False



def mop_equal(mop1, mop2):
    '''Returns mop1 if mop1 and mop2 are the same.'''
    if len(mop1.slots) == 0 and len(mop2.slots) == 0:
        return
    if mop1.includes(mop2) and mop2.includes(mop1):
        return mop1
    

def unlink_abstraction(mop1, mop2):
    if mop1.is_abstractionraction(mop2):
        mop1.absts.remove(mop2)
        mop2.specs.remove(mop1)

    if mop2.is_abstraction(mop1):
        mop2.absts.remove(mop1)
        mop1.specs.remove(mop2)


class MOP(ImprovedRomancerObject):
    '''An implementation of Roger Schank's concept of Memory Organization Packages (MOPs) designed to work with ROMANCER's simulation paradigm.

    This implementation is based on chapter three of Christopher Riesbeck and Roger Schank, _Inside Case-Based Reasoning_ (Lawrence Erlbaum, 1989).'''

    def __init__(self, environment, time, parent, mop_name, absts=None, specs=None, slots=None, mop_type='instance', is_default_mop=False, is_core_cbr_mop=False, num_mops=0):
        super().__init__(environment, time)
        if not absts:
            absts = set()   
        if not specs:
            specs = set()
        if not slots:
            slots = {} 
        if not mop_name:
            mop_name = self.make_name(list(absts), mop_type, num_mops)

        self.create_seq = parent.get_next_mop_seq()
        self.delete_seq = None
        self.unlogged_attrs.append('parent')
        self.parent = parent # parent is case-based reasoner containing collection of associated MOPs
        self.unlogged_attrs.append('mop_name')
        self.mop_name = mop_name # string giving name of MOP
        self.absts = LoggedSet(absts, self, "absts") # the immediate abstractions of this MOP--those that are exactly one abstraction link above it
        # self, data, parent, varname
        self.specs =  LoggedSet(specs, self, "specs") # the immediate specializations of this MOP--those that are exactly one abstraction link below it
        self.slots = LoggedDict(slots, self, "slots") # dict associating roles (names) with filler structures (MOPs)
        self.unlogged_attrs.append('mop_type')
        self.mop_type = mop_type # 'instance' or 'mop'
        self.is_default = is_default_mop
        self.is_core_cbr = is_core_cbr_mop

    def update_delete_seq(self):
        self.delete_seq = self.parent.get_next_mop_seq()

    def is_abstract_mop(self):
        '''Returns True if this MOP is an abstraction MOP.'''
        return self.mop_type == 'mop'

    def is_default_mop(self):
        # Core mops are automatically default, no matter what the caller said
        return (self.is_default or self.is_core_cbr)

    def is_core_cbr_mop(self):
        return self.is_core_cbr

    def is_instance_mop(self):
        '''Returns True if this MOP is an instance MOP.'''
        return self.mop_type == 'instance'


    def is_abstraction(self, spec): # abst.is_abstraction(spec)
        '''Returns True if other is an abtraction, not necessarily immediate, of self (specialization).'''
        '''Returns True when self is a is a specialization of other / other is a specializtion of slef (not necessarily immediate).'''
        # the other mop is in the mops abstractions
        return self == spec or self in spec.calc_all_abstractions()


    def calc_all_abstractions(self):
        '''Calculates all the abstractions of this MOP, not limited to immediate abstractions.'''
        # create a set of all MOPs "upstream" of self:
        # GOAL: lowest-level abstractions appear first in the list
        all_absts = []

        # loop over self's absts:
        for abst in self.absts:
            this_abst = abst if isinstance(abst, MOP) else self.parent.mops[abst]
            all_absts.append(this_abst) # add the immediate abst
            all_absts += this_abst.calc_all_abstractions() # add the absts of that abst

            # # call calc_all_absts on each abstraction
            # all_absts.update(abst.calc_all_abstractions())
            # # add the abst to your set
            # all_absts.add(abst)

        # return the list of abstractions
        return all_absts


    def is_group(self):
        '''Returns True if MOP is specialization of 'M-GROUP'. Group MOPs are used to hold groups of MOPs, e.g., the group of steps in a recipe or the group of events in a fight.'''
        m_pattern = self.parent.name_mop('M-GROUP')
        return m_pattern.is_abstraction(self) # Perhaps M-GROUP should be distinct Python subclasses of MOP

    def is_pattern(self):
        '''Returns True if MOP is specialization of 'M-PATTERN'. Pattern matching MOPs are used to hold pattern matching and role filling information.'''
        m_pattern = self.parent.name_mop('M-PATTERN')
        return m_pattern.is_abstraction(self) # Perhaps M-PATTERN should be distinct Python subclasses of MOP

    def add_role_filler(self, role, filler, verbose=False):
        # if not isinstance(filler, MOP):
        #     raise TypeError(f'Filler {filler} is not MOP')
        self.slots[role] = filler
        if verbose:
            print(f"{self}:{role} <= {filler}")   
        return filler


    def role_filler(self, role):
        if role not in self.slots:
            # raise KeyError('MOP lacks slot: ', role)
            return None
        else:
            return self.slots[role]


    def link_abst(self, abst): # self.link_abst(other)
        assert abst.is_abstract_mop(), f"{abst} is not abstract MOP" # equivilent of "insist" macro in Schank/Riesbeck code
        assert not self.is_abstraction(abst), f"Circular reference with abst:{abst}, spec:{self}" # don't create circular reference
        # if not self.is_abstraction(other): # abst is not currently abstract of self
        self.absts.add(abst) # make abst abstraction of self
        abst.specs.add(self) # make self specialization of abst
        return self


    def unlink_abst(self, abst): # self.unlink_abst(abst)
        if abst.is_abstraction(self): # abst is currently an abstraction of self
            self.absts.remove(abst) # remove abst as abstraction of self
            abst.specs.remove(self) # remove self as specialization of abstract
            return self
        # if self.is_abstraction(mop):
        #     mop.absts.remove(self)
        #     self.specs.remove(mop)
        #     return mop
        

    def inherit_filler(self, role):
        all_absts = self.calc_all_abstractions()
        for abst in all_absts:
            try:
                filler = abst.role_filler(role)
            except KeyError:
                filler = None
            if filler is not None:
                return filler


    def get_filler(self, role):
        try:
            filler = self.role_filler(role)
        except KeyError:
            filler = None
        if filler is not None:
            return filler
        else:
            inheritance = self.inherit_filler(role)
            if isinstance(inheritance, MOP) and inheritance.is_instance_mop():
                return inheritance
            # need to check if M-FUNCTION is an abstraction of inheritance (how?)
            elif callable(inheritance):
                return inheritance
            elif isinstance(inheritance, MOP):
                fn = inheritance.get_filler('calc_fn')
                if fn is not None:
                    new_filler = fn(inheritance, self)
                    if new_filler:
                        self.add_role_filler(role, new_filler)
                        return new_filler
            else:
                return inheritance
                    # raise MOPError(f"No filler for role {role} in mop {self}")


    def path_filler(self, path):
        mop = self
        for role in path:
            mop = mop.get_filler(role)
            # if not mop:
            #     return mop
        return mop
        

    def slots_satisfied_by(self, slot_source):
        '''Returns True if every slot in self is 'satisfied' by corresponding slot in slot_source. Slot_source is usually an instance, but it can also be a dict of slots. The slot fillers in self are treated as constraints on the slot fillers in slot_source. Equivilent of SLOTS-ABSTP in Schank/Riesbeck.'''
        if self.is_abstract_mop() and len(self.slots) > 0:
            for role, filler in self.slots.items():
                if isinstance(slot_source, MOP):
                    # eg, is ROOT-VEG's 'calories' satisfied by CARROT's calories?
                    # eg, is M-CALC-ESCALATION-MOTIVE's 'escalation' satisfied by I-M-CALC's 'escalation'?
                    comparison_filler = slot_source.get_filler(role)
                    s = is_satisfied(filler, comparison_filler, slot_source)
                else:
                    s = is_satisfied(filler, slot_source[role], slot_source) # if slot_source is dictionary
                if not s:
                    return False
            return True
            # I think this is correct

    def includes(self, mop2):
        '''Returns self if it is of the same mop_type and includes every slot in mop2. Self can have slots not in mop2.'''
        if self.mop_type == mop2.mop_type:
            for role in mop2.slots.keys():
                if role not in self.slots:
                    return False
                if self.get_filler(role) != mop2.slots[role]:
                    return False
            return self


    def get_twin(self):
        '''Returns the first MOP that it can find in memory that is equal to self, if any.'''
        for abst in self.absts:
            for spec in abst.specs:
                if spec is not self:
                    if mop_equal(spec, self):
                        return spec


    def refine_instance(self):
        '''Takes each abstraction of self, which should be an instance, and tries to replace it with one or more specializations of the abstraction. It repeats this process until all abstractions of self are as specialized as possible.'''
        if self.mop_type != 'instance':
            raise ValueError('Cannot refine abstraction MOP')
        else:
            for abst in self.absts:
                if self.mops_abstp(abst.specs):
                    self.unlink_abst(abst)
                    self.refine_instance()
                    break


    def mops_abstp(self, mops_list):
        '''Looks at each MOP in mops_list. If the MOP can abstract self, a link from self to the MOP is made. returns True if at least one such MOP was found.'''
        if self.mop_type != 'instance':
            raise ValueError('Cannot refine abstraction MOP')
        else:
            refinement = False
            for mop in mops_list:
                if mop.slots_satisfied_by(self):
                    refinement = True
                    self.link_abst(mop)
            return refinement

    
    def has_legal_absts(self):
        '''This method is used to support the install_instance method on the case-based reasoner class. It unlnks every immediate abstraction of instance that is not a legal place to put instance, and returns whatever immediate abstractions are left.'''
        abst_list = self.absts.data.copy()
        for abst in abst_list:
            if not abst.is_legal_abst(self):
                self.unlink_abst(abst)
        return self.absts


    def is_legal_abst(self, instance): # abst.is_legal_abst(instance)
        '''Returns True if self is a legal place to put instance, i.e., self is not slotless and does not have abstractions below it.'''
        if len(self.slots) > 0:
            for spec in self.specs:
                if not spec.is_instance_mop():
                    return False
            return True
        else:
            return False


    def reindex_siblings(self):
        '''This method is used to support the install_abstraction method on the case-based reasoner class. It finds all instances that are immediate specializations of the immediate abstractions of self. The instances are unlinked from their abstractions and relinked to self. Returns self.'''
        for abst in self.absts:
            for spec in abst.specs:
                if spec.is_instance_mop() and self.slots_satisfied_by(spec):
                    spec.unlink_abst(abst)
                    spec.link_abst(self)
        return self


    # this is probably superfluous for this implementation
    def group_size(self):
        '''If self is a group MOP, return the number of slots it contains. Returns None otherwise.'''
        if self.is_group():
            return len(self.slots)
        else:
            raise MOPError(f"Cannot give group size for non-group MOP {self}")


    def group_to_list(self):
        '''Returns a list of the members of the group.'''
        if not self.is_group():
            raise TypeError('Non-group MOP cannot be converted to list.')
        l = list()
        for i in self.slots.keys():
            l.append(self.get_filler(i))
        return l

    def list_to_group(self, I):
        self.slots_to_mop()

    def get_graph(self):
        '''Returns a networkx graph representing the MOP and its abstractions and specializations.'''
        G = nx.Graph()
        G.add_node(self.mop_name)

        for spec in self.specs:
            G = nx.union(G, spec.get_graph())
            G.add_edge(self.mop_name, spec.mop_name)
        return G      

    def __repr__(self):
        return self.mop_name


    def __str__(self):
        if self.mop_name:
            return self.mop_name
        return "None"


    def make_name(self, absts, mop_type, num_mops):
        '''Returns a name for a new MOP based on its abstractions and mop_type.'''
        name = str(absts[0])
        if mop_type == 'instance':
            name = 'I-' + str(absts[0]) + '.' + str(num_mops + 1)
        if mop_type == 'mop':
            name = str(absts[0]) + '.' + str(num_mops + 1)
        return name

    
    def equals(a,b):
        return a == b
    
    def less_than(a,b):
        return a < b