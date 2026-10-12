"""Local reference comparison. Optional Pillow dependency; no downloads.

Metrics need explicit foreground masks and compatible pose/camera. A background
scene or a T-pose versus a posed screenshot must not become a likeness score.
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

Image.MAX_IMAGE_PIXELS = 16_000_000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', required=True, type=Path)
    parser.add_argument('--render', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='output filename prefix')
    parser.add_argument('--reference-crop', nargs=4, type=int, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'))
    parser.add_argument('--reference-mask', type=Path)
    parser.add_argument('--render-mask', type=Path)
    parser.add_argument('--size', type=int, default=512)
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    if not 128 <= args.size <= 1024:
        parser.error('size must be 128–1024')
    if bool(args.reference_mask) != bool(args.render_mask):
        parser.error('provide both masks, or neither')
    inputs = [p.resolve() for p in (args.reference, args.render, args.reference_mask, args.render_mask) if p]
    outputs = [Path(str(args.output) + suffix).resolve() for suffix in ('-comparison.png', '-report.json')]
    if args.reference_mask:
        outputs.append(Path(str(args.output) + '-mask-overlay.png').resolve())
    if set(inputs) & set(outputs) or (not args.overwrite and any(p.exists() for p in outputs)):
        parser.error('refusing to overwrite an input or existing output')
    images = []
    originals = []
    for path in (args.reference, args.render):
        with Image.open(path) as image:
            originals.append(image.size)
            images.append(image.convert('RGB'))
    crop = None
    if args.reference_crop:
        x, y, w, h = args.reference_crop
        if min(x, y) < 0 or min(w, h) < 1 or x + w > images[0].width or y + h > images[0].height:
            parser.error('reference crop is outside the image')
        crop = (x, y, x + w, y + h)
        images[0] = images[0].crop(crop)
    frame = (args.size, args.size)
    fitted = [ImageOps.pad(image, frame, color='#243943', method=Image.Resampling.LANCZOS) for image in images]
    sheet = Image.new('RGB', (args.size * 2, args.size + 36), '#15212b')
    for index, image in enumerate(fitted):
        sheet.paste(image, (index * args.size, 36))
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), 'Reference (crop; hidden details inferred)', fill='white')
    draw.text((args.size + 12, 12), 'Actual Blender render / GLB preview', fill='white')
    metrics = None
    if args.reference_mask:
        masks = []
        for index, path in enumerate((args.reference_mask, args.render_mask)):
            with Image.open(path) as image:
                if image.size != originals[index]:
                    parser.error('mask dimensions must match their source image')
                mask = image.convert('L')
                if index == 0 and crop:
                    mask = mask.crop(crop)
                masks.append(ImageOps.pad(mask, frame, color=0, method=Image.Resampling.NEAREST))
        a, b = [[value > 127 for value in mask.getdata()] for mask in masks]
        intersection = sum(x and y for x, y in zip(a, b))
        union = sum(x or y for x, y in zip(a, b))
        if union == 0:
            parser.error('foreground masks are empty')
        metrics = {'silhouette_iou': intersection / union,
                   'meaning': '2D coverage of supplied masks in this framing, not identity or success probability'}
        overlay = Image.new('RGB', frame)
        overlay.putdata([(230, 201, 72) if x and y else (231, 76, 70) if x else (66, 190, 121) if y else (21, 33, 43) for x, y in zip(a, b)])
        outputs[2].parent.mkdir(parents=True, exist_ok=True)
        overlay.save(outputs[2])
    outputs[0].parent.mkdir(parents=True, exist_ok=True)
    sheet.save(outputs[0])
    report = {'reference': str(args.reference.resolve()), 'render': str(args.render.resolve()),
              'reference_crop': args.reference_crop, 'metrics': metrics,
              'limitations': ['Single images leave hidden geometry uncertain.', 'Camera, framing and pose differences require visual interpretation.'],
              'comparison': str(outputs[0])}
    outputs[1].write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
