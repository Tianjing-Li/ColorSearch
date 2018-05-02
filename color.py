from __future__ import print_function
import argparse
import numpy as np
import glob
import json
from sys import stdout
from skimage import io, color
from colorthief import ColorThief

def pivotxyz(n):
	epsilon = 0.008856 # 216/24389
	kappa = 903.3 # 24389/27

	if n > epsilon:
		return n ** (1.0 / 3)
	else:
		return (kappa * n + 16) / 116

def pivotrgb(n):

	if n > 0.04045:
		return (((n + 0.055) / 1.055) ** 2.4) * 100.0
	else:
		return (n / 12.92) * 100

def xyz2lab(xyz):
	# white reference for calculations
	whiteref = [95.047, 100.000, 108.883]

	x = pivotxyz(xyz[0] / whiteref[0])
	y = pivotxyz(xyz[1] / whiteref[1])
	z = pivotxyz(xyz[2] / whiteref[2])

	L = 116 * y - 16
	A = 500 * (x - y)
	B = 200 * (y - z)

	LAB = [L, A, B]

	return LAB

def rgb2xyz(V):
	# V is a tuple (R,G,B)
	# convert to companded energy vector v, (r,g,b)
	# using inverse gamma companding

	r = pivotrgb(V[0])
	g = pivotrgb(V[1])
	b = pivotrgb(V[2])

	X = r * 0.4124 + g * 0.3576 + b * 0.1805
	Y = r * 0.2126 + g * 0.7152 + b * 0.0722
	Z = r * 0.0193 + g * 0.1192 + b * 0.9505

	return xyz2lab([X, Y, Z])


def convert(palette):
	# convert RGB range to [0, 1] floats
	for i in range(len(palette)):
		palette[i] = [float(val) / 255.0 for val in palette[i]]
	
	LAB = []

	for RGB in palette:
		LAB.append(rgb2xyz(RGB))	

	return LAB

def calcmean(LAB):
	meanL = np.mean([x[0] for x in LAB])
	meanA = np.mean([x[1] for x in LAB])
	meanB = np.mean([x[2] for x in LAB])

	return [meanL, meanA, meanB]

def calcdelta(LAB1, LAB2):
	mean1 = calcmean(LAB1)
	mean2 = calcmean(LAB2)

	deltaL = mean1[0] - mean2[0]
	deltaA = mean1[1] - mean2[1]
	deltaB = mean1[2] - mean2[2]

	deltaE = ((deltaL ** 2) + (deltaA ** 2) + (deltaB ** 2)) ** (1.0 / 2)

	return deltaE

def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--image", required=True)
	ap.add_argument("-j", "--json", required=True)
	args = vars(ap.parse_args())

	JSON = []

	jname = args["json"]
	if not jname.endswith(".json"):
		jname = jname + ".json"

	images = []

	for ext in ("*.jpg", "*.JPG", "*.JPEG"):
		for path in glob.glob(args["image"] + "/" + ext):
			images.append(path)

	for i in range(len(images)):

		item = {}
		item["image_path"] = images[i]
		cf = ColorThief(images[i])

		#dominant = cf.get_color(quality=15)

		palette = cf.get_palette(color_count=4, quality=15)

		LAB = convert(palette)

		item["LAB"] = calcmean(LAB)

		JSON.append(item)

		stdout.write("\r{0}/{1}".format(i, len(images)))
		stdout.flush()

	with open(jname, 'w') as js:
			json.dump(JSON, js, indent=2)
			print ("JSON saved")
	
if __name__ == "__main__":
	main()








