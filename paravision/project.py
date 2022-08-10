from paraview.simple import *

from paravision.utils import default_origin_normal, get_bounds

def project(object, projectionType=None, geometry=None, origin=None, normal=None):

    if projectionType is None: 
        return object

    projection = None

    if projectionType.lower() == 'clip':
        ## WARNING: Commented out code is buggy for some reason. Use geometry == 'twice'
        ##          Final projection object doesn't show bounds. PV version 5.10-ish
        # if geometry == 'Box': 
        #     """Limited Box clipping"""
        #
        #     origin, dest = origin.split('-')
        #
        #     pos, _ = default_origin_normal(object, origin, normal)
        #
        #     pos2, _ = default_origin_normal(object, dest, normal)
        #
        #     length = [ p2-p1 for p1,p2 in zip(pos, pos2)]
        #
        #     projection = Clip(Input=object)
        #     projection.ClipType = 'Box'
        #     projection.ClipType.UseReferenceBounds = 1
        #     projection.Exact = 1
        #     projection.ClipType.Position = pos
        #     projection.ClipType.Length = length
        #
        if geometry == 'twice': 
            origin, dest = origin.split('-')

            pos1, norm1 = default_origin_normal(object, origin, normal)
            intermediate = Clip(Input=object)
            intermediate.Invert = 0
            intermediate.ClipType = 'Plane'
            intermediate.ClipType.Origin = pos1
            intermediate.ClipType.Normal = norm1

            pos2, norm2 = default_origin_normal(object, dest, normal)
            projection = Clip(Input=intermediate)
            projection.Invert = 1
            projection.ClipType = 'Plane'
            projection.ClipType.Origin = pos2
            projection.ClipType.Normal = norm2

        else: 
            origin, normal = default_origin_normal(object, origin, normal)
            projection = Clip(Input=object)
            projection.ClipType = geometry
            # projection.HyperTreeGridSlicer = geometry
            projection.ClipType.Origin = origin
            projection.ClipType.Normal = normal
            Hide3DWidgets(proxy=projection.ClipType)
    elif projectionType.lower() == 'slice':
        origin, normal = default_origin_normal(object, origin, normal)
        projection = Slice(Input=object)
        projection.SliceType = geometry
        projection.HyperTreeGridSlicer = geometry
        projection.SliceType.Origin = origin
        projection.SliceType.Normal = normal
        Hide3DWidgets(proxy=projection.SliceType)

    else:
        projection = object

    projection.UpdatePipeline()

    return projection
