#!/usr/bin/python
# a python script for testing the calibration of a phase space system.

import sys, re, numpy, time
try:
    from scipy.stats import scoreatpercentile
    from scipy.stats import nanmedian
except:
    print("Can't import scipy. Stats will not work.")
from pytimecode import * # this avoids pytimecode.pytimecode.PyTimeCode craziness
try:
    from OWL import *
except:
    print("Can't import OWL. There is no functionality for connecting to the Server.")
import csv


def fivenum(v):
    """Returns Tukey's five number summary (minimum, lower-hinge, median, upper-hinge, maximum) for the input vector, a list or array of numbers based on 1.5 times the interquartile distance"""
    try:
        numpy.sum(v)
    except TypeError:
        print('Error: you must provide a list or array of only numbers')
    q1 = scoreatpercentile(v,25)
    q3 = scoreatpercentile(v,75)
    iqd = q3-q1
    md = nanmedian(v)
    whisker = 1.5*iqd
    return numpy.nanmin(v), md-whisker, md, md+whisker, numpy.nanmax(v),


def owl_print_error(s, n):
    """Print OWL error."""
    if(n < 0): print("%s: %d" % (s, n))
    elif(n == OWL_NO_ERROR): print("%s: No Error" % s)
    elif(n == OWL_INVALID_VALUE): print("%s: Invalid Value" % s)
    elif(n == OWL_INVALID_ENUM): print("%s: Invalid Enum" % s)
    elif(n == OWL_INVALID_OPERATION): print("%s: Invalid Operation" % s)
    else: print("%s: 0x%x" % (s, n))

def euclidDist(a, b):
    """find the euclidian distance between two points a and b"""
    dist = numpy.linalg.norm(numpy.array(a)-numpy.array(b))
    return dist

class calibObject:
    """
    Sets up an object that should be used for calibration. 
    It reads in an objFile with specifies the location and 
    identity of each marker with the form:
    id, x y z

    Lines beginning with # are ignored. 
    The origin for the object can be arbitrary.
    """
    def __init__(self, objFile, markers = None):
        self.markers = self.readCalibOjectFile(objFile)
        self.objFile = objFile
        
    def readCalibOjectFile(self, objFile):
        # read in the object file
        f = open(objFile, 'r')
        obj = f.readlines()

        # setup a marker dictionary
        markers = {}
        for line in obj:
            # ignore commented lines, there must be a better way to do this.
            if line[0] != "#":
                # split the line into ids and coordinates
                idCoords = line.strip().split(",")
                id = int(idCoords[0])
                coords = idCoords[1]

                # split the coordinates into three groups, deleting whitespace
                coords = re.search('\s*(\S*)\s*(\S*)\s*(\S*)\s*', coords)

                # turn string coordinates into integers
                (x, y, z) = map(int, coords.groups())

                # add to markers dictionary
                markers[id] = (x, y, z)
        return markers

class OWLTimecode:
    def __init__(self, timecode='00:00:00:00', frameRate = '29.97', dropFrame = False):
        self.startTimecode = pytimecode.PyTimeCode(frameRate, timecode, drop_frame=dropFrame)
        self.startTime = time.time()

    def now(self):
        timecode = self.startTimecode + pytimecode.PyTimeCode('29.97', start_seconds=(time.time()-self.startTime))
        return timecode

    def grabOWL(self, tc_acc):
        # start with an empty list of timecodes
        timecodes = []
        n = 0
        # iterated through at least 100 grabs. (this would be infinite?
        while n < 100:
            # grab the timecode from the timecode accumulator (CommDataAccumulator() from the phasespace API)
            tc = tc_acc.ParseTimecode(owlGetString(OWL_COMMDATA))
            if tc != None:
                # append the timecode to the timecodes list
                timecodes.append(tc[4])
                # if the list is longer than 2, then check to see if this timecode is exactly one frame after the previous one (but is not 00:00:00:00 which sometimes gets put out, additionally some junk timecodes are sometimes spit out that are a truncation of the frame single digit.)
                if len(timecodes) > 1:
##                    if timecodes[-1][0:11] != "00:00:00:00"  and timecodes[-1][0:11] != timecodes[-2][0:11]: # checks if tc is not all 0s, and -1 is not the same as -2
##                    if timecodes[-1][0:11] != "00:00:00:00" and pytimecode.PyTimeCode('29.97', timecodes[-1][0:11]) - pytimecode.PyTimeCode('29.97', timecodes[-2][0:11]) == pytimecode.PyTimeCode('29.97', "00:00:00:01"): # does not work because time codes cannot be compared. Must turn to strings first.
                    if timecodes[-1][0:11] != "00:00:00:00" and str(pytimecode.PyTimeCode('29.97', timecodes[-1][0:11]) - pytimecode.PyTimeCode('29.97', timecodes[-2][0:11])) == "00:00:00:01":
                        # stop the while loop
                        break
            else:
                # if there is no time code print an error, and wait for one phasespace frame (there should be a more principled wait time, if no wait time there's a race.)
                print("No timecode yet!")
                time.sleep(1/480.)
            n += 1
        # store and return the last timecode on the list.
        try:
            timecode = timecodes[-1][0:11]
        except IndexError:
            # if no timecodes have been accumulated, start at 00:00:00:00, this is probably a bad idea because no error will be thrown.
            timecode = "00:00:00:00"
            print("No timecode found.")
        return timecode
    
    def jamToOWL(self, OWLConn):
        """ jams the local timecode to the owlserver."""
        # connect to the owlserver
        OWLConn.connect()

        # make an accumulator for the incoming comm data, and grab the most recent timecode
        tc_acc = CommDataAccumulator()
        timecode = self.grabOWL(tc_acc)

        # Reset timecode and startTime should happen immediately after the return of the timecode. (This is very time sensitive!) 
        self.startTimecode = pytimecode.PyTimeCode('29.97', timecode, drop_frame = False)
        self.startTime = time.time()

        # disconnect from the server
        OWLConn.disconnect()

    def checkOWL(self, OWLConn):
        """checks the local timecode with owl. Returns a tuple (owlserver timecode, local timecode)"""
        OWLConn.connect()

        # make an accumulator for the incoming comm data, and grab the most recent timecode
        tc_acc = CommDataAccumulator()
        timecode = self.grabOWL(tc_acc)

        # save the grabbed timecode (and local) which should happen immediately after the return of the timecode. (This is very time sensitive!) 
        newOWLTimecode = pytimecode.PyTimeCode('29.97', timecode, drop_frame = False)
        localTimecodeNow = self.now()

        # disconnect from the server
        OWLConn.disconnect()        

        return newOWLTimecode, localTimecodeNow

class checkObject:
    """
    """
    def __init__(self, calibObject):
        self.markersToCheck = calibObject.markers.keys()
        self.testData = []
        self.calibObject = calibObject

    def acquireData(self, OWLConn):
        OWLConn.connect()

        self.testData = []
        ## for i in self.markersToCheck:
        ##     self.testData[i] = []
        
        # main loop
        while len(self.testData) < 100 :
            # get some markers
            markers = owlGetMarkers()

            # check for error
            err = owlGetError()
            if(err != OWL_NO_ERROR):
                owl_print_error("error", err)
                break

            # no data yet
            if(markers == None): continue

            n = len(markers)

            if n > 0:
                frame = {}
                # currently this goes through the markers to check ids, and assigns the first to 0, etc. This is because there is no way(?) to recover the actual ids from the owl connection, maybe the ids should be done away with for good then?
                for i in range(len(self.markersToCheck)):
                    # markers[1].id might not work, try also just i, but then no check(?) There is no condition checking, which should be fixed.
                    frame[self.markersToCheck[i]] = (markers[i].x, markers[i].y, markers[i].z)
                self.testData.append(frame)
            else:
                print("No markers.")
                time.sleep(1/480.)
                pass
            
            # sleep until the next frame, this is not quite right, but will be close.
            time.sleep(1/480.)

        OWLConn.disconnect()

    def compare(self):
        """Compare testData to the calibObject"""
        # setup a frames list
        frames = []
        # for each frame in the testData, compute the set of distances given the self.distances() function.
        for frame in self.testData:
            frames.append(self.distances(frame))
            
        # generate reference distances, mabye this should be done elsewhere?
        refDists = self.distances(self.calibObject.markers)

        # make a list to store the comparisons in
        compFrames = []
        # iterate throught frames
        for frame in frames:
            # make a dictionary for the comparisons (to match to the reference object)
            compFrame = {}
            # iterate over distances (that is, pairs of markers) and find the difference between the calibObject and those observed.
            for pair in refDists.keys():
                compFrame[pair] = frame[pair] - refDists[pair]
            compFrames.append(compFrame)
        return compFrames

    def distances(self, markerSet):
        """Compute distances between a set of markers"""
        # make an emtpy dictionary of distancs
        dists = {}
        # iterate over the markers in the markerSet
        for x in markerSet.keys():
            # compare each marker with the first (there are a number of other methods of doing this. (Maybe this should be a part of the calibration object file, so that it varies with the calibration object?)
            dists[str(min(markerSet.keys()))+","+str(x)] = euclidDist(markerSet[min(markerSet.keys())],markerSet[x])
        return dists

    def summaryStats(self):
        # setup a frames list
        frames = []
        # for each frame in the testData, compute the set of distances given the self.distances() function.
        for frame in self.testData:
            frames.append(self.distances(frame))
            
        # generate reference distances, mabye this should be done elsewhere?
        refDists = self.distances(self.calibObject.markers)

        framesByMarker = {}
            
        for pair in refDists.keys():
            framesByMarker[pair] = []
        for frame in frames:
            for pair in refDists.keys():
                framesByMarker[pair].append(frame[pair] - refDists[pair])

        for pair in framesByMarker:
            print(pair)
            print('minimum: '+str(fivenum(framesByMarker[pair])[0]))
            print('lower-hinge: '+str(fivenum(framesByMarker[pair])[1]))
            print('median: '+str(fivenum(framesByMarker[pair])[2]))
            print('upper-hinge: '+str(fivenum(framesByMarker[pair])[3]))
            print('maximum: '+str(fivenum(framesByMarker[pair])[4]))


                
            
            

class OWLConnection:
    """A connection to an OWL server"""
    def __init__(self, server, initFlags):
        self.status = "disconnected"
        self.server = server
        self.initFlags = initFlags

    def connect(self):
        if self.status == "disconnected":
            # connect, and check for errors
            if owlInit(self.server, self.initFlags) < 0 :
                print("init error: ", owlGetError())
                sys.exit(0)

            # Set buffer size
            owlSetInteger(OWL_FRAME_BUFFER_SIZE, 0)

            # start streaming
            owlSetInteger(OWL_STREAMING, OWL_ENABLE)
            owlSetInteger(OWL_COMMDATA, OWL_ENABLE)
            self.status = "connected"
        else:
            # already connected
            pass
                
    def disconnect(self):
        if self.status == "connected":
            owlDone()
            self.status = "disconnected"
        else:
            # already disconnected
            pass


def dictOfListsWriter(dict, filename):
    # open file, establish headers
    f = open(filename, 'wb')
    w = csv.writer(f, dialect='excel-tab')
    # write headers
    w.writerow(dict.keys())
        
    
    lengths = []
    for key in dict.keys():
        lengths.append(len(dict[key]))

    if len(set(lengths)) != 1:
        print("Error!")

    n = lengths[0]

    for x in range(0,n):
        rw = []
        for key in dict.keys():
##            print(dict[key][x])
            rw.append(dict[key][x])
        w.writerow(rw)        
