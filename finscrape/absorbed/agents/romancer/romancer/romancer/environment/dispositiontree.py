from threading import RLock

from numpy import pi, sin, cos, sqrt, rad2deg, deg2rad, inf
from romancer.environment.location import GeographicLocation
from pathlib import Path
import matplotlib.patheffects as pe
from scipy.optimize import root_scalar
from romancer.supervisor.singlethreadsupervisor import SingleThreadSupervisor

EARTH_RADIUS_KM = 6378 
KM_PER_DEGREE = 111
RADII_PER_DEGREE = EARTH_RADIUS_KM / KM_PER_DEGREE
SCALE_RADIUS_BY = 1.1

def find_nearest_center(center, possible_centers):
        # find the closest possible center to this center
        min_distance = inf
        min_distance_center = possible_centers[0]
        for possible_center in possible_centers:
            distance = center.distance(possible_center)
            if distance < min_distance:
                min_distance = distance
                min_distance_center = possible_center  

        return min_distance_center


def compute_bounds(center, radius):
    adjustment = deg2rad(radius / KM_PER_DEGREE)
    bounds = (center.latitude - adjustment, 
            center.latitude + adjustment, 
            center.longitude - adjustment,
            center.longitude + adjustment) 
    return bounds


def compute_radius_for_resolution(resolution):
    radius = 1
    N = int(radius / resolution)
    a = 4 * pi * radius ** 2 / N
    d = sqrt(a)
    M_theta = round(pi / d)
    d_theta = pi / M_theta
    d_phi = a / d_theta
    avg_area = d_theta * d_phi
    avg_radius = sqrt(avg_area / pi) # as a percentage of the max radius
    return avg_radius * EARTH_RADIUS_KM * SCALE_RADIUS_BY


def generate_centers(bounds, resolution):
        N_count = 0
        radius = 1
        N = int(radius / resolution)
        a = 4 * pi * radius ** 2 / N
        d = sqrt(a)
        M_theta = round(pi / d)
        d_theta = pi / M_theta
        d_phi = a / d_theta
        centers = []
        for m in range(M_theta): # like varying latitude 
            theta = pi * (m + 0.5) / M_theta
            M_phi = round(2 * pi * sin(theta) / d_phi)
            for n in range(M_phi): # like varying longitude
                phi = 2 * pi * n / M_phi
                new_point = generate_center(theta, phi) # returns points as GeographicLocations
                if (bounds[0] <= new_point.latitude <= bounds[1]) and (bounds[2] <= new_point.longitude <= bounds[3]):
                    centers.append(new_point)
                    N_count += 1

        avg_area = d_theta * d_phi
        avg_radius = sqrt(avg_area / pi) # as a percentage of the max radius
        return centers, avg_radius


def generate_center(theta, phi):
    # convert polar angle theta to latitude and azimuthal angle phi to longitude
    lat = pi / 2 - theta
    lon = phi - pi
    return GeographicLocation(lat, lon, 0)


# NH Custom Exceptions
class DispositionError(Exception):
    """Base class for errors in the disposition tree."""
    pass

class LocationError(Exception):
    """Raised when a location is outside the bounds or on an invalid boundary."""
    pass

class ResolutionError(Exception):
    """Raised when an operation would result in a granularity that doesn't make sense."""
    pass

class DispositionStump():

    '''A disposition tree consisting solely of one (root) node, but adhering to the intended API. A placeholder during development but also potentially useful for scenarios that either largely discount physical space or are so simple as to not require full functionality.'''

    def __init__(self, bounds):
        self.bounds = bounds # tuple containing the left and right bounds of the one-dimensional space
        self.parent = None
        self.contents = list() # objects currently stored in root


    def set_disposition(self, obj, location, granularity):
        if self.bounds[0] <= location <= self.bounds[1]:
            self.contents.append(obj)
            return self
        else:
            raise ValueError('Location outside bounds.')


    def adjust_disposition(self, obj, location, granularity):
        if self.bounds[0] <= location <= self.bounds[1]:
            return self
        else:
            raise ValueError('Location outside bounds.')

        
    def identify_peers(self, obj):
        peers = self.contents.copy()
        peers.remove(obj)
        return peers
        

    def remove(self, obj):
        self.contents.remove(obj)

        
class GeographicDispositionStump(DispositionStump):
    '''Like DispositionStump, but with latitude and longitude bounds to work with GeographicLocation. GeographicDispositionStump.bounds takes the form of a (low_latitude, high_latitude, low_longitude, high_longitude) tuple with locations in radians.'''

    def set_disposition(self, obj, location, granularity):
        lowlat, highlat, lowlong, highlong = self.bounds
        if lowlat <= location.latitude <= highlat and  lowlong <= location.longitude <= highlong:
            self.contents.append(obj)
            return self
        else:
            raise ValueError('Location outside bounds.')


    def adjust_disposition(self, obj, location, granularity):
        lowlat, highlat, lowlong, highlong = self.bounds
        if lowlat <= location.latitude <= highlat and  lowlong <= location.longitude <= highlong:
            return self
        else:
            raise ValueError('Location outside bounds.')


class GeographicDispositionTree():
    '''
    The nodes of a geographic disposition tree. 
    Helps provide efficient clustering of items which may have interactions.
    '''
    _id_number = 1
    # Lock to protect id when allocating a new one
    _id_lock = RLock()

    def __init__(self, center, radius, bounds, resolution = 1, parent = None):
        self.parent = parent
        self.center = center
        self.radius = radius
        self.bounds = bounds
        self.children = list()
        self.contents = list()
        self.id = GeographicDispositionTree.get_next_id_number()
        self.resolution = resolution # this is the percent of Earth this node covers

    @staticmethod
    def get_next_id_number():
        GeographicDispositionTree._id_lock.acquire()
        GeographicDispositionTree._id_number += 1
        retval = GeographicDispositionTree._id_number
        GeographicDispositionTree._id_lock.release()
        return retval

    def plot_all(self, ax):
        # plot the parent
        for child in self.children:
            self.plot_line_to(child.center, ax)
            child.plot_all(ax)
        self.plot_objects(ax)
        self.plot(ax)



    def plot(self, ax, color='red'):
        self.plot_circle(ax)
        self.plot_point(ax, color)

        
    def plot_objects(self, ax):
        for obj in self.contents:                
            obj.plot(ax)


    def plot_peers(self, ax, color):
        self.plot_circle_at(ax, self.center, color)
        peers = self.identify_peers()
        for peer in peers:
            self.plot_circle_at(ax, peer.location, color)



    def plot_line_to(self, location, ax, style = '-'):
        from_lon = rad2deg(self.center.longitude)
        from_lat = rad2deg(self.center.latitude)
        to_lon = rad2deg(location.longitude)
        to_lat = rad2deg(location.latitude)
        ax.plot((from_lon, to_lon), (from_lat, to_lat), color='black', linestyle=style)
        

    def plot_point(self, ax, color):
        lon = rad2deg(self.center.longitude)
        lat = rad2deg(self.center.latitude)
        if self.parent:
            ax.plot(lon, lat, marker='o', color=color, linestyle='')
        else:
            ax.plot(lon, lat, marker='o', color='blue', linestyle='')
        # ax.annotate(self.id, (lon, lat))
        txt = ax.text(lon, lat, self.id,
              size=8,
              color='white',
              path_effects=[pe.withStroke(linewidth=1, foreground="black")])


    def plot_circle_at(self, ax, location, color):
        lon = rad2deg(location.longitude)
        lat = rad2deg(location.latitude)
        linewidth=2.0
        linestyle='-'
        circle = Circle((lon, lat), 0.5, edgecolor=color, fill=False, linewidth=2)
        ax.add_patch(circle)


    def plot_circle(self, ax):
        lon = rad2deg(self.center.longitude)
        lat = rad2deg(self.center.latitude)
        if self.parent:
            facecolor='orange'
            edgecolor='orange'
            alpha=0.1
        else:
            facecolor='black'
            edgecolor='black'
            alpha=0.1
        linewidth=2.0
        linestyle='--'
        # print(f"Trying to plot: {self.id} with radius {self.radius}")
        ax.tissot(rad_km=self.radius, lons=[lon,], lats=[lat,], n_samples=128, fc=facecolor, ec="black", alpha=alpha)
    

    def is_on_boundary(self, location): #NH implement the is_on_boundary method
        """
        Determines if the given location is within a tolerance beyond the boundary of this node.
        :param location: The location to check.        
        :return: True if on the boundary or close enough past it; False otherwise.
        """
        # a direct change to the lower and upper bounds for latitude/longitude (to account for something being "just over the border")
        ## TODO: brainstorm (with boss) how to calculate tolerance
        tolerance = self.granularity / self.granularity_reduction_factor * 0.001 # tolerance is a number of radians, scaled by the next smallest granularity
        lat_on_boundary = (self.bounds[0] - tolerance <= location.latitude <= self.bounds[0]) or (self.bounds[1] <= location.latitude <= self.bounds[1] + tolerance)
        lat_in_boundary = (self.bounds[0] - tolerance <= location.latitude <= self.bounds[1] + tolerance)
        long_on_boundary = (self.bounds[2] - tolerance <= location.longitude <= self.bounds[2]) or (self.bounds[3] <= location.longitude <= self.bounds[3] + tolerance)
        long_in_boundary = (self.bounds[2] - tolerance <= location.longitude <= self.bounds[3] + tolerance)
        return (lat_on_boundary and long_in_boundary) or (lat_in_boundary and long_on_boundary)
        
        
    def make_children(self, resolution):
        # make all children at a specified resolution
        potential_centers, avg_radius = generate_centers(self.bounds, resolution)
        for center in potential_centers:
            if center.distance(self.center) < self.radius / SCALE_RADIUS_BY and not self.has_child_near(center, resolution):
                child_radius = avg_radius * EARTH_RADIUS_KM * SCALE_RADIUS_BY
                child_bounds = compute_bounds(center, child_radius)
                child = GeographicDispositionTree(center, child_radius, child_bounds, resolution, self)
                self.children.append(child)


    def make_child(self, location, resolution):
        # child is in bounds
        if self.bounds[0] < location.latitude < self.bounds[1] and self.bounds[2] < location.longitude < self.bounds[3]:
            if self.has_child_near(location, resolution):
                return 
            child_center = location
            child_radius = compute_radius_for_resolution(resolution)
            child_bounds = compute_bounds(child_center, child_radius)
            child = GeographicDispositionTree(child_center, child_radius, child_bounds, resolution, self)
            self.children.append(child)
        else:
            raise LocationError(f"Location {location} out of bounds")


    def has_child_near(self, location,  resolution):
        for child in self.children:
            if child.resolution == resolution:
                if location.distance(child.center) < child.radius:
                    return True
            if child.resolution > resolution:
                return child.has_child_near(child.center, resolution)
        return False


    def find_child(self, location): #NH commented out orignal code
        '''
        Tries to find the lowest-level child which is closest to this location.

        If the location is on/near the boundary, return this node.
        If the location is within the boundary, find and return the child containing this location.
        If the location is outside the bounds, return None.
        '''
        distance_to_location = location.distance(self.center)
        if len(self.children) == 0:
            return self

        # each child of this node gets one candidate
        candidates = []
        for child in self.children:
            distance_to_child = location.distance(child.center)
            if distance_to_child <= child.radius:
                new_candidate = child.find_child(location)
                candidates.append(new_candidate)

        # find the closest candidate
        best_distance_so_far = distance_to_location
        best_candidate = self
        for candidate in candidates:
            distance = location.distance(candidate.center)
            if distance < best_distance_so_far:
                best_distance_so_far = distance
                best_candidate = candidate

        return best_candidate


    def location_in_bounds(self, location):
        '''
        If the node is a root node, we need to determine if the location is within the bounds.
        If the node is a child node, we only need to determine if the location is between two latitudes.
        '''
        if self.bounds[0] <= location.latitude <= self.bounds[1] and self.bounds[2] <= location.longitude <= self.bounds[3]:
            return True

        return False


    def set_disposition(self, obj, location, resolution): #NH commented out original code
        '''
        Used for setting initial disposition of the parent node of a disposition tree.
        The obj will be place in the contents of the currently existing, lowest-resolution node, whose resolution is higher than resolution
        Shifting an object should be done with adjust_disposition.
        :param obj: object to place into the disposition tree
        :param location: location of the object, used to place the object at the right node
        :param resolution: minimum acceptable granularity for the node obj will belong to
        Returns the node we attach the object to
        '''
        if self.parent:
            raise DispositionError('Cannot set disposition starting at non-root node.')

        # Find or create the node with the appropriate resolution
        try:
            node = self.find_child(location)
            # print(f"Found child node {node.id} for obj {obj.uid}")

        except LocationError:
            print("Object ", obj.uid, " is outside the bounds of this disposition tree.")
            print("TODO: send a message to alert the supervisor")
            return

        # walk up the tree until the node's resolution is smaller than resolution, or stop at the root node
        while node and node.resolution < resolution and node.parent:
            node = node.parent # if the node's resolution is too small, walk up the tree

        if node.resolution < resolution:
            raise ResolutionError(f'Object resolution too large. Node resolution: {node.resolution}, Requested resolution: {resolution}')
        
        node.contents.append(obj)
        return node


    def adjust_disposition(self, obj, location, resolution): #entire bottom changed
        '''
        Removes the object from this nodes contents.
        Sets the disposition to the correct new node, if a correct node exists.
        Returns the new node and a set containing the difference between old peers and new peers.
        Otherwise, it returns None.
        '''
        if obj not in self.contents:
            raise LocationError(f'Object {obj} not found in the current node.')
            
        old_peers = self.identify_peers()

        self.contents.remove(obj)
        root = self
        while root.parent:
            root = root.parent
        new_node = root.set_disposition(obj, location, resolution)

        new_peers = self.identify_peers()
        peer_difference = old_peers.difference(new_peers)

        return new_node, peer_difference


    def descendent_nodes(self):
        '''
        Collects and returns all descendents of this node.
        '''
        descendents = []

        for child in self.children:
            # append this child
            descendents.append(child)
            # append this child's children
            descendents += child.descendent_nodes()

        return descendents


    def identify_peers(self):
        '''
        Finds and returns all objects that may interact with one another.
        These objects are:
          - objects contained in this node
          - objects contained in any ancestor
          - objects contained in any descendent
          - objects contained in a sibling node but within this nodes radius
        '''
        peers = set()

        # Include objects in this node's contents.
        peers.update(self.contents)

        # Include objects in this node's ancestors' contents.
        ancestor = self.parent
        while ancestor:
            peers.update(ancestor.contents)
            ancestor = ancestor.parent

        # Include objects in this node's descendants' contents.
        descendents = self.descendent_nodes()
        for descendent in descendents:
            for desc_obj in descendent.contents:
                peers.add(desc_obj)

        # Include objects in this node's siblings' contents, if they are close enough to this node
        if self.parent:
            siblings = self.parent.children
            for sibling in siblings:
                for obj in sibling.contents:
                    if obj.location and obj.location.distance(self.center) < self.radius:
                        peers.add(obj)

        return peers


    def remove(self, obj):
        '''
        Remove obj from disposition tree. 
        May only be called on the root node.
        This method assumes multiple nodes can contain the same object,
        and will remove the object from all nodes in the tree.
        '''          
        if self.parent:
            raise LocationError('Cannot remove object from non-root node.')  # NH Use custom exception for clarity
        
        self._remove(obj)  # NH Call the internal _remove method to handle actual removal process


    def _remove(self, obj): #NH changed all
        '''
        Removes object from contents of node and all children.
        Should not be called outside of this class.
        '''
        if obj in self.contents:
            self.contents.remove(obj)
        for child in self.children:
            child._remove(obj)  # Recursively remove obj from all descendants


    def next_anticipated_disposition_change(self, obj):
        '''Identify future time at which obj will leave this disposition tree node based on its current speed and trajectory.'''
        # object speeds always in km/hr, but we want time t in seconds
        obj_speed_km_s = obj.speed / 3600

        # compute future distance as a function of time t, using speed and bearing
        distance_traveled = lambda t: obj_speed_km_s * t
        future_location = lambda t: obj.location.destination_point(distance_traveled(t))
        future_distance_from_center = lambda t: self.center.distance(future_location(t))

        # use diameter_travel_time as upper bound guess
        diameter_travel_time = self.radius * 2 / obj_speed_km_s

        # this will tell us when the distance = radius
        delta_t = root_scalar(lambda t: future_distance_from_center(t) - self.radius, x0=0, x1=diameter_travel_time).root

        return obj.time + delta_t


        # if obj.speed == 0: # disposition will never change
        #     return None
        # actual_speed = obj.speed / 3600.0 # speed in km/s
        
        # # use bearing to determine which boundaries plane will cross first
        # lowlat, highlat, lowlong, highlong = obj.dispositions[0].bounds
        # if obj.location.bearing > pi: # heading west
        #     longbound = lowlong
        # elif obj.location.bearing < pi: # heading east
        #     longbound = highlong
        # elif obj.location.bearing == 0 or obj.location.bearing == pi: # heading north or south
        #     longbound = None
        # if obj.location.bearing < pi / 2 or 1.5 * pi < obj.location.bearing: # heading north
        #     latbound = highlat
        # elif  pi / 2 < obj.location.bearing < 1.5 * pi: # heading south
        #     latbound = lowlat
        # elif obj.location.bearing == pi / 2 or obj.location.bearing == 1.5 * pi: # heading east or west
        #     latbound = None

        # # use scipy to find root

        # if latbound:
        #     x0 = obj.location.distance(GeographicLocation(latitude=latbound, longitude=obj.location.longitude, bearing=obj.location.bearing))
        #     delta_d1 = root_scalar(lambda d: obj.location.destination_point(d).latitude - latbound, x0 = x0, x1 = x0 + x0 * 0.01).root
        # else:
        #     delta_d1 = inf
        # if longbound:
        #     x0 = obj.location.distance(GeographicLocation(latitude=obj.location.latitude, longitude=longbound, bearing=obj.location.bearing))
        #     delta_d2 = root_scalar(lambda d: obj.location.destination_point(d).longitude - longbound, x0 = x0, x1 = x0 + x0 * 0.01).root
        # else:
        #     delta_d2 = inf

        # delta_d = min(delta_d1, delta_d2)
        
        # delta_t = delta_d / actual_speed    
        # return obj.time + delta_t


    def __repr__(self):
        return_str = ""
        return_str += f"Parent: {self.id}\n"
        children_ids = ""
        for c in self.children:
            children_ids += str(c.id)
            children_ids += " "
        return_str += f"Children: {children_ids}\n"
        return_str += "\n"

        for c in self.children:
            return_str += str(c)

        return return_str


class OneDimensionalDispositionTree():

    '''The root node for a one-dimensional disposition tree. The purpose of disposition trees is to provide efficient clustering of items that may have interactions.'''

    def __init__(self, bounds, granularity, gap_width, parent, granularity_reduction_factor = 10, gap_reduction_factor = 1):
        self.bounds = bounds # tuple containing the left and right bounds of the one-dimensional space
        self.parent = parent
        self.children = list() # child nodes of root
        self.contents = list() # objects currently stored in root
        self.granularity = granularity
        self.gap = ((bounds[1] - bounds[0]) / 2 - gap_width / 2, (bounds[1] - bounds[0]) / 2 + gap_width / 2) # gap in which objects that would otherwise be lower in the tree are contents of this node


    def find_or_make_child(self, location):
        '''Find the child into which a location falls, or if it does not exist, create it. Returns that child node.'''
        # check to see if the location of interest lies on the border
        # if it does, then the location belongs to this tree
        if self.gap[0] < location < self.gap[1]:
            return self
        # if it doesn't lie on the border, the location may belong to an existing child or we may need to make a new one
        else:
            # check if the location is within the bounds of any of the children
            for child in self.children:
                if child.bounds[0] < location < child.bounds[1]:
                    return child
            # location is 
            if location <= self.gap[0]:
                new_bounds = (self.bounds[0], self.gap[0]) # left
            else:
                new_bounds = (self.bounds[1], self.gap[1]) # right
            # new_gap = ((new_bounds[1] - new_bounds[0]) / 2 - (gap_width / gap_reduction_factor) / 2, (new_bounds[1] - new_bounds[0]) / 2 + (gap_width / gap_reduction_factor) / 2)
            new_child = OneDimensionalDispositionTree(new_bounds, self.granularity / self.granularity_reduction_factor, self.gap_width / self.gap_reduction_factor, self, self.granularity_reduction_factor, self.gap_reduction_factor)
            self.children.append(new_child)
            return new_child


    def set_disposition(self, obj, location, granularity):
        '''This method is intended to accomplish initial placement of an object in the disposition tree. Shifting an object that already exists in the disposition tree should be accomplished using adjust_disposition.'''
        if self.parent:
            raise Exception('Cannot set location starting at non-root node.') # TODO: define appropriate Exception class for this
        else:
            if self.gap[0] < location < self.gap[1]:
                self.contents.append(obj)
                return self
            else:
                while child.granularity > granularity:
                    child = self.find_or_make_child(location, granularity) # returns current node 
                    if granularity > child.granularity or child.gap[0] < location < child.gap[1]:
                        child.contents.append(obj)
                        return child
                    else:
                        child = child.find_or_make_child(location)

                        
    def descendent_nodes(self, nodes):
        '''Collects all descendent nodes that currently exist of this node.'''
        nodes = list()
        for c in self.children:
            nodes.append(c)
            c.descendent_nodes(nodes)
        return nodes
        
        
    def identify_peers(self, obj): #NH Implement the logic for identifying peers based on the definition provided
        '''This method uses the disposition tree to identify all of an object's peers--those objects with which it might interact.'''
        peers = set()

        # Include objects in this node's contents.
        peers.update(self.contents)

        # Include objects in this node's ancestors' contents.
        ancestor = self.parent
        while ancestor:
            peers.update(ancestor.contents)
            ancestor = ancestor.parent

        # Include objects in this node's descendants' contents.
        descendents = self.descendent_nodes()
        for descendent in descendents:
            peers.update(descendent.contents)

        # Ensure the original object is not considered its own peer.
        peers.discard(obj)

        return peers
        
        
    def adjust_disposition(self, obj, location, granularity):
        if obj in self.contents:
            if location in self.gap:
                return self, set() # same node
            else:
                self.contents.remove(obj)
                old_peers = {o.id for o in self.identify_peers(obj)}
        else:
            raise Exception('Cannot adjust disposition of object not in node.')
        p = self.parent
        while p.parent: # find root
            p = p.parent
        new_node = p.set_disposition(obj, location, granularity)
        new_peers = {o.id for o in new_node.identify_peers(obj)}
        return new_node, old_peers.difference(new_peers)
        
            
    def remove(self, obj):
        '''Remove obj from disposition tree. This method should only be called on the root node.'''
        def remove_inner(node):
            if obj in node.contents:
                node.contents.remove(obj)
            else:
                for child in node.children:
                    remove_inner(child)
                    
        if self.parent:
            raise Exception('Cannot set location starting at non-root node.') # TODO: define appropriate Exception class for this
        else:
            remove_inner(self)
        
