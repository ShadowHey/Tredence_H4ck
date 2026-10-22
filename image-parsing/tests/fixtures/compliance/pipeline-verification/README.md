# Pipeline verification shelf fixture

This fixture pairs the original Output #7 shelf photo with the frozen shelf planogram
and the operator-reviewed expected outcomes. `manifest.json` records provenance,
row/SKU ground truth, and the requested alert policy.

The ground truth is intentionally scoped to product rows and expected findings. It is
not a bounding-box labeling set: do not report detector AP/precision/recall from this
fixture. The photo is useful for an end-to-end smoke/regression run and for comparing
whether known rows and alert policies behave as expected. A future detector benchmark
needs reviewed pixel coordinates for each visible facing, including occlusion/edge
cases, saved in a separate annotation file.

The frozen planogram has four top-to-bottom rows, 15 expected facings per row, and a
120 cm usable width. Rows map to Amul Milk Chocolate (BEV-200), Yellow Lays (BEV-201),
Orange Juice (BEV-202), and Fresh Laundry Liquid (BEV-203), respectively.
