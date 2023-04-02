from PIL import Image
from alive_progress import alive_bar
import argparse
import random
import opensimplex as simplex
import numpy as np

#Colour thresholds
_colours = {
    "water": {
        "min": (4, 13, 54),
        "max": (82, 106, 210)
    },
    "sand": {
        "min": (239, 228, 122),
        "max": (199, 165, 39)
    },
    "grass": {
        "min": (36, 163, 70),
        "max": (3, 66, 20)
    },
    "rock": {
        "min": (61, 48, 40),
        "max": (135, 127, 122)
    },
    "snow": {
        "min": (219, 219, 219),
        "max": (255, 255, 255)
    }
}

#ArgumentParser
_parser = argparse.ArgumentParser()
_parser.add_argument("--size", type=int, required=True)
_parser.add_argument("--seed", type=int, default=int(random.random() * 1000))
_parser.add_argument("--mode", choices=["L", "RGB"], default="L")
_parser.add_argument("-f", "--frequency", type=float, default=4.0)
_parser.add_argument("-o", "--octaves", type=int, default=1)
_parser.add_argument("-a", "--amplitude", type=float, default=1.0)
_parser.add_argument("-e", "--exponent", type=float, default=1.0)
_args = _parser.parse_args()

#generate_image
#Creates an image from a heightmap array
def generate_image(mode, size, heightmap):
    img = Image.new(mode, (size[1], size[0]))

    for y in range(0, size[1]):
        for x in range(0, size[0]):
            if mode == "L":
                img.putpixel((x, y), int(heightmap[y, x] * 255))
            elif mode == "RGB":
                img.putpixel((x, y), get_colour(heightmap[y, x]))

    img.save("heightmap.png")
    img.show()

#scale_number
#Scale a number from one range to another
def scale_number(unscaled, to_min, to_max, from_min, from_max):
    return (to_max-to_min) * (unscaled-from_min) / (from_max-from_min) + to_min

#band_colour
#Return a banded colour based on min and max colour values
def band_colour(min, max, val, colour):
    rgb = [0, 0, 0]

    for i in range(0, 3):
        rgb[i] = int(scale_number(val, colour["min"][i], colour["max"][i], min, max))

    return tuple(rgb)

#get_colour
#Return a banded colour based on height and thresholds
def get_colour(height):
    if height <= 0.2:
        return band_colour(0, 0.2, height, _colours["water"])
    elif height <= 0.3:
        return band_colour(0.2, 0.3, height, _colours["sand"])
    elif height <= 0.75:
        return band_colour(0.3, 0.75, height, _colours["grass"])
    elif height <= 0.9:
        return band_colour(0.75, 0.9, height, _colours["rock"])
    else:
        return band_colour(0.9, 1, height, _colours["snow"])

#noise
#Produce a noise value depending on an amount of octaves and their corresponding amplitude
def noise(nx, ny, amps, exp):
    #sn
    #Rescale simplex noise output from -1.0:+1.0 to 0.0:1.0
    def sn(nx, ny):
        return simplex.noise2(nx, ny) / 2.0 + 0.5
    
    e = ampTotal = 0

    #Iterate amplitude values for each octave
    for amp in amps:
        ampDiv = 1 / amp
        ampTotal += ampDiv

        #Sample different areas of noise to avoid correlation
        e += ampDiv * sn(nx * amp, ny * amp)

    return (e / ampTotal) ** exp

#normalise_heightmap
#Rescales noise values depending on @min and @max to the 0 to 1 range
def normalise_heightmap(min, max, size, heightmap):
    scale = max - min
    for y in range(0, size[1]):
        for x in range(0, size[0]):
            heightmap[y,x] = (heightmap[y,x] - min) / scale

    return heightmap

#generate_heightmap
#Creates a numPy array of noise values
def generate_heightmap(mode, seed, size, freq, amps, exp):
    simplex.seed(seed)
    heightmap = np.zeros(size)

    min = 1
    max = 0
    freqX = size[0] / freq
    freqY = size[1] / freq

    with alive_bar(size[0] * size[1]) as bar:
        for y in range(0, size[1]):
            for x in range(0, size[0]):
                nx = x / freqX
                ny = y / freqY
                nv = noise(nx, ny, amps, exp)
                heightmap[y,x] = nv

                if nv < min:
                    min = nv
                if nv > max:
                    max = nv

                bar()
   
    generate_image(mode, size, normalise_heightmap(min, max, size, heightmap))

#main
#Obtain arguments from the arparse parser and call @generate_heightmap
def main():
    size = (_args.size, _args.size)
    seed = _args.seed
    freq = _args.frequency
    oct = _args.octaves
    amp = _args.amplitude
    exp = _args.exponent
    mde = _args.mode

    amps = np.arange(1.0, oct + 1)
    if amp > 1:
        for i in range(1, oct):
            amps[i] = (amps[i - 1]) * amp

    generate_heightmap(mde, seed, size, freq, amps, exp)
    print("Heightmap generated, seed:", seed)

if __name__ == "__main__":
    main()