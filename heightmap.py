from PIL import Image
from alive_progress import alive_bar
from enum import Enum
from tabulate import tabulate
import argparse
import random
import opensimplex as simplex
import numpy as np

#Colour modes
_mode = Enum("Mode", "L RGB")

#Biome colours: { [R,G,B], TD (tree density)}
_biome = {
    "BEACH":                        { "RGB": [160, 144, 119], "TD": 0 },
    "OCEAN":                        { "RGB": [68,  68 , 122], "TD": 0 },
    "SHALLOW_OCEAN":                { "RGB": [105, 105, 168], "TD": 0 },
    "DEEP_OCEAN":                   { "RGB": [54 , 54 , 94 ], "TD": 0 },
    "SCORCHED":                     { "RGB": [85 , 85 , 85 ], "TD": 0 },
    "BARE":                         { "RGB": [136, 136, 136], "TD": 0 },
    "TUNDRA":                       { "RGB": [187, 187, 170], "TD": 1 },
    "SNOW":                         { "RGB": [221, 221, 228], "TD": 0 },
    "TEMPERATE_DESERT":             { "RGB": [201, 210, 155], "TD": 0 },
    "SHRUBLAND":                    { "RGB": [136, 153, 119], "TD": 5 },
    "TAIGA":                        { "RGB": [153, 170, 119], "TD": 7 },
    "GRASSLAND":                    { "RGB": [136, 170, 85 ], "TD": 8 },
    "TEMPERATE_DECIDUOUS_FOREST":   { "RGB": [103, 148, 89 ], "TD": 9 },
    "TEMPERATE_RAIN_FOREST":        { "RGB": [68 , 136, 85 ], "TD": 10},
    "SUBTROPICAL_DESERT":           { "RGB": [210, 185, 139], "TD": 2 },
    "TROPICAL_SEASONAL_FOREST":     { "RGB": [85 , 153, 68 ], "TD": 9 },
    "TROPICAL_RAIN_FOREST":         { "RGB": [51 , 119, 85 ], "TD": 10}
}

#Max tree density within the biomes
_max_tree_density = 10

#ArgumentParser
_parser = argparse.ArgumentParser()
_parser.add_argument("--size", type=int, required=True)
_parser.add_argument("--seed", type=int, default=int(random.random() * 1000))
_parser.add_argument("--mode", choices=["L", "RGB"], default="L")
_parser.add_argument("-b", "--blend", type=int, choices=[0, 4, 8], default = 0)
_parser.add_argument("-f", "--frequency", type=float, default=4.0)
_parser.add_argument("-o", "--octaves", type=int, default=1)
_parser.add_argument("-a", "--amplitude", type=float, default=1.0)
_parser.add_argument("-e", "--exponent", type=float, default=1.0)
_parser.add_argument("-d", "--diverse", action="store_true")
_parser.add_argument("-t", "--trees", action="store_true")
_parser.add_argument("-v", "--verbose", action="store_true")
_args = _parser.parse_args()

#neighbours
#Obtains an amount of adjacent elements within an array based on @count
def neighbours(x, y, arr, count):
    nb = [arr[y, x]]

    if count > 0:
        if y - 1 > 0: nb.append(arr[y - 1, x]) #North
        if x + 1 < len(arr[0]): nb.append(arr[y, x + 1]) #East
        if y + 1 < len(arr): nb.append(arr[y + 1, x]) #South
        if x - 1 > 0: nb.append(arr[y, x - 1]) #West

        if count > 4:
            if y - 1 > 0 and x + 1 < len(arr[0]): nb.append(arr[y - 1, x + 1]) #Northeast
            if y + 1 < len(arr) and x + 1 < len(arr[0]): nb.append(arr[y + 1, x + 1]) #Southeast
            if y + 1 < len(arr) and x - 1 > 0: nb.append(arr[y + 1, x - 1]) #Southwest
            if y - 1 > 0 and x - 1 > 0: nb.append(arr[y - 1, x - 1]) #Northwest

    return nb

#biome_colour
#Return a biome colour based on height (@z) and moisture (@m) values
def biome(z, m):
    if z < 0.05: return "DEEP_OCEAN"
    if z < 0.08: return "OCEAN"
    if z < 0.1: return "SHALLOW_OCEAN"
    if z < 0.11: return "BEACH"
    
    if z > 0.8:
        if m < 0.1: return "SCORCHED"
        if m < 0.2: return "BARE"
        if m < 0.5: return "TUNDRA"
        return "SNOW"

    if z > 0.6:
        if m < 0.33: return "TEMPERATE_DESERT"
        if m < 0.66: return "SHRUBLAND"
        return "TAIGA"

    if z > 0.3:
        if m < 0.16: return "TEMPERATE_DESERT"
        if m < 0.40: return "GRASSLAND"
        if m < 0.60: return "TEMPERATE_DECIDUOUS_FOREST"
        return "TEMPERATE_RAIN_FOREST"

    if m < 0.16: return "SUBTROPICAL_DESERT"
    if m < 0.23: return "GRASSLAND"
    if m < 0.66: return "TROPICAL_SEASONAL_FOREST"
    return "TROPICAL_RAIN_FOREST"

#output_biome_details
#Counts individual biomes present in @biomemap and outputs their percentage
def output_biome_details(size, biomemap):
    total = size[0] * size[1]
    bd = {}

    for y in range(0, size[1]):
            for x in range(0, size[0]):
                b = biomemap[y, x].replace("_", " ").lower().title()

                #Count biomes
                bd[b] = 1 if not b in bd else bd[b] + 1
    
    #Convert counts into percentages
    for k in bd.keys():
        bd[k] = (bd[k] / total) * 100

    sbd = sorted(bd.items(), key = lambda x: x[1], reverse = True)
    print(tabulate(sbd, headers=["Biome", "Coverage (%)"], floatfmt=".2f", tablefmt="outline"))

#noise
#Produce a noise value depending on an amount of octaves and its corresponding amplitude
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
            heightmap[y, x] = (heightmap[y, x] - min) / scale

    return heightmap

#generate_heightmap
#Creates a numPy array of noise values
def generate_heightmap(seed, size, freq, amps, exp):
    simplex.seed(seed)
    heightmap = np.zeros(size)

    min = 1
    max = 0
    freqX = size[0] / freq
    freqY = size[1] / freq

    with alive_bar(size[0] * size[1]) as bar:
        bar.text("Generating heightmap")
        for y in range(0, size[1]):
            for x in range(0, size[0]):
                nx = x / freqX
                ny = y / freqY
                nv = noise(nx, ny, amps, exp)
                heightmap[y, x] = nv

                if nv < min:
                    min = nv
                if nv > max:
                    max = nv

                bar()
   
    return normalise_heightmap(min, max, size, heightmap)

#generate_treemap
#Creates a numPy array of RGB values based on @colourmap and places black pixels in specific positions determined by the biome
#obtained from @heightmap and @moisturemap and values of @noisemap 
def generate_treemap(size, noisemap, biomemap, colourmap):
    treemap = np.zeros((*size, 3))

    with alive_bar(size[0] * size[1]) as bar:
        bar.text("Generating treemap")
        for y in range(0, size[1]):
                for x in range(0, size[0]):
                    max = 0
                    td = _biome[biomemap[y, x]]["TD"]

                    if td > 0:
                        #Invert tree density value, lower radius to search equals more trees
                        density = (_max_tree_density + 1) - td

                        #Loop over a radius (determined by tree density) of the current y, x element
                        for dy in range(-density, density + 1):
                            for dx in range(-density, density + 1):
                                xn = dx + x
                                yn = dy + y

                                #Ensure element is within bounds
                                if yn > 0 and yn < size[1] and xn > 0 and xn < size[0]:
                                    nv = noisemap[yn][xn]
                                    if nv > max: max = nv
                        
                        treemap[y][x] = [0, 0, 0] if noisemap[y][x] == max else colourmap[y][x]
                    else:
                        treemap[y][x] = colourmap[y][x]

                    bar()
    
    return treemap

#generate_blendmap
#Creates a numPy array of averaged RGB values based on @colourmap and the amount of neighbours to obtain provided by @blnd
def generate_blendmap(blnd, size, colourmap):
    blendmap = np.zeros((*size, 3))

    with alive_bar(size[0] * size[1]) as bar:
        bar.text("Generating blendmap")
        for y in range(0, size[1]):
            for x in range(0, size[0]):
                nb = neighbours(x, y, colourmap, blnd)
                blendmap[y, x] = np.average(nb, axis = 0).astype(int)
                bar()
    
    return blendmap

#generate_colourmap
#Creates a numPy array of RGB values based on @biomemap
def generate_colourmap(size, biomemap):
    colourmap = np.zeros((*size, 3))

    for y in range(0, size[1]):
            for x in range(0, size[0]):
                colourmap[y, x] = _biome[biomemap[y, x]]["RGB"]

    return colourmap

#generate_biomemap
#Creates a numPy array of biomes based on @heightmap and @moisturemap
def generate_biomemap(size, heightmap, moisturemap):
    biomemap = np.empty(size, dtype = object)

    for y in range(0, size[1]):
            for x in range(0, size[0]):
                biomemap[y, x] = biome(heightmap[y, x], moisturemap[y, x])

    return biomemap

#generate_imagemap
#Convert a heightmap to colour values based on @mode
def generate_imagemap(mode, seed, size, freq, amps, exp, div, blnd, tree, ver):
    heightmap = generate_heightmap(seed, size, freq, amps, exp)

    if mode == _mode.L:
        return heightmap * 255
    elif mode == _mode.RGB:
        moisturemap = generate_heightmap(seed + 1, size, freq, amps, exp) if div else np.flip(np.flip(heightmap, 0), 1)
        biomemap = generate_biomemap(size, heightmap, moisturemap)
        colourmap = generate_colourmap(size, biomemap) if blnd == 0 else generate_blendmap(blnd, size, generate_colourmap(size, biomemap))
        finalmap = generate_treemap(size, generate_heightmap(seed, size, size[0], [1.0], 1), biomemap, colourmap) if tree else colourmap

        print("\nHeightmap generated, seed:", seed)
        if ver: output_biome_details(size, biomemap)
        
        return finalmap

#generate_image
#Creates an image from an array of colours
def generate_image(mode, colourmap):
    img = Image.fromarray(colourmap.astype("uint8"), mode.name)
    img.save("heightmap.png")
    img.show()

#main
#Obtain arguments from @_args and call generate_image
def main():
    size = (_args.size, _args.size)
    mode = _mode[_args.mode]
    seed = _args.seed
    freq = _args.frequency
    blnd = _args.blend
    tree = _args.trees
    oct = _args.octaves
    amp = _args.amplitude
    exp = _args.exponent
    div = _args.diverse
    ver = _args.verbose

    amps = np.arange(1.0, oct + 1)
    if amp > 1:
        for i in range(1, oct):
            amps[i] = (amps[i - 1]) * amp

    generate_image(mode, generate_imagemap(mode, seed, size, freq, amps, exp, div, blnd, tree, ver))

if __name__ == "__main__":
    main()