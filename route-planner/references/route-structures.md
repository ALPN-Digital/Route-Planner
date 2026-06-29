# Route structures

Pick the structure from what the user wants, then build the points list accordingly.

## Loop
Start and finish at the same point. Pass the origin as both the first and last point in `route.py --points`, with via-points shaping the loop. Best default when the user gives a distance/duration and a start but no destination.

## Out-and-back
Go to a point and return the same way (or a parallel return). For land, list start, [vias], turnaround; for a same-way return either route there and mirror, or add a return leg with different vias for variety. For water, use `water_route.py --out-and-back`.

## Point-to-point
Start and destination differ, no return. The plain case for "route me to X".

## Ride/run out, train back
Point-to-point to a destination near a railway (or bus) station, so the user travels home by train.
1. Find the destination or the far end of the desired distance.
2. `web_search` for the nearest station with the right line home; confirm it has services and bike spaces if cycling.
3. Route point-to-point to that station.
4. In the brief, name the station, the line, and a sensible train to aim for, and remind them to check live times.

## Train out, then loop or ride home
The mirror image: travel out by train, then a loop from the destination station or a one-way back.
1. Pick a station in good riding/running country.
2. Build a loop from that station, or a point-to-point back towards home.
3. In the brief, name the outbound train and the start station.

## Multi-day
Split the total into day legs sized to the user's form (from Strava). Produce one GPX per day, each a point-to-point between overnight stops, and list the stops. Search for accommodation/food at each stop if asked.

In all cases, prefer quiet, scenic lines per `routing-engines.md`, and tune distance to within ~5% of any target.
