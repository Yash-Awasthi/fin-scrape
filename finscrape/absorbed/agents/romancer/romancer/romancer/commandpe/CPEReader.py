from datetime import datetime
import csv
import numpy as np
import matplotlib.pyplot as plt
from collections import namedtuple


class CPEWeaponFiredReader:
    ''' A class for reading outputs from CommandPE '''

    def __init__(self, weapon_class_csv, target_class_csv, target_unit_csv, weapon_fired_csv, weapon_endgame_csv, shooter_side='BLUE'):
        self.shooterSide = shooter_side
        ''' Weapon Class is a configuration file mapping Weapon Class [from Command PE] to a Consideration-Level'''
        self.weapon_scale = self.load_weapon_scale(weapon_class_csv)
        ''' Target Class is two configuration files mapping targets to Consideration-level'''
        ''' The "Target Unit" file is so that specific units can be assigned specific consideration levels and takes priority'''
        ''' The "Target Class" file is so that targets can be assigned specific consideration levels by their type'''
        self.target_scale, self.target_unit_scale = self.load_target_scale(target_class_csv, target_unit_csv)

        print("Loaded Scaling Maps for Weapons and Targets:")
        print(f"Weapon Category: {len(self.weapon_scale)} items, Target Category: {len(self.target_scale)} items, Target Unit Category: {len(self.target_unit_scale)} items")

        # Weapon Fired is one category of thing
        weaponfired_f = open(weapon_fired_csv, "r")
        self.weaponfired_reader = csv.DictReader(weaponfired_f)
        # First row is comments. Ignore it
        next(self.weaponfired_reader)
        # Because this is a stateful API, we'll start off with the first one
        self.last_weapon_fired_record = next(self.weaponfired_reader)

        # Weapon Endgame is a different thing
        weaponendgame_f = open(weapon_endgame_csv, "r")
        self.weaponendgame_reader = csv.DictReader(weaponendgame_f)
        # First row is comments. Ignore it
        next(self.weaponendgame_reader)
        # Because this is a stateful API, we'll start off with the first one
        self.last_weapon_endgame_record = next(self.weaponendgame_reader)
        # Weapon and Target class are not stored in the endgame csv - capture it
        self.weapon_name_to_class = {}
        self.target_name_to_class = {}

        self.WeaponTargetCount = namedtuple('WeaponTargetCount', ['event_type', 'weapon', 'target', 'count', 'all_events'])

        self.curr_time_s = 0

        self.scenario_complete = False
        self.records_read_fires = 0
        self.records_read_endgame = 0

        self.plot_event_fires = []
        self.report_rollup_times = []

    def load_target_scale(self, target_class_csv, target_unit_csv):
        target_scale = {}
        with open(target_class_csv, "r") as f:
            csv_reader = csv.DictReader(f)
            target_scale = {row['TargetClass']: row['TargetCategory'] for row in csv_reader}

        target_unit = {}
        with open(target_unit_csv, "r") as f:
            csv_reader = csv.DictReader(f)
            target_unit = {row['TargetUnit']: row['TargetCategory'] for row in csv_reader}

        return target_scale, target_unit

    def load_weapon_scale(self, weapon_class_csv):
        weapon_scale = {}
        with open(weapon_class_csv, "r") as f:
            csv_reader = csv.DictReader(f)
            weapon_scale = {row['WeaponClass']: row['WeaponCategory'] for row in csv_reader}

        return weapon_scale

    def get_time_s(self, t_str):
        ''' Accept a timestamp in CommandPE's format, return t_s '''
        # For simplicity, ignore sub-second component of time
        #   Decision may need revisiting once AI is in charge of Nuclear decision-making
        timefmt = "%H:%M:%S"
        time_obj = datetime.strptime(t_str.split(".")[0], timefmt)
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

    def get_current_time_s(self):
        return self.curr_time_s

    def get_records_read_fires(self):
        return self.records_read_fires

    def get_records_read_endgame(self):
        return self.records_read_endgame

    def is_scenario_complete(self):
        ''' Return true if the scenario is "complete" [ie, ran out of inputs] '''
        return self.scenario_complete

    def _read_next_weapons_fired(self, timeframe_s):
        ''' Get a namedtuple of weapon/tgt/count 3-tuples during the next timeframe_s seconds from last time this returned '''
        if self.scenario_complete:
            return []

        t_end = self.curr_time_s + timeframe_s
        total_counts = {}  # A map of weaponcategory => { target category => [event list] }
        time_last_weapon_fired_s = self.get_time_s(self.last_weapon_fired_record['Time'])

        while time_last_weapon_fired_s < t_end:
            self.records_read_fires += 1

            wpn_name = self.last_weapon_fired_record['WeaponName']
            wpn_class = self.last_weapon_fired_record['WeaponClass']
            this_wpn_scale = self.weapon_scale.get(wpn_class)
            # The endgame reader only has access to WeaponName, so store class for reference
            self.weapon_name_to_class[wpn_name] = wpn_class

            firing_side = self.last_weapon_fired_record['FiringUnitSide']

            target_name = self.last_weapon_fired_record['TargetContactActualUnitName']
            target_class = self.last_weapon_fired_record['TargetContactActualUnitClass']
            self.target_name_to_class[target_name] = target_class
            this_target_scale = self.target_unit_scale[target_name] if target_name in self.target_unit_scale else self.target_scale.get(target_class, None)

            if firing_side.upper() == self.shooterSide.upper():
                if this_target_scale is None:
                    print(f"Fires: Couldn't find a target scaling lookup for class '{target_class}' or unit name '{target_name}'")
                elif this_wpn_scale is None:
                    print(f"Fires: Couldn't find a weapon scaling lookup for class '{wpn_class}'")
                else:
                    if this_wpn_scale not in total_counts:
                        total_counts[this_wpn_scale] = {}
                    tgt_map = total_counts[this_wpn_scale]
                    event_list = tgt_map.get(this_target_scale, [])
                    event_list.append(self.last_weapon_fired_record)
                    tgt_map[this_target_scale] = event_list

            time_last_weapon_fired_str = self.last_weapon_fired_record['Time']

            try:
                self.last_weapon_fired_record = next(self.weaponfired_reader)
                time_last_weapon_fired_s = self.get_time_s(time_last_weapon_fired_str)

                if this_target_scale is not None and this_wpn_scale is not None:
                    self.plot_event_fires.append((time_last_weapon_fired_s, int(this_target_scale), int(this_wpn_scale)))

            except StopIteration:
                self.scenario_complete = True
                break

        self.curr_time_s = t_end
        self.report_rollup_times.append(t_end)

        # Convert the created map into a list of namedTuples
        result = []
        for weapon, targets in total_counts.items():
            for target, event_list in targets.items():
                result.append(self.WeaponTargetCount('fired', weapon, target, len(event_list), event_list))

        return result

    def _read_next_weapons_endgame(self):
        ## Very dangerously stateful indeed. MUST BE CALLED *AFTER* READ NEXT WEAPONS FIRED
        ## Timestep is "until the end of the last event from NEXT WEAPONS FIRED"

        if self.scenario_complete:
            return []

        total_counts = {}  # A map of weaponcategory => { target category => [event list] }
        time_last_weapon_endgame_s = self.get_time_s(self.last_weapon_endgame_record['Time'])

        while time_last_weapon_endgame_s < self.curr_time_s:
            self.records_read_endgame += 1

            wpn_name = self.last_weapon_endgame_record['WeaponName']
            wpn_class = self.weapon_name_to_class.get(wpn_name, None)
            if wpn_class is None:
                print(f"Error: Weapon Endgame for {wpn_name} that doesn't seem to have been fired")
            this_wpn_scale = self.weapon_scale.get(wpn_class, None)

            firing_side = self.last_weapon_endgame_record['WeaponSide']

            target_name = self.last_weapon_endgame_record['TargetName']
            target_class = self.target_name_to_class.get(target_name, None)
            if target_class is None:
                print(f"Error: Weapon Endgame for tgt {target_name} doesn't seem to have been fired")

            this_target_scale = self.target_unit_scale[target_name] if target_name in self.target_unit_scale else self.target_scale.get(target_class, None)

            if firing_side.upper() == self.shooterSide.upper():
                if this_target_scale is None:
                    print(f"Endgame: Couldn't find a target scaling lookup for class '{target_class}' or unit name '{target_name}'")
                elif this_wpn_scale is None:
                    print(f"Endgame: Couldn't find a weapon scaling lookup for class '{wpn_class}'")
                else:
                    if this_wpn_scale not in total_counts:
                        total_counts[this_wpn_scale] = {}
                    tgt_map = total_counts[this_wpn_scale]
                    event_list = tgt_map.get(this_target_scale, [])
                    event_list.append(self.last_weapon_fired_record)
                    tgt_map[this_target_scale] = event_list

            time_last_weapon_endgame_str = self.last_weapon_endgame_record['Time']
            try:
                self.last_weapon_endgame_record = next(self.weaponendgame_reader)
                time_last_weapon_endgame_s = self.get_time_s(time_last_weapon_endgame_str)
            except StopIteration:
                self.scenario_complete = True
                break

        # Convert the created map into a list of namedTuples
        result = []
        for weapon, targets in total_counts.items():
            for target, event_list in targets.items():
                result.append(self.WeaponTargetCount('endgame', weapon, target, len(event_list), event_list))

        return result

        return []

    def read_next_weapons_events(self, timeframe_s=(15*60)):
        retval = self._read_next_weapons_fired(timeframe_s)
        # retval.extend(self._read_next_weapons_endgame())
        return retval

    def visualise_final(self):
        filename = "cpe_events_" + self.shooterSide + ".png"

        times = [event[0] for event in self.plot_event_fires]
        weaponscale = [event[2] for event in self.plot_event_fires]
        cmap = plt.get_cmap('viridis')
        norm = plt.Normalize(min(weaponscale), max(weaponscale))

        fig, ax = plt.subplots(figsize=(10, 3))
        for v_time in self.report_rollup_times:
            ax.axvline(x=v_time, color="grey", linestyle="--", linewidth=1,
                       label='Report Times' if v_time == self.report_rollup_times[0] else "")

        for i, (time, target_scale, weapon_scale) in enumerate(self.plot_event_fires):
            plt.scatter(time, target_scale, color=cmap(norm(weapon_scale)), s=40)
        # plt.xlabel("Time (s)")
        plt.ylabel("Target Class")

        # plt.yticks([])
        plt.title("Weapon Fires Timeline")
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax, ticks=range(min(weaponscale), max(weaponscale)+1))

        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, loc='upper left')

        plt.show()
        plt.savefig(filename)
        plt.close()


if __name__ == "__main__":
    cpeoutputfolder = "data/commandpe_output"
    cpeinputfolder = "data/commandpe_input"
    cper = CPEWeaponFiredReader(f"{cpeinputfolder}/weaponClass.csv", f"{cpeinputfolder}/targetClass.csv",
                                f"{cpeinputfolder}/targetUnitClass.csv",
                                f"{cpeoutputfolder}/WeaponFired.csv", f"{cpeoutputfolder}/WeaponEndgame.csv",
                                'BLUE')
    while not cper.is_scenario_complete():
        event_list = cper.read_next_weapons_events(15 * 60)
        # Full event list isn't helpful to print
        to_print = []
        for e in event_list:
            e_dict = e._asdict()
            e_dict.pop('all_events')
            to_print.append(e_dict)
        print(to_print)
        print(f"Time is: {cper.get_current_time_s()}, total wpns fired = {cper.get_records_read_fires()}, total endgames = {cper.get_records_read_endgame()}")
    cper.visualise_final()

