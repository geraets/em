#!/usr/bin/env python

# **************************************************************************
# *
# * Author:  James A. Geraets (j.geraets@fz-juelich.de)
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# **************************************************************************

import os
import sys
import math
import numpy as np
from itertools import izip

from pyrelion import MetaData
import argparse

from decimal import Decimal
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA as sklearnPCA

class LazyExtract(MetaData):
    def __iter__(self):
        for item in self._data:
            yield item.rlnHelicalTubeID, item.rlnClassNumber
    def classIds(self):
        return dict((j,i) for i,j in enumerate(sorted(set(item.rlnClassNumber for item in self._data))))
    def filamentIds(self):
        return dict((j,i) for i,j in enumerate(sorted(set(item.rlnHelicalTubeID for item in self._data))))

class CreateClusters():
    def define_parser(self):
        self.parser = argparse.ArgumentParser(
            description="Clusters helical particles from 2D classification.")
        self.parser.add_argument('input_star', help="Input STAR filename with particles and micrograph names.")

    def usage(self):
        self.parser.print_help()

    def error(self, *msgs):
        self.usage()
        print "Error: " + '\n'.join(msgs)
        print " "
        sys.exit(2)

    def main(self):

        self.define_parser()
        args = self.parser.parse_args()

        if len(sys.argv) == 1:
            self.error("No input particles STAR file given.")

        print "Creating coordinate files..."

        #md = MetaData(args.input_star)

        #filaments, classes = izip(*((particle.rlnHelicalTubeID, particle.rlnClassNumber) for particle in md))

        #filament_ids = dict((j,i) for i,j in enumerate(sorted(set(filaments))))
        #class_ids = dict((j,i) for i,j in enumerate(sorted(set(classes))))
        
        #fc_matrix = np.zeros((len(filament_ids), len(class_ids)))
        #fc_matrix_norm = np.zeros((len(filament_ids), len(class_ids)))
        
        #for f, c in izip(filaments, classes):
        #    print f, filament_ids[f], c, class_ids[c]

        #print filament_ids, class_ids

        le = LazyExtract(args.input_star)

        filament_ids = le.filamentIds()
        class_ids = le.classIds()

        fc_matrix = np.zeros((len(filament_ids), len(class_ids)), dtype=np.float)

        for f,c in le:
            fc_matrix[filament_ids[f], class_ids[c]] += 1
        fc_matrix_norm = fc_matrix / fc_matrix.sum(axis=1,keepdims=True)

        print fc_matrix_norm 
        kmeans = KMeans(n_clusters=2, random_state=2).fit(fc_matrix_norm)
        y_kmeans = kmeans.predict(fc_matrix_norm)
        print("kmeans clustering")
        print(y_kmeans)

if __name__ == "__main__":
    CreateClusters().main()
