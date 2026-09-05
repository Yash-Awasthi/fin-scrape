import random

from romancer.environment.object import ImprovedRomancerObject
from typing import NamedTuple
import math
import matplotlib.pyplot as plt

class CurrentAmygdalaParameters(NamedTuple):
    current_pbf: float
    current_fight: float
    current_flight: float
    current_freeze: float
    current_dominant_response: any # can be 'fight', 'flight', 'freeze', or None


class UpdateAmygdalaParameters(NamedTuple):
    delta_pbf: float
    delta_fight: float
    delta_flight: float
    delta_freeze: float

class Amygdala(ImprovedRomancerObject):
    '''The purpose of this class is to represent the neuroendocrine and limbic systems in a modular way that can be employed with different kinds of reasoners within 'person-like' agents.

    As a rudimentary approximation of the neuroendocrine system, the Amygdala object provides a 'precious bodily fluid' parameter that represents the role of cortisol in human cognition. The reasoner can use the pbf level as a proxy for 'stress' or 'desperation', in turn using it to approximate resulting cognitive impairment. Cortisol is presumed to drop over time unless new stressors cause it to be replenished, and it can only rise up to a biological maximum represented by max_pbf.

    To represent 'lizard brain' types of responses, the Amygdala object provides proxies for fight, flight, or freeze responses. The agent's reasoner can either act on the basis of these responses or not as it sees fit. The reasoner also needs to incorporate funtionality to update these parameters on the basis of its evolving state--otherwise, they are ignored.
    '''

    # Constants.
    FIGHT_STR = "fight"
    FLIGHT_STR = "flight"
    FREEZE_STR = "freeze"

    def __init__(self, environment, time, fight_weight = 1.0, flight_weight = 1.0, freeze_weight = 1.0, initial_fight = 0.0, initial_flight = 0.0, initial_freeze = 0.0, initial_pbf = 0.0001, pbf_halflife = 38400, max_pbf = 1.0, response_threshhold = 1.0, name=""):
        super().__init__(environment, time)
        self.fight_weight = fight_weight
        self.flight_weight = flight_weight
        self.freeze_weight = freeze_weight
        self.fight = initial_fight
        self.flight = initial_flight
        self.freeze = initial_freeze
        self.pbf = 0.0
        self.last_pbf_update_time = time
        self.pbf_decay_rate = 0.0
        self.pbf_halflife = 0.0
        self.max_pbf = 0.0
        self.response_threshhold = 0.0
        self.name = name

        # Eventually capture from the logged object, but for now capture these synchronously as they change.
        self.plot_time = []
        self.plot_fight = []
        self.plot_flight = []
        self.plot_freeze = []
        self.plot_pbf = []
        self.set_weights(fight_weight, flight_weight, freeze_weight)
        self.set_response_values(initial_fight, initial_flight, initial_freeze)
        self.set_pbf(initial_pbf, pbf_halflife, max_pbf, response_threshhold)
        self.capture_plot()

    def set_weights(self, fight_weight = 1.0, flight_weight = 1.0, freeze_weight = 1.0):
        self.fight_weight = fight_weight # used to update/predict fight response
        self.flight_weight = flight_weight # used to update/predict flight response
        self.freeze_weight = freeze_weight # used to update/predict freeze response
        self.capture_plot()

    def set_response_values(self, initial_fight = 0.0, initial_flight = 0.0, initial_freeze = 0.0):
        self.fight = initial_fight # fight response level
        self.flight = initial_flight # flight response level
        self.freeze = initial_freeze # freeze response level
        self.capture_plot()

    def set_pbf(self, initial_pbf = 0.0001, pbf_halflife = 38400, max_pbf = 1.0, response_threshhold = 1.0):
        self.pbf = initial_pbf # initial cortisol level
        self.last_pbf_update_time = self.time # used to calculate pbf decay
        self.pbf_decay_rate = (1 / math.log(2)) * pbf_halflife # rate at which cortisol is metabolized
        self.pbf_halflife = pbf_halflife # half-life of cortisol
        self.max_pbf = max_pbf # maximum possible cortisol level
        self.response_threshhold = response_threshhold # below this threshold, fight/flight/freeze responses do not activate ('business as usual')
        self.capture_plot()

    def capture_plot(self):
        params = self.current_amygdala_parameters()
        self.plot_time.append(self.environment.time)
        self.plot_fight.append(params.current_fight)
        self.plot_flight.append(params.current_flight)
        self.plot_freeze.append(params.current_freeze)
        self.plot_pbf.append(params.current_pbf)

    def export_plot(self, filename=None, title=None):
        if filename is None:
            filename = "amygdala.png"

        self.environment.matplotlib_lock.acquire()
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax1.set_xlim([0, self.environment.time])

        ax1.plot(self.plot_time, self.plot_fight, label="Fight", color="r")
        ax1.plot(self.plot_time, self.plot_flight, label="Flight", color="g")
        ax1.plot(self.plot_time, self.plot_freeze, label="Freeze", color="b")
        ax1.set_ylim(ymin=0)
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Response")
        ax1.legend(loc="upper left")

        ax2 = ax1.twinx()
        ax2.plot(self.plot_time, self.plot_pbf, label="PBF", color="grey")
        ax2.set_ylim(ymin=0)
        ax2.set_ylabel("PBF")
        ax2.legend(loc="upper right")
        threshold_y = max(0.0, self.response_threshhold)
        ax2.axhline(y=threshold_y, color="gray", linestyle="--")
        ax2.annotate('Response Threshold', xy=(0.5, threshold_y), xytext=(0.52, threshold_y),
                     textcoords='data', fontsize=8, color='gray')

        plt.title(f"{self.name} Mood Meter" if title is None else title)
        try:
            plt.savefig(filename)
        except Exception as e:
            print("Warning! Could not save Amygdala plot.")
            print(str(e))
        plt.show()
        plt.close()
        self.environment.matplotlib_lock.release()


    def current_amygdala_parameters(self):
        # print(f"T={self.time} {self.name} FIGHT {self.fight}")
        '''This method returns a CurrentAmygdalaParameters object reflecting the present cortisol level and dominant reseponse, if any.'''
        delta_t = self.time - self.last_pbf_update_time # maybe check for negative value and raise exception if so
        halflife_eps = 0.0000001
        if self.pbf_halflife < halflife_eps:
            self.pbf_halflife = halflife_eps
        cur_pbf = self.pbf * 2**(-delta_t / self.pbf_halflife)
        self.pbf = cur_pbf
        self.last_pbf_update_time = self.time
        # determine dominant response, if any
        responses = [(self.FIGHT_STR, self.fight * self.fight_weight),
                     (self.FLIGHT_STR, self.flight * self.flight_weight),
                     (self.FREEZE_STR, self.freeze * self.freeze_weight)]
        dominant_response = max(responses, key = lambda n: n[1])
        if cur_pbf > self.response_threshhold: # if too stressed
            dominant_response = dominant_response[0]
        else: # otherwise, not srtressed
            dominant_response = None
        current_fight = self.fight * self.fight_weight
        current_flight = self.flight * self.flight_weight
        current_freeze = self.freeze * self.freeze_weight
        params = CurrentAmygdalaParameters(current_pbf = cur_pbf, current_fight = current_fight, current_flight = current_flight, current_freeze = current_freeze, current_dominant_response = dominant_response)
        # self.capture_plot(params)
        return params

        
    def anticipated_parameters_at_time(self, time):
        '''As part of the agent's deliberation process, it needs to be able to anticipate the state of the amygdala at arbitrary points in the future prsuming no additional outside influences in the interim. This method returns a CurrentAmygdalaParameters object reflecting anticipated parameters at the future time, but leaves the Amygdala object at the same state as when it was called.'''
        if time == self.time:
            return self.current_amygdala_parameters() # return current state
        elif time < self.time: # may need this for deliberation
            cur_time = self.time
            self.rewind(time)
            state = self.current_amygdala_parameters() # return current state
            self.forward_simulation(cur_time) # revert state
            return state # return past state
        else:
            cur_time = self.time
            self.forward_simulation(cur_time)
            state = self.current_amygdala_parameters() # return current state
            self.rewind(cur_time) # revert state
            return state # return past state


    def update_parameters(self, parameters):
        '''The purpose of this method is to update the amygdala parameters that takes into account the decay of pbf while ensuring proper logging. Note that it returns the amygdala object to its initial time, while logging anticipated future changes if needed.'''
        # update parameters if needed
        update_parameters = parameters # UpdateAmygdalaParameters object
        # cause the parameters to decay
        cur_parameters = self.current_amygdala_parameters()
        if update_parameters.delta_pbf != 0:
            self.last_pbf_update_time = self.time
            self.pbf = cur_parameters.current_pbf + update_parameters.delta_pbf
            # self.pbf += update_parameters.delta_pbf
            if self.pbf > self.max_pbf:
                self.pbf = self.max_pbf
            if self.pbf < 0:
                self.pbf = 0
        self.fight += update_parameters.delta_fight
        self.flight += update_parameters.delta_flight
        self.freeze += update_parameters.delta_freeze
        self.capture_plot()
        self.last_pbf_update_time = self.time # update last pbf update time

    def dominant_response(self):
        dominant_response = self.current_amygdala_parameters().current_dominant_response
        return dominant_response
    
    
    def get_dominance_change_time(self):
        if self.dominant_response() is not None:
            # calculate time until we decay below threshold
            delta_t = -self.pbf_halflife * math.log(max(self.response_threshhold, 10e-10) / self.pbf, 2)
            return self.time + delta_t
        else: # already non-dominant, current time is the answer
            return self.time

    @staticmethod
    def short_desc():
        return "Default Amygdala"


''' An Amygdala class that doesn't change over time'''
class FixedAmgydala(Amygdala):
    def update_parameters(self, parameters):
        # Override update so no responses change
        nothingupdate = UpdateAmygdalaParameters(0.0, 0.0, 0.0, 0.0)
        super().update_parameters(nothingupdate)

''' An Amygdala class that doesn't change it's response over time [but may change whether that response happens or not]'''
class FixedResponseAmgydala(Amygdala):
    def update_parameters(self, parameters):
        # Override update so we remain fixed on mood
        nothingupdate = UpdateAmygdalaParameters(parameters.delta_pbf, 0.0, 0.0, 0.0)
        super().update_parameters(nothingupdate)

''' Joker archetype'''
class Amygdala_Loki(Amygdala):
    def __init__(self, environment, time, name=""):
        super().__init__(environment, time, name=name)
        self.pbf = 1.0
        self.response_threshhold = 0.5

    @staticmethod
    def short_desc():
        return "Joker Archetype Amygdala"

    def update_parameters(self, parameters):
        next_mood = random.choice([self.FIGHT_STR, self.FLIGHT_STR, self.FREEZE_STR])
        if next_mood == self.FIGHT_STR:
            self.fight = self.fight_weight = 1.0
            self.flight = self.flight_weight = 0.0
            self.freeze = self.freeze_weight = 0.0
        elif next_mood == self.FLIGHT_STR:
            self.fight = self.fight_weight = 0.0
            self.flight = self.flight_weight = 1.0
            self.freeze = self.freeze_weight = 0.0
        elif next_mood == self.FREEZE_STR:
            self.fight = self.fight_weight = 0.0
            self.flight = self.flight_weight = 0.0
            self.freeze = self.freeze_weight = 1.0
        self.capture_plot()


''' Fighter archetype '''
class Amygdala_Fight(FixedAmgydala):
    def __init__(self, environment, time, name=""):
        super().__init__(environment, time, name=name)
        self.set_weights(1.0, 0.0, 0.0)
        self.set_response_values(1.0, 0.0, 0.0)
        self.pbf = 1.0
        self.response_threshhold = 0.0

    @staticmethod
    def short_desc():
        return "Fight Archetype Amygdala"

    def dominant_response(self):
        return self.FIGHT_STR

''' Runner archetype '''
class Amygdala_Flight(FixedAmgydala):
    def __init__(self, environment, time, name=""):
        super().__init__(environment, time, name=name)
        self.set_weights(0.0, 1.0, 0.0)
        self.set_response_values(0.0, 1.0, 0.0)
        self.pbf = 1.0
        self.response_threshhold = 0.0

    @staticmethod
    def short_desc():
        return "Flight Archetype Amygdala"

    def dominant_response(self):
        return self.FLIGHT_STR


''' Runner archetype '''
class Amygdala_Freeze(FixedAmgydala):
    def __init__(self, environment, time, name=""):
        super().__init__(environment, time, name=name)
        self.set_weights(0.0, 0.0, 1.0)
        self.set_response_values(0.0, 0.0, 1.0)
        self.pbf = 1.0
        self.response_threshhold = 0.0

    @staticmethod
    def short_desc():
        return "Freeze Archetype Amygdala"

    def dominant_response(self):
        return self.FREEZE_STR

''' Purely Analytic brain feels no emotion '''
class Amygdala_StoneCold(FixedAmgydala):
    def __init__(self, environment, time, name=""):
        super().__init__(environment, time, name=name)
        self.set_weights(0.0, 0.0, 0.0)
        self.set_response_values(0.0, 0.0, 0.0)
        self.pbf = 0.0
        self.response_threshhold = 1e9

    @staticmethod
    def short_desc():
        return "Spock Archetype Amygdala"

    def dominant_response(self):
        return None

# This is always going to choose "fight" but does change based on pbf
class Amygdala_ResponseFight(FixedResponseAmgydala):
    def __init__(self, environment, time, name=""):
        super().__init__(environment, time, name=name)
        self.set_weights(1.0, 0.0, 0.0)
        self.set_response_values(1.0, 0.0, 0.0)

    @staticmethod
    def short_desc():
        return "Fight-Leaning Archetype Amygdala"


# This is always going to choose "flight" but does change based on pbf
class Amygdala_ResponseFlight(FixedResponseAmgydala):
    def __init__(self, environment, time, name=""):
        super().__init__(environment, time, name=name)
        self.set_weights(0.0, 1.0, 0.0)
        self.set_response_values(0.0, 1.0, 0.0)

    @staticmethod
    def short_desc():
        return "Flight-Leaning Archetype Amygdala"

# This is always going to choose "freeze" but does change based on pbf
class Amygdala_ResponseFreeze(FixedResponseAmgydala):
    def __init__(self, environment, time, name=""):
        super().__init__(environment, time, name=name)
        self.set_weights(0.0, 0.0, 1.0)
        self.set_response_values(0.0, 0.0, 1.0)

    @staticmethod
    def short_desc():
        return "Freeze-Leaning Archetype Amygdala"

all_amygdala_archetypes = [
    Amygdala,
    Amygdala_StoneCold,
    Amygdala_Loki,
    Amygdala_Fight,
    Amygdala_Flight,
    Amygdala_Freeze,
    Amygdala_ResponseFight,
    Amygdala_ResponseFlight,
    Amygdala_ResponseFreeze
]
