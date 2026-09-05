from typing import NamedTuple
# DO NOT IMPORT THIS MODULE!!!
# Its purpose is to describe APIs that should be implemented explicitly by ROMANCER classes


# This module contains the various types of messages used by various parts of ROMANCER to interact with each other.
# These messages need to be immutable Python objects in order to pass them between threads without complications.
# typing.NamedTuple offsers efficient and convenient support for this. Unfortunately, unlike dataclasses.dataclass
# typing.NamedTuple does not offer real inheritance. Therefore, all message classes need to implement all of their
# associated methods directly.

class ROMANCERMessage(NamedTuple):
    '''This class describes the base API that all message classes should implement.'''
    
    id: int # unique identifier used for routing message and confirming receipt
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    messagetype: str # this string can be employed to dispatch messages
    confirmReceipt: bool = False # can be ignored if there isn't a good reason to check if messages were received (e.g., in a single-threaded environment)


# In a single-thread environment, these are probably superfluous
class ROMANCERMessageReceipt(NamedTuple):
    '''This kind of message is used to inform a sender that the message was received.'''
    
    id: int # unique identifier used for routing message and confirming receipt
    sentid: int # unique identifier of message that has been received
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    confirmReceipt: bool = False 

    
class ROMANCERMessageEnqueued(NamedTuple):
    '''This kind of message is used to inform a sender that the message was enqueued for (possible) later processing.'''

    id: int # unique identifier used for routing message and confirming receipt
    sentid: int # unique identifier of message that has been received
    recipient: tuple[int, int] # recipient can be specific object, category of possible recipients, etc.
    sender: tuple[int, int] # specific object sending message
    confirmReceipt: bool = False


# These messages are intended to take advantage of Python's duck typing to allow for the
# introduction of new kinds of messages with arbitrary slots as the need arises. 

# For routing purposes, messages require 'addresses.' For these purposes we define a tuple of two
# ints, where the first represents a kind of 'zip code' used for routing and the second is
# associated with one specific recipient object

# For consistence, '1' should be assigned to the supervisor and '2' to the environment
# If the 'zip code' is the actual recipient then the second integer in the tuple can be '0'
# e.g., the address (2, 0) will send a message to the environment as a whole

# The Environment needs to assign a unique integer address for each object in order to route
# messages. In the basic implementation this can be used as indices in a dict associated with a
# direct reference to the object in question. To 'send' a message to an object, the Environment
# can use this reference to deliver the message to the recipient's inbox

# Every object in ROMANCER needs to have a function that it uses to act on messages. So long as
# this function has the necessary properties, it can be implemented however the user sees fit.
# There are times when a match ... case statement is called for, and others in which which a
# global dict is a more appropriate solution.


def sample_dispatcher(obj, message):
    '''An example of the dispatcher function used by various parts of ROMANCER to act on the basis of received messages.

    Objects can do three things in response to messages: change state under their purview (including that of child objects), send one or more new messages, or ignore the message. Changing state and sending messages will often occur together.'''
    if message.messagetype == 'type1':
        new_attribute = my_func(obj.attribute, message)
        object.attribute = new_attribute # change object state
    elif message.messagetype == 'type2':
        new_message_id = obj.new_message_id()
        sender = obj.full_address
        new_message_type = my_other_func(obj, message)
        new_message = ROMANCERMessage(id = new_message_id, sender = sender,
                                      recipient = (1, 0), # supervisor
                                      messagetype = new_message_type)
        obj.outbox.append(new_message) # send new message
    elif message.messagetype in ['ignorable', 'message', 'types']:
        pass # ignore message and do nothing
    else:
        except UndispatchedMessageError: # throw error
            print("Undispatched message:", message)

            
# Rather than storing all of the dispatch logic inside of a function, it may be preferable in
# some cases to store this information inside of a more inspectable, modifiable structure, such
# as a dict containing callables with an (object, message) signature. For example:

my_dispatch_table = {'type1' = lambda obj, message: my_state_modifying_func(obj, message),
                     'type2' = my_message_sending_callable, # so long as my_message_sending_callable has appropriate call signature
                     'ignorable' = lambda obj, message: pass,
                     'message' = lambda obj, message: pass,
                     'types' = lambda obj, message: pass}

def alternative_sample_dispatcher(obj, message):
    f = my_dispatch_table.get(message.messagetype, None) # returns None if key not in table
    if f:
        f(obj, message)
    else:
        except UndispatchedMessageError as err:
            print("Undispatched message error:", err)


# It may be desirable in some cases to have a heirarchical set of dispatch tables that are
# searched on a local-global basis. For example, each instance can have a dispatch table that
# is searched first, with a table assocaited with the class searched if the instance table does
# not contain the relevant key. This arrangement has the advantage of high customizability:
# a single instance can be endowed with customized behavior if desired without impacting the
# others.
