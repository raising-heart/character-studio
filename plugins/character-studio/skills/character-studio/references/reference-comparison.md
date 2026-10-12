# Reference comparisons

Inspect the actual images. Use the reference's silhouette and head/body, torso/leg and footwear relationships to guide construction. Keep comparison cameras and scale fixed between revisions. A pose change or perspective difference can change the outline even when the geometry is correct. Compare neutral construction views for joints, and a reference-like pose for visual similarity.

The optional local tool needs Python with Pillow. Use an existing trusted environment; it does not install packages or contact a service. If Pillow is unavailable, compare images directly or use Blender views instead.

```text
python <skill>/scripts/compare_reference.py --reference <supplied-image> --render <actual-render> --reference-crop X Y WIDTH HEIGHT --output <new-prefix>
```

The crop is explicit and must lie inside the image. It does not remove a forest, companion animal or other background automatically. The tool produces a labelled comparison and JSON report with no numerical score by default.

For a controlled silhouette check, supply `--reference-mask` and `--render-mask`: white foreground, black background, dimensions matching their source images. Align pose/camera and subject scale first. The tool produces red reference-only, green render-only and yellow shared coverage plus silhouette IoU. This is 2D coverage of supplied masks, not likeness, animation quality or reconstruction success. Do not impose a universal pass threshold or derive a mask from a busy background without reviewing it.

Use close-ups for eyes, neckline, braids, boots and suspect intersections. For each correction, record the visible defect, changed parameters/geometry and new preview. Stop once the requested checks pass; report uncertainty where one image cannot define the back/hidden parts.
