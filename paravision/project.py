from paraview.simple import *

from paravision.utils import default_origin_normal

def project(object, args):

    projectionType = args['project'][0]
    geometry = args['project'][1]
    origin = args['project'][2]
    normal = args['project'][3]

    # projectionView = GetActiveViewOrCreate('RenderView')
    # display = Show(object, projectionView)
    # (xmin,xmax,ymin,ymax,zmin,zmax) = GetActiveSource().GetDataInformation().GetBounds()
    # Hide(object, projectionView)
    # center = [ (xmax+xmin)/2, (ymax+ymin)/2, (zmax+zmin)/2,]
    # if not origin:
    #     origin=center
    # else:

    projection = None
    if projectionType.lower() == 'clip':
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
