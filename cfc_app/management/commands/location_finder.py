import sys
import getopt


def main(argv):
    bill_file = ''  # text file for the bill
    cities_file = ''  # text file of cities in the state, one per line
    counties_file = ''  # text file of counties in the state, one per line
    cities = []
    counties = []

    try:
        opts, args = getopt.getopt(
            argv, "b:c:o:", ["bill=", "cities=", "counties="])
    except getopt.GetoptError:
        print("Usage: extract_location.py -b <bill> -c <cities> -o <counties>")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-b", "--bill"):
            bill_file = arg
        elif opt in ("-c", "--cities"):
            cities_file = arg
        elif opt in ("-o", "--counties"):
            counties_file = arg

    # read the cities into array
    with open(cities_file, 'r') as file:
        cities = file.readlines()
        cities = [x.strip() for x in cities]

    # read the counties into array
    with open(counties_file, 'r') as file:
        counties = file.readlines()
        counties = [x.strip() for x in counties]

    # count all occurrences of cities and counties in bill
    with open(bill_file, 'r') as file:
        bill = file.read()
        for city in cities:
            occurrences = bill.count(city)
            print("Occurrences of %s: %d" % (city, occurrences))
        print("\n")
        for county in counties:
            occurrences = bill.count(county)
            print("Occurrences of %s: %d" % (county, occurrences))


if __name__ == '__main__':
    main(sys.argv[1:])
