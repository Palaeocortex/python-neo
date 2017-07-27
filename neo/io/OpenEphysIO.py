# -*- coding: utf-8 -*-
"""
Class for reading OpenEphys continuous data from a folder.

Generates a :class:`Segment` or a :class:`Block` with a
sinusoidal :class:`AnalogSignal`

Depends on: analysis-tools/OpenEphys.py

Supported: Read

Acknowledgements: :ref:`neo_io_API` sgarcia, open-ephys

Author: Cristian Tatarau, Charite Berlin, Experimental Psychiatry Group
"""

# needed for python 3 compatibility
from __future__ import absolute_import
from __future__ import division

# note neo.core needs only numpy and quantities
import numpy as np
import quantities as pq
import datetime as dt

# I need to subclass BaseIO
from neo.io.baseio import BaseIO

# to import from core
from neo.core import Block, Segment, AnalogSignal, SpikeTrain, EventArray

# need to link to open-ephys/analysis-tools
import os, sys
from neo.io import OpenEphys as OEIO


# I need to subclass BaseIO
class Open_Ephys_IO(BaseIO):
    """
    Class for reading OpenEphys data from a folder
    """

    is_readable = True # This class can only read data
    is_writable = False # write is not supported

    # This class is able to directly or indirectly handle the following objects
    supported_objects  = [ Block, Segment , AnalogSignal ]

    # This class can return either a Block or a Segment
    # The first one is the default ( self.read )
    # These lists should go from highest object to lowest object because
    # common_io_test assumes it.
    readable_objects    = [ Block, Segment , AnalogSignal ]
    # This class is not able to write objects
    writeable_objects   = [ ]

    has_header         = False
    is_streameable     = False

    # # This is for GUI stuff : a definition for parameters when reading.
    # # This dict should be keyed by object (`Block`). Each entry is a list
    # # of tuple. The first entry in each tuple is the parameter name. The
    # # second entry is a dict with keys 'value' (for default value),
    # # and 'label' (for a descriptive name).
    # # Note that if the highest-level object requires parameters,
    # # common_io_test will be skipped.
    # read_params = {
    #     Segment : [
    #         ('segment_duration',
    #             {'value' : 0., 'label' : 'Segment size (s.)'}),
    #         ('num_analogsignal',
    #             {'value' : 0, 'label' : 'Number of recording points'}),
    #         ],
    #     }

    # do not supported write so no GUI stuff
    write_params       = None
    name               = 'Open Ephys IO'
    extensions          = [ 'nof' ]
    mode = 'dir'

    def __init__(self , dirname) :
        """
        Arguments:
            pathname : the file or dir pathname
        """
        BaseIO.__init__(self)
        self.dirname = dirname


    def read_block(self,
                     # the 2 first keyword arguments are imposed by neo.io API
                     lazy = False,
                     cascade = True
                    ):
        """
        In this IO read by default a Block with one or many Segments.
        """

        header=OEIO.get_header_from_folder(self.dirname, recording= 2)


        # create an empty block
        block = Block( name = header['date_created'],
                       description=header['format'],
                       file_datetime= dt.datetime.strptime(header['date_created'], "'%d-%b-%Y %H%M%S'"),
                       rec_datetime=dt.datetime.strptime(header['date_created'], "'%d-%b-%Y %H%M%S'"),
                       file_origin=self.dirname)
        seg = Segment(name = header['date_created'],
                       description=header['format'],
                       file_datetime= dt.datetime.strptime(header['date_created'], "'%d-%b-%Y %H%M%S'"),
                       rec_datetime=dt.datetime.strptime(header['date_created'], "'%d-%b-%Y %H%M%S'"),
                       file_origin=self.dirname)
        if cascade:
            # read nested analosignal
            # data, filelist=OEIO.loadFolderToArray(self.dirname, channels='all', dtype=float)
            data, filelist=OEIO.loadFolderToArray(self.dirname, channels='all', recording= 2, dtype=float)
            if data.size == 0:
                print "Folder ", self.dirname, "is empty or can't be read"
                return
            if len(data.shape) ==1:
                # just one single channel
                n = 1
            else:
                # more than 1 channel
                n = data.shape[1]

            for i in range(n):
                ana = AnalogSignal(signal=data[:,i],
                                   units=pq.microvolt,
                                   sampling_rate=header['sampleRate']*pq.Hz,
                                   name='analog signal '+ str(i),
                                   channel_index=i,
                                   description=header['format'],
                                   file_origin= os.path.join(self.dirname,
                                                             filelist[i]))
                seg.analogsignals += [ ana ]
        block.segments.append(seg)
        block.create_many_to_one_relationship()
        return block

