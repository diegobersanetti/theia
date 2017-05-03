'''Geometry module for theia.'''

# Provides:
#   refrAngle(theta, n1, n2)
#   linePlaneInter(pos, dirV, planeC, normV, diameter)
#   lineSurfInter(pos, dirV, chordC, chordNorm, kurv, diameter, minK = 1.0e-5)
#   lineCylInter(pos, dirV, faceC, normV, thickness, diameter)

import numpy as np
np.seterr(divide = 'raise', invalid = 'raise')  # np raises FloatingPointError

from helpers import TotalReflectionError

def refrAngle(theta, n1, n2):
    '''Returns the refraction angle at n1/n2 interface for incoming theta.

        May raise a TotalReflectionError.
    '''
    try:
        return np.arcsin(n1*np.sin(theta)/n2)
    except FloatingPointError:
        msg = 'Total reflection occured.'
        raise TotalReflectionError(msg)

def linePlaneInter(pos, dirV, planeC, normV, diameter):
    '''Computes the intersection between a line and a plane.

    pos: position of the begining of the line. [3D vector]
    dirV: directing vector of the line. [3D vector]
    planeC: position of the center of the plane. [3D vector]
    normV: vector normal to the plane. [3D vector]
    diameter: diameter of the plane.

    Returns a dictionnary with keys:
        'isHit': whether of not the plane is hit. [boolean]
        'distance': geometrical distance from line origin to intersection point.
            [float]
        'intersection point': position of intersection point. [3D vector]


    '''

    # Convert to np arrays and normalize
    pos = np.array(pos, dtype=np.float64)
    planeC = np.array(planeC, dtype=np.float64)
    dirV = np.array(dirV, dtype=np.float64)
    dirV = dirV/np.linalg.norm(dirV)
    normV = np.array(normV, dtype=np.float64)
    normV = normV/np.linalg.norm(normV)
    diameter = float(diameter)

    noInterDict = {'isHit': False,  # return this if no intersect
            'distance': 0.,
            'intersection point': np.array([0., 0., 0.], dtype=np.float64)
            }

    # If plane and dirV are orthogonal then no intersection
    if np.dot(normV, dirV) == 0.:
        return noInterDict

    # If not then there is a solution to pos + lam*dirV in plane, it is:
    lam = np.dot(normV, planeC - pos)/np.dot(normV, dirV)

    # If lam is negative no intersection
    if lam <= 0.:
        return noInterDict

    # find intersection point:
    intersect = pos + lam * dirV
    dist = np.linalg.norm(intersect - planeC)

    # if too far from center, no intersection:
    if dist >= diameter / 2.:
        return noInterDict

    return {'isHit': True,
            'distance': lam,
            'intersection point': intersect}


def lineSurfInter(pos, dirV, chordC, chordNorm, kurv, diameter, minK = 1.0e-5):
    '''Computes the intersection between a line and a spherical surface.

    The spherical surface is supposed to have a cylindrical symmetry around
        the vector normal to the 'chord', ie the plane which undertends
        the surface.

    Note: the normal vector always looks to the center of the sphere

    pos: position of the begingin of the line. [3D vector]
    dirV: direction of the line. [3D vector]
    chordC: position of the center of the 'chord'. [3D vector]
    chordNorm: normal vector the the chord in its center. [3D vector]
    kurv: curvature (1/ROC) of the surface. [float]
    diameter: diameter of the surface. [float]
    minK = curvature under which spherical surfaces are considered planes.
        [float]

    Returns a dictionnary with keys:
        'is Hit': whether the surface is hit or not. [boolean]
        'distance': distance to the intersection point from pos. [float]
        'intersection point': position of intersection point. [3D vector]

    '''

    # Convert to np.array and normalize
    pos = np.array(pos, dtype=np.float64)
    chordC = np.array(chordC, dtype=np.float64)
    dirV = np.array(dirV, dtype=np.float64)
    dirV = dirV/np.linalg.norm(dirV)
    chordNorm = np.array(chordNorm, dtype=np.float64)
    chordNorm = chordNorm/np.linalg.norm(chordNorm)
    diameter = float(diameter)
    kurv = float(kurv)

    noInterDict = {'isHit': False,  # return this if no intersect
            'distance': 0.,
            'intersection point': np.array([0., 0., 0.], dtype=np.float64)}

    # if surface is too plane, it is a plane
    if np.abs(kurv) < minK:
        return linePlaneInter(pos, dirV, chordC, chordNorm, diameter)


    # find center of curvature of surface:
    theta = np.arcsin(diameter*kurv/2.)  # this is half undertending angle
    sphereC = chordC + np.cos(theta)*chordNorm/kurv
    R = 1/kurv  # radius
    PC = sphereC - pos  # vector from pos to center of curvature

    # first find out if there is a intersection between the line and the whole
    # sphere. a point pos + lam * dirV is on the sphere if and only if it is
    # at distance R from sphereC.

    # discriminant of polynomial ||pos + lam*dirV - sphereC||**2 = R**2
    delta = 4.*(np.dot(dirV,PC))**2. + 4.*(R**2. - np.linalg.norm(PC)**2.)

    if delta <= 0.:
        # no intersection at all or beam is tangent to surface
        return noInterDict

    # intersection parameters
    lam1 = ( 2.*np.dot(dirV, PC) - np.sqrt(delta))/2.  # < lam2
    lam2 = ( 2.*np.dot(dirV, PC) + np.sqrt(delta))/2.

    if lam1 < 0. and lam2 < 0.:
        # sphere is behind
        return noInterDict

    if lam1 < 0. and lam2 > 0.:
        # we found a point and have to verify that its on the surface (we
        # already know its on the sphere)
        intersect = pos + lam2 * dirV
        localNorm = sphereC - intersect
        localNorm = localNorm/np.linalg.norm(localNorm)

        # compare angles theta and thetai (between chordN and localN) to
        # to know if the point is on the coated surface
        if np.dot(localNorm, chordNorm) > diameter * kurv/2. :
            # it is on the surface
            return {'isHit': True,
                    'distance': lam2,
                    'intersection point': intersect}

    if lam1 > 0. and lam2 > 0.:
        # we got to points, take the closest which is on the surface
        intersect = pos + lam1 * dirV
        localNorm = sphereC - intersect
        localNorm = localNorm/np.linalg.norm(localNorm)

        if np.dot(localNorm, chordNorm) > diameter * kurv/2. :
            # the first is on the surface
            return {'isHit': True,
                    'distance': lam1,
                    'intersection point': intersect}

        # try the second
        intersect = pos + lam2 * dirV
        localNorm = sphereC - intersect
        localNorm = localNorm/np.linalg.norm(localNorm)

        if np.dot(localNorm, chordNorm) > diameter * kurv/2. :
            # the second is on the surface
            return {'isHit': True,
                    'distance': lam2,
                    'intersection point': intersect}

    return noInterDict

def lineCylInter(pos, dirV, faceC, normV, thickness, diameter):
    '''Computes the intersection of a line and a cylinder in 3D space.

    The cylinder is specified by a disk of center faceC, an outgoing normal
    normV, a thickness (thus behind the normal) and a diameter.

    pos: origin of the line. [3D vector]
    dirV: directing vector of the line. [3D vector]
    faceC: center of the face of the cylinder where lies the normal vector.
        [3D vector]
    normV: normal vector to this face (outgoing). [3D vector]
    thickness: thickness of the cylinder (counted from faceC and behind normV)
        [float]
    diameter: of the cylinder. [float]

    Returns a dictionnary with keys:
        'isHit': whether of not. [boolean]
        'distance': geometrical distance of the intersection point from pos.
            [float]
        'intersection point': point of intersection. [3D vector]

    '''

    # Convert to np.array and normalize
    pos = np.array(pos, dtype=np.float64)
    faceC = np.array(faceC, dtype=np.float64)
    dirV = np.array(dirV, dtype=np.float64)
    dirV = dirV/np.linalg.norm(dirV)
    normV = np.array(normV, dtype=np.float64)
    normV = normV/np.linalg.norm(normV)
    diameter = float(diameter)
    thickness = float(thickness)

    noInterDict = {'isHit': False,  # return this if no intersect
            'distance': 0.,
            'intersection point': np.array([0., 0., 0.], dtype=np.float64)}

    # if the line is parallel to the axis of the cylinder, no intersection
    if np.abs(np.dot(dirV,normV)) == 1.:
        return noInterDict

    # parameters
    PC = faceC - pos
    dirn = np.dot(dirV, normV)
    PCn = np.dot(PC, normV)
    PCdir = np.dot(PC, dirV)
    PC2 = np.dot(PC,PC)
    R = diameter/2
    center = faceC - thickness*normV/2.    # center of cylinder
    dist = np.sqrt(R**2. + thickness**2./4.)    # distance from center to edge

    # the cylinder's axis is faceC + x*normV for x real. this axis is at
    # a distance R to pos + lam*dirV if a P(lam)=0 whose discriminant is:
    delta = 4.*(dirn*PCn - PCdir)**2. - 4.*(1.-dirn**2.)*(PC2 - R**2. - PCn**2.)

    if delta <= 0.:
        #no intersection or line is tangent
        return noInterDict

    # intersection parameters
    lam1 = (2.*(PCdir - dirn*PCn) - np.sqrt(delta))/(2.*(1. - dirn**2.))# < lam2
    lam2 = (2.*(PCdir - dirn*PCn) + np.sqrt(delta))/(2.*(1. - dirn**2.))

    if lam1 < 0. and lam2 < 0.:
        # cylinder is behind
        return noInterDict

    if lam1 < 0. and lam2 > 0.:
        # we found a point and have to verify that its on the physical surface
        intersect = pos + lam2 * dirV

        # check if it is at distance sqrt(R**2 + dia**2/4) or less to center:
        if np.linalg.norm(intersect - center) < dist:
            # it is on the cylinder
            return {'isHit': True,
                    'distance': lam2,
                    'intersection point': intersect}

    if lam1 > 0. and lam2 > 0.:
        # we got two points, take the closest which is on the surface
        intersect = pos + lam1 * dirV

        if np.linalg.norm(intersect - center) < dist:
            # the first is on the surface
            return {'isHit': True,
                    'distance': lam1,
                    'intersection point': intersect}

        # try the second
        intersect = pos + lam2 * dirV

        if np.linalg.norm(intersect - center) < dist :
            # the second is on the surface
            return {'isHit': True,
                    'distance': lam2,
                    'intersection point': intersect}

    return noInterDict


def newDir(inc, nor, n1, n2):
    '''Computes the refl and refr directions produced by inc at interface n1/n2.

    inc: director vector of incoming beam. [3D vector]
    nor: normal to the interface at the intersection point. [3D vector]
    n1: refractive index of the first medium. [float]
    n2: idem.

    Returns a dictionnary with keys:
        'r': normalized direction of reflected beam. [3D vector]
        't': normalized direction of refracted beam. [3D vector]

    Note: if total reflection then refr is None.

    '''
    inc = np.array(inc, dtype=np.float64)
    inc = inc/np.linalg.norm(inc)
    nor = np.array(nor, dtype=np.float64)
    nor = nor/np.linalg.norm(nor)


    # normal incidence case:
    if np.abs(np.dot(inc,nor)) == 1.:
        return {'r': nor,
                't': inc}

    # reflected (see documentation):
    refl = inc - 2.*np.dot(inc,nor)*nor
    refl = refl/np.linalg.norm(refl)

    # incident and refracted angles
    theta1 = np.arccos(- np.dot(nor,inc))
    try:
        theta2 = refrAngle(theta1, n1, n2)
    except TotalReflectionError :
        return {'r': refl,
                't': None}

    # sines and cosines
    c1 = np.cos(theta1)
    c2 = np.cos(theta2)
    s1 = np.sin(theta1)

    alpha = n1/n2
    beta = n1*c1/n2 - c2

    # refracted:
    refr = (alpha*inc + beta*nor)
    refr = refr/np.linalg.norm(refr)

    return {'r': refl,
            't': refr}
