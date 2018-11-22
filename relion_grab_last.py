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
import subprocess
from shutil import copyfile
import argparse
import sys

parser = argparse.ArgumentParser(description="Grab last iterations from relion Class2D for further analysis. Renames to condense directory structure.")
parser.add_argument('project', help="Relion project base location.")
parser.add_argument('output', nargs='?', help="Output location for star files (optional).")
parser.add_argument('--scp', '--ssh', '-s', action='store_true', help="Move files to output location connection via scp.")
parser.add_argument('--prefix', '-p', default=None, help="Provide different prefix (default is folder name)")
args = parser.parse_args()

if args.scp and args.output is None:
    parser.error("argument --scp/--ssh/-s: requires output to be specified")

outfiles = []

if args.scp:
    import tempfile
    from shutil import rmtree
    dirpath = tempfile.mkdtemp()
elif args.output:
    dirpath = args.output
else:
    dirpath = "."

if args.prefix:
    projectname = args.prefix
else:
    projectname = os.path.basename(os.path.normpath(os.path.abspath(args.project)))
for jobname in sorted(os.listdir(os.path.join(args.project,"Class2D"))):
    fullname = os.path.join(args.project,"Class2D", jobname)
    if os.path.isdir(fullname) and not os.path.islink(fullname):
        #print name
        files = os.listdir(fullname)
        datastars = filter(lambda x: "_data.star" in x and "sub" not in x, files)
        ct_datastars = filter(lambda x: "_ct" in x, datastars)
        init_datastars = filter(lambda x: "_ct" not in x, datastars)
        if ct_datastars:
            lastfile = sorted(ct_datastars, key=lambda x: 1000*int(x[x.rindex("_ct") + 3: x.index("_it")]) + int(x[x.index("_it") + 3: x.index("_data")]))[-1]
            copyfile(os.path.join(fullname, lastfile), os.path.join(dirpath, os.path.join(projectname, "Class2D", jobname, lastfile).replace("/","_")))
            outfiles.append(os.path.join(dirpath, os.path.join(projectname, "Class2D", jobname, lastfile).replace("/","_")))
        elif init_datastars:
            lastfile = sorted(init_datastars)[-1]
            copyfile(os.path.join(fullname, lastfile), os.path.join(dirpath, os.path.join(projectname, "Class2D", jobname, lastfile).replace("/","_")))
            outfiles.append(os.path.join(dirpath, os.path.join(projectname, "Class2D", jobname, lastfile).replace("/","_")))
        else:
            print "Folder " + fullname + " does not include data star files" 

if args.scp:
    print "Copying in progress ..."
    subprocess.Popen(["scp"] + outfiles + [args.output]).wait()
    rmtree(dirpath)
    print "Done"
