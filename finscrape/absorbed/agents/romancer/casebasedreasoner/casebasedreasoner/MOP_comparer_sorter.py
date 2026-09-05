from casebasedreasoner.mop import MOP
from romancer.environment.object import LoggedDict
import matplotlib.pyplot as plt
import copy
import numpy as np

class ComparerSorterError(Exception):
    pass

'''
This class is used by the stochastic case selector.

Given a CBR, and the name of a mop [that is already inserted into the CBR], and a list of mop names to compare it to 
Return the list of compare_mop_names, sorted by comparison-to-specific-mop.
"Most like" should be first on the returned list, and "least like" should be last.
'''
class MOPComparerSorter:
    # This method is the one that will be called by the CBR while doing stochastic tests
    # There is a dummy implementation in here that should not be used by anyone, ever.
    def compare_mops_and_sort(self, cbr, mop_name, compare_mop_names):
        return sorted(compare_mop_names)


# Recursively get all slot values, with "closer" keys taking priority over "further" keys
# Then do a naive cosine-distance-like metric
class SimpleSlotSorter(MOPComparerSorter):
    def compare_mops_and_sort(self, cbr, mop_name, compare_mop_names):
        ''' Return a map of mop_name => similarity_score, showing how similar
        every other mop in this CBR is, to the mop requested '''
        this_mop_dict = self.get_mop_slots_r(cbr, mop_name)
        other_dicts = {}
        # In keeping with get_sibling: Only search through MOPs that come from the same abst as the one we're holding

        for other_mop in compare_mop_names:
            other_mop_dict = self.get_mop_slots_r(cbr, other_mop)
            other_dicts[other_mop] = other_mop_dict

        self.normalise_mop_dicts(this_mop_dict, other_dicts)

        comparisons = {}
        for other_mop in other_dicts:
            comparisons[other_mop] = self.compare_two_mop_dicts(this_mop_dict, other_dicts[other_mop])

        sorted_items = sorted(comparisons.items(), key=lambda x: x[1], reverse=True)
        sorted_mops = [item[0] for item in sorted_items]
        return sorted_mops

    def get_mop_slots_r(self, cbr, mop_name, root_mop=None, curr_dict=None, depth=0):
        ''' For a given mop, return a map of all slot->slot_value.
         Do this recursively [ie, if a slot references another mop, go down into that]
          A higher-level dict value should not be overwritten by a lower level one '''
        if root_mop is None:
            root_mop = mop_name
        if curr_dict is None:
            curr_dict = dict()
        if mop_name not in cbr.mops:
            return curr_dict
        if depth > 200:
            raise ComparerSorterError("Recursively getting slots went too deep (cycle in graph?)")

        this_mop = cbr.mops[mop_name]
        recurse_mop_queue = []

        for slot in this_mop.slots:
            # Already have a key
            if slot in curr_dict:
                continue

            slot_val = this_mop.slots[slot]
            if slot_val == root_mop:
                continue
            if slot_val in cbr.mops:
                curr_dict[slot] = slot_val
                recurse_mop_queue.append(slot_val)
            elif isinstance(slot_val, MOP):
                mop_name = slot_val.mop_name
                curr_dict[slot] = slot_val.mop_name
                recurse_mop_queue.append(slot_val)
            elif isinstance(slot_val, (str, int, float)):
                curr_dict[slot] = slot_val
            elif callable(slot_val):
                # print(f"Slot {slot} on mop {mop_name} is a callable. Fix plz")
                pass
            elif slot_val is None:
                pass
            # else:
            #     print(f"Slot {slot} on mop {mop_name} has unknown slot type {type(slot_val)}")

        for r_mop in recurse_mop_queue:
            self.get_mop_slots_r(cbr, r_mop, root_mop, curr_dict, depth=depth + 1)

        return curr_dict

    def compare_two_mop_dicts(self, mop_1, mop_2):
        ''' Provide two dictionaries, representing two mops. get_mop_slots_r(mop_name) creates those dicts '''
        # Function is not required to be symmetric; it's reasonable to only calculate based on keys in mop_1
        # Function should return float >0, where 0 = "nothing in common", and higher numbers = "lots in common"
        # For now, naively calculate cosine distance. If values are strings, then they either match, or do not match.
        retval = 0.0
        for k1 in mop_1:
            if k1 not in mop_2:
                # No comparison to be done
                continue

            v1 = mop_1[k1]
            v2 = mop_2[k1]
            if not isinstance(v1, type(v2)):
                # Don't know how to compare this
                print(f"Don't know how to compare a {type(v1)} and a {type(v2)}")
                continue
            if isinstance(v1, str):
                if v1 == v2:
                    retval += 1
            elif isinstance(v1, (int, float)):
                retval -= pow((v1 - v2), 2)
            else:
                print(f"Don't know how to compare two {type(v1)}")

        return retval

    def normalise_mop_dicts(self, key_mop, other_dicts):
        for k in key_mop.keys():
            if isinstance(key_mop[k], (int, float)):
                min_val = 1000000
                max_val = -1000000
                for other_mop in other_dicts.keys():
                    other_dict = other_dicts[other_mop]
                    if k in other_dict:
                        min_val = min(min_val, other_dict[k])
                        max_val = max(max_val, other_dict[k])
                for other_mop in other_dicts.keys():
                    other_dict = other_dicts[other_mop]
                    if k in other_dict:
                        other_dict[k] = (other_dict[k] - min_val) / (max_val - min_val)
                key_mop[k] = (key_mop[k] - min_val) / (max_val - min_val)


class ELRPerceptMOPComparer(MOPComparerSorter):
    def __init__(self, keycols=None, valcols=None):
        if keycols is None:
            keycols = ["weapon", "target"]
        if valcols is None:
            valcols = ["count"]
        self.keycols = keycols
        self.valcols = valcols


    def compare_mops_and_sort(self, cbr, mop_name, compare_mop_names, visual=False):
        pivot_percepts = self.get_percept_list(cbr, mop_name)
        # pivot_percepts.sort(key=lambda x: (x['weapon'], x['target']))
        compare_percepts = { comp_mopname : self.get_percept_list(cbr, comp_mopname) for comp_mopname in compare_mop_names }
        distances = { comp_mopname : self.compare_two_percept_lists(pivot_percepts, compare_percepts[comp_mopname]) for comp_mopname in compare_mop_names }
        sorted_mopnames = sorted(distances, key=lambda k: distances[k])
        if visual:
            print("For mop " + mop_name + " " + str(pivot_percepts))
            self.visualise(pivot_percepts, compare_percepts, sorted_mopnames, 20)
            reverse_mopnames = sorted(distances, key=lambda k: distances[k], reverse=True)
            self.visualise(pivot_percepts, compare_percepts, reverse_mopnames, 20, "rev")
            for i in range(min(len(sorted_mopnames), 10)):
                these_percepts = compare_percepts[sorted_mopnames[i]]
                these_percepts.sort(key=lambda x: (x['weapon'], x['target']))
                print(f"#{i}: {sorted_mopnames[i]} = {distances[sorted_mopnames[i]]} - {these_percepts}")
        return sorted_mopnames

    # Return a map of sorted lists, of the possible values for each key
    def get_possible_keys(self, compare_percepts):
        retval = { k : [] for k in self.keycols }
        for percepts in compare_percepts.values():
            for p in percepts:
                for k in self.keycols:
                    retval[k].append(p[k]) if p[k] not in retval[k] else None
        for lst in retval.values():
            lst.sort()
        return retval

    def create_heatmap(self, possible_keys, percepts):
        k0 = self.keycols[0]
        k1 = self.keycols[1]
        heatmap = np.full((len(possible_keys[k0]), len(possible_keys[k1])), np.nan)
        for p in percepts:
            idx_a = possible_keys[k0].index(p[k0])
            idx_b = possible_keys[k1].index(p[k1])
            cnt = p[self.valcols[0]]
            if cnt > 0:
                heatmap[idx_a, idx_b] = cnt
        return heatmap


    def visualise(self, pivot_percepts, compare_percepts, sorted_keys, n_charts, suffix=""):
        possible_keys = self.get_possible_keys(compare_percepts)

        heatmap_compare = self.create_heatmap(possible_keys, pivot_percepts)
        fig, axes = plt.subplots(nrows=n_charts, ncols=2, figsize=(10, 5 * n_charts))
        for i, percepts in enumerate([compare_percepts[k] for k in sorted_keys]):
            if i >= n_charts:
                break
            cax = axes[i][0].imshow(heatmap_compare, aspect='auto')
            axes[i][0].set_title(f"Compare_to")
            axes[i][0].set_xlabel(self.keycols[0])
            axes[i][0].set_ylabel(self.keycols[1])
            axes[i][0].set_xticks([])
            axes[i][0].set_yticks([])

            heatmap = self.create_heatmap(possible_keys, percepts)
            cax = axes[i][1].imshow(heatmap, aspect='auto')
            axes[i][1].set_title(f"{i} {suffix}: {sorted_keys[i]}")
            axes[i][1].set_xlabel(self.keycols[0])
            axes[i][1].set_ylabel(self.keycols[1])
            axes[i][1].set_xticks([])
            axes[i][1].set_yticks([])
        plt.tight_layout()
        plt.show()
        plt.close()


    def compare_two_percept_groups(self, pg1, pg2):
        pl1 = pg1.group_to_list()
        pl2 = pg2.group_to_list()
        return self.compare_two_percept_lists(pl1, pl2)


    def compare_two_percept_lists(self, pl1, pl2):
        # For each item in pl1, Find the closest item in p2, then add that to the cumulative distance
        # Does not need to be symmetric; comp(pl1, pl2) does not need to equal comp(pl2, pl1)
        total_dist = 0
        for p1 in pl1:
            data = {}
            for i in range(len(pl2)):
                p2 = pl2[i]
                data[i] = self.singlepercept_dist(p1, p2)
            min_dist_idx = min(data, key=lambda k: data[k])
            total_dist += data[min_dist_idx]
        return total_dist

    def singlepercept_dist(self, p1, p2):
        # What's the distance between a pair of single percepts
        dist = 0.0
        # Use taxicab distance on keycols, multiply by 100, add taxicab on valcols
        for k in self.keycols:
            try:
                dist += abs(float(p1[k]) - float(p2[k]))
            except:
                pass
        dist *= 100
        for k in self.valcols:
            try:
                dist += abs(float(p1[k]) - float(p2[k]))
            except:
                pass
        return dist

    def get_percept_list(self, cbr, mop_name):
        flattened_percepts = self.get_flattened_percept_list(cbr, mop_name)
        combined_percepts = self.combine_percept_list(flattened_percepts)
        return combined_percepts

    def combine_percept_list(self, percept_list):
        # We may have percepts that need combining [eg same weapon/target pairing should have their counts summed]
        # This is destructive on the passed list. Pass a deepcopy if you don't want that
        combined_percept_list = []

        while len(percept_list) > 0:
            percept = percept_list.pop(0)
            i = 0
            while i < len(percept_list):
                p_test = percept_list[i]
                is_match = True
                for k in self.keycols:
                    if p_test[k] != percept[k]:
                        is_match = False
                        break
                if is_match:
                    # print("Combining " + str(percept) + " and " + str(p_test))
                    for valcol in self.valcols:
                        percept[valcol] += p_test[valcol]
                    percept_list.pop(i)
                else:
                    i+=1

            combined_percept_list.append(percept)
        return combined_percept_list

    # For a given mop, get all the individual percepts as a single list-of-dicts
    #  May have to traverse lists mutliple times, recursively
    def get_flattened_percept_list(self, cbr, mop_name):
        # Not doing any sanity checking. If you don't pass this a scenario, expect it to break
        mop = cbr.mops[mop_name]
        percepts = mop.slots["percepts"]
        group_mop = cbr.mops["M_percept_group"]
        return self.get_flattened_percept_list_r(cbr, percepts, group_mop)

    def get_flattened_percept_list_r(self, cbr, percept_mop, group_mop, depth=0):
        retval = []
        if group_mop.is_abstraction(percept_mop):
            for next_mop in percept_mop.slots.values():
                retval.extend(self.get_flattened_percept_list_r(cbr, next_mop, group_mop, depth+1))
        else:
            slots = percept_mop.slots
            # Sometimes the percept is just a list of things.
            #  It still gets stored as a key then a value that is a group.
            #  Throw away the key and start again with the value
            if 1 == len(slots):
                slotval = next(iter(slots.values()))
                if isinstance(slotval, MOP) and group_mop.is_abstraction(slotval):
                    retval.extend(self.get_flattened_percept_list_r(cbr, slotval, group_mop))
                    return retval
            if isinstance(slots, LoggedDict):
                slots = slots.data
            retval.append(copy.deepcopy(slots))
        # print(".".join(["" for _ in range(depth+1)]) + " " + str(len(retval)))
        return retval


class HLRComparerSorter(MOPComparerSorter):
    def compare_mops_and_sort(self, cbr, mop_name, compare_mop_names):
        ''' Return a map of mop_name => similarity_score, showing how similar
        every other mop in this CBR is, to the mop requested '''
        this_mop_dict = self.get_mop_slots_r(cbr, mop_name)
        other_dicts = {}
        # In keeping with get_sibling: Only search through MOPs that come from the same abst as the one we're holding

        for other_mop in compare_mop_names:
            other_mop_dict = self.get_mop_slots_r(cbr, other_mop)
            other_dicts[other_mop] = other_mop_dict

        # self.normalise_mop_dicts(this_mop_dict, other_dicts)

        comparisons = {}
        for other_mop in other_dicts:
            comparisons[other_mop] = self.compare_two_mop_dicts(this_mop_dict, other_dicts[other_mop])

        sorted_items = sorted(comparisons.items(), key=lambda x: x[1], reverse=True)
        sorted_mops = [item[0] for item in sorted_items]
        return sorted_mops

    def get_mop_slots_r(self, cbr, mop_name, root_mop=None, curr_dict=None, depth=0):
        ''' For a given mop, return a map of all slot->slot_value.
         Do this recursively [ie, if a slot references another mop, go down into that]
          A higher-level dict value should not be overwritten by a lower level one '''
        if root_mop is None:
            root_mop = mop_name
        if curr_dict is None:
            curr_dict = dict()
        if mop_name not in cbr.mops:
            return curr_dict
        if depth > 200:
            raise ComparerSorterError("Recursively getting slots went too deep (cycle in graph?)")

        this_mop = cbr.mops[mop_name]
        recurse_mop_queue = []

        for slot in this_mop.slots:
            # Already have a key
            if slot in curr_dict:
                continue

            slot_val = this_mop.slots[slot]
            if slot_val == root_mop:
                continue
            if slot_val in cbr.mops:
                curr_dict[slot] = slot_val
                recurse_mop_queue.append(slot_val)
            elif isinstance(slot_val, MOP):
                mop_name = slot_val.mop_name
                curr_dict[slot] = slot_val
                recurse_mop_queue.append(slot_val)
            elif isinstance(slot_val, (str, int, float)):
                curr_dict[slot] = slot_val
            elif callable(slot_val):
                # print(f"Slot {slot} on mop {mop_name} is a callable. Fix plz")
                pass
            elif slot_val is None:
                pass
            # else:
            #     print(f"Slot {slot} on mop {mop_name} has unknown slot type {type(slot_val)}")

        for r_mop in recurse_mop_queue:
            self.get_mop_slots_r(cbr, r_mop, root_mop, curr_dict, depth=depth + 1)

        return curr_dict


    def compare_two_percept_groups(self, pg1, pg2):
        pl1 = pg1.group_to_list()
        pl2 = pg2.group_to_list()
        return self.compare_two_percept_lists(pl1, pl2)

    def compare_two_percept_lists(self, pl1, pl2):
        # For each item in pl1, Find the closest item in p2, then add that to the cumulative distance
        # Does not need to be symmetric; comp(pl1, pl2) does not need to equal comp(pl2, pl1)
        total_dist = 0
        for p1 in pl1:
            data = {}
            for i in range(len(pl2)):
                p2 = pl2[i]
                data[i] = self.percept_difference(p1, p2)
            min_dist_idx = min(data, key=lambda k: data[k])
            try:
                total_dist += data[min_dist_idx]
            except:
                pass
        return total_dist


    def percept_difference(self, p1, p2):
        # What's the difference between percept p1 and percept p2
        difference = 0.0
        for p1_role, p1_filler in p1.slots.items():
            p2_filler = p2.get_filler(p1_role)
            if p2_filler and isinstance(p2_filler, type(p1_filler)): # they are the same type of thing
                if p1_role == 'actor' and isinstance(p2_filler, int):
                    difference += (p2_filler != p1_filler) * 10 # actor mistmatch means we should probably ignore
                elif isinstance(p2_filler, float) or isinstance(p2_filler, int):
                    difference += abs(p2_filler - p1_filler) # action/weapon/etc mismatch equal to difference
                elif isinstance(p2_filler, str):
                    difference += p1_filler != p2_filler # string mismatch has "size" 1
                else:
                    try:
                        difference += p2_filler - p1_filler # we must implement - (__sub__) in NamedTuples
                    except:
                        pass # fillers can't be subtracted
            else: # filler type mismatch means significant difference
                difference += 100
        return difference
                


    def compare_two_mop_dicts(self, mop_1, mop_2, verbose=False):
        ''' Provide two dictionaries, representing two mops. get_mop_slots_r(mop_name) creates those dicts '''
        # Function is not required to be symmetric; it's reasonable to only calculate based on keys in mop_1
        # Function should return float >0, where 0 = "nothing in common", and higher numbers = "lots in common"
        # For now, naively calculate cosine distance. If values are strings, then they either match, or do not match.
        retval = 0.0
        for k1 in mop_1:
            if k1 not in mop_2:
                # No comparison to be done
                continue

            v1 = mop_1[k1]
            v2 = mop_2[k1]
            if not isinstance(v1, type(v2)):
                # Don't know how to compare this
                if verbose:
                    print(f"Don't know how to compare a {type(v1)} and a {type(v2)}")
                continue
            if isinstance(v1, str):
                if v1 == v2:
                    retval += 1
            elif isinstance(v1, (int, float)):
                retval -= pow((v1 - v2), 2)
            elif isinstance(v1, MOP) and v1.is_group():
                retval -= self.compare_two_percept_groups(v1, v2)
            else:
                if verbose:
                    print(f"Don't know how to compare two {type(v1)}")

        return retval