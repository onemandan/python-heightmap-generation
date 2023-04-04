# python-heightmap-generation
Simple Python script to generate a heightmap using PIL and simplex noise

options:
- -h, --help
- --size (REQUIRED) - Size of the resulting heightmap image in pixels size x size
- --seed - (DEFAULT: RAND) - Number to generate the simplex noise generator with
- --mode {L, RGB} - (DEFAULT: "L") - Greyscale or colour
- -f|--frequency - (DEFAULT: 4.0) - How 'zoomed' the heightmap is, lower is more 'zoomed in'
- -o|--octaves - (DEFAULT: 1) - Amount of noise passes when generating the heightmap, higher is slower but more detailed
- -a|--amplitude - (DEFAULT: 1.0) - How 'smooth' the noise is, lower is smoother
- -e|--exponent - (DEFAULT: 1.0) - Pulls middling noise values down, higher increases pull
- -d|--diverse - (DEFAULT: FALSE) - If provided and in RGB mode, creates another heightmap for biome diversity
- -t|--trees  - (DEFAULT: FALSE) - If provided and in RGB mode, populates trees
- -v|--verbose - (DEFAULT: FALSE) - if provided and in RGB mode, provides biome percentage information in the CLI
