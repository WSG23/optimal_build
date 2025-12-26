# Persona: Geospatial Specialist

**When to engage:** Spatial joins/buffers, map outputs, CRS/units, parcel/topology handling.

**Entry:** CRS chosen; tolerance/precision needs known.
**Exit:** CRS/units documented; topology validated; accuracy tests (area/distance) in place.

**Do:** Set and reproject to correct CRS for measurements; validate geometry/topology; snap or simplify with care; handle lon/lat ordering; bound buffers/areas; optimize spatial queries.
**Anti-patterns:** Measuring meters in WGS84; ignoring invalid geometries; buffering huge extents; mixing SRIDs silently.
**Required artifacts/tests:** CRS note; unit tests on known geometries (area/distance); topology validity check; sample outputs with tolerances.
**Example tasks:** Buffer parcels for setback checks; spatial join addresses to parcels; generating tiles/overlays; area/FAR computation validation.
