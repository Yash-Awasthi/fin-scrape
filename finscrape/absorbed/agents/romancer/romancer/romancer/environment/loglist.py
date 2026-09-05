from collections import UserList

class Loglist(UserList):
    '''ROMANCER objects need to store enough information about their evolution over time to revert back to their states at earlier times. The Loglist is intended as a means to store that state.'''
    
    def minimum_time(self):
        return self.data[0].time

    
    def maximum_time(self):
        return self.data[-1].time

    
    def temporal_bounds(self):
        '''This method returns a tuple containing the minimum and maximum times in the Loglist. Raises an exception if the Loglist is empty.'''
        if len(self.data) > 1:
            return self.data[0].time, self.data[-1].time
        elif len(self.data) == 1:
            return self.data[0].time, self.data[0].time
        else:
            raise Exception('Empty Loglist')

        
    def max_index_under_time(self, time):
        '''Identify the index in the Loglist whose time is the greatest that is less than or equal to time.'''
        if time < self.minimum_time():
            raise Exception('Time less than minimum in Loglist')
        else:
            return next((i for i,v in enumerate(self.data) if v.time > time), len(self.data))


    def truncate_to_time(self, time):
        '''This method truncates the list to remove all logpoints with time greater than time.'''
        i = self.max_index_under_time(time)
        self.data = self.data[0:i]


    def bracketing_logpoints(self, time):
        '''Return a tuple containing the two logpoints bracketing point in time time. If time is equal to or greater than the maximum in loglist, returns logpoint, None. Raises an exception if time is less than mimimum in Loglist.'''
        if time >= self.maximum_time():
            return self.data[-1], None
        elif self.minimum_time() <= time < self.maximum_time():
            i = self.max_index_under_time(time)
            return self.data[i - 1], self.data[i]
        else:
            raise Exception('Time less than minimum in Loglist')


class Logpoint():
    '''The purpose of Logpoints is to save sufficient past state in order to reconstruct an object's history. Most object classes will need their own unique Logpoint subclass. These all need a time attribute in order for the Loglist methods to work.'''

    def __init__(self, time):
        self.time = time
    
