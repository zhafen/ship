import numpy as np
import numpy.testing as npt
import os
import mock
import unittest

import matplotlib
import matplotlib.pyplot as plt

import verdict

import ship

# Patch this object throughout
default_criteria = [ 'functionality', 'understandability' ]
test_data = {
    'Chell': {
        'functionality': 10,
        'understandability': 5,
    },
    'Pip': {
        'functionality': 7,
        'understandability': 3,
    },
    'Crouton': {
        'functionality': 9,
        'understandaility': 6,
    },
    'Melville': {
        'functionality': 8,
        'understandability': 9,
    },
}

########################################################################

class TestConstruct( unittest.TestCase ):

    def test_init( self ):

        fleet = ship.Fleet()

    ########################################################################

    def test_construct_ship( self ):

        fleet = ship.Fleet( criteria=default_criteria )
        fleet.construct_ship(
            'The Ship',
            description = 'The default test ship.',
            category = 'code package',
        )

        assert sorted( fleet['The Ship'].criteria() ) == default_criteria
        assert fleet['The Ship'].data['attrs']['description'] == 'The default test ship.'
        assert fleet['The Ship'].data['attrs']['category'] == 'code package'

    ########################################################################

    def test_move_ship( self ):

        fleet1 = ship.Fleet( criteria=default_criteria )
        fleet1.construct_ship(
            'The Ship',
            description = 'The default test ship.',
            category = 'code package',
        )
        fleet2 = ship.Fleet( criteria=default_criteria )

        fleet2.move_ship( 'The Ship', fleet1 )

########################################################################

class TestIO( unittest.TestCase ):

    def setUp( self ):

        self.save_fp = './test.dock.json'
        self.hdf5_save_fp = './test.dock.hdf5'

        for fp in [ self.save_fp, self.hdf5_save_fp ]:
            if os.path.exists( fp ):
                os.remove( fp )

    ########################################################################

    def tearDown( self ):

        for fp in [ self.save_fp, self.hdf5_save_fp ]:
            if os.path.exists( fp ):
                os.remove( fp )

    ########################################################################

    def test_save( self ):

        # Parameters
        names = [ 'The Ship', 'Melvulu', 'Chellship', ]
        expected = {
            'functionality': 0.5,
            'understandability': 0.25
        }

        # Setup
        self.fleet = ship.Fleet( criteria=default_criteria )
        for name in names:
            self.fleet.construct_ship( name )
            self.fleet[name]['criteria values'] = expected

        # Save
        self.fleet.save( self.save_fp )

        # Check
        actual = verdict.Dict.from_json( self.save_fp )
        for name in names:
            for key, item in expected.items():
                npt.assert_allclose( actual[name]['criteria values'][key], item )

    ########################################################################

    def test_save_hdf5( self ):

        # Parameters
        names = [ 'The Ship', 'Melvulu', 'Chellship', ]
        expected = {
            'functionality': 0.5,
            'understandability': 0.25
        }
        expected_market = {
            'peers': 0.2,
            'friends': 0.9,
        }

        # Setup
        self.fleet = ship.Fleet( criteria=default_criteria )
        for name in names:
            self.fleet.construct_ship( name )
            self.fleet[name]['criteria values'] = expected
            self.fleet[name]['market segments'] = expected_market
            self.fleet[name]['markets'] = expected_market

        # Save
        self.fleet.save( self.hdf5_save_fp )

        # Check
        actual = verdict.Dict.from_hdf5( self.hdf5_save_fp )
        for name in names:
            for key, item in expected.items():
                npt.assert_allclose( actual[name]['criteria values'][key], item )

    ########################################################################

    def test_load( self ):

        # Paramters
        names = [ 'The Ship', 'Melvulu', 'Chellship', ]
        expected = {
            'functionality': 0.5,
            'understandability': 0.25
        }

        # Save
        expected_full = verdict.Dict({})
        for name in names:
            expected_full[name] = {
                'criteria values': expected,
            }
        expected_full.to_json( self.save_fp )

        # Load
        fleet = ship.load( self.save_fp )

        # Check
        for name in names:
            for key, item in expected.items():
                npt.assert_allclose( fleet[name]['criteria values'][key], item )

    ########################################################################

    def test_load_hdf5( self ):

        # Paramters
        names = [ 'The Ship', 'Melvulu', 'Chellship', ]
        expected = {
            'functionality': 0.5,
            'understandability': 0.25
        }

        # Save
        expected_full = verdict.Dict({})
        for name in names:
            expected_full[name] = {
                'criteria values': expected,
            }
        expected_full.to_hdf5( self.hdf5_save_fp )

        # Load
        fleet = ship.load( self.hdf5_save_fp )

        # Check
        for name in names:
            for key, item in expected.items():
                npt.assert_allclose( fleet[name]['criteria values'][key], item )

########################################################################

class TestEvaluate( unittest.TestCase ):

    def setUp( self ):

        self.fleet = ship.Fleet( criteria=default_criteria )
        self.fleet.construct_ship( 'The Ship' )
        self.ship = self.fleet['The Ship']

    ########################################################################

    def test_evaluate_ship( self ):

        output = self.ship.evaluate( understandability=0.5, functionality=0.25 )

        npt.assert_allclose( output, 0.5*0.25 )

    ########################################################################

    def test_evaluate_ship_input( self ):

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = [ 0.5, 0.25 ]

            output = self.ship.evaluate( True )

        npt.assert_allclose( output, 0.5*0.25 )

    ########################################################################

    def test_evaluate_ship_input_exit_code( self ):

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = [ 'q', 0.25 ]

            output = self.ship.evaluate( True )

        assert output == 'q'

    ########################################################################

    def test_evaluate_ship_d_deletes( self ):

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = [ 'd', 0.25 ]

            output = self.ship.evaluate( True )

        npt.assert_allclose( output, 0.25 )
        assert len( self.fleet['The Ship'].criteria() ) == 1

    ########################################################################

    def test_evaluate_fleet_input( self ):

        self.fleet.construct_ship( 'The Second Ship' )
        self.fleet.construct_ship( 'The Third Ship' )

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = [  0.5, 0.1, 0.2, 0.1, 0., 1., ]

            output = self.fleet.evaluate( 'all', True )

        expected = {
            'The Ship': 0.05,
            'The Second Ship': 0.02,
            'The Third Ship': 0.0,
        }
        for key, item in expected.items():
            npt.assert_allclose( item, output[key] )

    ########################################################################

    def test_evaluate_fleet_input_break( self ):

        self.fleet.construct_ship( 'The Second Ship' )
        self.fleet.construct_ship( 'The Third Ship' )

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = [  0.5, 0.1, 'q', 0.1 ]

            output = self.fleet.evaluate( 'all', True )

        assert output == 'q'

########################################################################

class TestEvaluateMarket( unittest.TestCase ):

    def setUp( self ):

        self.fleet = ship.Fleet( criteria=default_criteria )
        self.fleet.construct_ship( 'The Ship' )
        self.ship = self.fleet['The Ship']
        n_ma = len( self.ship.market_segments.index )
        self.side_effect = np.random.uniform( 0, 1, n_ma )

    ########################################################################

    def test_evaluate_ship( self ):

        output = self.ship.evaluate_market_segments( understandability=0.5, functionality=0.25 )

        npt.assert_allclose( np.prod( output.array() ), 0.5*0.25 )

    ########################################################################

    def test_evaluate_ship_input( self ):

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = self.side_effect

            output = self.ship.evaluate_market_segments( True )

        npt.assert_allclose( np.prod( output.array() ), np.prod( self.side_effect ) )

    ########################################################################

    def test_evaluate_ship_input_default( self ):

        with mock.patch( 'builtins.input' ) as mock_input:
            self.side_effect = list( self.side_effect )
            self.side_effect = [ '' for _ in self.side_effect ]
            mock_input.side_effect = self.side_effect

            output = self.ship.evaluate_market_segments( True )

        def_comp = self.ship.market_segments['Default Compatibility']
        for key in def_comp.index:
            npt.assert_allclose(
                def_comp.loc[key],
                output[key]
            )

    ########################################################################

    def test_evaluate_ship_input_exit_code( self ):

        with mock.patch( 'builtins.input' ) as mock_input:
            self.side_effect = list( self.side_effect )
            self.side_effect[0] = 'q'
            mock_input.side_effect = self.side_effect

            output = self.ship.evaluate_market_segments( True )

        assert output == 'q'

    ########################################################################

    def test_evaluate_fleet_input( self ):

        self.fleet.construct_ship( 'The Second Ship' )
        self.fleet.construct_ship( 'The Third Ship' )

        side_effect = np.random.uniform( 0, 1, self.side_effect.size * 3 )
        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = side_effect

            output = self.fleet.evaluate_market_segments( 'all', True )

        expected = np.prod( side_effect )
        actual = 1.
        for key, item in output.items():
            actual *= np.prod( item.array() )
        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_evaluate_fleet_input_break( self ):

        self.fleet.construct_ship( 'The Second Ship' )
        self.fleet.construct_ship( 'The Third Ship' )

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = [  0.5, 0.1, 'q', 0.1 ]

            output = self.fleet.evaluate_market_segments( 'all', True )

        assert output == 'q'

########################################################################

class TestSendShipToMarket( unittest.TestCase ):

    def setUp( self ):

        self.fleet = ship.Fleet( criteria=default_criteria )
        self.fleet.construct_ship( 'The Ship' )
        self.ship = self.fleet['The Ship']
        n_m = len( self.fleet.markets.index )
        self.side_effect = np.random.uniform( 0, 1, n_m )
        for i, market_name in enumerate( self.fleet.markets.index ):
            self.ship['markets'][market_name] = self.side_effect[i]

    ########################################################################

    def test_evaluate_ship( self ):

        output = self.ship.send_to_market( arXiv=0.5, cats=0.25 )

        npt.assert_allclose( output['arXiv'], 0.5 )
        npt.assert_allclose( output['cats'], 0.25 )
        
    ########################################################################

    def test_evaluate_ship_input( self ):
        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = self.side_effect

            output = self.ship.send_to_market( True )

        npt.assert_allclose( np.prod( output.array() ), np.prod( self.side_effect ) )

    ########################################################################

    def test_evaluate_ship_input_exit_code( self ):

        with mock.patch( 'builtins.input' ) as mock_input:
            self.side_effect = list( self.side_effect )
            self.side_effect[0] = 'q'
            mock_input.side_effect = self.side_effect

            output = self.ship.send_to_market( True )

        assert output == 'q'


########################################################################

class TestEstimateImpact( unittest.TestCase ):

    def setUp( self ):

        # Construct
        self.fleet = ship.Fleet( criteria=default_criteria )
        for name in test_data.keys():
            self.fleet.construct_ship( name )
            ship_i = self.fleet[name]
            ship_i.evaluate( **test_data[name] )
            
            # Use default values for market segment compatibility
            f_i = {}
            for ms_name in ship_i.market_segments.index:
                f_i[ms_name] = ship_i.market_segments.loc[ms_name]['Default Compatibility']
            ship_i.evaluate_market_segments( **f_i )

            # Use a constant value for market compatibility
            F_j = {}
            for m_name in self.fleet.markets.index:
                F_j[m_name] = 0.6
            self.fleet[name].send_to_market( **F_j )

            # Make all markets the same for ease of testing
            for m_name in ship_i.markets.index:
                ship_i.markets.loc[m_name] = ship_i.markets.loc[ship_i.markets.index[0]]

        self.ship = self.fleet['Chell']
        self.m = self.fleet.markets
        self.m_name = self.m.index[0]
        self.ms = self.ship.market_segments
        self.ms_name = self.ms.index[0]
        self.q_expected = ( 10. * 5. ) / 64.
        self.F_expected = F_j[m_name]
        self.N_j_expected = len( self.ship['markets'] )
        self.sum_expected = np.sum(
            self.ms['Weight'] * self.m.loc[self.m_name] * self.ms['Default Compatibility']
        )

    ########################################################################

    def test_estimate_quality( self ):

        actual = self.ship.estimate_quality()

        npt.assert_allclose( self.q_expected, actual )

    ########################################################################

    def test_estimate_market_segment_buyin( self ):

        actual = self.ship.estimate_market_segment_buyin( self.ms_name )

        ms_row = self.ms.loc[self.ms_name]
        expected = (
            self.q_expected * ms_row['Weight'] * ms_row['Default Compatibility']
        )

        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_estimate_market_segment_buyin_no_entry( self ):

        del self.ship['market segments'][self.ms_name]

        actual = self.ship.estimate_market_segment_buyin( self.ms_name )

        ms_row = self.ms.loc[self.ms_name]
        expected = (
            self.q_expected * ms_row['Weight'] * ms_row['Default Compatibility']
        )

        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_estimate_market_buyin( self ):

        actual = self.ship.estimate_market_buyin( self.m_name )

        expected = (
            self.q_expected * self.F_expected * self.sum_expected
        )

        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_estimate_buyin( self ):

        actual = self.ship.estimate_buyin()

        expected = (
            self.N_j_expected * self.q_expected * self.F_expected * self.sum_expected
        )

        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_estimate_buyin_landscape( self ):

        actual = self.ship.estimate_buyin_landscape()

        # Net values
        expected = self.q_expected
        npt.assert_allclose( expected, actual['quality'] )
        expected = (
            self.N_j_expected * self.q_expected * self.F_expected * self.sum_expected
        )
        npt.assert_allclose( expected, actual['buy-in'] )

        # Criteria values
        expected = self.ship['criteria values']['functionality']
        npt.assert_allclose( expected, actual['criteria values']['functionality'] )

        # Market segment
        ms_row = self.ms.loc[self.ms_name]
        expected = (
            self.q_expected * ms_row['Weight'] * ms_row['Default Compatibility']
        )
        npt.assert_allclose( expected, actual['market segments'][self.ms_name] )

        # Market
        expected = (
            self.q_expected * self.F_expected * self.sum_expected
        )
        npt.assert_allclose( expected, actual['markets'][self.m_name] )

    ########################################################################

    def test_estimate_dBdq( self ):

        actual = self.ship.estimate_buyin_change( variable='quality' )

        expected = (
            self.N_j_expected * self.F_expected * self.sum_expected
        )

        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_estimate_dBdc( self ):

        actual = self.ship.estimate_buyin_change(
            variable = 'criteria values',
            name = 'functionality',
        )

        dBdq = (
            self.N_j_expected * self.F_expected * self.sum_expected
        )
        expected = dBdq * self.q_expected / self.ship['criteria values']['functionality']

        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_estimate_dBdF( self ):

        actual = self.ship.estimate_buyin_change(
            variable = 'markets',
            name = self.m_name,
        )

        expected = (
            self.q_expected * self.sum_expected
        )

        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_estimate_dBdF_no_entry( self ):

        del self.ship['markets'][self.m_name]

        actual = self.ship.estimate_buyin_change(
            variable = 'markets',
            name = self.m_name,
        )

        expected = (
            self.q_expected * self.sum_expected
        )

        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_estimate_dBdf( self ):

        actual = self.ship.estimate_buyin_change(
            variable = 'market segments',
            name = self.ms_name,
        )

        ms_row = self.ms.loc[self.ms_name]
        expected = (
            self.F_expected * self.N_j_expected *
            self.q_expected * ms_row['Weight'] * self.m[self.ms_name].loc[self.m_name]
        )

        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_estimate_dBdf_no_entry( self ):

        del self.ship.data['market segments'][self.ms_name]

        actual = self.ship.estimate_buyin_change(
            variable = 'market segments',
            name = self.ms_name,
        )

        ms_row = self.ms.loc[self.ms_name]
        expected = (
            self.F_expected * self.N_j_expected *
            self.q_expected * ms_row['Weight'] * self.m[self.ms_name].loc[self.m_name]
        )

        npt.assert_allclose( expected, actual )


    ########################################################################

    def test_estimate_dB_landscape( self ):

        actual = self.ship.estimate_buyin_change_landscape()

        # dB/dq
        expected = (
            self.N_j_expected * self.F_expected * self.sum_expected
        )
        npt.assert_allclose( expected, actual['quality'] )

        # dB/dc
        dBdq = (
            self.N_j_expected * self.F_expected * self.sum_expected
        )
        expected = dBdq * self.q_expected / self.ship['criteria values']['functionality']
        npt.assert_allclose( expected, actual['criteria values']['functionality'] )

        # dB/dF
        expected = (
            self.q_expected * self.sum_expected
        )
        npt.assert_allclose( expected, actual['markets'][self.m_name] )

        # dB/df
        ms_row = self.ms.loc[self.ms_name]
        expected = (
            self.F_expected * self.N_j_expected *
            self.q_expected * ms_row['Weight'] * self.m[self.ms_name].loc[self.m_name]
        )
        npt.assert_allclose( expected, actual['market segments'][self.ms_name] )

########################################################################

class TestPlot( unittest.TestCase ):

    def setUp( self ):

        # Construct
        self.fleet = ship.Fleet( criteria=default_criteria )
        for name in test_data.keys():
            self.fleet.construct_ship( name )
            ship_i = self.fleet[name]
            ship_i.evaluate( **test_data[name] )
            
            # Use default values for market segment compatibility
            f_i = {}
            for ms_name in ship_i.market_segments.index:
                f_i[ms_name] = ship_i.market_segments.loc[ms_name]['Default Compatibility']
            ship_i.evaluate_market_segments( **f_i )

            # Use a constant value for market compatibility
            F_j = {}
            for m_name in self.fleet.markets.index:
                F_j[m_name] = 0.6
            self.fleet[name].send_to_market( **F_j )

            # Make all markets the same for ease of testing
            for m_name in ship_i.markets.index:
                ship_i.markets.loc[m_name] = ship_i.markets.loc[ship_i.markets.index[0]]

        self.ship = self.fleet['Chell']
        self.m = self.fleet.markets
        self.m_name = self.m.index[0]
        self.ms = self.ship.market_segments
        self.ms_name = self.ms.index[0]
        self.q_expected = ( 10. * 5. ) / 64.
        self.F_expected = F_j[m_name]
        self.N_j_expected = len( self.ship['markets'] )
        self.sum_expected = np.sum(
            self.ms['Weight'] * self.m.loc[self.m_name] * self.ms['Default Compatibility']
        )

    ########################################################################

    def test_plot_fleet( self ):
        '''Just make sure it doesn't crash.'''

        for y_axis in [ 'quality', 'buy-in', 'max buy-in change' ]:
            self.fleet.plot_fleet( y_axis=y_axis, )
            plt.close()

        v_names = {
            'criteria values': 'functionality',
            'markets': self.m_name,
            'market segments': self.ms_name,
        }
        for variable in [ 'criteria values', 'markets', 'market segments' ]:
            self.fleet.plot_fleet( y_axis='buy-in change', variable=variable, name=v_names[variable] )
            plt.close()
     
    ########################################################################

    def test_plot_ship( self ):
        '''Just make sure it doesn't crash.'''

        for y_axis in [ 'buy-in', 'buy-in change', ]:
            for variable in [ 'criteria values', 'markets', 'market segments' ]:
                self.fleet.plot_ship( self.ship.name, y_axis=y_axis, variable=variable )
                plt.close()
     