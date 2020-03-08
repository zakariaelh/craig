import time
import json 
import requests 
from bs4 import BeautifulSoup

from constants import LINK_CITIES, PATH_CITIES


def extract_cities(soup_cities):
	"""Extract the list of cities from the soup"""
	cities = cities = {i.get_text(): i.a['href'] for i in soup_cities.find_all('li')}  
	return cities

def extract_state_cities(soup_state):
	state_name = soup_state.get_text()
	# get the soup of cities 
	soup_cities = soup_state.find_next_sibling('ul')
	cities = extract_cities(soup_cities)
	return state_name, cities

def extract_box_state_cities(soup_box):
	# dictionary for state and cities in that box 
	d_box = dict()
	# get the first state 
	soup_state = soup_box.find('h4')
	state_name, cities = extract_state_cities(soup_state)
	# append to dic 
	d_box[state_name] = cities
	# keep looking for the next sibling of h4 until there are none 
	while soup_state.find_next_sibling('h4'):
		soup_state = soup_state.find_next_sibling('h4')
		state_name, cities = extract_state_cities(soup_state)
		d_box[state_name] = cities

	return d_box 

def extract_box(soup_main):
	soup_all_box = soup_main.find('div', class_ = 'colmask')  
	l_box_soup = soup_all_box.find_all('div', class_='box') 
	return l_box_soup

def get_main_soup(link):
	# call website
	page = requests.get(link)
	# create soup 
	soup_main = BeautifulSoup(page.content, 'html.parser')
	return soup_main

def save_cities(d_all):
	with open(PATH_CITIES, 'w') as f:
		json.dump(d_all, f)

def main_cities(save=False):
	# get the main soup 
	soup_main = get_main_soup(LINK_CITIES)
	# extract boxes 
	l_box_soup = extract_box(soup_main)
	# for each box extract all (state, cities)
	d_all = dict()
	for soup_box in l_box_soup:
		d_box = extract_box_state_cities(soup_box)
		d_all.update(d_box)
	if save:
		save_cities(d_all)
	return d_all 

def extract_areas(link):
	soup_main = get_main_soup(link)
	soup_areas = soup_main.find('ul', class_='sublinks')
	if soup_areas:
		l_areas = soup_areas.find_all('li')
		d_areas = dict()
		for area in l_areas:
			try: 
				d_areas[area.a['title']] = link + area.a['href'] 
			except Exception as e:
				print(e)
				print('error while extracting {} in {}'.format(area, link))
	else:
		d_areas = None 
	return d_areas

def main(save=False):
	d_all = main_cities(save=save)
	# loop through states 
	for state in d_all.keys():
		for city, link in d_all[state].items():
			d_areas = extract_areas(link)
			d_all[state][city] = {'general': d_all[state][city]}
			if d_areas:
				d_all[state][city].update(d_areas)
				print('Areas in {} : {}'.format(city, d_areas.keys()))
			print('city: {} DONE'.format(city))

		time.sleep(4)
	return d_all


if __name__ == '__main__':
	main_cities(save=False)


