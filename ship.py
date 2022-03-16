import numpy as np

import verdict

########################################################################

class Docks( object ):

    def __init__(
        self,
        criteria = [
            'functionality',
            'polish',
            'allure',
            'confidence',
            'understandability',
            'accuracy',
            'compatibility',
            'usability',
            'audience customization',
        ],
    ):
        '''Construct a Docks object that tracks various deliverables.

        Args:
            criteria (list of strs):
                Default criteria for evaluating a deliverable's readiness for release.
        '''
        self.criteria = criteria

        self.ships = verdict.Dict({})

    ########################################################################
    # Access methods
    ########################################################################

    def __getitem__( self, key ):

        return self.ships[key]

    def __setitem__( self, key, value ):

        self.ships[key] = value

    ########################################################################
    # Shipbuilding methods
    ########################################################################

    def construct_ship( self, name, criteria=[], *args, **kwargs ):
        '''Start tracking progress for a deliverable.

        Args:
            name (str):
                Name of the deliverable.

            criteria (list of strs):
                List of names of criteria to evaluate for when the deliverable is ready.
        '''

        # Combination of particular criteria and default criteria
        criteria=list( set( self.criteria ).union( criteria ) )

        self[name] = Ship( name, criteria, *args, **kwargs )
    
    ########################################################################

    def evaluate_ship( self, name, *args, **criteria_values ):
        '''Evaluate the current status of a ship.

        Args:
            name (str):
                Name of the deliverable.

            criteria_values (dict of floats):
                Values for the criteria.
        '''

        return self[name].evaluate( *args, **criteria_values )

    ########################################################################
    # I/O
    ########################################################################

    def save( self, filepath, *args, **kwargs ):
        '''Save the data.
        Standard file format is *.dock.h5

        Args:
            filepath (str):
                File location.

            *args, **kwargs:
                Passed to verdict.Dict.to_hdf5
        '''

        self.ships.data.to_hdf5( filepath, *args, **kwargs )

    ########################################################################

    @classmethod
    def load( cls, filepath, *args, **kwargs ):
        '''Load the data.
        Standard file format is *.dock.h5

        Args:
            filepath (str):
                File location.

            *args, **kwargs:
                Passed to verdict.Dict.from_hdf5
        '''

        # Get data
        data = verdict.Dict.from_hdf5( filepath, *args, **kwargs )

        # Construct
        docks = Docks()
        for name, ship_data in data.items():
            docks.ships[name] = Ship( name )
            docks.ships[name].data = ship_data

        return docks

########################################################################

# Convenience wrapper for docks constructor
def load( *args, **kwargs ):
    return Docks.load( *args, **kwargs )
load.__doc__ = Docks.load.__doc__

########################################################################

class Ship( object ):

    def __init__( self, name, criteria=[] ):
        '''Object for a tracked deliverable.

        Args:
            name (str):
                Name of the deliverable.

            criteria (list of strs):
                List of names of criteria to evaluate for when the deliverable is ready.

            status (dict of floats):
                Initial status of the ship.
        '''

        # Store properties
        self.name = name
        self.data = verdict.Dict({
            'status': {},
        })

        # Initial state
        for key in criteria:
            self.data['status'][key] = 0.

    ########################################################################
    # Access methods
    ########################################################################

    def __getitem__( self, key ):

        return self.data[key]

    def __setitem__( self, key, value ):

        self.data[key] = value

    ########################################################################
    # Ship state
    ########################################################################

    def criteria( self ):
        '''The criteria used for evaluating the ship.'''

        return list( self.data['status'].keys() )

    ########################################################################

    def evaluate( self, request_user_input=False, **criteria_values ):
        '''Evaluate the current status of the ship.

        Args:
            request_user_input (bool):
                If True, ask the user to update the ship values.

            criteria_values (dict of floats):
                Values for the criteria.
        '''

        if request_user_input:
            print( 'Updating values for Ship {}...'.format( self.name ) )
            for key, item in self['status'].items():
                if key not in criteria_values:
                    value = input( '    {} = {}. New value?'.format( key, item ) )
                    
                    # Skip
                    if value == '':
                        continue

                    criteria_values[key] = float( value )

        # Update the current ship values
        self['status'].update( criteria_values )

        # Perform the evaluation
        overall_status = np.prod( self['status'].array() )

        return overall_status

