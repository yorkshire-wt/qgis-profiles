from qgis.core import *
from qgis.gui import *
import math

@qgsfunction(args='auto', group='Custom', referenced_columns=[])
def st_gridref(geom, max_figs=6, var_figs=False, include_spaces=False, feature=None, parent=None):
    """
    Converts a geometry to an Ordnance Survey Grid Reference (British National Grid).
    
    The function automatically transforms coordinates from the layer's CRS to EPSG:27700 (British National Grid).
    For non-point geometries, the grid reference is calculated from the geometric centroid.
    
    <h2>Syntax</h2>
    <p>st_gridref(<i>geometry</i>, [<i>max_figs=6</i>], [<i>var_figs=False</i>], [<i>include_spaces=False</i>])</p>
    
    <h2>Arguments</h2>
    <p><i>geometry</i> &rarr; input geometry. Will be automatically transformed to British National Grid (EPSG:27700) if in a different CRS.</p>
    <p><i>max_figs</i> &rarr; maximum number of figures for easting and northing (combined). Must be an even number between 0 and 10. Default is 6 (6-figure grid reference, 100m precision).</p>
    <ul>
    <li>0 = 100km grid square only (e.g., 'TQ')</li>
    <li>2 = 10km precision (e.g., 'TQ12')</li>
    <li>4 = 1km precision (e.g., 'TQ1234')</li>
    <li>6 = 100m precision (e.g., 'TQ123456')</li>
    <li>8 = 10m precision (e.g., 'TQ12345678')</li>
    <li>10 = 1m precision (e.g., 'TQ1234567890')</li>
    </ul>
    <p><i>var_figs</i> &rarr; if True, removes trailing zeros to give variable precision output. Default is False.</p>
    <p><i>include_spaces</i> &rarr; if True, includes spaces between grid letters, easting, and northing. Default is False.</p>
    
    <h2>Examples</h2>
    <ul>
    <li><code>st_gridref($geometry)</code> &rarr; <code>'TQ123456'</code></li>
    <li><code>st_gridref($geometry, 4)</code> &rarr; <code>'TQ1234'</code></li>
    <li><code>st_gridref($geometry, 10)</code> &rarr; <code>'TQ1234567890'</code></li>
    <li><code>st_gridref($geometry, 6, true)</code> &rarr; <code>'TQ12'</code> (if easting/northing end in 000)</li>
    <li><code>st_gridref($geometry, 6, false, true)</code> &rarr; <code>'TQ 123 456'</code></li>
    </ul>
    
    <h2>Notes</h2>
    <p>Created by Dom Hinchley. Based on the PostGIS function by atph: https://gist.github.com/atph/0829d8d645720e679d8d04cbd7cfd5de</p>
    """
    
    # Validate max_figs
    if max_figs % 2 != 0 or max_figs < 0 or max_figs > 10:
        parent.setEvalErrorString('ERROR: max_figs must be an even number between 0 and 10')
        return None
    
    if geom is None or geom.isNull():
        return None
    
    # Get the layer's CRS and create transform to BNG (EPSG:27700)
    # In QGIS expressions, we use the project CRS as the source
    # This assumes the geometry is in the same CRS as the current layer/project
    source_crs = QgsProject.instance().crs()
    dest_crs = QgsCoordinateReferenceSystem('EPSG:27700')
    
    # Transform geometry to BNG if needed
    if source_crs.authid() != 'EPSG:27700':
        transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
        geom = QgsGeometry(geom)  # Create a copy
        geom.transform(transform)
    
    # Get centroid
    centroid = geom.centroid().asPoint()
    e = int(centroid.x())
    n = int(centroid.y())
    
    # Get the 100km-grid indices
    e100k = math.floor(e / 1e5)
    n100k = math.floor(n / 1e5)
    
    # Translate those into numeric equivalents of the grid letters
    l1 = (19 - n100k) - (19 - n100k) % 5 + math.floor((e100k + 10) / 5)
    l2 = (19 - n100k) * 5 % 25 + e100k % 5
    
    # Compensate for skipped 'I' and build grid letter-pairs
    if l1 > 7:
        l1 += 1
    if l2 > 7:
        l2 += 1
    
    letter_pair = chr(ord('A') + l1) + chr(ord('A') + l2)
    
    # Strip 100km-grid indices from easting & northing
    e = math.floor(e % 1e5)
    n = math.floor(n % 1e5)
    
    # Calculate number of figures
    figs = max_figs // 2
    
    # Pad eastings & northings with leading zeros and take required figures
    e_char = str(e).zfill(5)[:figs]
    n_char = str(n).zfill(5)[:figs]
    
    # Handle variable figure precision
    if var_figs:
        # Count trailing zeros
        e_zeros = len(e_char) - len(e_char.rstrip('0'))
        n_zeros = len(n_char) - len(n_char.rstrip('0'))
        
        # Use the minimum number of trailing zeros
        nzeros = min(e_zeros, n_zeros)
        
        # Remove trailing zeros
        if nzeros > 0:
            e_char = e_char[:-nzeros]
            n_char = n_char[:-nzeros]
    
    # Format output
    if include_spaces:
        gridref = f"{letter_pair} {e_char} {n_char}".strip()
    else:
        gridref = letter_pair + e_char + n_char
    
    return gridref
