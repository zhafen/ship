import copy
import datetime
import numpy as np
import os
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt

import verdict

########################################################################

MODIFIABLE_VARIABLES = [ 'criteria values', 'markets', 'market segments' ]
MODIFIABLE_VARIABLE_SHORTHAND = {
    'criteria values': 'c',
    'markets': 'F',
    'market segments': 'f',
}

########################################################################

class Fleet( object ):

    def __init__(
        self,
        criteria = [
            'functionality',
            'accuracy',
            'understandability',
            'allure',
            'polish',
            'confidence',
            'compatibility',
            'usability',
        ],
        critical_value = 8.,
        markets_fp = None,
        market_segments_fp = None,
    ):
        '''Construct a fleet object that tracks various deliverables.

        Args:
            criteria (list of strs):
                Default criteria for evaluating a deliverable's readiness for release.

            critical_value (float):
                The necessary value per criteria for which a criteria is
                acceptable.
        '''
        self.criteria = criteria
        self.critical_value = critical_value

        self.ships = verdict.Dict({})

        # Settings
        if markets_fp is None:
            markets_fp = os.path.join(
                os.path.dirname( __file__ ),
                'markets.csv'
            )
        self.markets = pd.read_csv( markets_fp )
        self.markets = self.markets.set_index( 'Market Name' )

        if market_segments_fp is None:
            market_segments_fp = os.path.join(
                os.path.dirname( __file__ ),
                'market_segments.csv'
            )
        self.market_segments = pd.read_csv( market_segments_fp )
        self.market_segments = self.market_segments.set_index( 'Name' )

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

        assert name not in self.ships.keys(), "Ship {} already exists!".format( name )

        # Combination of particular criteria and default criteria
        criteria=list( set( self.criteria ).union( criteria ) )
        used_kwargs = {
            'critical_value': self.critical_value,
        }
        used_kwargs.update( kwargs )

        self[name] = Ship( name, criteria, *args, **used_kwargs )

    ########################################################################

    def move_ship( self, name, other_fleet, new_name=None ):
        '''Move a ship from another fleet to this fleet.
        This function can be used to rename if other_fleet is self.

        Args:
            name (str):
                Name of the deliverable.

            other_fleet (ship.Fleet):
                Other fleet to move ship from.

            new_name (str):
                New name, if changing.
        '''

        if new_name is None:
            new_name = name

        self[new_name] = copy.deepcopy( other_fleet[name] )
        del other_fleet.ships[name]
        self[new_name].name = new_name

    ########################################################################

    def launch_ship( self, name, dock_fleet ):
        '''Launch a ship from the docks to here.
        (Move the ship, and hold all the quality and market segment values constant.)

        Args:
            name (str):
                Name of the deliverable.

            dock_fleet (ship.Fleet):
                Other fleet to move ship from.
        '''

        self.move_ship( name, dock_fleet )

        for variable in [ 'criteria values', 'market segments' ]:
            for v_name in self[name][variable].keys():
                self[name].hold_variable_constant( variable, v_name )
    
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

    def evaluate_market_segments( self, ship_names='all', request_user_input=False, **kwargs ):
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
            result[name] = self[name].evaluate_market_segments( request_user_input, **kwargs )
            if result[name] == 'q':
                print( 'Exit code received. Exiting...' )
                return 'q'

        return result

    ########################################################################
    # I/O
    ########################################################################

    def save( self, filepath, save_changelog=True, changelog_fp=None, *args, **kwargs ):
        '''Save the data.
        Standard file format is *.dock.h5

        Args:
            filepath (str):
                File location.

            *args, **kwargs:
                Passed to verdict.Dict.to_hdf5
        '''

        if save_changelog:

            # If not provided, defaults to no-extension-filename.changelog.json
            if changelog_fp is None:
                changelog_fp = (
                    os.path.splitext( os.path.splitext( filepath )[0] )[0] +
                    '.changelog.json'
                )

            # Open changelog
            changelog = verdict.Dict.load( changelog_fp, create_nonexistent=True )

            # Open the data saved on disk
            prior_data = verdict.Dict.load( filepath, create_nonexistent=True )

            # Identify changes
            diff = prior_data.diff( self.ships.data )

            # Save
            if len( diff ) > 0:
                timestamp = str( datetime.datetime.now() )
                changelog[timestamp] = diff
                changelog.save( changelog_fp )

        self.ships.data.save( filepath, *args, **kwargs )

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
        y_axis = 'buy-in',
        ax = None,
        rotation = -45.,
        background_linecolor = '.4',
        **y_kwargs
    ):
        
        if ax is None:
            fig = plt.figure( figsize=(8,4), facecolor='w' )
            ax = plt.gca()
            
        # Get data
        if y_axis == 'quality':
            ys = self.ships.estimate_quality()
        elif y_axis == 'buy-in':
            ys = self.ships.estimate_buyin()
        elif y_axis in [ 'buy-in change', 'dB/dt' ]:
            dt = y_axis == 'dB/dt'
            ys = self.ships.estimate_buyin_change( dt=dt, **y_kwargs )
        elif y_axis in [ 'max buy-in change', 'max dB/dt' ]:
            dt = y_axis == 'max dB/dt'
            ys_unformatted = self.ships.estimate_buyin_change_max( dt=dt )
            ys = verdict.Dict({})
            for name, (v_key, value) in ys_unformatted.items():
                v_key_str = '{}.{}'.format( MODIFIABLE_VARIABLE_SHORTHAND[v_key[0]], v_key[1] )
                y_key = '{}\n{}'.format( name, v_key_str )
                ys[y_key] = value
        else:
            raise KeyError( 'Unrecognized y_axis, {}'.format( y_axis ) )
        
        plot_quant_vs_qual( ax, ys, rotation=rotation )

        # Draw relative line
        if y_axis == 'quality':
            ax.axhline(
                1,
                linewidth = 1,
                color = background_linecolor,
                zorder = -1,
            )
        
        # Set scale
        ax.set_yscale( 'log' )
        
        ax.set_ylabel( y_axis )

        return ys

    ########################################################################

    def plot_fleet_overview(
        self,
        fig = None,
        y_axes = [ 'quality', 'buy-in', 'max dB/dt' ],
    ):    
        
        mosaic = [ [ _, ] for _ in y_axes ]
        if fig is None:
            n_rows = len( y_axes )
            fig = plt.figure( figsize=(8,4*n_rows), facecolor='w' )
            
        ax_dict = fig.subplot_mosaic( mosaic )
                
        for y_axis in y_axes:
            _ = self.plot_fleet( y_axis=y_axis, ax=ax_dict[y_axis] )
            
        fig.tight_layout()

    ########################################################################

    def plot_ship(
        self,
        name,
        y_axis = 'buy-in',
        variable = 'criteria values',
        ax = None,
        rotation = -45.,
    ):
    
        if ax is None:
            fig = plt.figure( figsize=(8,4), facecolor='w' )
            ax = plt.gca()
            
        # Get data
        if y_axis == 'values':
            if variable == 'criteria values':
                ys = self.ships[name]['criteria values'] / self.critical_value
            elif ( variable == 'markets' ) or ( variable == 'market segments' ):
                ys = self.ships[name][variable]
            else:
                raise KeyError( 'Unrecognized variable, {}'.format( variable ) )
        elif y_axis == 'buy-in':
            if variable == 'criteria values':
                ys = self.ships[name]['criteria values'] / self.critical_value
            else:
                bl = self.ships[name].estimate_buyin_landscape()
                ys = bl[variable]
                all_v_names = {
                    'markets': self.markets.index,
                    'market segments': self.market_segments.index,
                }[variable]
                for v_name in all_v_names:
                    if v_name not in ys:
                        ys[v_name] = 0.
        elif y_axis in [ 'buy-in change', 'dB/dt' ]:
            dt = y_axis == 'dB/dt'
            dbl = self.ships[name].estimate_buyin_change_landscape( dt=dt )
            ys = dbl[variable]
        else:
            raise KeyError( 'Unrecognized y_axis, {}'.format( y_axis ) )

        plot_quant_vs_qual( ax, ys, rotation=rotation )
        
        # Set scale
        ax.set_yscale( 'log' )

        y_label = '{} {}'.format( variable, y_axis ) 

        # Plot maximum buy-ins
        if y_axis == 'buy-in' and variable != 'criteria values':

            dbl = self.ships[name].estimate_buyin_change_landscape()
            max_ys = dbl[variable]

            plot_quant_vs_qual( ax, max_ys, rotation=rotation, color='none', edgecolor='k' )
        
        if y_axis in [ 'buy-in', 'values' ]:
            # Draw relative line
            ax.axhline(
                1,
                linewidth = 1,
                color = 'k',
                zorder = 9,
            )
        
            if variable == 'criteria values':
                ax.tick_params( left=False, labelleft=False, which='minor' )
            
                # Draw relative line
                ax.axhline(
                    1,
                    linewidth = 1,
                    color = 'k',
                    zorder = 9,
                )

                # Set yticks to values
                ytick_labels = np.arange( 1, 11 )
                ytick_values = ytick_labels / self.critical_value
                ax.set_yticks( ytick_values )
                ax.set_yticklabels( ytick_labels )
                ax.set_ylim( ytick_values[0], ytick_values[-1], )

                # Note quality value
                quality = self[name].estimate_quality() 
                ax.annotate(
                    text = r'$q =$' + '{:.2g}'.format( quality ),
                    xy = ( 1, 1 ),
                    xycoords = 'axes fraction',
                    xytext = ( 5, -5 ),
                    textcoords = 'offset points',
                    va = 'top',
                    ha = 'left',
                )

                y_label = variable
        
        ax.set_ylabel( y_label )

        return ys

    ########################################################################

    def plot_ship_overview( self, name, fig=None, y_axis='buy-in' ):    
        
        mosaic = [ [ _, ] for _ in MODIFIABLE_VARIABLES ]
        if fig is None:
            n_rows = len( MODIFIABLE_VARIABLES )
            fig = plt.figure( figsize=(8,4*n_rows), facecolor='w' )
            
        ax_dict = fig.subplot_mosaic( mosaic )
            
        # Plot
        y_mins = []
        y_maxs = []
        for variable in MODIFIABLE_VARIABLES:
            ax = ax_dict[variable]
            
            ys = self.plot_ship( name, y_axis=y_axis, variable=variable, ax=ax, )
            
            # Store limits
            if not ( variable == 'criteria values' and y_axis in [ 'buy-in', 'values' ] ):
                y_mins.append( ax.get_ylim()[0] )
                y_maxs.append( ax.get_ylim()[1] )
                
        # Adjust limits
        y_min = np.min( y_mins )
        y_max = np.max( y_maxs )
        for variable in MODIFIABLE_VARIABLES:
            ax = ax_dict[variable]
            if not ( variable == 'criteria values' and y_axis in [ 'buy-in', 'values' ] ):
                ax.set_ylim( y_min, y_max )

        # Add annotation of name
        ax_dict[mosaic[0][0]].annotate(
            text = name,
            xy = ( 0, 1 ),
            xycoords = 'axes fraction',
            xytext = ( 5, 5 ),
            textcoords = 'offset points',
            va = 'bottom',
            ha = 'left',
        )
            
        fig.tight_layout()
        
        return fig

    ########################################################################

    def plot_markets(
        self,
        ax = None,
        rotation = -45.,
    ):
        
        if ax is None:
            fig = plt.figure( figsize=(8,4), facecolor='w' )
            ax = plt.gca()
        
        # Get y values
        y_series = ( self.markets * self.market_segments['Weight'] ).sum( axis=1 )
        ys = verdict.Dict({})
        for name in y_series.index:
            ys[name] = y_series.loc[name]
            
        plot_quant_vs_qual( ax, ys, rotation=rotation )
        
        # Set scale
        ax.set_yscale( 'log' )
        
        ax.set_ylabel( 'max buy-in' )

        return ys

########################################################################

def plot_quant_vs_qual( ax, ys, rotation=-45., **scatter_kwargs ):

    ys_arr = ys.array()
    xs = np.arange( ys_arr.size )
    
    used_scatter_kwargs = dict(
        color = 'k',
        marker = 'd',
        zorder = 2,
    )
    used_scatter_kwargs.update( scatter_kwargs )
    # Actual plot
    ax.scatter(
        xs,
        ys_arr,
        **used_scatter_kwargs
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
        critical_value = 8.,
        description = '',
        category = '',
        markets_fp = None,
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
            'criteria values': {},
            'market segments': {},
            'markets': {},
            'attrs': {
                'name': name,
                'description': description,
                'category': category,
            }
        })
        self.critical_value = critical_value

        # Settings
        if markets_fp is None:
            markets_fp = os.path.join(
                os.path.dirname( __file__ ),
                'markets.csv'
            )
        self.markets = pd.read_csv( markets_fp )
        self.markets = self.markets.set_index( 'Market Name' )

        if market_segments_fp is None:
            market_segments_fp = os.path.join(
                os.path.dirname( __file__ ),
                'market_segments.csv'
            )
        self.market_segments = pd.read_csv( market_segments_fp )
        self.market_segments = self.market_segments.set_index( 'Name' )

        # Initial state
        for key in criteria:
            self.data['criteria values'][key] = 0.

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

        return list( self.data['criteria values'].keys() )

    ########################################################################

    def hold_variable_constant( self, variable, name ):
        '''Set a variable as constant, i.e. dB/dvariable = 0.

        Args:
            variable (str):
                Type of variable, e.g. 'criteria values'.

            name (str):
                Specific variable, e.g. 'functionality'
        '''

        key = 'variables held constant'
        if key not in self.data:
            self.data[key] = []
        self.data[key].append( [variable, name] )

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
            for key, item in copy.deepcopy( self['criteria values'].items() ):
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
                        del self['criteria values'][key]
                        continue

                    criteria_values[key] = float( value )

        # Update the current ship values
        self['criteria values'].update( criteria_values )

        # Return a number representative of the status.
        # This number is not typically used elsewhere.
        overall_status = np.prod( self['criteria values'].array() )
        return overall_status

    ########################################################################

    def evaluate_market_segments( self, request_user_input=False, **compatibility_values ):
        '''Estimate parameters related to the market for the deliverable.
        Right now this just stores the data in the right spot.
        '''

        used_keys = set( self['market segments'].keys() ).union(
            set( self.market_segments.index )
        )
        if request_user_input:
            print( 'Evaluating market segments for [ {} ]...'.format( self.name ) )
            for key in used_keys:
                if key not in compatibility_values:

                    if key in self['market segments'].keys():
                        item = self['market segments'][key]
                    else:
                        item = self.market_segments.loc[key]['Default Compatibility']
                    value = input( '    {} = {}. Updated ='.format( key, item ) )
                    
                    # Skip
                    if value == '':
                        value = item
                    elif value == 'q':
                        print( '    Exit code received. Saving and quitting.' )
                        return 'q'
                    elif value == 'd':
                        print( '    Removing criteria {}'.format( key ) )
                        del self['market segments'][key]
                        continue

                    compatibility_values[key] = float( value )
        else:
            # Replace empty values
            for key in used_keys:
                if ( key in self['market segments'] ) or ( key in compatibility_values ):
                    continue
                compatibility_values[key] = self.market_segments.loc[key]['Default Compatibility']

        # Update the current ship values
        self['market segments'].update( compatibility_values )

        return verdict.Dict( self['market segments'] )

    ########################################################################

    def send_to_market( self, request_user_input=False, **markets ):
        '''Estimate parameters related to the market for the deliverable.
        Right now this just stores the data in the right spot.
        '''

        if request_user_input:
            print( 'Sending [ {} ] to markets...'.format( self.name ) )
            for key, item in self['markets'].items():
                if key not in markets:
                    value = input( '    {} = {}. Updated ='.format( key, item ) )
                    
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

                    markets[key] = float( value )

        # Update the current ship values
        self['markets'].update( markets )

        return verdict.Dict( self['markets'] )

    ########################################################################

    def estimate_quality( self ):
        '''Estimate the quality of the deliverable assuming quality is:
        q_k = product( criteria_value / critical_value )
        This is a Cobb-Douglas utility function.

        Returns:
            quality (float):
                Estimate for the quality.
        '''

        scaled = self['criteria values'] / 10.
        quality = np.prod( scaled.array() )

        return quality

    ########################################################################

    def estimate_market_segment_buyin(
        self,
        ms_name,
        use_default_for_missing_values = True,
    ):
        '''Estimate the buy-in expected from one person that is
        representative of a specified market segment,
        B_ik = q_k * b_i * f_ik
        where...
        i tracks market segment
        k tracks ship
        q_k := quality of the ship
        b_i := weight of the market segment
        f_ik := compatibility between the ship and the market segment

        Args:
            ms_name (str):
                Market segment to consider.
            
        Returns:
            market_segment_buyin (float):
                Estimate for the market segment buy-in.
        '''

        q_k = self.estimate_quality()
        b_i = self.market_segments.loc[ms_name]['Weight']
        f_ik = self['market segments'][ms_name]

        return q_k * b_i * f_ik

    ########################################################################

    def estimate_market_buyin( self, m_name ):
        '''Estimate the buy-in expected from sending the ship to a specific market,
        B_jk = F_jk * sum( n_ij * B_ik )
        where...
        i tracks market segment
        j tracks market
        k tracks ship
        F_jk := compatibility between ship k and market j as a whole
        n_ij := number of individuals from market segment i in market j
        B_ik := market segment buyin
            (Note that B_jk = B_ik when j is actually just a market segment)

        Args:
            m_name (str):
                Market to consider.

        Returns:
            market_buyin (float):
                Estimate for the market buy-in.
        '''

        B_jk = 0.
        market_row = self.markets.loc[m_name]
        for ms_name in market_row.index:
            n_ij = market_row[ms_name]
            B_ik = self.estimate_market_segment_buyin( ms_name )
            B_jk += n_ij * B_ik

        F_jk = self['markets'][m_name]
        B_jk *= F_jk

        return B_jk

    ########################################################################

    def estimate_buyin( self ):
        '''Estimate the buy-in expected from sending the ship to all markets,
        B_k = sum( B_jk )
        where...
        j tracks market
        k tracks ship
        B_jk := market buyin
            
        Returns:
            buyin (float):
                Estimate for the buy-in.
        '''

        B_k = 0.
        for m_name in self['markets'].keys():
            B_jk = self.estimate_market_buyin( m_name )
            B_k += B_jk

        return B_k

    ########################################################################

    def estimate_buyin_landscape( self ):
        '''Function for showing all user-controllable buy-in estimates.
            
        Returns:
            landscape:
                Dict containing all buy-in estimates.
        '''

        landscape = {}
        landscape['quality'] = self.estimate_quality()
        landscape['buy-in'] = self.estimate_buyin()

        # Variables with multiple options
        landscape['criteria values'] = self['criteria values']
        keys = {
            'markets': self['markets'].keys(),
            'market segments': self.market_segments.index,
        }
        for variable, used_keys in keys.items():
            fn = getattr( self, 'estimate_{}_buyin'.format( variable.replace( ' ', '_' )[:-1] ) )
            landscape[variable] = {}
            for v_name in used_keys:
                landscape[variable][v_name] = fn( v_name )

        return verdict.Dict( landscape )

    ########################################################################

    def estimate_buyin_change( self, variable, name=None, dt=False ):
        '''Estimate the instantaneous change in buyin, dB/dX.
        Note that this calculation currently duplicates options, and could be sped up.

        The options are...
        'quality' (aka 'q' or 'q_k'):
            dB_k/dq_k = B_k / q_k
        'criteria value' (aka 'c' or 'c_m'):
            dB_k/dc_m = alpha_m * B_k / c_m
        'market compatibility' (aka 'F' or 'F_jk'):
            dB_k/dF_jk = B_jk / F_jk
        'market segment compatibility' (aka 'f' or 'f_ik'):
            dB_k/df_ik = B_ik / f_ik * sum_j( F_jk * n_ij )
        where...
        i trackets market segment
        j tracks market
        k tracks ship
        m tracks criteria value
        B_k := ship buyin
        B_jk := market buyin
        B_ik := market segment buyin
        q_k := ship quality
        c_m := criteria value
        alpha_m := weight for criteria value c_m. Not yet implemented.
        F_jk := market compatibility
        f_jk := market segment compatibility
        n_ij := number of members of market segment i in market j

        Args:
            variable (str):
                What to take the derivative w.r.t.

            name (str):
                When multiple variables of a given type, which particular variable.

            dt (bool):
                If True, convert dB/dX to dB/dt via dX/dt = 1 - X, i.e. improving X too much
                produces diminishing returns.

        Returns:
            dB/dX (float):
                Estimate for derivative of buy-in
        '''

        # Map to shorthands
        if variable in [ 'quality', 'q', 'q_k' ]:
            variable = 'quality'
        elif variable in [ 'criteria values', 'c', 'c_m' ]:
            variable = 'criteria values'
        elif variable in [ 'markets', 'F', 'F_jk' ]:
            variable = 'markets'
        elif variable in [ 'market segments', 'f', 'f_ik' ]:
            variable = 'market segments'

        # Skip constant variables
        if 'variables held constant' in self.data:
            if [ variable, name ] in self.data['variables held constant']:
                return 0.

        if variable == 'quality':
            B_k = self.estimate_buyin()
            q_k = self.estimate_quality()
            dB = B_k / q_k
            if dt:
                dB *= 1. - q_k
            return dB
        
        elif variable == 'criteria values':
            B_k = self.estimate_buyin()
            c_m = self['criteria values'][name] / 10.

            # Largely unconstrained scenario.
            if np.isclose( B_k, 0. ) and np.isclose( c_m, 0. ):
                return 0.

            dB = B_k / c_m
            if dt:
                dB *= 1. - c_m
            return dB

        elif variable == 'markets':
            dB = 0.
            market_row = self.markets.loc[name]
            for ms_name in market_row.index:
                n_ij = market_row.loc[ms_name]
                B_ik = self.estimate_market_segment_buyin( ms_name )
                dB += n_ij * B_ik

            if dt:
                dB *= 1. - self['markets'][name]

            return dB

        elif variable == 'market segments':
            q_k = self.estimate_quality()
            b_i = self.market_segments['Weight'].loc[name]
            sum_term = 0.
            for m_name, F_jk in self['markets'].items():
                sum_term += F_jk * self.markets.loc[m_name].loc[name]
            dB = q_k * b_i * sum_term

            if dt:
                f_ik = self['market segments'][name]
                dB *= 1. - f_ik

            return dB

        else:
            raise KeyError( 'Unrecognized variable, {}'.format( variable ) )

    ########################################################################

    def estimate_buyin_change_landscape( self, dt=False ):
        '''Function for showing all user-controllable derivatives of buyin.

        Args:
            dt (bool):
                If True, convert dB/dX to dB/dt via dX/dt = 1 - X, i.e. improving X too much
                produces diminishing returns.
            
        Returns:
            landscape:
                Dict containing all instantaneous variable values.
        '''

        landscape = {}
        landscape['quality'] = self.estimate_buyin_change( 'q', dt=dt )

        for variable in MODIFIABLE_VARIABLES:
            landscape[variable] = {}
            for v_name in self[variable].keys():
                landscape[variable][v_name] = self.estimate_buyin_change(
                    variable,
                    name = v_name,
                    dt = dt,
                )

        return verdict.Dict( landscape )

    ########################################################################

    def estimate_buyin_change_max( self, dt=False ):
        '''Function for showing all user-controllable derivatives of buyin.

        Args:
            dt (bool):
                If True, convert dB/dX to dB/dt via dX/dt = 1 - X, i.e. improving X too much
                produces diminishing returns.
            
        Returns:
            maxkeys (tuple of strs):
                Strings indicating what variable is the max.

            max (float):
                Max value.
        '''

        dbl = self.estimate_buyin_change_landscape( dt=dt )

        v_maxs = verdict.Dict({})
        for variable in MODIFIABLE_VARIABLES:

            # Skip empty
            if len( dbl[variable] ) == 0:
                continue

            v_name, value = dbl[variable].keymax()
            v_key = ( variable, v_name )
            v_maxs[v_key] = value

        # Fully empty scenario
        if len( v_maxs ) == 0:
            return 'not enough info', 0.

        v_key, value = v_maxs.keymax()

        return v_key, value