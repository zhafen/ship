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
        assert docks['The Ship'].data['attrs']['description'] == 'The default test ship.'
        assert docks['The Ship'].data['attrs']['category'] == 'code package'

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
        self.docks = ship.Docks( criteria=default_criteria )
        for name in names:
            self.docks.construct_ship( name )
            self.docks[name]['status'] = expected

        # Save
        self.docks.save( self.save_fp )

        # Check
        actual = verdict.Dict.from_json( self.save_fp )
        for name in names:
            for key, item in expected.items():
                npt.assert_allclose( actual[name]['status'][key], item )

    ########################################################################

    def test_save_hdf5( self ):

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
        self.docks.save( self.hdf5_save_fp )

        # Check
        actual = verdict.Dict.from_hdf5( self.hdf5_save_fp )
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
        expected_full.to_json( self.save_fp )

        # Load
        docks = ship.load( self.save_fp )

        # Check
        for name in names:
            for key, item in expected.items():
                npt.assert_allclose( docks[name]['status'][key], item )

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
                'status': expected,
            }
        expected_full.to_hdf5( self.hdf5_save_fp )

        # Load
        docks = ship.load( self.hdf5_save_fp )

        # Check
        for name in names:
            for key, item in expected.items():
                npt.assert_allclose( docks[name]['status'][key], item )

########################################################################

class TestEvaluate( unittest.TestCase ):

    def setUp( self ):

        self.docks = ship.Docks( criteria=default_criteria )
        self.docks.construct_ship( 'The Ship' )
        self.ship = self.docks['The Ship']

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

class TestEstimateAudience( unittest.TestCase ):

    def setUp( self ):

        self.docks = ship.Docks( criteria=default_criteria )
        self.docks.construct_ship( 'The Ship' )
        self.ship = self.docks['The Ship']

        self.audience_args = dict(
            tags = [
                'subfield experts',
                'field experts',
                'astrophysicists',
                'coworkers',
            ],
            n = [
                2,
                4,
                3,
                10,
            ],
            suitability = [
                1,
                0.5,
                0.1,
                0.1,
            ]
        )

        self.default_side_effect = []
        for i, key in enumerate( self.ship.config['audiences']['count'] ):
            if i == 0:
                self.default_side_effect += [ '', '' ]
            else:
                self.default_side_effect += [ np.random.randint( 1000 ), np.random.uniform( 0, 1 ) ]

    ########################################################################

    def test_evaluate_audience( self ):

        self.ship.evaluate_audience( **self.audience_args )

        actual = self.ship['audience']

        assert actual['tags'] == self.audience_args['tags']
        npt.assert_allclose( actual['n'], self.audience_args['n'] )
        npt.assert_allclose( actual['suitability'], self.audience_args['suitability'] )

    ########################################################################

    # def test_evaluate_audience_input( self ):

    #     with mock.patch( 'builtins.input' ) as mock_input:
    #         mock_input.side_effect = self.default_side_effect

    #         output = self.ship.evaluate_audience( True )

    #     expected = {
    #         'n': 
    #     }

    # ########################################################################

    # def test_evaluate_ship_input_exit_code( self ):

    #     with mock.patch( 'builtins.input' ) as mock_input:
    #         mock_input.side_effect = [ 'q', 0.25 ]

    #         output = self.ship.evaluate( True )

    #     assert output == 'q'

    # ########################################################################

    # def test_evaluate_ship_d_deletes( self ):

    #     with mock.patch( 'builtins.input' ) as mock_input:
    #         mock_input.side_effect = [ 'd', 0.25 ]

    #         output = self.ship.evaluate( True )

    #     npt.assert_allclose( output, 0.25 )
    #     assert len( self.docks['The Ship'].criteria() ) == 1

    # ########################################################################

    # def test_evaluate_docks_input( self ):

    #     self.docks.construct_ship( 'The Second Ship' )
    #     self.docks.construct_ship( 'The Third Ship' )

    #     with mock.patch( 'builtins.input' ) as mock_input:
    #         mock_input.side_effect = [  0.5, 0.1, 0.2, 0.1, 0., 1., ]

    #         output = self.docks.evaluate( 'all', True )

    #     expected = {
    #         'The Ship': 0.05,
    #         'The Second Ship': 0.02,
    #         'The Third Ship': 0.0,
    #     }
    #     for key, item in expected.items():
    #         npt.assert_allclose( item, output[key] )

    # ########################################################################

    # def test_evaluate_docks_input_break( self ):

    #     self.docks.construct_ship( 'The Second Ship' )
    #     self.docks.construct_ship( 'The Third Ship' )

    #     with mock.patch( 'builtins.input' ) as mock_input:
    #         mock_input.side_effect = [  0.5, 0.1, 'q', 0.1 ]

    #         output = self.docks.evaluate( 'all', True )

    #     assert output == 'q'

########################################################################

class TestEstimateImpact( unittest.TestCase ):

    def setUp( self ):
        self.docks = ship.Docks( criteria=default_criteria )
        for name in test_data.keys():
            self.docks.construct_ship( name )
            self.docks[name].evaluate( **test_data[name] )

        self.ship = self.docks['Chell']
        self.audience_args = dict(
            tags = [
                'subfield experts',
                'field experts',
                'astrophysicists',
                'coworkers',
            ],
            n = [
                2,
                4,
                3,
                10,
            ],
            suitability = [
                1,
                0.5,
                0.1,
                0.1,
            ]
        )

        self.expected_weights = [ 30, 10, 3, 10 ]

    ########################################################################

    def test_estimate_reception( self ):

        expected = ( 10. * 5. ) / 64.
        actual = self.ship.estimate_reception()

        npt.assert_allclose( expected, actual )

    ########################################################################

    def test_estimate_impact( self ):

        # Setup expected
        expected_r = ( 10. * 5. ) / 64.
        n = np.array( self.audience_args['n'] )
        s = np.array( self.audience_args['suitability'] )
        w = np.array( self.expected_weights )
        expected_audience = np.sum( n * w * s )
        expected = expected_r * expected_audience

        # Setup
        self.ship.evaluate_audience( **self.audience_args )

        # Calculate
        actual = self.ship.estimate_impact()

        npt.assert_allclose( expected, actual )


