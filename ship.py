import copy
import numpy as np
import os
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt

import verdict

########################################################################

class Fleet( object ):

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
            'market customization',
        ],
    ):
        '''Construct a fleet object that tracks various deliverables.

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

    def evaluate( self, ship_names='all', request_user_input=False, **kwargs ):
        '''Evaluate the current status of all ships.

        Args:
            ship_names (str or list of strs):
                Names of ships to evaluate. If 'all' then all are evaluated.

            **kwargs:
                Passed to Ship.evaluate
        '''

        if ship_names == 'all':
            ship_names = list( self.ships.keys() )

        result = {}
        for name in ship_names:
            result[name] = self[name].evaluate( request_user_input, **kwargs )
            if result[name] == 'q':
                print( 'Exit code received. Exiting...' )
                return 'q'

        return result

    ########################################################################

    def evaluate_market( self, ship_names='all', request_user_input=False, **kwargs ):
        '''Evaluate the current status of all ships.

        Args:
            ship_names (str or list of strs):
                Names of ships to evaluate. If 'all' then all are evaluated.

            **kwargs:
                Passed to Ship.evaluate
        '''

        if ship_names == 'all':
            ship_names = list( self.ships.keys() )

        result = verdict.Dict({})
        for name in ship_names:
            result[name] = self[name].evaluate_market( request_user_input, **kwargs )
            if result[name] == 'q':
                print( 'Exit code received. Exiting...' )
                return 'q'

        return result

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

        # Identify filetype to choose how to save
        filetype = os.path.splitext( filepath )[1]

        if filetype == '.json':
            self.ships.data.to_json( filepath, *args, **kwargs )
        elif filetype in [ '.hdf5', '.h5' ]:
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

        # Identify filetype to choose how to load
        filetype = os.path.splitext( filepath )[1]

        # Get data
        if filetype == '.json':
            data = verdict.Dict.from_json( filepath, *args, **kwargs )
        elif filetype in [ '.hdf5', '.h5' ]:
            data = verdict.Dict.from_hdf5( filepath, *args, **kwargs )

        # Construct
        fleet = Fleet()
        for name, ship_data in data.items():
            fleet.ships[name] = Ship( name )
            fleet.ships[name].data = ship_data

        return fleet

    ########################################################################
    # Plotting
    ########################################################################

    def plot_fleet(
        self,
        y_axis = 'impact',
        ax = None,
        critical_value = 8.,
        rotation = -45.,
        background_linecolor = '.4',
    ):
        
        if ax is None:
            fig = plt.figure()
            ax = plt.gca()
            
        # Get data
        if y_axis == 'quality':
            ys = self.ships.estimate_quality( critical_value=critical_value )
            ys_arr = ys.array()
            xs = np.arange( ys_arr.size )
        elif y_axis == 'impact':
            ys = self.ships.estimate_impact( critical_value=critical_value )
            ys_arr = ys.array()
        xs = np.arange( ys_arr.size )
        
        # Actual plot
        ax.scatter(
            xs,
            ys_arr,
            color = 'k',
            marker = 'd',
            zorder = 2,
        )

        if y_axis == 'impact':
            market_arr = self.ships.estimate_market().array()
            ax.scatter(
                xs,
                market_arr,
                color = 'k',
                marker = 'd',
                zorder = 2,
                facecolor = 'none',
            )
        
        # Draw relative line
        if y_axis == 'quality':
            ax.axhline(
                1,
                linewidth = 1,
                color = background_linecolor,
                zorder = -1,
            )
        
        # Set xtick labels to sim names
        ax.xaxis.set_ticks( xs )
        ax.xaxis.set_ticklabels(
            ys.keys_array(),
            rotation=rotation,
            va='top',
            ha='left',
        )
        ax.grid(
            axis = 'x',
            which = 'major',
            zorder = -1,
        )
        
        # Set scale
        ax.set_yscale( 'log' )
        
        ax.set_ylabel( y_axis )

    ########################################################################

    def plot_ship(
        self,
        name,
        ax=None,
        critical_value=8.,
        rotation=-45.,
    ):
    
        if ax is None:
            fig = plt.figure()
            ax = plt.gca()
            
        # Get data
        criteria = self.ships[name]['status'] / critical_value
        criteria_values = criteria.array()
        xs = np.arange( criteria_values.size )
        
        # Actual plot
        ax.scatter(
            xs,
            criteria_values,
            color = 'k',
            zorder = 10,
        )
        
        # Draw relative line
        ax.axhline(
            1,
            linewidth = 1,
            color = 'k',
            zorder = 9,
        )
        
        # Set scale
        ax.set_yscale( 'log' )
        
        ax.tick_params( left=False, labelleft=False, which='minor' )
        
        # Set xtick labels to sim names
        ax.xaxis.set_ticks( xs )
        ax.xaxis.set_ticklabels( criteria.keys_array(), rotation=rotation, va='top', ha='left', )
        
        # Set yticks to values
        ytick_labels = np.arange( 1, 11 )
        ytick_values = ytick_labels / critical_value
        ax.set_yticks( ytick_values )
        ax.set_yticklabels( ytick_labels )
        ax.set_ylim( ytick_values[0], ytick_values[-1], )
        
        # Setup gridlines
        ax.grid(
            which = 'major',
            zorder = -2,
        )

        # Note quality value
        quality = self[name].estimate_quality( critical_value=critical_value ) 
        ax.annotate(
            text = r'$r =$' + '{:.2g}'.format( quality ),
            xy = ( 1, 1 ),
            xycoords = 'axes fraction',
            xytext = ( 5, -5 ),
            textcoords = 'offset points',
            va = 'top',
            ha = 'left',
            fontsize = 16,
        )
        
        ax.set_ylabel( r'criteria value' )

########################################################################

# Convenience wrapper for fleet constructor
def load( *args, **kwargs ):
    return Fleet.load( *args, **kwargs )
load.__doc__ = Fleet.load.__doc__

########################################################################

class Ship( object ):

    def __init__(
        self,
        name,
        criteria = [],
        description = '',
        category = '',
        market_segments_fp = None,
    ):
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
            'market': {},
            'attrs': {
                'name': name,
                'description': description,
                'category': category,
            }
        })

        # Settings
        if market_segments_fp is None:
            market_segments_fp = os.path.join(
                os.path.dirname( __file__ ),
                'market_segments.csv'
            )
        self.market_segments = pd.read_csv( market_segments_fp )
        self.market_segments = self.market_segments.set_index( 'Name' )


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
            print( 'Evaluating [ {} ]...'.format( self.name ) )
            for key, item in copy.deepcopy( self['status'].items() ):
                if key not in criteria_values:
                    value = input( '    {} = {}. Updated ='.format( key, item ) )
                    
                    # Skip
                    if value == '':
                        continue
                    elif value == 'q':
                        print( '    Exit code received. Saving and quitting.' )
                        return 'q'
                    elif value == 'd':
                        print( '    Removing criteria {}'.format( key ) )
                        del self['status'][key]
                        continue

                    criteria_values[key] = float( value )

        # Update the current ship values
        self['status'].update( criteria_values )

        # Return a number representative of the status.
        # This number is not typically used elsewhere.
        overall_status = np.prod( self['status'].array() )
        return overall_status

    ########################################################################

    def evaluate_market( self, request_user_input=False, **compatibility_values ):
        '''Estimate parameters related to the market for the deliverable.
        Right now this just stores the data in the right spot.
        '''

        if request_user_input:
            print( 'Evaluating market segments for [ {} ]...'.format( self.name ) )
            used_keys = set( self['market'].keys() ).union( set( self.market_segments.index ) )
            for key in used_keys:
                if key not in compatibility_values:

                    if key in self['market'].keys():
                        item = self['market'][key]
                        value = input( '    {} = {}. Updated ='.format( key, item ) )
                    else:
                        value = input( '    {} = 0. Updated ='.format( key ) )
                    
                    # Skip
                    if value == '':
                        continue
                    elif value == 'q':
                        print( '    Exit code received. Saving and quitting.' )
                        return 'q'
                    elif value == 'd':
                        print( '    Removing criteria {}'.format( key ) )
                        del self['market'][key]
                        continue

                    compatibility_values[key] = float( value )

        # Update the current ship values
        self['market'].update( compatibility_values )

        return verdict.Dict( self['market'] )

    ########################################################################

    # BUYIN
    # def estimate_market( self ):
    #     '''Estimate the impact of a deliverable, assuming
    #     weighted market = product( n, s, w )
    #     where n is the number of market members identified,
    #     w is the relevance of each market member to the user's goals,
    #     and s is the compatibility of the ship to each market.
    #     '''

    #     weighted_market = 0.
    #     for i, market_key in enumerate( self['market']['tags'] ):
    #         n = self['market']['n'][i]
    #         compatibility = self['market']['compatibility'][i]
    #         weight = self.config['markets']['weight'][market_key]
    #         weighted_market += n * compatibility * weight

    #     return weighted_market

    ########################################################################

    def estimate_quality( self, critical_value=8. ):
        '''Estimate the quality of the deliverable assuming quality is:
        r = product( criteria_value / critical_value )

        Args:
            critical_value (float):
                The necessary value per criteria for which a criteria is
                acceptable.

        Returns:
            quality (float):
                Estimate for the quality.
        '''

        scaled = self['status'] / critical_value
        quality = np.prod( scaled.array() )

        return quality

    ########################################################################