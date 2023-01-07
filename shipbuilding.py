import numpy as np
import pandas as pd
import unyt

import matplotlib
import matplotlib.pyplot as plt

import verdict

########################################################################
########################################################################

BEDTIME = 21. * unyt.hr

REFERENCE_TIMES = {
    'sunrise': 6. * unyt.hr,
    'early morning': 7. * unyt.hr,
    'morning': 9. * unyt.hr,
    'midday': 12. * unyt.hr,
    'afternoon': 16. * unyt.hr,
    'evening': 20. * unyt.hr,
}

TIME_VARIABLES = [
    't',
    'tau',
    'T',
    'L'
]

########################################################################
########################################################################

class Schedule( object ):
    '''Schedule for a single activity.
    '''
    
    def __init__(
        self,
        p,
        domain = None,
        color = 'k',
        time_units = 'hr',
    ):
        '''
        Args:
            p (dict of values):
                Parameters governing the schedule.
                If values are unyt quantities, those units are used.
                Otherwise values are assumed to be in time_units

            domain (dict of arrays):
                Viable range for parameters.

            color (matplotlib-recognized color object):
                Color to use for plotting.
        '''
        
        self.p = verdict.Dict( p )
        self.domain = domain
        self.color = color
        self.time_units = time_units

        self.p['t_0'] = REFERENCE_TIMES[p['t_0_key']]

        # Add time units
        for key in TIME_VARIABLES:
            if not hasattr( self.p[key], 'units' ):
                self.p[key] *= unyt.unyt_quantity( 1, time_units )
        
        # Calculate some key quantities
        self.duty_cycle = self.p['t'] + self.p['tau']
        self.n_sessions_per_day = self.p['T'] / self.p['t']
        self.full_duration_per_day = self.n_sessions_per_day * self.duty_cycle
        self.time_until_sleep = BEDTIME - self.p['t_0']
        self.time_per_week = self.p['T'] * self.p['d']
        self.t_default = ( np.arange( 0., 24. + 1./12., 1./12. ) - 0.001 / 12. ) * unyt.hr
        self.session_start_times = np.arange( self.n_sessions_per_day ) * self.duty_cycle + self.p['t_0']
        self.session_end_times = self.session_start_times + self.p['t']

    ########################################################################

    def saveable_parameters( self ):

        saveable_params = {}
        for key, param in self.p.items():
            if isinstance( param, unyt.unyt_quantity ):
                saveable_params[key] = float( param.to( self.time_units ).value )
            else:
                saveable_params[key] = param

        return saveable_params

    ########################################################################
        
    def __repr__( self ):
        
        display_str = '{}\n    {:.2g} sessions, {} per session, {:.0f} between\n    {:.0f}/day, {:.0f}/week, {:.0f}-day week, {} start'.format(
            self.p['activity'],
            self.n_sessions_per_day.value,
            self.p['t'],
            self.p['tau'],
            self.p['T'],
            self.p['L'],
            self.p['d'],
            self.p['t_0_key'],
        )
        
        return display_str

    ########################################################################
        
    def prune( self ):
        
        invalids = []
        
        # Identify parameters outside the domain
        if self.domain is not None:
            for p_key, ( p_min, p_max ) in self.domain.items():
                invalid_str = '{} outside domain ({}, {})'.format( p_key, p_min, p_max )
                if self.p[p_key] < p_min:
                    invalids.append( invalid_str )
                    continue
                if self.p[p_key] > p_max:
                    invalids.append( invalid_str )
    
        # Cut out activities that cannot be accomplished with the alotted time
        if self.full_duration_per_day > self.time_until_sleep:
            invalids.append( 'full_duration_per_day > time_until_sleep' )

        # Cut out activities that don't fit the time cap
        if self.time_per_week < self.p['L']:
            invalids.append( 'time_per_week < L' )
        if self.time_per_week - self.p['T'] >= self.p['L']:
            invalids.append( 'time_per_week - T >= L' )
                
        return invalids

    ########################################################################
    
    def priority_at_t( self, t ):
        
        # If in a session, return the priority
        for i, session_start_time in enumerate( self.session_start_times ):
            if t < session_start_time:
                continue
            if t > self.session_end_times[i]:
                continue      
            return self.p['P']
        
        # Otherwise return 0
        return 0.

    ########################################################################

    def priority( self, t=None ):
        
        if t is None:
            t = self.t_default
        
        if pd.api.types.is_list_like( t ):
            return np.array([ self.priority_at_t( _ ) for _ in t ])
        else:
            return self.priority_at_t( t )

    ########################################################################
        
    def plot_priority( self, t=None, ax=None ):
        
        if t is None:
            t = self.t_default
        
        if ax is None:
            fig = plt.figure( figsize=(9,3) )
            ax = plt.gca()
            
        priority = self.priority( t )
            
        ax.fill_between(
            t.value,
            priority,
            color = self.color,
            step = 'pre',
            linewidth = 0,
        )
    
        y_max = self.p['P'] * 1.05
    
        ax.set_xlim( 0, 24 )
        ax.set_ylim( 0, y_max )
        
        ax.set_ylabel( 'priority' )
        
        # Ticks
        xticks = np.arange( 0, 24.1, 3 )
        xtick_labels = [ '12 AM', '3 AM', '6 AM', '9 AM', '12 PM', '3 PM', '6 PM', '9 PM', '12 AM' ]
        ax.set_xticks( xticks )
        ax.set_xticklabels( xtick_labels )
        ax.set_yticks( np.arange( 0, y_max, 1 ) )
        
        # Spines
        ax.spines[['right', 'top']].set_visible(False)
        
        return plt.gcf()
