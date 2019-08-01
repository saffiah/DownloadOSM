#!/usr/bin/env python
import os, shutil
from osgeo import gdal, ogr, osr, gdal_array
import numpy as np
import csv
import time
from glob import glob

#need to run this script with /usr/bin/python 

def GetCoors(shpfile):
	os.chdir(shpfile)
	largeTiles=glob('*.shp')
	#North America
	# ['Merge_G07.shp','Merge_G08.shp','Merge_G09.shp','Merge_G010.shp','Merge_G011.shp','Merge_G18.shp','Merge_G19.shp','Merge_G110.shp','Merge_G111.shp']
	
	largeTiles=['Merge_G00.shp'] #Merge_G010.shp
	#europe (need to include other tiles that were included in Africa)
	# ['Merge_G01.shp'] #Merge_G00.shp,'Merge_G02.shp'
	#Asia
	# ['Merge_G03a.shp','Merge_G04.shp','Merge_G05.shp','Merge_G06.shp','G13_2.shp','Merge_G14.shp','Merge_G15a.shp','Merge_G16.shp','Merge_G23.shp','Merge_G24a.shp','Merge_G25.shp','Merge_G26.shp','Merge_G27.shp']
	# Australia/NZ
	# ['Merge_G34.shp','Merge_G35.shp','Merge_G36.shp','Merge_G45.shp','Merge_G46.shp']
	#SouthAmerica + little bit of north America
	# ['Merge_G29.shp','Merge_G210.shp','Merge_G211.shp','Merge_G39.shp','Merge_G310.shp','Merge_G311.shp','Merge_G410.shp','Merge_G411.shp']
	#Africa
	# largeTiles=['Merge_G20.shp','Merge_G21.shp','Merge_G22.shp','Merge_G31.shp','Merge_G32.shp']
	# 'Merge_G10.shp','Merge_G11.shp','Merge_G12.shp'

	CoorList=[]
	for file in largeTiles:
		print file
		#read in the shape file
		driver=ogr.GetDriverByName('ESRI Shapefile')
		shp=driver.Open(file,0)
		layer=shp.GetLayer()
		ext=layer.GetExtent()
		minLon=ext[0]
		maxLon=ext[1]
		minLat=ext[2]
		maxLat=ext[3]
		print ext
		shp=None
		CoorList.append([minLon,maxLon,minLat,maxLat])

	return CoorList

def writeTextFile(minLat,minLon,maxLat,maxLon,fname):
	print minLat,minLon,maxLat,maxLon
	string = '\n'.join([
        '<osm-script output="xml" timeout="2500">',
        '    <union>',
        '        <query type="node">',
        '            <has-kv k="natural" v="water"/>',
        '            <bbox-query e="{0}" n="{1}" w="{2}" s="{3}"/>'.format(maxLon,maxLat,minLon,minLat),
        '        </query>',
        '        <query type="way">',
        '            <has-kv k="natural" v="water"/>',
        '            <bbox-query e="{0}" n="{1}" w="{2}" s="{3}"/>'.format(maxLon,maxLat,minLon,minLat),
        '        </query>',
        '        <query type="relation">',
        '            <has-kv k="natural" v="water"/>',
        '            <bbox-query e="{0}" n="{1}" w="{2}" s="{3}"/>'.format(maxLon,maxLat,minLon,minLat),
        '        </query>',
        '    </union>',
        '    <union>',
        '        <item/>',
        '        <recurse type="down"/>',
        '    </union>',
        '    <print mode="body"/>',
        '</osm-script>'
        ])


	print string

	outfile=fname+'.txt'
	f=open(outfile,'w')
	f.write(string)
	f.close()

def createFilename(minLat,minLon,maxLat,maxLon):

	if minLat<0:
		n_s='s'
		LL_Lat=str(abs(int(minLat)))
		LL_Lat=LL_Lat.zfill(2)
	else:
		n_s='n'
		LL_Lat=str(int(minLat))
		LL_Lat=LL_Lat.zfill(2)
	if minLon<0:
		e_w='w'
		LL_Lon=str(abs(int(minLon)))
		LL_Lon=LL_Lon.zfill(3)
	else:
		e_w='e'
		LL_Lon=str(int(minLon))
		LL_Lon=LL_Lon.zfill(3)

	outfile=n_s+LL_Lat+e_w+LL_Lon

	return outfile

def extractOSM(outname):

	#download osm data from query
	command='wget --wait=1000 --random-wait --timeout=0 -O ' + outname+'.osm'+' --post-file='+outname+'.txt '+'\"http://overpass-api.de/api/interpreter\"'
	print command
	os.system(command)
	
	#convert to shapefile and keep only multipolygons
	command2=('ogr2ogr -overwrite --config OSM_CONFIG_FILE /cygdrive/c/Users/hossainzadehs/Desktop/WorldWideLakes/osmconf.ini '
		+outname+'.shp '+ outname+'.osm '+'-lco ENCODING=UTF-8 -progress -sql "select * from multipolygons"')
	print command2
	os.system(command2)

	#creates outname_NR.shp; 
	#restricts water tags; we want only features that care not rivers, etc
	command3=('ogr2ogr -overwrite '+outname+'_NR.shp '+ outname+'.shp '+
		'-lco ENCODING=UTF-8 -progress -sql "select * from '+outname + ' where (water is null or (water!=\'river\' and water!=\'canal\' and water!=\'oxbow\' and water!=\'riverbank\'))"')
	print command3
	os.system(command3)

	#creates outname_NWW.shp
	#restricts the waterway tag; we don't want riverbanks, etc
	command4=('ogr2ogr -overwrite '+outname+'_NWW.shp '+ outname+'_NR.shp '+
		'-lco ENCODING=UTF-8 -progress -sql "select * from '+outname + '_NR where (waterway is null or (waterway!=\'river\' and waterway!=\'stream\' and waterway!=\'dock\' and waterway!=\'boatyard\' and waterway!=\'ditch\' and waterway!=\'canal\' and waterway!=\'weir\' and waterway!=\'riverbank\'))"')
	print command4
	os.system(command4)

def deleteRest(outname):

	os.remove(outname+'.osm')
	os.remove(outname+'.txt')
	os.remove(outname+'.dbf')
	os.remove(outname+'.prj')
	os.remove(outname+'.shx')
	os.remove(outname+'.cpg')
	os.remove(outname+'.shp')

	
	os.remove(outname+'_NR.dbf')
	os.remove(outname+'_NR.prj')
	os.remove(outname+'_NR.shx')
	os.remove(outname+'_NR.cpg')
	os.remove(outname+'_NR.shp')

	# os.remove(outname+'_NWW.osm')
	# os.remove(outname+'_NWW.txt')
	# os.remove(outname+'_NWW.dbf')
	# os.remove(outname+'_NWW.prj')
	# os.remove(outname+'_NWW.shx')
	# os.remove(outname+'_NWW.cpg')
	# os.remove(outname+'_NWW.shp')


def calcArea(outname):
	driver=ogr.GetDriverByName('ESRI Shapefile')
	data=driver.Open(outname+'_NWW.shp',1)

	layer=data.GetLayer()

	field_defn=ogr.FieldDefn("Round",ogr.OFTReal)
	field_defn.SetWidth(18)
	field_defn.SetPrecision(10)
	layer.CreateField(field_defn)

	field_defn=ogr.FieldDefn("Area",ogr.OFTReal)
	field_defn.SetWidth(18)
	field_defn.SetPrecision(10)
	layer.CreateField(field_defn)

	for feat in layer:
		geom=feat.GetGeometryRef()
		env=geom.GetEnvelope()
		s1=env[1]-env[0]
		s2=env[3]-env[2]
		EnvArea=(s1*s2)
		area=geom.GetArea()
		AreaDiff=EnvArea-area
		perc= AreaDiff/EnvArea
		#Then need to multiply by ratio of smallest side to longest side
		minside=min(s1,s2)
		maxside=max(s1,s2)
		proxy=perc*minside/maxside #add a scale factor essectially; want features that are not 'skinny'
		#if proxy is gt 70% then the lake is round...
		layer.SetFeature(feat)
		feat.SetField("Round",AreaDiff/EnvArea)
		feat.SetField("Area",area)
		layer.SetFeature(feat)

	data=None



if __name__ == '__main__':

    shpfile_dir='/cygdrive/c/Users/hossainzadehs/Desktop/ALOSOutput/MergeGTiles'
    extents=GetCoors(shpfile_dir)

    os.chdir('/cygdrive/c/Users/hossainzadehs/Desktop/WorldWideLakes/natural_water')
    count=0
    # rangeGrid=range(3400,3700)
    totNumCells=len(extents)

    for i in range(totNumCells):
    	print 'Executing file ', i
    	minLon=extents[i][0]
    	maxLon=extents[i][1]
    	minLat=extents[i][2]
    	maxLat=extents[i][3]
    	print minLon,maxLon,minLat,maxLat

    	# minLon=90
    	# maxLon=120
    	# minLat=20
    	# maxLat=50
    	# minLon=0 #15
    	# maxLon=15 #30
    	# minLat=50
    	# maxLat=65
    	outname=createFilename(minLat,minLon,maxLat,maxLon)
    	#below will create a filename called outname+'.txt'
    	writeTextFile(minLat,minLon,maxLat,maxLon,outname)
		
        extractOSM(outname)
        # os.chdir('SecondaryExamples')
        calcArea(outname)

        #creates outname_LL.shp (large lakes only)
        #restrict by area
        command4=('ogr2ogr -overwrite '+outname+'_LLNew.shp '+ outname+'_NWW.shp '+
        	'-lco ENCODING=UTF-8 -progress -sql "select * from '+outname + '_NWW where (Area>0.040 or (Area> 0.01 and Round > 0.7))"')
        print command4
        os.system(command4)

        time.sleep(10)
        deleteRest(outname)

        count+=1

        
        
    	



