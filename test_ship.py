import numpy as np
import numpy.testing as npt
import mock
import unittest

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