import random

from romancer.environment.object import ImprovedRomancerObject, LoggedList, LoggedSet, LoggedDict
from romancer.agent.amygdala import UpdateAmygdalaParameters
from romancer.agent.reasoner import Reasoner
from romancer.agent.personlikeagent import PersonlikeActionROMANCERMessage
from romancer.commandpe.watchlist import CommandPEWatchlistItem
from collections import UserList
from heapq import heapify, heappush, heappop
from scipy import optimize
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import math
from collections import namedtuple


class EscalationLadder(UserList):
    '''The EscalationLadderReasoner stores its ontology in an instance of the EscalationLadder class. This is an ordered collection of Rung objects representing the ascending levels of escalation. The information about what internal perceptions (perception filter outpus) will cause the reasoner to match against these rungs and perceive that a particular rung of the escalation ladder has been reached is stored in the Rung objects, as are the actions that the reasoner considers appropriate at this rung of the escalation ladder given its intentions/internal state.

    Note that this EscalationLadder is not logged and is therefore meant to be treated as a static, unchanging object in the context of the simulation.

    A key purpose for the EscalationLadder class that is not yet implemented here is a visualization method.'''

    # default __init__ method is probably already sufficient here, although it might be appropriate to make it assert that the EscalationLadder contains only Rung objects

    def next_rung(self, current_rung, default_retval=None):
        '''This method returns the next rung on the escalation ladder after current_rung, or None if current_rung is the top rung.'''
        rung_index = self.data.index(current_rung)
        if rung_index < len(self.data) - 1:
            next_index = rung_index + 1
            return self.data[next_index], next_index
        else:
            return current_rung, rung_index

    def previous_rung(self, current_rung):
        '''The opposite of next_rung.'''
        rung_index = self.data.index(current_rung)
        if rung_index > 0:
            previous_index = rung_index - 1
            return self.data[previous_index], previous_index
        else:
            return current_rung, rung_index
        

    # for deliberating into the future
    def next_matched_rung(self, current_rung, reasoner, amygdala):
        matched = False
        next_rung = self.next_rung(current_rung)
        while next_rung:
            matched = next_rung.rung_matched(reasoner, amygdala)
            if matched:
                return next_rung
            next_rung = self.next_rung(next_rung)

    # for deliberaing present time
    def highest_matched_rung(self, current_rung, reasoner, amygdala):
        matched_rungs = [rung.rung_matched(reasoner, amygdala) for rung in self.data]
        # print(f"T={reasoner.environment.time}. {reasoner.identity} matched rungs: {matched_rungs}. n_percepts={len(reasoner.digested_percepts)}")

        matched_indices = [i for i, match in enumerate(matched_rungs) if match]
        highest_matched_rung = current_rung
        highest_matched_rung_idx = self.rung_number(current_rung)
        if len(matched_indices) > 0:
            highest_matched_rung_idx = max(matched_indices)
            highest_matched_rung = self.data[highest_matched_rung_idx]
        return highest_matched_rung, highest_matched_rung_idx


    def rung_number(self, rung):
        return self.data.index(rung)
    

class EscalationLadderRung():
    '''Much of the logic of the EscalationLadderReasoner is stored in EscalationLadderRung instances. This permits these rungs to exhibit custom behavior if necessary.'''
    rung_id = 1

    def __init__(self, match_attributes=None, actions=[], deescalation_actions=[], pbf_threshold = 1.0, amygdala_update=UpdateAmygdalaParameters(0, 0, 0, 0), name=""):
        self.match_attributes = match_attributes # a sequence of patterns that are used to check whether agent believes that this rung has been reached
        self.pbf_threshold = pbf_threshold # what stress level would trigger this rung regardless of match_attributes
        self.actions = actions # collection of actions that reasoner will take at this rung, associated with amount of time that must pass before/between those actions
        self.deescalation_actions = deescalation_actions # collection of actions that reasoner will take at this rung if it is attempting to de-escalate the situation, associated with amount of time that must pass before/between those actions
        self.amygdala_update = amygdala_update
        self.id = EscalationLadderRung.rung_id
        self.name = name
        EscalationLadderRung.rung_id += 1

    def rung_matched(self, reasoner, amygdala):
        if self.match_attributes is None:
            return False

        evaluate_op = getattr(self.match_attributes, 'evaluate', None)
        if callable(evaluate_op):
            return evaluate_op(reasoner, amygdala)

        # ANY attribute in match_attributes matches a digested percept
        for attribute, value in self.match_attributes.items():
            for percept in reasoner.digested_percepts:
                try:
                    for event in percept.events_list:
                        percept_value = event[attribute]
                        if value == percept_value:
                            return True # an attribute matched
                except AttributeError:
                    pass # not a problem
        return False
    

    def coerce_attribues_to_matcher(self, attributes):
        '''This method uses the information stored in match_attributes to return a Python callable with an EscalationLadderReasoner, Amygdala call signature. Returns True if these attributes are met based on current state of reasoner and amygdala, False otherwise.'''
        def matcher(reasoner, amygdala_params): # possibly create lexical closure storing information for use by matcher
            return False

        return matcher


    def update_planned_actions(self, reasoner):
        '''This method mutates the passed reasoner's planned_actions attribute. Defaults to simply resetting planned action queue. This method assumes that all matchers associated with this rung have been evaluated.'''
        reasoner.planned_actions.clear()


    def untaken_actions(self, actions, reasoner):
        '''This method returns a set of actions that are not in the reasoner's actions_taken list. It may be handy to override this method to get more subtle, custom behavior from certain rungs.'''
        # return set(reasoner.actions_taken).difference(actions) # FIX
        return actions

    def __repr__(self):
        return "Rung " + str(self.id)
    
class MatchAllRung(EscalationLadderRung):
    def rung_matched(self, reasoner, amygdala):
        dominant_response = amygdala.dominant_response()
        if dominant_response == amygdala.FREEZE_STR: # never escalate
            return False
        if dominant_response == amygdala.FIGHT_STR: # always escalate
            return True
        if dominant_response == amygdala.FLIGHT_STR: # try to de-escalate
            return False

        # if any digested percept's singular event matches all attributes, the rung is matched
        for percept in reasoner.digested_percepts:
            # we want to match EVERY attribute in match_attributes against SOME event in the percept's event list
            for event in percept.events_list:
                match = True # try to proce there ISN't a match
                for attribute, value in self.match_attributes.items():
                    try: # attempt to access the match attribute out of the current event
                        if event[attribute] != value:
                            match = False # at least one attribute does not match
                    except:
                        match = False # the event does not have the right attributes
                if match: # all rung attributes have a matching value in the event
                    return True
        return False # no event in any percept matches this rung

class EscalationLadderReasoner(Reasoner):
    '''
    '''

    def __init__(self,  environment, time, escalation_ladder, identity, current_rung = None,
                 planned_actions = None, actions_taken = None, digested_percepts = None,
                 cbr = None, cbr_train=True, cbr_run=False):
        super().__init__(environment, time)
        self.idle_time = 60*60 # Anytime we need to just throw a dummy event in the queue, use this delay on it
        self.escalation_ladder = escalation_ladder # an EscalationLadder instance
        self.identity = identity # 'blue' or 'red'
        self.planned_actions = list()
        if current_rung and current_rung in self.escalation_ladder: # rung of escalation ladder agent believes represents current state of conflict
            self.current_rung = current_rung
        elif current_rung == None:
            self.current_rung = self.escalation_ladder[0]
        else:
            raise ValueError('Current rung not in EscalationLadder')
        heapify(self.planned_actions) # ensure planned actions are heapified
        if planned_actions: # should planned_actions be a logged UserList?
            self._enqueue_actions(planned_actions)
        if actions_taken:
            self.actions_taken = LoggedList(data = sorted(actions_taken, key = lambda p: p[0]), parent = self, varname = 'actions_taken') # actions taken sorted in ascending chronological time
        else:
            self.actions_taken = LoggedList(data = list(), parent = self, varname = 'actions_taken')
        if digested_percepts:
            self.digested_percepts = LoggedList(data = digested_percepts, parent = self, varname = 'digested_percepts')
        else:
            self.digested_percepts = LoggedList(data = list(), parent = self, varname = 'digested_percepts')
        self.max_deliberation_time = self.time # maximum time to which reasoner has deliberated; should this be unlogged?
        self.most_recent_percept_time = self.time
        self.plot_time = []
        self.plot_rungs = []
        self.cbr = cbr
        self.cbr_train = cbr_train
        self.cbr_run = cbr_run
        self.redeliberate_action = None
        self.redeliberate_action = None
        self.capture_plot()

    def reset_reasoner(self, rung_num=0):
        self.rewind(0)
        self.digested_percepts.clear()
        self.actions_taken.clear()
        self.planned_actions.clear()
        self.current_rung = self.escalation_ladder[rung_num]

    def enqueue_digested_percept(self, digested_percept, percept_time):
        '''This method is used to update the EscalationLadderReasoner's internal state on the basis of the output of the egent's perception filter. What this does is enque the digested percept in the history of percepts digested by the reasoner, and update the reasoner's max_deliberation_time so that the next time that its deliberate method is called, its planned future actions will be recalculated if necessary.'''
        if percept_time < self.most_recent_percept_time:
            self.rewind(percept_time) # this
            self.max_deliberation_time = percept_time
            # what, if anything, should be done with planned_actions at this juncture?
            # presumably deliberate() should check if a new percept has been received since those actions were planned and then
            # edit planned actions accordingly
            # maybe add attr to EscalationLadderReasoner to act as flag for this, containing planned action most recent percept time?
            no_digested_percepts = len(self.digested_percepts)
            # pop self.digested_percepts until percepts are earlier than the  new digested percepts
            for i in range(no_digested_percepts):
                if self.digested_percepts.time > percept_time:
                    self.digested_percepts.pop()
                else:
                    break
            self.digested_percepts.append(digested_percept)
        elif percept_time == self.time: # this should be the case when the percept is the "next interesting event" processed by the supervisor
            self.max_deliberation_time = percept_time
            self.digested_percepts.append(digested_percept)

        if percept_time > self.most_recent_percept_time:
            self.most_recent_percept_time = percept_time


    def match_rung(self, max_time, amygdala):
        if self.cbr_run:
            new_scenario_slots = self.cbr.make_scenario_slots(percepts=self.digested_percepts, current_rung=self.escalation_ladder.rung_number(self.current_rung), next_rung=None)
            matched_rung_idx = self.cbr.make_decision(new_scenario_slots)
            matched_rung = self.escalation_ladder.data[matched_rung_idx]
        else:
            matched_rung, matched_rung_idx = self.escalation_ladder.highest_matched_rung(self.current_rung, self, amygdala)
        return matched_rung, matched_rung_idx


    def deliberate(self, max_time, amygdala):
        '''This method causes the agent to cogitate and predict how its mental state and intentions will evolve up until max_time in the future, presuming that it receives no additional percepts after the current time. One of the purposes of this method is to establish the evolution of the internal mental state of the agent. These changes can be stored on the loglist and then used to account for how a new percept can interrupt the agent's 'chain of thought.'
        '''

        super().deliberate(max_time, amygdala)
        current_rung = self.current_rung
        current_rung_idx = self.escalation_ladder.rung_number(self.current_rung)
        # determine if a different rung is matched
        # Even if the amygdala is dominant, we want to do this if we're training the ELCBR
        why = "reasoning"
        matched_rung, matched_rung_idx = self.match_rung(max_time, amygdala)
        if self.cbr_train:
                self._remember_scenario(percepts = self.digested_percepts,
                                        current_rung_idx = current_rung_idx,
                                        next_rung_idx = matched_rung_idx)


        amygdala_dominant_response = amygdala.dominant_response()
        amygdala_rung = None
        amygdala_rung_idx = None
        amygdala_dominant = (amygdala_dominant_response is not None)
        if amygdala.FIGHT_STR == amygdala_dominant_response:
            amygdala_rung, amygdala_rung_idx = self.escalation_ladder.next_rung(self.current_rung)
            why = "fight"
        elif amygdala.FREEZE_STR == amygdala_dominant_response:
            amygdala_rung, amygdala_rung_idx = self.current_rung, current_rung_idx
            why = "freeze"
            if matched_rung != amygdala_rung: # we only want to declare failure to chnage rungs if we SHOULD have changed rungs
                self._push_rung_change_action(current_rung, amygdala_rung, why)
        elif amygdala.FLIGHT_STR == amygdala_dominant_response:
            amygdala_rung, amygdala_rung_idx = self.escalation_ladder.previous_rung(self.current_rung)
            why = "flight"
        curr_rungname = self.current_rung.name
        amygdala_rungname = amygdala_rung.name if amygdala_rung else "None"
        matched_rungname = matched_rung.name if matched_rung else "None"
        # print(f"{self.identity} next rungs: Curr_Rung={curr_rungname}, Amygdala={amygdala_rungname}, Matcher={matched_rungname}. Current dominant response: {amygdala_dominant_response}")

        chosen_rung = matched_rung
        chosen_rung_idx = matched_rung_idx
        if amygdala_dominant:
            chosen_rung = amygdala_rung
            chosen_rung_idx = amygdala_rung_idx

        if chosen_rung_idx > current_rung_idx:
            self._escalate(chosen_rung, amygdala, why)
            self._push_rung_change_action(current_rung, chosen_rung, why)
        elif chosen_rung_idx < current_rung_idx:
            if amygdala_dominant:
                self._deescalate(chosen_rung, self.current_rung.deescalation_actions, why)
            else:
                self._deescalate(chosen_rung, None, why)
            self._push_rung_change_action(current_rung, chosen_rung, why)

        # we need to redeliberate AFTER escalation/deescalation, because those events cause us to clear our planned actions
        if chosen_rung != matched_rung: # what if I chose a rung I didn't actually match with?
            # then I need to push a re-deliberate action in the future, once my amygdala is no longer dominant!
            self._push_redeliberate_action(max_time, amygdala)

        amygdala.capture_plot()
    

    def _find_amygdala_dominance_change_time(self, max_time, amygdala):
        # def dominant_at_time(t):
        #     if t < self.time:
        #         amygdala.rewind(t)
        #     elif t > self.time:
        #         amygdala.forward_simulation(t)
        #     amygdala_dominant_response = amygdala.dominant_response()
        #     amygdala_dominant = (amygdala_dominant_response is not None)
        #     if amygdala_dominant:
        #         return 1
        #     else:
        #         return -1
            

        # present_time = self.time
        # dominance_change_time = optimize.bisect(dominant_at_time, present_time, max_time)
        # return dominance_change_time
        
        pad_time = 10 # to ensure the dominance change time actually lets pbf level decay below threshold
        dominance_change_time = amygdala.get_dominance_change_time()    
        return max(dominance_change_time, 0) + pad_time


    def _escalate(self, next_rung, amygdala, why="no reason"):
        next_rung.update_planned_actions(self)
        self.current_rung = next_rung
        self._enqueue_actions(next_rung.actions)
        self.capture_plot()


    def _deescalate(self, next_rung, events_to_enqueue, why="no reason"):
        if next_rung is not None:
            next_rung.update_planned_actions(self)
            self.current_rung = next_rung
        if events_to_enqueue is not None:
            self._enqueue_actions(events_to_enqueue)
        self.capture_plot()    
    

    def _push_redeliberate_action(self, max_time, amygdala):
        # heappush(self.planned_actions, (self.time + self.idle_time, tuple(), UpdateAmygdalaParameters(0, 0, 0, 0)))
        pass


    def _push_rung_change_action(self, current_rung, next_rung, why=""):
        pass

    def _remember_scenario(self, percepts, current_rung_idx, next_rung_idx):
        if self.cbr:
            # must ensure we pass percepts as a list of dictionaries and current_rung_match_attributes is a dictionary
            ## percepts has attribute events_list, which is a list of percept dictionaries
            percepts_as_list_of_dict = []
            for percept in percepts:
                percepts_as_list_of_dict.append(percept.get_percept_items())
            self.cbr.add_ELRScenario(percepts, current_rung_idx, next_rung_idx)

    @property
    def next_deliberate_action(self):
        if len(self.planned_actions):
            return self.planned_actions[0][1] # this is an iterable of messages for the supervisor
        else:
            return None


    @property
    def next_deliberate_action_time(self):
        if len(self.planned_actions):
            return self.planned_actions[0][0]
        else:
            return None

        
    def take_next_action(self):
        '''This method is meant to be called when a WatchListItem reflecting the agent's planned action is processed by the Supervisor. It should be an internal implementation detail which is called via a method on the PersonLikeAgent, which uses the values it returns to update the Amygdala state.'''
        action_time, messages, params = heappop(self.planned_actions) # This should return an iterable of messages 
        self.forward_simulation(action_time) # make sure that Reasoner is at correct time, although in practice this should do nothing as forward_simulation should have been called on the Agent first
        # send messages to supervisor reflecting actions, if necessary
        actions = []
        for message in messages:
            actions.append(message.actions)
        if len(messages) > 0:
            self.environment.supervisor.inbox.clear() # should already be empty
            self.environment.supervisor.deliver_messages(messages)
            self.environment.supervisor.process_inbox() # all messages should be at the same time, otherwise would be separate actions
            self.environment.supervisor.inbox.clear() # remove action messages
        self.actions_taken.append((self.environment.time, actions))
        return params # the caller should use these to update the agent's amygdala parameters; much of the time taking action should reduce pbf, inclination to fight or flight



    def _enqueue_actions(self, actions):
        if len(actions) == 0 or actions is None:
            return

        for action in actions:
            delta_t, draft_messages, update_params = action # unpack 3-tuple
            action_time = self.time + delta_t
            action_messages = [draft_message.coerce_to_message(**{'uid': self.new_message_index(), 'time': action_time, 'sender': (self.environment.uid, self.uid), 'recipient': (1, 1)}) for draft_message in draft_messages]
            # action_messages = self.untaken_actions(action_messages, reasoner)
            heappush(self.planned_actions, (action_time, tuple(action_messages), update_params))


    def capture_plot(self):
        self.plot_time.append(self.time)
        self.plot_rungs.append(self.escalation_ladder.rung_number(self.current_rung))
        

    def export_plot(self, filename=None, title=None):
        self.plot_ladder("ladder" + filename, title)
        self.plot_timeline("timeline" + filename, None)

    def plot_timeline(self, filename, title):
        if filename is None:
            filename = f"escalationladder{self.identity}.png"

        self.environment.matplotlib_lock.acquire()
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xlim([0, self.environment.time])
        ax.set_ylim(0, 3)
        actions_yval = 1
        plt.yticks([actions_yval], ["Actions"])
        plt.xlabel("Time (s)")
        plt.title(f"{self.identity} Timeline" if title is None else title)
        times = [a[0] for a in self.actions_taken]
        evts = [actions_yval + random.uniform(-0.1, 0.1) for a in self.actions_taken]
        plt.scatter(times, evts, color="blue", label="Actions")
        plt.legend()
        plt.show()
        plt.close()
        self.environment.matplotlib_lock.release()

    def plot_ladder(self, filename, title):
        if filename is None:
            filename = f"escalationladder{self.identity}.png"

        self.environment.matplotlib_lock.acquire()
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_xlim([0, self.environment.time])
        # plt.figure(figsize=(10, 6))
        rung_labels = [rung.name for rung in self.escalation_ladder]
        show_ladder_y_axis = False
        if show_ladder_y_axis:

            ax.yaxis.set_visible(False)
            ladder_halfwidth = 180
            ax.set_xlim(-ladder_halfwidth - 5, self.plot_time[len(self.plot_time) - 1])
            ax.set_ylim(-1, len(self.escalation_ladder))

            ladder_linewidth = 3
            ax.axvline(x=-ladder_halfwidth, color='grey', linewidth=ladder_linewidth)
            ax.axvline(x=0, color='grey', linewidth=ladder_linewidth)
            for y in range(len(rung_labels)):
                # ax.axhline(y=y, xmin=-ladder_halfwidth, xmax=0, linewidth=ladder_linewidth, color="grey")
                rung = mlines.Line2D([-ladder_halfwidth, 0], [y, y], color='grey', linewidth=ladder_linewidth)
                ax.add_line(rung)
                ax.text(-ladder_halfwidth / 2, y + 0.1, rung_labels[y], ha='center', va='center')
        plot_time = self.plot_time.copy()
        plot_time.append(self.environment.time)
        plot_rungs = self.plot_rungs.copy()
        plot_rungs.append(plot_rungs[-1])
        plt.step(plot_time, plot_rungs, label="Rung", marker="o", where="post")
        plt.xlabel("Time (s)")
        plt.ylabel("Ladder")
        plt.title(f"{self.identity} Escalation Ladder" if title is None else title)
        plt.legend()
        plt.yticks(range(len(rung_labels)), labels=rung_labels, rotation=60, fontsize=7)

        try:
            plt.savefig(filename)
        except Exception as e:
            print("Warning! Could not save Ladder plot.")
            print(str(e))
        plt.show()
        plt.close()
        self.environment.matplotlib_lock.release()

    def visualise_final(self):
        super().visualise_final()
        self.export_plot()