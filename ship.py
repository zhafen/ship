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
            'accuracy',
            'understandability',
            'allure',
            'polish',
            'confidence',
            'compatibility',
            'usability',
        ],
        markets_fp = None,
        market_segments_fp = None,
    ):
        '''Construct a fleet object that tracks various deliverables.

        Args:
            criteria (list of strs):
                Default criteria for evaluating a deliverable's readiness for release.
        '''
        self.criteria = criteria

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

        # Combination of particular criteria and default criteria
        criteria=list( set( self.criteria ).union( criteria ) )

        self[name] = Ship( name, criteria, *args, **kwargs )

    ########################################################################

    def move_ship( self, name, other_fleet ):
        '''Move a ship from another fleet to this fleet.

        Args:
            name (str):
                Name of the deliverable.

            other_fleet (ship.Fleet):
                Other fleet to move ship from.
        '''

        self[name] = copy.deepcopy( other_fleet[name] )
        del other_fleet.ships[name]
    
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
        y_axis = 'buy-in',
        ax = None,
        critical_value = 8.,
        rotation = -45.,
        background_linecolor = '.4',
        **y_kwargs
    ):
        
        if ax is None:
            fig = plt.figure( figsize=(8,4), facecolor='w' )
            ax = plt.gca()
            
        # Get data
        if y_axis == 'quality':
            ys = self.ships.estimate_quality( critical_value=critical_value )
        elif y_axis == 'buy-in':
            ys = self.ships.estimate_buyin( critical_value=critical_value )
        elif y_axis == 'buy-in change':
            ys = self.ships.estimate_buyin_change( critical_value=critical_value, **y_kwargs )
        
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

    def plot_ship(
        self,
        name,
        y_axis = 'buy-in',
        variable = 'criteria values',
        ax = None,
        critical_value = 8.,
        rotation = -45.,
    ):
    
        if ax is None:
            fig = plt.figure( figsize=(8,4), facecolor='w' )
            ax = plt.gca()
            
        # Get data
        if y_axis == 'buy-in':
            if variable == 'criteria values':
                ys = self.ships[name]['criteria values'] / critical_value
            else:
                bl = self.ships[name].estimate_buyin_landscape( critical_value=critical_value )
                ys = bl[y_axis]
        elif y_axis == 'buy-in change':
            dbl = self.ships[name].estimate_buyin_change_landscape( critical_value=critical_value )

        plot_quant_vs_qual( ax, ys, rotation=rotation )
        
        # Set scale
        ax.set_yscale( 'log' )
        
        ax.tick_params( left=False, labelleft=False, which='minor' )
        
        if y_axis == 'criteria values':
            # Draw relative line
            ax.axhline(
                1,
                linewidth = 1,
                color = 'k',
                zorder = 9,
            )

            # Set yticks to values
            ytick_labels = np.arange( 1, 11 )
            ytick_values = ytick_labels / critical_value
            ax.set_yticks( ytick_values )
            ax.set_yticklabels( ytick_labels )
            ax.set_ylim( ytick_values[0], ytick_values[-1], )

            # Note quality value
            quality = self[name].estimate_quality( critical_value=critical_value ) 
            ax.annotate(
                text = r'$q =$' + '{:.2g}'.format( quality ),
                xy = ( 1, 1 ),
                xycoords = 'axes fraction',
                xytext = ( 5, -5 ),
                textcoords = 'offset points',
                va = 'top',
                ha = 'left',
            )
        
        ax.set_ylabel( '{} buy-in'.format( y_axis[:-1] ) )

        return ys

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

def plot_quant_vs_qual( ax, ys, rotation=-45. ):

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

        if request_user_input:
            print( 'Evaluating market segments for [ {} ]...'.format( self.name ) )
            used_keys = set( self['market segments'].keys() ).union(
                set( self.market_segments.index )
            )
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

    def estimate_quality( self, critical_value=8. ):
        '''Estimate the quality of the deliverable assuming quality is:
        q_k = product( criteria_value / critical_value )

        Args:
            critical_value (float):
                The necessary value per criteria for which a criteria is
                acceptable.

        Returns:
            quality (float):
                Estimate for the quality.
        '''

        scaled = self['criteria values'] / critical_value
        quality = np.prod( scaled.array() )

        return quality

    ########################################################################

    def estimate_market_segment_buyin(
        self,
        ms_name,
        critical_value = 8.,
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

            critical_value (float):
                The necessary value per criteria for which a criteria is
                acceptable.
            
        Returns:
            market_segment_buyin (float):
                Estimate for the market segment buy-in.
        '''

        q_k = self.estimate_quality( critical_value=critical_value )
        b_i = self.market_segments.loc[ms_name]['Weight']
        try:
            f_ik = self['market segments'][ms_name]
        except KeyError:
            if use_default_for_missing_values:
                f_ik = self.market_segments.loc[ms_name]['Default Compatibility']
            else:
                raise KeyError( 'Missing market segment compatibility for category {}'.format( ms_name ) )

        return q_k * b_i * f_ik

    ########################################################################

    def estimate_market_buyin( self, m_name, critical_value=8. ):
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

            critical_value (float):
                The necessary value per criteria for which a criteria is
                acceptable.
            
        Returns:
            market_buyin (float):
                Estimate for the market buy-in.
        '''

        B_jk = 0.
        market_row = self.markets.loc[m_name]
        for ms_name in market_row.index:
            n_ij = market_row[ms_name]
            B_ik = self.estimate_market_segment_buyin( ms_name, critical_value=critical_value )
            B_jk += n_ij * B_ik

        F_jk = self['markets'][m_name]
        B_jk *= F_jk

        return B_jk

    ########################################################################

    def estimate_buyin( self, critical_value=8. ):
        '''Estimate the buy-in expected from sending the ship to all markets,
        from a specified market segment,
        B_k = sum( B_jk )
        where...
        j tracks market
        k tracks ship
        B_jk := market buyin

        Args:
            critical_value (float):
                The necessary value per criteria for which a criteria is
                acceptable.
            
        Returns:
            buyin (float):
                Estimate for the buy-in.
        '''

        B_k = 0.
        for m_name in self['markets'].keys():
            B_jk = self.estimate_market_buyin( m_name, critical_value=critical_value )
            B_k += B_jk

        return B_k

    ########################################################################

    def estimate_buyin_landscape( self, critical_value=8. ):
        '''Function for showing all user-controllable buy-in estimates.

        Args:
            critical_value (float):
                The necessary value per criteria for which a criteria is
                acceptable.
            
        Returns:
            landscape:
                Dict containing all buy-in estimates.
        '''

        landscape = {}
        landscape['quality'] = self.estimate_quality( critical_value=critical_value )
        landscape['buy-in'] = self.estimate_buyin( critical_value=critical_value )

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
                landscape[variable][v_name] = fn( v_name, critical_value = critical_value )

        return verdict.Dict( landscape )

    ########################################################################

    def estimate_buyin_change( self, variable, name=None, critical_value=8. ):
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

            critical_value (float):
                The necessary value per criteria for which a criteria is
                acceptable.
            
        Returns:
            dB/dX (float):
                Estimate for derivative of buy-in
        '''

        if variable in [ 'quality', 'q', 'q_k' ]:
            B_k = self.estimate_buyin( critical_value=critical_value )
            q_k = self.estimate_quality( critical_value=critical_value )
            return B_k / q_k
        
        elif variable in [ 'criteria values', 'c', 'c_m' ]:
            B_k = self.estimate_buyin( critical_value=critical_value )
            c_m = self['criteria values'][name]
            return B_k / c_m

        elif variable in [ 'markets', 'F', 'F_jk' ]:
            result = 0.
            market_row = self.markets.loc[name]
            for ms_name in market_row.index:
                n_ij = market_row.loc[ms_name]
                B_ik = self.estimate_market_segment_buyin(
                    ms_name,
                    critical_value = critical_value
                )
                result += n_ij * B_ik

            return result

        elif variable in [ 'market segments', 'f', 'f_ik' ]:
            B_ik = self.estimate_market_segment_buyin( name, critical_value=critical_value )
            f_ik = self['market segments'][name]
            sum_term = 0.
            for m_name, F_jk in self['markets'].items():
                sum_term += F_jk * self.markets.loc[m_name].loc[name]
            return B_ik / f_ik * sum_term

        else:
            raise KeyError( 'Unrecognized variable, {}'.format( variable ) )

    ########################################################################

    def estimate_buyin_change_landscape( self, critical_value=8. ):
        '''Function for showing all user-controllable derivatives of buyin.

        Args:
            critical_value (float):
                The necessary value per criteria for which a criteria is
                acceptable.
            
        Returns:
            landscape:
                Dict containing all instantaneous variable values.
        '''

        landscape = {}
        landscape['quality'] = self.estimate_buyin_change( 'q', critical_value=critical_value )

        # Variables with multiple options
        variables = [ 'criteria values', 'markets', 'market segments' ]
        for variable in variables:
            landscape[variable] = {}
            for v_name in self[variable].keys():
                landscape[variable][v_name] = self.estimate_buyin_change(
                    variable,
                    name = v_name,
                    critical_value = critical_value
                )

        return verdict.Dict( landscape )