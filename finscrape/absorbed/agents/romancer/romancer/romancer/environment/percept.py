class Percept():
    '''The purpose of percepts is to convey information that may translate into experiences for agents. Percepts need to be able to convey arbitrary information, including mutable state. Percepts are digested by an agent's perception filter that translates the information in the percept into the agent's inner ontology.

    This base Percept class can be subclassed in order to endow percepts with methods that are convenienmt for the implementation of an agent's idiosyncratic perception filter.'''
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__setattr__(key, value)
        # At this point, we have a list of keys of attributes we've added.
        #  It's hard to cleanly untangle what's default vs what we added,
        #  later, so we keep the list of additions on hand for future needs.
        self.param_names = kwargs.keys()


    def __repr__(self):
        class_name = self.__class__.__name__
        results = {key: self.__getattribute__(key) for key in self.param_names}
        return f"{class_name}({', '.join([f'{k}={v.__repr__()}' for k,v in results.items()])})"

    def get_percept_items(self):
        ret = {}
        for k in self.param_names:
            ret[k] = getattr(self, k)
        return ret
