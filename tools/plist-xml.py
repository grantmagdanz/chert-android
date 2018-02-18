#!/usr/bin/env python
# -*- coding: utf-8 -*-

import plistlib
import glob
import os
import shutil
import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom
import sys

OUTPUT_FILE_NAME = 'donottranslate-more-keys.xml'
UNIX_FOLDER_SEPERATOR = '/'

# I used this in the iOS version to represent a key that will hold accents
PUNCTUATION_PLACE_HOLDER = '___'

def get_output_folder_name(filename):
    # Drop '.plist', make it lower case, and remove parenthesis, spaces, and apostrophes.
    filename = filename[:-6].lower().replace('(', '').replace(')', '').replace(' ', '').replace('\'', '')

    # Android's Locale limits locale names to 8 characters, so only keep 8.
    filename = filename[:8]

    # The Android localization folder name is of the structure 'values-<locale>'
    return 'values-' + filename

# Creates a donottranslate-more-keys.xml file that maps the letters in
# letters_to_characters to their extra characters.
def create_xml_file(letters_to_characters, output_dir):
    root = ET.Element('resources')
    root.attrib['xmlns:xliff']='urn:oasis:names:tc:xliff:document:1.2'

    for letter, extra_characters in letters_to_characters.iteritems():
        create_string_element(root, letter.lower(), [c.lower() for c in extra_characters])

    # XML encodes '&' to '&amp'. We don't want that to just replace it.
    pretty_xml = to_pretty_xml(root).replace('&amp;', '&')
    fh = open(output_dir + UNIX_FOLDER_SEPERATOR + OUTPUT_FILE_NAME, 'w')
    fh.write(pretty_xml)
    fh.close()

# Takes in a root element and returns a nicely formated string representation
def to_pretty_xml(root):
    # UTF-8 because that's what Android's XML files use
    xml_string = ET.tostring(root, encoding='UTF-8', method='xml')

    # Using minidom to parse the Element Tree's xml and then create a nicely formatted
    # string. No particular reason to use both, I just started on Element Tree before
    # I realized that it wouldn't print pretty.
    return minidom.parseString(xml_string).toprettyxml(indent='    ', encoding='UTF-8')

# Adds a 'string' XML element to root that maps letter to extra_characters.
#
# Example: <string name="morekeys_l">ł,ḷ,ł̣</string>
def create_string_element(root, letter, extra_characters):
    if letter == PUNCTUATION_PLACE_HOLDER:
        # Need to change this to 'punctuation' as we want the element to map
        # accents to 'morekeys_punctuation' which adds the accents to the
        # period next to the space bar.
        letter = 'punctuation'

        # Convert accennts to their unicode value
        extra_characters = [get_unicode_for_accent(c) for c in extra_characters]
    elif letter.encode('UTF-8') == '√':
        # The square root character is used in Tlingit. It needed to be manually
        # added for the iOS keyboard, but AOSP has it already, so just skip it.
        return

    # 'morekeys_<letter>' is what the AOSP keyboard looks for
    element_name = 'morekeys_' + letter
    string = ET.SubElement(root, 'string', name=element_name)

    # Put commas between them and add it to the element. This is what
    # the AOSP keyboard expects.
    string.text = ','.join(extra_characters)

# In the plist files, accents are represented by their string names.
# This method hard codes those and maps them to their unicode representation.
def get_unicode_for_accent(accent):
    accent_map = {'ACUTE': '&#x0301;',
                  'GRAVE': '&#x0300;',
                  'CIRCUMFLEX': '&#x0302;',
                  'CARON': '&#x030C;',
                  'DOUBLE_ACUTE': '&#x030B;',
                  'COMBINING_DOUBLE_INVERTED_BREVE': '&#x0361;'}

    return accent_map[accent.upper()]

# Converts a character to the hex representation.
#
# Example: á -> &#x00E1;
def get_hex_for_char(character):
    hex_char = ''
    # Some are made up of multiple unicode characters such as ł̣.
    # This creates a unicode character for each and concatenates them.
    for sub_char in character.lower():
        hex_char = hex_char + '&#x{:04X};'.format(ord(sub_char))
    return hex_char

plist_dir = sys.argv[1]
output_dir = sys.argv[2]

for full_path in glob.glob(plist_dir + "/*.plist"):
    filename = os.path.basename(full_path)
    # Not a language file
    if filename == "Info.plist":
	    continue
    print "Reading {:s}".format(filename)
    values_dir_name = get_output_folder_name(filename)
    language_output_dir = output_dir + UNIX_FOLDER_SEPERATOR + values_dir_name
    language_more_keys_file = language_output_dir + UNIX_FOLDER_SEPERATOR + OUTPUT_FILE_NAME
    if not os.path.exists(language_output_dir):
        os.makedirs(output_dir + '/' + values_dir_name)
    print "Writing {:s}\n".format(language_more_keys_file)
    letters_to_characters = plistlib.readPlist(full_path)
    create_xml_file(letters_to_characters, language_output_dir)
