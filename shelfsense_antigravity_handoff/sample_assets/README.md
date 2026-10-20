# ShelfSense AI sample assets

These six original, unbranded SVG packshots are bundled as local demo images for the first planogram-editor prototype. They were created specifically for this handoff rather than downloaded from a third-party product listing.

- `catalogue.sample.json` is the recommended seed-data source for the app.
- `catalogue.sample.csv` is an easy-to-edit spreadsheet-style alternative.
- `images/` contains the corresponding product images.

Dimensions are in centimetres and prices are synthetic INR examples. They are illustrative only and must not be treated as real manufacturer/product measurements or prices. Preserve product aspect ratios when rendering; use width and height metadata for physical sizing and use depth for reference/export data.

The app should copy/import these files into its own local product catalogue during explicit seed-data setup, or use them as bundled sample products. Do not assume every user-created product has an SVG: normal image uploads should support common raster formats such as JPEG, PNG, and WebP, with file type/size validation.
