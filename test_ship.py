import numpy as np
import numpy.testing as npt
import os
import mock
import unittest

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

        docks = ship.Docks()

    ########################################################################

    def test_construct_ship( self ):

        docks = ship.Docks( criteria=default_criteria )
        docks.construct_ship(
            'The Ship',
            description = 'The default test ship.',
            category = 'code package',
        )

        assert sorted( docks['The Ship'].criteria() ) == default_criteria
        assert docks['The Ship'].description == 'The default test ship.'
        assert docks['The Ship'].category == 'code package'

########################################################################

class TestIO( unittest.TestCase ):

    def setUp( self ):

        self.save_fp = './test.dock.h5'

        if os.path.exists( self.save_fp ):
            os.remove( self.save_fp )

    ########################################################################

    def tearDown( self ):

        if os.path.exists( self.save_fp ):
            os.remove( self.save_fp )

    ########################################################################

    def test_save( self ):

        # Parameters
        names = [ 'The Ship', 'Melvulu', 'Chellship', ]
        expected = {
            'functionality': 0.5,
            'understandability': 0.25
        }

        # Setup
        self.docks = ship.Docks( criteria=default_criteria )
        for name in names:
            self.docks.construct_ship( name )
            self.docks[name]['status'] = expected

        # Save
        self.docks.save( self.save_fp )

        # Check
        actual = verdict.Dict.from_hdf5( self.save_fp )
        for name in names:
            for key, item in expected.items():
                npt.assert_allclose( actual[name]['status'][key], item )

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
                'status': expected,
            }
        expected_full.to_hdf5( self.save_fp )

        # Load
        docks = ship.load( self.save_fp )

        # Check
        for name in names:
            for key, item in expected.items():
                npt.assert_allclose( docks[name]['status'][key], item )

########################################################################

class TestEvaluate( unittest.TestCase ):

    def setUp( self ):

        self.docks = ship.Docks( criteria=default_criteria )
        self.docks.construct_ship( 'The Ship' )

    ########################################################################

    def test_evaluate_ship( self ):

        output = self.docks.evaluate_ship( 'The Ship', understandability=0.5, functionality=0.25 )

        npt.assert_allclose( output, 0.5*0.25 )

    ########################################################################

    def test_evaluate_ship_input( self ):

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = [ 0.5, 0.25 ]

            output = self.docks.evaluate_ship( 'The Ship', True )

        npt.assert_allclose( output, 0.5*0.25 )

    ########################################################################

    def test_evaluate_ship_input_exit_code( self ):

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = [ 'q', 0.25 ]

            output = self.docks.evaluate_ship( 'The Ship', True )

        assert output == 'q'

    ########################################################################

    def test_evaluate_ship_d_deletes( self ):

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = [ 'd', 0.25 ]

            output = self.docks.evaluate_ship( 'The Ship', True )

        npt.assert_allclose( output, 0.25 )
        assert len( self.docks['The Ship'].criteria() ) == 1

    ########################################################################

    def test_evaluate_docks_input( self ):

        self.docks.construct_ship( 'The Second Ship' )
        self.docks.construct_ship( 'The Third Ship' )

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = [  0.5, 0.1, 0.2, 0.1, 0., 1., ]

            output = self.docks.evaluate( 'all', True )

        expected = {
            'The Ship': 0.05,
            'The Second Ship': 0.02,
            'The Third Ship': 0.0,
        }
        for key, item in expected.items():
            npt.assert_allclose( item, output[key] )

    ########################################################################

    def test_evaluate_docks_input_break( self ):

        self.docks.construct_ship( 'The Second Ship' )
        self.docks.construct_ship( 'The Third Ship' )

        with mock.patch( 'builtins.input' ) as mock_input:
            mock_input.side_effect = [  0.5, 0.1, 'q', 0.1 ]

            output = self.docks.evaluate( 'all', True )

        assert output == 'q'

########################################################################

class TestEstimateImpact( unittest.TestCase ):

    def setUp( self ):
        self.docks = ship.Docks( criteria=default_criteria )
        for name in test_data.keys():
            self.docks.construct_ship( name )
            self.docks.evaluate_ship( name, **test_data[name] )

        self.ship = self.docks['Chell']
        self.audience_args = dict(
            tags = [
                'T&Z',
                'friends',
                'family',
                'coworkers',
            ],
            n = [
                2,
                4,
                3,
                10,
            ],
            # This weighting is based on time
            w = [
                24.,
                1. / 7.,
                0.25 / 7.,
                0.25 / 30.,
            ],
        )

    ########################################################################

    def test_estimate_reception( self ):

        expected = ( 10. * 5. ) / 64.
        actual = self.ship.estimate_reception()

        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_estimate_audience( self ):

        self.ship.estimate_audience( **self.audience_args )

        actual = self.ship['audience']

        assert actual['tags'] == self.audience_args['tags']
        npt.assert_allclose( actual['n'], self.audience_args['n'] )
        npt.assert_allclose( actual['w'], self.audience_args['w'] )

    ########################################################################

    def test_estimate_impact( self ):

        # Setup expected
        expected_r = ( 10. * 5. ) / 64.
        n = np.array( self.audience_args['n'] )
        w = np.array( self.audience_args['w'] )
        expected_audience = np.sum( n * w )
        expected = expected_r * expected_audience

        # Setup
        self.ship.estimate_audience( **self.audience_args )

        # Calculate
        actual = self.ship.estimate_impact()

        npt.assert_allclose( expected, actual )


