import numpy as np
import numpy.testing as npt
import unittest

import ship

# Patch this object throughout
default_criteria = [ 'understandability', 'functionality', ]

########################################################################

class TestConstruct( unittest.TestCase ):

    def test_init( self ):

        docks = ship.Docks()

    ########################################################################

    def test_construct_ship( self ):

        docks = ship.Docks( criteria=default_criteria )
        docks.construct_ship( 'The Ship', )

        assert docks['The Ship']['criteria'] == default_criteria

    ########################################################################

class TestEvaluate( unittest.TestCase ):

    def setUp( self ):

        self.docks = ship.Docks()
        self.docks.construct_ship( 'The Ship', [ 'pointiness', 'strangeness' ] )

    ########################################################################

    def test_evaluate_ship( self ):

        output = self.docks.evaluate( 'The Ship', pointiness=0.5, strangeness=0.25)

        npt.assert_allclose( output, 0.5*0.25 )