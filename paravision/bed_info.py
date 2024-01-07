#!/usr/bin/env python3

"""
Get info about the packed bed to be used in building a cadet simulation corresponding to the given HD mesh.

The code is replicated from pack.py.
"""

import csv
from addict import Dict
from rich import print, print_json
from rich.pretty import pprint
from math import asin,sqrt,pi
from mpmath import ellipk, ellipe, ellipf, nstr
from multiprocessing import Pool
from functools import partial

from paraview.simple import *
from paravision.utils import script_main_new, default_parser, create_threshold, get_bounds

import numpy as np

def csvWriter(filename, x, y):
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(zip(x, y))

class Bounds:
    def __init__(self, x0, x1, y0, y1, z0, z1):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.z0 = z0
        self.z1 = z1

        self.dx = x1 - x0
        self.dy = y1 - y0
        self.dz = z1 - z0
        self.xc = (x0 + x1) / 2
        self.yc = (y0 + y1) / 2
        self.zc = (z0 + z1) / 2


class Bead:
    """Class for individual beads"""

    def __init__(self, x, y, z, r):
        self.x = x
        self.y = y
        self.z = z
        self.r = r

    def pos(self):
        return np.sqrt(self.x**2 + self.y**2)

    def volume(self):
        return 4/3 * np.pi * self.r**3

    def distance(self, other):
        return sqrt((self.x-other.x)**2 + (self.y-other.y)**2 + (self.z-other.z)**2)

    def serialize(self):
        return (self.x, self.y, self.z, self.r)

class PackedBed:
    """Class for packed bed of beads. Can apply transformations on beads"""

    def __init__(self):
        self.beads = []

    def add(self, bead):
        self.beads.append(bead)

    def size(self):
        return len(self.beads)

    def radii(self):
        return list(map(lambda b: b.r, self.beads))

    def volume(self):
        vol = 0
        for bead in self.beads:
            vol = vol + bead.volume()
        return vol

    def serialize(self):
        return np.array(list(map(lambda b: b.serialize(), self.beads)))

    def write(self, filename):
        np.savetxt(filename, self.serialize(), delimiter=',')

    def updateBounds(self):
        """
        Calculate bounding points for the packed bed.
        """

        xpr = []
        xmr = []
        ypr = []
        ymr = []
        zpr = []
        zmr = []
        z = []

        for bead in self.beads:
            xpr.append(bead.x + bead.r)
            xmr.append(bead.x - bead.r)
            ypr.append(bead.y + bead.r)
            ymr.append(bead.y - bead.r)
            zpr.append(bead.z + bead.r)
            zmr.append(bead.z - bead.r)
            z.append(bead.z)

        radList = [ bead.r for bead in self.beads ]
        self.rmax = max(radList)
        self.rmin = min(radList)
        self.ravg = sum(radList)/len(radList)

        self.xmax = max(xpr)
        self.ymax = max(ypr)
        self.ymin = min(ymr)
        self.xmin = min(xmr)
        self.zmax = max(zpr)
        self.zmin = min(zmr)

        self.dx = self.xmax - self.xmin
        self.dy = self.ymax - self.ymin
        self.dz = self.zmax - self.zmin

        self.R = max((self.xmax-self.xmin)/2, (self.ymax-self.ymin)/2) ## Similar to Genmesh
        self.h = self.zmax - self.zmin
        self.CylinderVolume = pi * self.R**2 * self.h

    def moveBedtoCenter(self):
        """
        Translate bed center to origin of coordinate system.
        """
        self.updateBounds()
        offsetx = -(self.xmax + self.xmin)/2
        offsety = -(self.ymax + self.ymin)/2
        for bead in self.beads:
            bead.x = bead.x + offsetx
            bead.y = bead.y + offsety
        self.updateBounds()

def volShellRegion(beads, rShells, i):
    """
    Find the intersection volumes between rShells[i] & rShells[i+1]

    @input: beads, shell_radii, index of shell
    @output:
        - total volume of all particles within the i'th shell
        - list of all radii based on intersected volumes.

    """
    volShell=0
    radsShell=[]
    for bead in beads:
        volBead = volBeadSlice(bead, rShells[i], rShells[i+1])
        volShell = volShell + volBead
        radBead = pow(volBead/(4.0/3.0*pi), 1.0/3.0)
        if radBead != 0:
            radsShell.append(radBead)
    return volShell, radsShell

# def radsShellRegion(beads, rShells, i):
#     """
#     In order to calculate histogram for beads in individual shells.
#     > 1. Calculate Volumes of each bead in given shell,
#     > 2. Extrapolate "radius" from each volume, even sliced ones.
#     > 3. Return list of radii to be used by histo()
#     """
#     radsShell=[]
#     for bead in beads:
#         volBead = volBeadSlice(bead, rShells[i], rShells[i+1])
#         radBead = pow(volBead/(4.0/3.0*pi), 1.0/3.0)
#         radsShell.append(radBead)
#     return radsShell

def bridgeVolumes(beads, bridgeTol, relativeBridgeRadius, bridgeOffsetRatio):
    """
    Find the total volume of the bridges between beads
    """
    addedBridgeVol = 0
    removedBridgeVol = 0
    count = 0
    beadsCopy = beads.copy()
    for bead1 in beads:
        beadsCopy.remove(bead1)
        for bead2 in beadsCopy:
            beadDistance = bead1.distance(bead2)
            if beadDistance < bead1.r + bead2.r + bridgeTol:
                count = count + 1
                bridgeRadius = relativeBridgeRadius * min(bead1.r, bead2.r)
                intVol1 = volBridgeSlice(bead1, bridgeRadius, bridgeOffsetRatio)
                intVol2 = volBridgeSlice(bead2, bridgeRadius, bridgeOffsetRatio)
                addedBridgeVol = addedBridgeVol + pi * bridgeRadius**2 * (beadDistance - bridgeOffsetRatio * bead1.r - bridgeOffsetRatio * bead2.r) - intVol1 - intVol2
                removedBridgeVol = removedBridgeVol + intVol1 + intVol2
                ## NOTE: Some beads will be intersecting due to single precision. That's not handled here.
    print("Number of Bridges:", count)
    return addedBridgeVol, removedBridgeVol

def volBridgeSlice(bead, bridgeRadius, offsetRatio):
    """
    Volume of intersection between bridge and bead
    """
    rho = bridgeRadius/bead.r
    # eta = bead.pos()/bead.r ##FIXME, eta == 0
    eta = 0
    vol = CylSphIntVolume(rho, eta) * bead.r**3
    ## There's no need to find the accurate internal union volume since it will be deleted to find only the extra volume added by bridges in the first place.
    vol = vol/2 - pi * bridgeRadius**2 * offsetRatio * bead.r
    return vol

def volBeadSlice(bead, rInnerShell, rOuterShell):
    """
    Find intersection volume of an individual bead between two shells (cylinders)
    """
    rhoOuter = rOuterShell/bead.r
    etaOuter = bead.pos()/bead.r
    volOuter = CylSphIntVolume(rhoOuter, etaOuter) * bead.r**3
    rhoInner = rInnerShell/bead.r
    etaInner = bead.pos()/bead.r
    volInner = CylSphIntVolume(rhoInner, etaInner) * bead.r**3
    volIntBead = volOuter - volInner
    return volIntBead


def histo(radii, **kwargs):
    """Create histogram for a particular bead size distribution.
        Also output volume fractions & mean radii to be used in CADET Polydisperse"""

    bins = kwargs.get('bins', 1)

    V=[4*np.pi*x*x*x/3 for x in radii]

    ## Dump into bins by weight of each bead's volume
    ## h (height of histogram bar) is then a representation of
    ## the volume of beads present at a certain radius (partype).
    ## if density==true weights are normalized
    h,e = np.histogram(radii, bins=bins, density=True, weights=V)

    ## Find the volume fraction at each point
    frac=[x/sum(h) for x in h]
    # print(sum(frac))

    ## Find means of each bin from the edges (e)
    w=2
    avg=np.convolve(e, np.ones(w), 'valid') / w

    return frac, list(avg)

def CylSphIntVolume(rho, eta):
    """ Analytical Formulae to calculate intersection between cylinder and sphere.
        See http://dx.doi.org/10.1016/s1385-7258(61)50049-2 for more info.
    """
    if rho == 0.0:
        return 0
    elif (eta - rho) <= -1:
        return 4/3 * pi
    elif (eta - rho) >= 1:
        return 0

    ## NOTE: Ideally eta & rho are floats & never equal. But test cases are not handled yet. Similarly rho+eta == 1
    if eta == rho:
        print("Rho & Eta are Equal")

    if eta == 0 and 0 <= rho <= 1:
        V = 4/3 * pi - 4/3 * pi * (1 - rho**2)**(3/2)
        return V
    elif (rho + eta > 1):
        nu = asin(eta - rho)
        m = (1-(eta - rho)**2)/(4*rho*eta)

        K = ellipk(m)
        E = ellipe(m)

        F = ellipf(nu ,1-m)
        Ep = ellipe(nu, 1-m)

        L0 = 2/pi * (E * F + K * Ep - K * F )

        # V = (2/3 * pi * ( 1 - L0(nu, m) ) )\
        V = (2/3 * pi * ( 1 - L0 ) )\
        - (8/9 * sqrt(rho * eta) * (6 * rho**2 + 2 * rho * eta - 3) * (1 - m) * K)\
        + (8/9 * sqrt(rho * eta) * (7 * rho**2 + eta**2 - 4) * E)

        return V

    elif (rho + eta < 1):
        nu = asin((eta - rho)/(eta + rho))
        m = 4*rho*eta / (1 - (eta-rho)**2)
        K = ellipk(m)
        E = ellipe(m)
        F = ellipf(nu ,1-m)
        Ep = ellipe(nu, 1-m)
        L0 = 2/pi * (E * F + K * Ep - K * F )

        V = (2/3 * pi * ( 1 - L0 ))\
        - (4 * sqrt(1 - (eta-rho)**2) / (9*(eta+rho)) ) * (2*rho - 4*eta + (eta+rho)*(eta-rho)**2) * (1-m) * K\
        + (4/9 * sqrt(1 - (eta-rho)**2) * (7*rho**2 + eta**2 - 4) * E)

        return V

    else:
        print("ERROR")
        return 0

def plotter(x, y, title, filename):
    with plt.style.context(['science']):
        fig, ax = plt.subplots()
        ax.plot(x, y)
        # legend = ax.legend(loc='best', shadow=True)
        ax.set(title=title)
        ax.set(xlabel='Radius')
        ax.set(ylabel='Porosity')
        ax.autoscale(tight=True)
        ax.set_ylim(0,1)
        fig.savefig(filename)

def driver(obj, **args):
    args = Dict(args)

    full_bounds = Bounds(*get_bounds(obj))
    pprint(vars(full_bounds))

    surfaces = ExtractSurface(obj)
    connectivity = Connectivity(surfaces)
    conn_data = servermanager.Fetch(connectivity)
    nParticles = int(conn_data.GetCellData().GetArray('RegionId').GetRange()[1] + 1)

    print(f"Found {nParticles} objects!")

    xyzr = []
    fullBed = PackedBed()

    for i in range(nParticles):
        threshold = create_threshold(connectivity, 'RegionId', 'between', i, i)
        ## These bounds are going to be not-so-accurate since we're dealing with meshed geometries
        b = Bounds(*get_bounds(threshold))
        print(f"Processing object {(i+1)}/{nParticles}")

        ## Assert that we have a cube => assert we have an underlying sphere
        # Don't dump other container surfaces
        atol = 0.0
        rtol = 1e-1
        if (np.isclose(b.dy, b.dx, atol=atol, rtol=rtol) and np.isclose(b.dz, b.dx, atol=atol, rtol=rtol)):
            d = np.max([b.dx, b.dy, b.dz])
            fullBed.add(Bead(b.xc, b.yc, b.zc, d/2))
            # xyzr.append((b.xc, b.yc, b.zc, b.dx/2 ))
        Delete(threshold)

    print(f"Processed {fullBed.size()}/{nParticles} spherical particles.")

    column_length = None
    if fullBed.size() != nParticles:
        column_bounds = Bounds(*get_bounds(obj))
        column_length = column_bounds.dz
        print(f"Assuming an interstitial mesh is provided, column_length = {column_length}")

    fullBed.updateBounds()

    # meshScalingFactor = 1e-4 # see genmesh/pymesh
    # rCylDelta = 0.01*meshScalingFactor
    # R = fullBed.R + rCylDelta ## Adding Rcyldelta

    R = args['column_radius']
    hBed = fullBed.h

    filename = 'xyzr.csv'
    fullBed.write(filename)
    print(f"Saved to {filename}")

    volFrac, bin_radii = histo(fullBed.radii(), nbins=args['npartype'])
    _,BINS = np.histogram(fullBed.radii(), bins=args['npartype'])

    print(BINS)

    print("\n--- Full Bed Histogram ---")
    print('vol_frac:\n', volFrac,)
    print('mean_radii:\n', bin_radii)
    print("----\n")

    nRegions = args.nrad
    nShells = nRegions + 1 #Including r = 0
    rShells = []

    shellType = args['shelltype']

    if shellType == 'EQUIVOLUME':
        for n in range(nShells):
            rShells.append(R * sqrt(n/nRegions))
    elif shellType == 'EQUIDISTANT':
        for n in range(nShells):
            rShells.append(R * (n/nRegions))

    print(rShells)

    total_beads_volume_per_shell = [0] * nRegions

    ## Multiprocessing code.
    ##      Create a partial function of volShellRegion(beads, rShells, i) --> parfunc(i)
    ##      map each 'i' to each process
    pool = Pool()
    parfunc = partial(volShellRegion, fullBed.beads, rShells)
    # volRegions = pool.map(parfunc, range(nRegions))
    total_beads_volume_per_shell, radii_beads_per_shell = zip(*pool.map(parfunc, range(nRegions)))
    pool.close()
    pool.join()

    # print(volShellRegion(fullBed.beads, rShells, 0))

    total_beads_volume_per_shell = np.array(total_beads_volume_per_shell).astype(np.float64)
    radii_beads_per_shell = [ np.array(item).astype(np.float64) for item in radii_beads_per_shell ]

    volCylRegions_bed = [pi * hBed * (rShells[i+1]**2 - rShells[i]**2) for i in range(nRegions)]
    porosities_bed = [ float(1-n/m) for n,m in zip(total_beads_volume_per_shell, volCylRegions_bed) ]

    avg_shell_radii = [ (rShells[i] + rShells[i+1])/2 for i in range(nRegions) ]

    print("\n--- Radial Porosity Distribution in Bed ---")
    print("col_porosity_bed:\n", porosities_bed)
    print("---\n")


    ## Get histogram data: volume fractions and radii, for each shell
    ## bin_radii is the list of mean bin radii for each shell, which is set to BINS
    volFracs = []
    for rads in radii_beads_per_shell:
        volFrac, bin_radii = histo([float(x) for x in rads], bins=BINS)
        volFracs.extend(volFrac)

    print("\n--- Particle Distribution per Shell ---")
    print("vol_frac length (NRAD * NPARTYPE) =", len(volFracs))
    print("avg_radii length (NPARTYPE) =", len(bin_radii))
    print("par_type_volfrac =", volFracs)
    print("par_radius = ", bin_radii)
    print("---\n")

    # plotter(avg_shell_radii, porosities_bed, '', args['output_prefix'] + '_bedpor_rad.pdf')
    # plotter(avg_shell_radii, porosities_column, '', args['output_prefix'] + '_colpor_rad.pdf')

    csvWriter(str(args['output_prefix']) + '_bedpor_rad.csv', avg_shell_radii, porosities_bed)

    if column_length:
        volCylRegions_column = [pi * column_length * (rShells[i+1]**2 - rShells[i]**2) for i in range(nRegions)]
        porosities_column = [ float(1-n/m) for n,m in zip(total_beads_volume_per_shell, volCylRegions_column) ]
        print("\n--- Radial Porosity Distribution in FULL COLUMN ---")
        print("col_porosity:\n", porosities_column)
        print("---\n")
        csvWriter(args['output_prefix'] + '_colpor_rad.csv', avg_shell_radii, porosities_column)

    Delete(connectivity)
    Delete(surfaces)

def parser(argslist):
    ap = default_parser()
    ap.add_argument("--nrad", type=int, default=1, help="NRAD, number of radial shells in 2D model")
    ap.add_argument("--npartype", type=int, default=1, help="NPARTYPE, number of bins to sort particles by size")
    ap.add_argument("-st"  , "--shelltype", choices = ['EQUIDISTANT', 'EQUIVOLUME'], default='EQUIDISTANT', help="Shell discretization type")
    ap.add_argument("-R"  , "--column-radius", type=float, required=True, help="Column radius")
    args = Dict(vars(ap.parse_args(argslist)))
    print_json(data=args)
    return args

if __name__ == "__main__":
    script_main_new(parser, driver)
