# TODO
- Add gates and entrances to park in osm



# 3-30-300 Athens, based on Treepedia

The repository began as a fork of [Treepedia_Public](https://github.com/mittrees/Treepedia_Public) from the MIT Senseable City Lab. It's a brilliant approach to measuring street trees and I'm grateful for their work. 

### Process

The only change to the process that is really Chicago-specifc is batching the processing by community area. This code begins by downloading shapefiles of the drivable street network within multipolygon boundaries of each community area. The code that follows would still work with any shapefile input. Other than that, since the original project was from 2018, I have upgarded the everything to work with Python 3 and the latest Google APIs.

So far, what I have implemented can be run as follows.

1. Download the street network for an individual community area with:
  ```bash
  python treepedia/download_street_network.py
  ```
  The current default is Community Area #1, Rogers Park. Edit the file to change the community area. 

1. Tag the steet network with evenly spaced points, from which we will grab...
  ```bash
  python treepedia/create_points.py
  ```

1. Metadata.

### Development

To break up the processing, we download the drivable street network and parse streetview data by Chicago Community Area, the official boundaries defined by the city. Conveniently, community area #1, Rogers Park, is one of the smaller boundaries so it's a good one for testing and development.
- [Boundaries - Community Areas (current)](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Community-Areas-current-/cauq-8yn6)

#### Dependencies

1. Before installing dependencies per `requirements.txt`, you must install GDAL.
```bash
brew install gdal
```

2. Check that it has been installed with: 
```bash
gdal-config --version
```

3. Then, you can install gdal with pip, but be sure to specify the same version spit out by the previous command.
```bash
pip install gdal==<version>
```

4. You may then install the rest of the dependencies.
```bash
pip install -r requirements.txt
```

5. Additionally, you will need to manually download and install [pymeanshift](https://github.com/fjean/pymeanshift). To quickly install it within your virtualenv, move the downloaded folder into this directory, `cd` into to, then run `python setup.py install`. Alternatively, if you'd rather store the folder somewhere else, you can still install it within your virtualenv by specifying the python path:
  ```bash
  /home/username/virtualpy/bin/python setup.py install
  ```

### More Work To DO
- For the [Google Street View API](https://developers.google.com/maps/documentation/streetview/metadata), I am currently using an API Key but not a digital signature. Let's set one up.



### SentinelHub

needs a file in ~/.config/sentinelhub/config.toml

[default-profile]
sh_client_id = "sh-xxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
sh_client_secret = "xxxxxxxxxxxxxxxxxx"

[Athens-330300]
instance_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
sh_client_id = "sh-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
sh_client_secret = "xxxxxxxxxxxxxxxxxx"
sh_base_url = "https://sh.dataspace.copernicus.eu"
sh_auth_base_url = "https://identity.dataspace.copernicus.eu"
sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"



# Little Helper funcitons:

Syncing server with local downloads
```bash

rsync -avz /Users/nono/Documents/workspaces/GIS/3-30-300-Athens-Data/spatial-data/panoramas-final nono@10.0.77.26:/home/nono/Documents/workspaces/cpp/darknet/Training/Athens-3-30-300  
```

  

# 
# 
#   
_Below is the original README of [Treepedia_Public](https://github.com/mittrees/Treepedia_Public):_
# Treepedia
Developed by the MIT [Senseable City Lab](https://senseable.mit.edu/), *Treepedia* aims to raise a proactive awareness of urban vegetation improvement, using computer vision techniques applied to Google Street View images. Our focus is on street trees: Treepedia doesn't map parks, as GSV doesn't venture into them as it does on average streets.

*Treepedia* measures and maps the amount of vegetation cover along a city's streets by computing the Green View Index (GVI) on Google Street View (GSV) panoramas. This method considers the obstruction of tree canopies and classifies the images accordingly. The GVI presented here is on a scale of 0-100, showing the percentage of canopy coverage of a particular location. Explore the maps on the [*Treepedia*](http://senseable.mit.edu/treepedia/) website to see how the GVI changes across a city, and how it compares across cities and continents.

The following repo provides a <a href="https://github.mit.edu/abdulhai/Treepedia/wiki/Analyze-Your-City"> library to implement the GVI computation</a> for a city or region defined by a boundary shapefile, given that GSV imagery is available for the street network within it. It also includes documentation of the workflow of the project so that stakeholders, municipalities, researchers or public alike may run the analysis for their cities. We will continue to grow the *Treepedia* database to span cities all over the globe. What does your green canopy look like? If you'd like to answer this question please install this python library and run the analysis for your area. 

If you are a government, researcher or stakeholder that has used this library to compute the GVI for your city and would like us to include a mapping of it on the *Treepedia* website, please contact us at: senseable-trees@mit.edu

<br />

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/img.jpg">
</p>


# Workflow 

The project has the following workflow:

## Step 1: Point Sampling on Street Network of City 
With the street network and boundary shapefile for your city as input, a shapefile containing points every 20m (which can be changed depending on the size of the city) will be generated to be fed into the Google API to retrieve Google Street View Images. 

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img2.jpg">
</p>

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img1.jpg">
</p>

Note that spatial files must be in the projected WGS84 system.

Example:
You can just run the code of "createPoints.py" [here](https://github.com/ianseifs/Treepedia_Public/blob/master/Treepedia/createPoints.py)

python createPoints.py

In the example, I use Cambridge as example. At the buttom of the code, you can specify the input shapefile of the street map, the minimum distance for sampling, and the number of the output shapefile for your cities.



## Step 2: Metadata containing GSV panoID's

With the shapefile as input, metadata containing the panoID, panoDate, latitude, longitude and tilt specifications for the image will be stored in textfiles to be later used to calculate the Green View Index. 

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img3.jpg">
</p>

Example:
You can just run the code of "metadataCollector.py" [here](https://github.com/ianseifs/Treepedia_Public/blob/master/Treepedia/metadataCollector.py)

python metadataCollector.py

The input of this code is created sample site shapefile. In the example, I use Cambridge20m.shp in the sample-spatialdata folder. You can generate your own sample sites based on the createPnt.py. At the buttom of the code, you can specify different sample site file. The batch size is 1000, which means the code will save metadata of every 1000 point to a txt file.



## Step 3: GVI Calculation of points with final shapefile display 
Using Otsu's method and the pymeanshift package, the Green View Index is computed for all 6 images at each sampling point; for each sampling point the GVI values are then averaged to provide a single GVI value for every point along the street network. Finally, a shapefile will be generated containing all attributes, including the GVI, of the points on the street network. 

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img4.jpg">
</p>

Example:

You can just run the code of "GreenView_Calculate.py" [here](https://github.com/ianseifs/Treepedia_Public/blob/master/Treepedia/GreenView_Calculate.py)

python GreenView_Calculate.py

The input of this code is the collected metadata of GSV. By reading the metadat, this code will collect GSV images and segmente the greenery, and calculate the green view index. Considering those GSV images captured in winter are leafless, thiwh are not suitable for the analysis. You also need to specific the green season, for example, in Cambridge, the green months are May, June, July, August, and September.

You can open several process to run this code simutaniously, because the output will be saved as txt files in folder. If the output txt file is already there, then the code will move to the next metadata txt file and generate the GVI for next 1000 points.

After finishing the computing, you can run the code of "Greenview2Shp.py" [here](https://github.com/ianseifs/Treepedia_Public/blob/master/Treepedia/Greenview2Shp.py), and save the result as shapefile, if you are more comfortable with shapefile.


# Dependencies
  * Pyshiftmean package
  * Numpy
  * GDAL
  * PIL
  * Shapely
  * Fiona
  * xmltodict 
  * Python (2.7)

# Contributors
Project Co-Leads: Xiaojiang Li and Ian Seiferling

Researchers: Bill Cai, Marwa Abdulhai

Website and Visualization: Wonyoung So
