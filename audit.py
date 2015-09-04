"""
Your task in this exercise has two steps:

- audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix 
    the unexpected street types to the appropriate ones in the expected list.
    You have to add mappings only for the actual problems you find in this OSMFILE,
    not a generalized solution, since that may and will depend on the particular area you are auditing.
- write the update_name function, to actually fix the street name.
    The function takes a string with street name as an argument and should return the fixed name
    We have provided a simple test so that you see what exactly is expected
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
import sys
import os



street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_type_re_begin = re.compile(r'^\S+\.?\b', re.IGNORECASE)
is_in_re = re.compile(r'is_in', re.IGNORECASE)
gnis_re = re.compile(r'gnis', re.IGNORECASE)
east_st_re = re.compile('e(ast)? street', re.IGNORECASE)
has_letters = re.compile(r'[a-zA-Z]', re.IGNORECASE)

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Bend", "Cirle", "Point", "Row", "Terrace", "Way",
            "Walk", "View", "Canyon"]

begin_expected = ["Camino", "Caminito", "Avenida", "Villa", "Via", "Calle", "Paseo", "Plaza", 
				  "Rue", "Rancho", "Highway", "Vista", "Callejon", "Circa", "Circo", "Circulo", 
				  "Corte", "Corta"]

# UPDATE THIS VARIABLE
mapping = { "Ave" : "Avenue",
			"Ave." : "Avenue",
			"Av" : "Avenue",
			"Bl" : "Boulevard",
			"Blvd" : "Boulevard",
			"Blvd." : "Boulevard",
			"Ci" : "Circle",
			"Cr" : "Circle",
			"Ct" : "Court",
			"Ct." : "Court",
			"Cte" : "Corte",
			"Cv" : "Cove",
			"Cy" : "Canyon",
			"Dive" : "Drive",
			"Dr" : "Drive",
			"Hwy" : "Highway",
			"Hy" : "Highway",
			"La" : "Lane",
			"Ln" : "Lane",
			"Pa" : "Path",
			"Pk" : "Parkway",
			"Pkwy" : "Parkway",
			"Pl" : "Place",
			"Pt" : "Point",
			"Py" : "Parkway",
			"Ro" : "Road",
			"Rd" : "Road",
            "Rd." : "Road",
            "Rw" : "Row",
            "ST." : "Street",
            "Sq" : "Square",
            "St" : "Street",
            "St." : "Street",
            "Te" : "Terrace",
            "Tl" : "Trail",
            "Tr" : "Trail",
            "Wa" : "Way",
            "Wy" : "Way",
            "Wk" : "Walk",
            "Wl" : "Walk",
            "Vw" : "View"
            }

begin_map = { "Cam" : "Camino ",
			  "Camto" : "Caminito ",
			  "Camta" : "Caminito ",
			  "Cte" : "Corte ",
			  "Av." : "Avenida ",
			  "Avnda" : "Avenida ",
			  "Aveinda" : "Avenida ",
              "E" : "East ",
              "N" : "North ",
              "S" : "South ",
              "W" : "West "
			  }
			  


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    n = street_type_re_begin.search(street_name)
    if m and n:
        street_end = m.group()
        street_begin = n.group()
        if (street_end not in expected) and (street_begin not in begin_expected):
            if street_end not in mapping.keys():
                street_types[street_begin].add(street_name)
            else:
                street_types[street_end].add(street_name)
            return True
        return False

def audit_is_in(is_in_types, tag):
	try:
		tag_type = tag.attrib['k'].split(':')[1]
		is_in_types[tag_type].add(tag.attrib['v'])
	except IndexError:
		tag_type = tag.attrib['k']
		is_in_types[tag_type].add(tag.attrib['v'])

def audit_gnis(gnis_types, tag):
    try:
        tag_type = tag.attrib['k'].split(':')[1]
        gnis_types[tag_type].add(tag.attrib['v'])
    except IndexError:
        tag_type = tag.attrib['k']
        gnis_types[tag_type].add(tag.attrib['v'])
		
def audit_zip(zip_codes, zip_code):
	try:
		zip_codes[zip_code] += 1
	except:
		zip_codes[zip_code] = 1

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")
    
def is_zip(elem):
    return (elem.attrib['k'] == "addr:postcode")
    
def is_in_tag(elem):
	m = is_in_re.search(elem.attrib['k'])
	if m:
		return True
	else:
		return False

def is_gnis(elem):
    m = gnis_re.search(elem.attrib['k'])
    n = re.compile('ele').search(elem.attrib['k'])
    if m or n:
        return True
    else:
        return False


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    is_in_types = defaultdict(set)
    gnis_types = defaultdict(set)
    zip_codes = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
            	if is_in_tag(tag):
            		audit_is_in(is_in_types, tag)
                if is_gnis(tag):
                    audit_gnis(gnis_types, tag)
            	if is_zip(tag):
            		audit_zip(zip_codes, tag.attrib['v'])

    return street_types, is_in_types, gnis_types, zip_codes


def update_name(name):
    
    m = street_type_re.search(name)
    n = street_type_re_begin.search(name)
    if m and n:
        street_end = m.group()
        street_begin = n.group()
        if street_end not in expected and street_end in mapping.keys():
            name = name[:-len(street_end)] + mapping[street_end]
        p = east_st_re.search(name) #to ensure E St is not converted to East St
        if street_begin not in begin_expected and street_begin in begin_map.keys() and not p:
            name = begin_map[street_begin] + name[len(street_begin):].strip()
	return name


def test(OSMFILE):
    street_types, is_in_types, gnis_types, zip_codes = audit(OSMFILE)
    
    #uncomment whichever data type is being audited
    
    #pprint.pprint(dict(street_types))
    #pprint.pprint(dict(is_in_types))
    pprint.pprint(dict(gnis_types))

#	clean_zips = defaultdict(int)
# 	for zip, num in zip_codes.iteritems():
# 		newzip = clean_zip(zip)
# 		clean_zips[newzip] += num
# 	pprint.pprint(dict(clean_zips))


if __name__ == '__main__':
    test(sys.argv[1])