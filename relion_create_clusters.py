#!/usr/bin/env python

# **************************************************************************
# *
# * Author:  James A. Geraets (j.geraets@fz-juelich.de)
# *          Karunakar Pothula
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
from itertools import izip, count
from collections import defaultdict

from pyrelion import MetaData
import argparse
import os.path

from decimal import Decimal
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA as sklearnPCA
from scipy.spatial.distance import cdist

class LazyExtract(MetaData):
    def __init__(self, input_star):
        MetaData.__init__(self, input_star=input_star)
        self._filamentIds = None
        self._classIds = None
    def __iter__(self):
        self.filamentIds()
        for item in self._data:
            yield item.rlnFilamentID, item.rlnClassNumber
    def classIds(self):
        if self._classIds:
            return self._classIds
        else:
            self._classIds = dict((j,i) for i,j in enumerate(sorted(set(item.rlnClassNumber for item in self._data))))
            return self._classIds
    def filamentIds(self):
        if self._filamentIds:
            return self._filamentIds
        else:
            filamentIdAssign = defaultdict(count(start=1).next)
            for item in self._data:
                item.rlnFilamentID = filamentIdAssign[str(item.rlnHelicalTubeID) + "-" + item.rlnMicrographName]
            self._filamentIds = dict((i,i-1) for i in filamentIdAssign.values())
            return self._filamentIds
        #return dict((j,i) for i,j in enumerate(sorted(set(item.rlnHelicalTubeID for item in self._data))))

class CreateClusters():
    def define_parser(self):
        self.parser = argparse.ArgumentParser(
            description="Clusters helical particles from 2D classification.")
        self.parser.add_argument('input_star', nargs='+', help="Input STAR filename(s) with particles and micrograph names.")
        self.parser.add_argument('-x', action='store_true', help="No display - run as command line only.")

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

        print "Creating coordinate files..."
        
        for star in args.input_star:
            print star

            le = LazyExtract(star)

            filament_ids = le.filamentIds()
            class_ids = le.classIds()

            print filament_ids

            print class_ids

            fc_matrix = np.zeros((len(le.filamentIds()), len(le.classIds())), dtype=np.float)

            for f,c in le:
                fc_matrix[le.filamentIds()[f], le.classIds()[c]] += 1
            fc_matrix_norm = fc_matrix / fc_matrix.sum(axis=1,keepdims=True)

            print fc_matrix_norm 
            kmeans = KMeans(n_clusters=2, random_state=2).fit(fc_matrix_norm)
            y_kmeans = kmeans.predict(fc_matrix_norm)
            print "kmeans clustering"
            print y_kmeans
            ward_clust = AgglomerativeClustering(n_clusters=2, affinity = 'euclidean', linkage = 'ward')
            ward_link = ward_clust.fit_predict(fc_matrix_norm)
            print "ward clustering"
            print ward_link
            comp_clust = AgglomerativeClustering(n_clusters=2, affinity = 'euclidean', linkage = 'complete')
            comp_link = comp_clust.fit_predict(fc_matrix_norm)
            print "complete clustering"
            print comp_link
            aver_clust = AgglomerativeClustering(n_clusters=2, affinity = 'euclidean', linkage = 'average')
            aver_link = aver_clust.fit_predict(fc_matrix_norm)
            print "average clustering"
            print aver_link

            try:
                sklearn_pca = sklearnPCA(n_components=2)
                y_pca = sklearn_pca.fit_transform(fc_matrix_norm)
            except ValueError as e:
                print "WARNING: PCA failed with 2 components"
                print e
                continue

            distortions = []
            K = range(1,10)
            for k in K:
                kmeanModel = KMeans(n_clusters=k).fit(fc_matrix_norm)
                kmeanModel.fit(fc_matrix_norm)
                distortions.append(sum(np.min(cdist(fc_matrix_norm, kmeanModel.cluster_centers_, 'euclidean'), axis=1)) / fc_matrix_norm.shape[0])

            fig=plt.figure()
            plt.subplot(231)
            plt.scatter(y_pca[:, 0], y_pca[:, 1], c=y_kmeans, label=y_kmeans, alpha=0.5)
            plt.title("k-means")

            plt.subplot(232)
            plt.scatter(y_pca[:, 0], y_pca[:, 1], c=ward_link, label=ward_link, alpha=0.5)
            plt.title("Ward Linkage")

            plt.subplot(233)
            plt.scatter(y_pca[:, 0], y_pca[:, 1], c=comp_link, label=comp_link,alpha=0.5)
            plt.title("Complete Linkage")

            plt.subplot(234)
            plt.scatter(y_pca[:, 0], y_pca[:, 1], c=aver_link, label=aver_link, alpha=0.5)
            plt.title("Average Linkage")

            plt.subplot(235)
            plt.plot(K, distortions, '-ok', c='black')
            plt.xlabel('k')
            plt.ylabel('Distortion')
            plt.title('The Elbow Method showing the optimal k')
            if not args.x:
                plt.show()
            fig.savefig(os.path.splitext(star)[0] + ".clustering.pdf")
            plt.clf()

if __name__ == "__main__":
    CreateClusters().main()
