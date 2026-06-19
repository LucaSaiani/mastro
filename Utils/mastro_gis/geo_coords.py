# SPDX-FileCopyrightText: 2010 Maximilian Hoegner <hp.maxi@hoegners.de>
# SPDX-FileCopyrightText: 2011-2012 Michael Martin
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Ported from Blender's "Sun Position" addon (geo.py / sun_calc.py) so the
# GIS origin field can accept/display the same tolerant lat/lon notations
# (decimal, DMS, NMEA-style) with the same globe-icon "Coordinates" widget.

import re


class _Parser:
	"""A parser class using regular expressions."""

	def __init__(self):
		self.patterns = {}
		self.raw_patterns = {}
		self.virtual = {}

	def add(self, name, pattern, virtual=False):
		self.raw_patterns[name] = "(?:" + pattern + ")"
		self.virtual[name] = virtual
		self.patterns[name] = ("(?:" + pattern + ")") % self.patterns

	def parse(self, pattern_name, text):
		sub_dict = {}
		subpattern_names = []
		for s in re.finditer(r"%\(.*?\)s", self.raw_patterns[pattern_name]):
			subpattern_name = s.group()[2:-2]
			if not self.virtual[subpattern_name]:
				sub_dict[subpattern_name] = "(" + self.patterns[subpattern_name] + ")"
				subpattern_names.append(subpattern_name)
			else:
				sub_dict[subpattern_name] = self.patterns[subpattern_name]

		pattern = "^" + (self.raw_patterns[pattern_name] % sub_dict) + "$"
		m = re.match(pattern, text)
		if m is None:
			return None

		tree = {"TEXT": text}
		for i in range(len(subpattern_names)):
			text_part = m.group(i + 1)
			if text_part is not None:
				subpattern = subpattern_names[i]
				tree[subpattern] = self.parse(subpattern, text_part)
		return tree


_position_parser = _Parser()
_position_parser.add("direction_ns", r"[NSns]")
_position_parser.add("direction_ew", r"[EOWeow]")
_position_parser.add("decimal_separator", r"[\.,]", True)
_position_parser.add("sign", r"[+-]")

_position_parser.add("nmea_style_degrees", r"[0-9]{2,}")
_position_parser.add("nmea_style_minutes", r"[0-9]{2}(?:%(decimal_separator)s[0-9]*)?")
_position_parser.add("nmea_style", r"%(sign)s?\s*%(nmea_style_degrees)s%(nmea_style_minutes)s")

_position_parser.add("number", r"[0-9]+(?:%(decimal_separator)s[0-9]*)?|%(decimal_separator)s[0-9]+")

_position_parser.add("plain_degrees", r"(?:%(sign)s\s*)?%(number)s")

_position_parser.add("degree_symbol", r"°", True)
_position_parser.add("minutes_symbol", r"'|′|`|´", True)
_position_parser.add("seconds_symbol", r"%(minutes_symbol)s%(minutes_symbol)s|″|\"", True)
_position_parser.add("degrees", r"%(number)s\s*%(degree_symbol)s")
_position_parser.add("minutes", r"%(number)s\s*%(minutes_symbol)s")
_position_parser.add("seconds", r"%(number)s\s*%(seconds_symbol)s")
_position_parser.add(
	"degree_coordinates",
	r"(?:%(sign)s\s*)?%(degrees)s(?:[+\s]*%(minutes)s)?(?:[+\s]*%(seconds)s)?|(?:%(sign)s\s*)%(minutes)s(?:[+\s]*%(seconds)s)?|(?:%(sign)s\s*)%(seconds)s"
)

_position_parser.add("coordinates_ns", r"%(nmea_style)s|%(plain_degrees)s|%(degree_coordinates)s")
_position_parser.add("coordinates_ew", r"%(nmea_style)s|%(plain_degrees)s|%(degree_coordinates)s")

_position_parser.add(
	"position", (
		r"\s*%(direction_ns)s\s*%(coordinates_ns)s[,;\s]*%(direction_ew)s\s*%(coordinates_ew)s\s*|"
		r"\s*%(direction_ew)s\s*%(coordinates_ew)s[,;\s]*%(direction_ns)s\s*%(coordinates_ns)s\s*|"
		r"\s*%(coordinates_ns)s\s*%(direction_ns)s[,;\s]*%(coordinates_ew)s\s*%(direction_ew)s\s*|"
		r"\s*%(coordinates_ew)s\s*%(direction_ew)s[,;\s]*%(coordinates_ns)s\s*%(direction_ns)s\s*|"
		r"\s*%(coordinates_ns)s[,;\s]+%(coordinates_ew)s\s*"
	)
)

_position_parser.add(
	"single_ns",
	r"\s*%(direction_ns)s\s*%(coordinates_ns)s\s*|\s*%(coordinates_ns)s\s*%(direction_ns)s\s*|\s*%(coordinates_ns)s\s*"
)
_position_parser.add(
	"single_ew",
	r"\s*%(direction_ew)s\s*%(coordinates_ew)s\s*|\s*%(coordinates_ew)s\s*%(direction_ew)s\s*|\s*%(coordinates_ew)s\s*"
)


def _get_number(b):
	s = b["TEXT"].replace(",", ".")
	return float(s)


def _get_coordinate(b):
	r = 0.

	if b.get("nmea_style"):
		if b["nmea_style"].get("nmea_style_degrees"):
			r += _get_number(b["nmea_style"]["nmea_style_degrees"])
		if b["nmea_style"].get("nmea_style_minutes"):
			r += _get_number(b["nmea_style"]["nmea_style_minutes"]) / 60.
		if b["nmea_style"].get("sign") and b["nmea_style"]["sign"]["TEXT"] == "-":
			r *= -1.
	elif b.get("plain_degrees"):
		r += _get_number(b["plain_degrees"]["number"])
		if b["plain_degrees"].get("sign") and b["plain_degrees"]["sign"]["TEXT"] == "-":
			r *= -1.
	elif b.get("degree_coordinates"):
		if b["degree_coordinates"].get("degrees"):
			r += _get_number(b["degree_coordinates"]["degrees"]["number"])
		if b["degree_coordinates"].get("minutes"):
			r += _get_number(b["degree_coordinates"]["minutes"]["number"]) / 60.
		if b["degree_coordinates"].get("seconds"):
			r += _get_number(b["degree_coordinates"]["seconds"]["number"]) / 3600.
		if b["degree_coordinates"].get("sign") and b["degree_coordinates"]["sign"]["TEXT"] == "-":
			r *= -1.

	return r


def parse_position(s):
	"""Take a string describing a lat/lon position (decimal, DMS, or NMEA-style,
	with optional N/S/E/W) and return (latitude, longitude) as floats, or None
	if parsing fails."""
	parse_tree = _position_parser.parse("position", s)
	if parse_tree is None:
		return None

	lat_sign = +1.
	if parse_tree.get("direction_ns") and parse_tree["direction_ns"]["TEXT"] in ("S", "s"):
		lat_sign = -1.

	lon_sign = +1.
	if parse_tree.get("direction_ew") and parse_tree["direction_ew"]["TEXT"] in ("W", "w"):
		lon_sign = -1.

	lat = lat_sign * _get_coordinate(parse_tree["coordinates_ns"])
	lon = lon_sign * _get_coordinate(parse_tree["coordinates_ew"])

	return lat, lon


def format_lat_long(latitude, longitude):
	"""Format a (latitude, longitude) pair in degrees as a DMS string with
	N/S/E/W suffixes, e.g. 45°27'52.80"N 9°11'24.00"E."""
	coordinates = ""

	for i, co in enumerate((latitude, longitude)):
		dd = abs(int(co))
		mm = abs(co - int(co)) * 60.0
		ss = abs(mm - int(mm)) * 60.0
		if co == 0:
			direction = ""
		elif i == 0:
			direction = "N" if co > 0 else "S"
		else:
			direction = "E" if co > 0 else "W"

		coordinates += f"{dd:02d}°{int(mm):02d}'{ss:05.2f}\"{direction} "

	return coordinates.strip(" ")


def _format_single(co, positive_letter, negative_letter):
	dd = abs(int(co))
	mm = abs(co - int(co)) * 60.0
	ss = abs(mm - int(mm)) * 60.0
	if co == 0:
		direction = ""
	else:
		direction = positive_letter if co > 0 else negative_letter
	return f"{dd:02d}°{int(mm):02d}'{ss:05.2f}\"{direction}".strip()


def format_latitude(latitude):
	"""Format a single latitude in degrees as a DMS string, e.g. 45°27'52.80"N."""
	return _format_single(latitude, "N", "S")


def format_longitude(longitude):
	"""Format a single longitude in degrees as a DMS string, e.g. 9°11'24.00"E."""
	return _format_single(longitude, "E", "W")


def parse_latitude(s):
	"""Take a string describing a single latitude (decimal, DMS, or NMEA-style,
	with optional N/S) and return degrees as a float, or None if parsing fails."""
	tree = _position_parser.parse("single_ns", s)
	if tree is None:
		return None
	sign = -1. if tree.get("direction_ns") and tree["direction_ns"]["TEXT"] in ("S", "s") else +1.
	return sign * _get_coordinate(tree["coordinates_ns"])


def parse_longitude(s):
	"""Take a string describing a single longitude (decimal, DMS, or NMEA-style,
	with optional E/W) and return degrees as a float, or None if parsing fails."""
	tree = _position_parser.parse("single_ew", s)
	if tree is None:
		return None
	sign = -1. if tree.get("direction_ew") and tree["direction_ew"]["TEXT"] in ("W", "w") else +1.
	return sign * _get_coordinate(tree["coordinates_ew"])
