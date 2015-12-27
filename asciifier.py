#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Convert an image to ASCII art.
#
# Copyright (c) 2015 Oliver Lau <ola@ct.de>, Heise Medien GmbH & Co. KG
# All rights reserved.

from PIL import Image, ImageFont, ImageDraw, ImageColor
from datetime import datetime
from math import ceil
import string
import argparse


class Asciifier:
    PAPER_SIZES = {
        'a6': (105, 148),
        'a5': (148, 210),
        'a4': (210, 297),
        'a3': (297, 420),
        'a2': (420, 594),
        'a1': (594, 841),
        'a0': (841, 1189),
        'letter': (215.9, 279.4)
    }
    TYPE_CHOICES = ['text', 'postscript']
    PAPER_CHOICES = PAPER_SIZES.keys()
    result = [[]]
    margins = (10, 10)
    im = None
    luminosity = ['B', '@', 'M', 'Q', 'W', 'N', 'g', 'R', 'D', '#', 'H', 'O', '&', '0', 'K', '8', 'U', 'd', 'b', '6',
                  'p', 'q', '9', 'G', 'E', 'A', '$', 'm', 'h', 'P', 'Z', 'k', 'X', 'S', 'V', 'a', 'e', '5', '4', '3',
                  'y', 'w', '2', 'F', 'I', 'o', 'u', 'n', 'j', 'C', 'Y', '1', 'f', 't', 'J', '{', '}', 'z', '%', 'x',
                  'T', 's', 'l', '7', 'L', '[', 'v', ']', 'i', 'c', '=', ')', '(', '+', '|', '<', '>', 'r', '?', '*',
                  '/', '!', ';', '~', '-', ':', '.', ' ']

    def __init__(self, font_file):
        if font_file is not None:
            self.generate_luminosity_mapping(font_file)

    @staticmethod
    def mm_to_pt(mm):
        return 2.834645669 * mm

    def generate_luminosity_mapping(self, font_file):
        n = 64
        image_size = (n, n)
        font = ImageFont.truetype(font_file, int(3 * n / 4))
        self.luminosity = []
        intensity = []
        for c in range(32, 127):
            image = Image.new('RGB', image_size, ImageColor.getrgb('#ffffff'))
            draw = ImageDraw.Draw(image)
            draw.text((0, 0), chr(c), font=font, fill=(0, 0, 0))
            l = 0
            for pixel in image.getdata():
                r, g, b = pixel
                l += 0.2126 * r + 0.7152 * g + 0.0722 * b
            intensity.append({l: l, c: chr(c)})
        self.luminosity = map(lambda i: i['c'], sorted(intensity, key=lambda lum: lum['l']))

    def to_plain_text(self):
        txt = zip(*self.result)
        return "\n".join([''.join(line).rstrip() for line in txt])

    def to_postscript(self, **kwargs):
        paper = kwargs.get('paper', 'a4')
        font_name = kwargs.get('font_name', 'Hack-Bold')
        paper_size = self.PAPER_SIZES[string.lower(paper)]
        paper_width_pt = Asciifier.mm_to_pt(paper_size[0])
        paper_height_pt = Asciifier.mm_to_pt(paper_size[1])
        size_pt = (ceil(paper_width_pt - 2 * Asciifier.mm_to_pt(self.margins[0])),
                   ceil(paper_height_pt - 2 * Asciifier.mm_to_pt(self.margins[1])))
        width_pt = size_pt[0]
        height_pt = size_pt[1]
        grid_pt = 12
        font_pt = 12
        size = self.im.width * grid_pt, self.im.height * grid_pt
        w, h = size
        scale = width_pt / w
        now = datetime.today()
        offset = (self.margins[0] + (width_pt - w * scale) / 2, self.margins[1] + (height_pt - h * scale) / 2)
        lines = [
            "%!PS-Adobe-3.0",
            "%%%%BoundingBox: 0 0 %d %d" % size,
            "%%Creator: asciifier",
            "%%%%CreationDate: %s" % now.isoformat(),
            "%%%%DocumentMedia: %s %d %d 80 white ()" % (paper, paper_width_pt, paper_height_pt),
            "%%Pages: 1",
            "%%EndComments",
            "%%BeginSetup",
            "  % A4, unrotated",
            "  << /PageSize [%d %d] /Orientation 0 >> setpagedevice" % (paper_width_pt, paper_height_pt),
            "%%EndSetup",
            "%Copyright: Copyright (c) 2015 Oliver Lau <ola@ct.de>, Heise Medien GmbH & Co. KG",
            "%Copyright: All rights reserved.",
            "% Image converted to ASCII by asciifier.py (https://github.com/ola-ct/asciifier)",
            "",
            "/%s findfont" % font_name,
            "%d scalefont" % font_pt,
            "setfont",
            "",
            "/c { moveto show } def",
            "",
            "%d %d translate" % offset,
            "%f %f scale" % (scale, scale)
        ]
        for y in range(0, self.im.height):
            for x in range(0, self.im.width):
                c = self.result[x][y]
                if c != ' ':
                    c = string.replace(c, '\\', "\\\\")
                    c = string.replace(c, '(', "\\(")
                    c = string.replace(c, ')', "\\)")
                    lines.append("(%s) %d %d c" % (c, x * grid_pt, (self.im.height - y) * grid_pt))

        lines += [
            "",
            "showpage"
        ]
        return "\n".join(lines)

    def process(self, image_filename, **kwargs):
        self.im = Image.open(image_filename)
        if 'aspect_ratio' in kwargs:
            self.im = self.im.resize((int(self.im.width * kwargs['aspect_ratio']), self.im.height), Image.BILINEAR)
        resolution = kwargs.get('resolution', 80)
        self.im.thumbnail((resolution, self.im.height), Image.ANTIALIAS)
        w, h = self.im.size
        nchars = len(self.luminosity)
        self.result = [x[:] for x in [[' '] * h] * w]
        for x in range(0, w):
            for y in range(0, h):
                r, g, b = self.im.getpixel((x, y))
                l = 0.2126 * r + 0.7152 * g + 0.0722 * b
                self.result[x][y] = self.luminosity[int(l * nchars / 255)]


def main():
    parser = argparse.ArgumentParser(description='Convert images to ASCII art.')
    parser.add_argument('--image', type=str, help='file name of image to be converted')
    parser.add_argument('--out', type=str, help='file name of postscript file to write.')
    parser.add_argument('--type', type=str, choices=Asciifier.TYPE_CHOICES, help='output type.')
    parser.add_argument('--aspect', type=float, help='aspect ratio of terminal font.')
    parser.add_argument('--font', type=str, help='file name of font to be used.')
    parser.add_argument('--paper', type=str, choices=Asciifier.PAPER_CHOICES, help='paper size.')
    parser.add_argument('--resolution', type=int, help='number of characters per line.')
    args = parser.parse_args()

    font_path = args.font
        
    asciifier = Asciifier(font_path)

    output_type = 'text'
    if args.out is not None and args.out.endswith('.ps'):
            output_type = 'postscript'
    if args.type == 'postscript':
        output_type = 'postscript'

    aspect_ratio = 2.0
    if args.aspect is not None:
        aspect_ratio = args.aspect

    resolution = 80
    if args.resolution is not None:
        resolution = args.resolution

    if output_type == 'text':
        asciifier.process(args.image, resolution=resolution, aspect_ratio=aspect_ratio)
        result = asciifier.to_plain_text()
    elif output_type == 'postscript':
        asciifier.process(args.image, resolution=resolution)
        result = asciifier.to_postscript(paper=args.paper, font_name=args.psfont)
    else:
        result = ''

    if args.out is None:
        print result
    else:
        with open(args.out, 'w+') as f:
            f.write(result)


if __name__ == '__main__':
    main()
