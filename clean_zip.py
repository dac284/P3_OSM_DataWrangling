def clean_zips(zip)
	if length(zip) != 5:
		if 'CA'.match(zip):
			zip = zip.lstrip('CA ')
		m = has_letters.search(zip)
		if m:
			return None
		if int(zip[0:2]) > 92:
			return "Bad Zip"
		zip = zip.split('-')[0]
		return zip

if __name__ == '__main__':
    
    test(sys.argv[1])