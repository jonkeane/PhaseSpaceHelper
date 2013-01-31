#!/usr/bin/python
# a python script for testing the calibration of a phase space system.

import PhaseSpaceHelper

wand = calibObject(objFile = 'wand.rb')

owlServer = OWLConnection()

##check = checkObject(calibObject = wand)
##check.acquireData(owlServer)
##framesByMarkerer = check.summaryStats()

##tc = OWLTimecode()
##
##time.sleep(1)
##
##tc.jamToOWL(owlServer)
##
##time.sleep(1)
##
##tc.checkOWL(owlServer)
