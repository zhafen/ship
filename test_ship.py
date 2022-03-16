import numpy as np
import numpy.testing as npt
import os
import mock
import unittest

import verdict

import ship

# Patch this object throughout
default_criteria = [ 'functionality', 'understandability' ]

########################################################################

class TestConstruct( unittest.TestCase ):

    def test_init( self ):

        docks = ship.Docks()

    ########################################################################

    def test_construct_ship( self ):

        docks = ship.Docks( criteria=default_criteria )
        docks.construct_ship( 'The Ship', )

        assert sorted( docks['The Ship'].criteria() ) == default_criteria

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

        npt.assert_allclose( output, 0. )

