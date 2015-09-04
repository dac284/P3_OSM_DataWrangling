#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
import sys
import audit

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
diego_re = re.compile('diego', re.IGNORECASE)
usa_re = re.compile('us', re.IGNORECASE)
ca_re = re.compile('(?<!baja\W)ca', re.IGNORECASE)

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

def check_bounds(osmfile):
	# get the bounds of the city
	bounds = {}
	for _, element in ET.iterparse(osmfile):
		if element.tag == "bounds":
			for key, value in element.attrib.iteritems():
				bounds[key] = value
			return bounds
		return False

def inbounds(elem, bounds):
	# check if current element falls within bounds
	try:
		if elem.attrib['lat'] <= maxlat & elem.attrib['lat'] >= minlat & elem.attrib['lon'] <= maxlon & elem.attrib['lon'] >= minlon:
			return True
		else:
			print "Element OOB: {0}".format(elem)
			return False
	except:
		return True # need to check if ways have lat/lon and figure out what to do here
		
def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        node['type'] = element.tag
        created = {}
        
        # create position key from lat lon data
        try:
            node['pos'] = [float(element.attrib['lat']), float(element.attrib['lon'])]
        except:
            pass
        
        # Process attributes of node/way tag
        for k,v in element.attrib.iteritems():
        	# but creation data in sub-dictionary
            if k in CREATED:
                created[k] = v
                node['created'] = created
            #ignore lat, lon (already processed)
            elif k in ['lat', 'lon']:
                continue 
            # other attributes
            else:
                node[k] = v
        
        # Process child 'tag' tags
        for tag in element.iter('tag'):
        
        	# skip tags where the key contains problem characters - write to error file?
            if problemchars.search(tag.attrib['k']):
                continue
        
        	# Check for address tags
            elif re.compile(r'addr:').match(tag.attrib['k']):
                if not ('address' in node):
                    node['address'] = {}
                if lower_colon.search(tag.attrib['k'][5:]):
                    continue

                # Need to clean street names/zip if applicable
                if audit.is_street_name(tag):
                    name = audit.update_name(tag.attrib['v'])
                    node['address'][tag.attrib['k'][5:]] = name
                elif audit.is_zip(tag):
                    zip = clean_zip(tag.attrib['v'])
                    #if zip == "Bad Zip":                           
                    #    continue
                    node['address'][tag.attrib['k'][5:]] = zip
                else:
                    node['address'][tag.attrib['k'][5:]] = tag.attrib['v']
        
            # Check for is_in tags
            elif re.compile(r'is_in').match(tag.attrib['k']):
                if not ('is_in' in node):
                    node['is_in'] = {}
                
                # split 'is_in' list values into appropriate keys
                if tag.attrib['k'] == 'is_in':
                    if diego_re.search(tag.attrib['v']): #compile diego regx
                        node['is_in']['city'] = 'San Diego'
                    if usa_re.search(tag.attrib['v']):
                        node['is_in']['country'] = 'United States of America'
                        node['is_in']['country_code'] = 'US'
                    if ca_re.search(tag.attrib['v']):
                        node['is_in']['state'] = 'California'
                        node['is_in']['state_code'] = 'CA'
                    if node['is_in'] == {}:
                        node['is_in']['city'] = tag.attrib['v'] #catch for baja and lakeside
                elif lower_colon.search(tag.attrib['k']):
                    key, val = clean_is_in(tag)
                    node['is_in'][key] = val

            # Check for GNIS data - including ele tag
            elif audit.is_gnis(tag):
                if not ('gnis' in node):
                    node['gnis'] = {}
                key, val = clean_gnis(tag)
                node['gnis'][key] = val


            # all other tags - be careful that 'type' does not get overwritten here
            elif tag.attrib['k'] == 'type':
            	node['tag_type'] = tag.attrib['v']
            else:
                node[tag.attrib['k']] = tag.attrib['v']
        
        # node_refs for ways        
        if element.tag == "way" :
            node['node_refs'] = []
            for nd in element.iter('nd'):
                node['node_refs'].append(nd.attrib['ref'])
        return node
    else:
        return None #relations not returned?


def process_map(file_in, pretty = False):
    bounds = check_bounds(file_in)
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            if inbounds(element, bounds):
                el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def clean_zip(zip):
	zip = zip.split('-')[0]
	zip = zip.lstrip('CA ')
	if len(zip) != 5:
		return "Bad Zip"
	elif int(zip[0:2]) > 92:
		return "Bad Zip"
	else:
		return zip

def clean_is_in(tag):
    key = tag.attrib['k'].split(':')[1]
    val = tag.attrib['v']
    if key == 'iso_3166_2':
        key, val = 'state_code', 'CA'
    elif val == 'USA':
        val = 'United States of America'
    return key, val


def clean_gnis(tag):
    try:
        key = tag.attrib['k'].split(':')[1]
    except IndexError:
        key = tag.attrib['k']
    val = tag.attrib['v']

    # correct keys according to OSM documentation for most recent (2009) gnis import style
    # fix values where appropriate
    if key == 'elevation' or key == 'ele':
        key = 'ele'
        val = val.rstrip('ft').rstrip('metros').split(';')[0]
    elif key == 'ST_num':
        key = 'state_id'
    elif key == 'County_num':
        key = 'county_id'
    elif key == 'county_name':
        key = 'county'
    elif key == 'id':
        key = 'feature_id'
        val = val.split(';')
    elif key == 'created':
        val = val.split(';')[0]

    return key, val

def test(filename):
    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.
    data = process_map(filename, False)
    #pprint.pprint(data)
    
    # Test to check first element
    correct_first_elem = {
         "id": "680927",
         "created_by" : "JOSM",
         "type": "node", 
         "pos": [32.9538785, -117.14506],
         "created": {
             "changeset": "492332",
             "user": "Devin",
             "version": "2",
             "uid": "1885",
             "timestamp": "2007-12-31T07:39:37Z"
        }
    }
    assert data[0] == correct_first_elem
     
#     assert data[-1]["address"] == {
#                                     "street": "West Lexington St.", 
#                                     "housenumber": "1412"
#                                       }
#     assert data[-1]["node_refs"] == [ "2199822281", "2199822390",  "2199822392", "2199822369", 
#                                     "2199822370", "2199822284", "2199822281"]

if __name__ == "__main__":
    test(sys.argv[1]) # osm file can be input with cmd line arg