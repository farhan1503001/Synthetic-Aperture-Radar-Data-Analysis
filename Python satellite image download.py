import ee
import rasterio
from rasterio.plot import show as showRasterio
import zipfile
import os
import requests
import numpy as np
import matplotlib.pyplot as plt

# Trigger the authentication flow.
ee.Authenticate()

# Initialize the library.
ee.Initialize()


lat =  50.4501
lon =  30.5234
sze = 0.65
filename='Dhaka.tif'

dateMin='2022-04-01'
dateMax = '2022-04-30'

# define the area of interest, using the Earth Engines geometry object
coords = [
     [lon - sze/2., lat - sze/2.],
     [lon + sze/2., lat - sze/2.],
     [lon + sze/2., lat + sze/2.],
     [lon - sze/2., lat + sze/2.],
     [lon - sze/2., lat - sze/2.]
]
aoi = ee.Geometry.Polygon(coords)
# get the image using Google's Earth Engine
collection = ee.ImageCollection('COPERNICUS/S2_SR')\
                   .filterBounds(aoi)\
                   .filterDate(ee.Date(dateMin), ee.Date(dateMax))\
                   .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE',20))
                  



        
mosaic_image=collection.mosaic()
mosaic_image.addBands(ee.Image.pixelLonLat())


print(mosaic_image.bandNames())



bands = ['B4', 'B3', 'B2']   # R->B4, G->B3, B->B2

    # export geotiff images, these go to Drive and then are downloaded locally
for selection in bands:
        task = ee.batch.Export.image.toDrive(image=mosaic_image.select(selection),
                                     description=selection,
                                     scale=30,
                                     region=aoi,
                                     fileNamePrefix=selection,
                                     crs='EPSG:4326',
                                     fileFormat='GeoTIFF')
        task.start()
        url = mosaic_image.select(selection).getDownloadURL({
            'scale': 30,
            'crs': 'EPSG:4326',
            'fileFormat': 'GeoTIFF',
            'region': aoi})
    
        r = requests.get(url, stream=True)

        filenameZip = selection+'.zip'
        filenameTif = selection+'.tif'

        # unzip and write the tif file, then remove the original zip file
        with open(filenameZip, "wb") as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)

        zipdata = zipfile.ZipFile(filenameZip)
        zipinfos = zipdata.infolist()

        # iterate through each file (there should be only one)
        for zipinfo in zipinfos:
            zipinfo.filename = filenameTif
            zipdata.extract(zipinfo)
    
        zipdata.close()
        
    # create a combined RGB geotiff image
    # https://gis.stackexchange.com/questions/341809/merging-sentinel-2-rgb-bands-with-rasterio
print('Creating 3-band GeoTIFF image ... ')
    
    # open the images
B2 = rasterio.open('B2.tif')
B3 = rasterio.open('B3.tif')
B4 = rasterio.open('B4.tif')

    # get the scaling
image = np.array([B2.read(1), B3.read(1), B4.read(1)]).transpose(1,2,0)
p2, p98 = np.percentile(image, (2,98))

    # use the B2 image as a starting point so that I keep the same parameters
B2_geo = B2.profile
B2_geo.update({'count': 3})

with rasterio.open(filename, 'w', **B2_geo) as dest:
        dest.write( (np.clip(B4.read(1), p2, p98) - p2)/(p98 - p2)*255, 1)
        dest.write( (np.clip(B3.read(1), p2, p98) - p2)/(p98 - p2)*255, 2)
        dest.write( (np.clip(B2.read(1), p2, p98) - p2)/(p98 - p2)*255, 3)

        B2.close()
        B3.close()
        B4.close()
    
    # remove the intermediate files
for selection in bands:
      os.remove(selection + '.tif')
      os.remove(selection + '.zip')

f,ax = plt.subplots(figsize=(15,15))

chicago = rasterio.open('Dhaka.tif')
showRasterio(chicago.read(), ax = ax, transform=chicago.transform)

chicago.close()

def get_ndvi(image):
  return image.normalizedDifference(['B8','B3'])

ndvi=get_ndvi(mosaic_image).rename('NDVI')
mosaic_image=mosaic_image.addBands(ndvi)

task = ee.batch.Export.image.toDrive(image=mosaic_image.select('ndvi'),
                                     description='NDVI',
                                     scale=30,
                                     region=aoi,
                                     fileNamePrefix=selection,
                                     crs='EPSG:4326',
                                     fileFormat='GeoTIFF')
task.start()
url = mosaic_image.select('NDVI').getDownloadURL({
            'scale': 30,
            'crs': 'EPSG:4326',
            'fileFormat': 'GeoTIFF',
            'region': aoi})
    
r = requests.get(url, stream=True)
filenameZip = "NDVI"+'.zip'
filenameTif = "NDVI"+'.tif'

        # unzip and write the tif file, then remove the original zip file
with open(filenameZip, "wb") as fd:
  for chunk in r.iter_content(chunk_size=1024):
    fd.write(chunk)

zipdata = zipfile.ZipFile(filenameZip)
zipinfos = zipdata.infolist()

        # iterate through each file (there should be only one)
for zipinfo in zipinfos:
  zipinfo.filename = filenameTif
  zipdata.extract(zipinfo)
zipdata.close()


f,ax = plt.subplots(figsize=(15,15))

ndvi = rasterio.open('NDVI.tif')
showRasterio(ndvi.read(), ax = ax, transform=ndvi.transform)

chicago.close()


def get_ndwi(image):
  expression='(NIR-MIR)/(NIR+MIR)'
  ndwi=image.expression(
      expression=expression,
      opt_map={
          'NIR':image.select('B8'),
          'MIR':image.select('B12')
      }
  )
  return ndwi


ndwi=get_ndwi(mosaic_image).rename("NDWI")
mosaic_image=mosaic_image.addBands(ndwi)


task = ee.batch.Export.image.toDrive(image=mosaic_image.select('NDWI'),
                                     description='NDWI',
                                     scale=30,
                                     region=aoi,
                                     fileNamePrefix=selection,
                                     crs='EPSG:4326',
                                     fileFormat='GeoTIFF')
task.start()
url = mosaic_image.select('NDWI').getDownloadURL({
            'scale': 30,
            'crs': 'EPSG:4326',
            'fileFormat': 'GeoTIFF',
            'region': aoi})
    
r = requests.get(url, stream=True)
filenameZip = "NDWI"+'.zip'
filenameTif = "NDWI"+'.tif'

        # unzip and write the tif file, then remove the original zip file
with open(filenameZip, "wb") as fd:
  for chunk in r.iter_content(chunk_size=1024):
    fd.write(chunk)

zipdata = zipfile.ZipFile(filenameZip)
zipinfos = zipdata.infolist()

        # iterate through each file (there should be only one)
for zipinfo in zipinfos:
  zipinfo.filename = filenameTif
  zipdata.extract(zipinfo)
zipdata.close()


f,ax = plt.subplots(figsize=(15,15))

ndwi = rasterio.open('NDWI.tif')
showRasterio(ndwi.read(), ax = ax, transform=ndwi.transform)

ndwi.close()