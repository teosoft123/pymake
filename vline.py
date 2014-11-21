#!/usr/bin/env python3

# "Virtual Block" -- a 2D array of characters with visible/not visible
# attribute. 
#
# Created to handle joining backslash'd lines together for the tokenizer. Has
# evolved into something that will be useful for the makefile View. 
#
# davep 01-Oct-2014

import sys
import itertools

# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

import hexdump
from scanner import ScannerIterator

eol = set("\r\n")
# can't use string.whitespace because want to preserve line endings
whitespace = set( ' \t' )

# indices into VirtualLine's characters' position.
VCHAR_ROW = 0
VCHAR_COL = 1

def is_line_continuation(line):
    # does this line end with "\" + eol? 
    # (hiding in own function so can eventually handle "\"+CR+LF)
    
    # if we don't end in an EOL, definitely not a continuation
    if len(line) and not line[-1] in eol : 
        return False

    # back up past the EOL then verify the next char is \
    pos = len(line)-1
    while pos >=0 and line[pos] in eol : 
        pos -= 1
    return pos>=0 and line[pos]=='\\'

# using a class for the virtual char so can interchange string with VirtualLine
# in ScannerIterator
class VChar(object):
    def __init__(self,char,pos):
        self.char = char
        self.pos = pos
        self.hide = False

    def __getitem__(self,key):
        if key=="char" : return self.char
        if key=="pos" : return self.pos
        if key=="hide" : return self.hide
        raise KeyError(key)
    
    def __setitem__(self,key,value):
        if key=="char" : 
            assert type(value)==type('42'),value
            self.char=value
        elif key=="pos" : 
            assert type(value)==type(42),value
            self.pos=value
        elif key=="hide" : 
            assert type(value)==type(True),value
            self.hide=value
        else :
            raise KeyError(key)

    def __str__(self):
        # created this class pretty much just for this method, e.g., 
        #   while str(self.data[self.idx]) in string.whitespace :
        return self.char

    @staticmethod
    def string_from_vchars(vchar_list):
        # convert array of vchar into a Python string
        return "".join([v.char for v in vchar_list])

class VirtualLine(object):

    def __init__(self,phys_lines_list, starts_at_file_line ):
        # need an array of strings (2-D array of characters)
        assert type(phys_lines_list)==type([])

        # save a pristine copy of the original list 
        self.phys_lines = phys_lines_list

        # this is where this line blob started in the original source file
        self.starting_file_line = starts_at_file_line

        # create a single array of all the characters with their position in
        # the 2-d array
        self.make_virtual_line()

        # Based on the \ line continuation rules, collapse 2-D array into a new
        # 1-D "virtual" array of characters that will be sent to the tokenizer. 
        self.collapse_virtual_line()

    def make_virtual_line(self):
        # Create a 2-D array of vchar (hash) from our 2-D array (array of
        # strings).
        #
        # The new 2-D array will be the characters with their row,col in the
        # 2-D array. 

        self.virt_lines = []
        for row_idx,line in enumerate(self.phys_lines) : 
            vline = []
            for col_idx,char in enumerate(line):
                # char is the original character
                # pos is the (row,col) of the char in the file
                # hide indicates a hidden character (don't feed to the
                # tokenizer, don't highlight in View)
#                vchar = { "char" : char, 
#                          "pos"  : (row_idx+self.starting_file_line,col_idx),
#                          "hide" : False } 
                vchar = VChar(char,(row_idx+self.starting_file_line,col_idx))
                vline.append(vchar)
            self.virt_lines.append(vline)

    def collapse_virtual_line(self):
        # collapse continuation lines according to the whitepace rules around
        # the backslash (The rules will change if we're inside a recipe list or
        # if .POSIX is enabled or or or or ...)
        
        # if only a single line, don't bother
        if len(self.phys_lines)==1 : 
            assert not is_line_continuation(self.phys_lines[0]), self.phys_lines[0] 
            return

        row = 0

        # for each line in our virtual lines
        # kill the eol and whitepace on both sides of \
        # kill empty lines
        # replace \ with <space>
        #
        # For example:
        # """this \
        #      is \
        #       a \
        #         \
        #    test
        # """
        # becomes "this is a test"
        #
        while row < len(self.virt_lines)-1 : 
#            print("row={0} {1}".format(row, hexdump.dump(self.phys_lines[row],16)),end="")

            # start at eol
            col = len(self.virt_lines[row])-1

            # kill EOL
            assert self.virt_lines[row][col]["char"] in eol, (row,col,self.virt_lines[row][col]["char"])
            self.virt_lines[row][col]["hide"] = True
            col -= 1

            # replace \ with <space>
            assert self.virt_lines[row][col]["char"]=='\\', (row,col,self.virt_lines[row][col]["char"])
            self.virt_lines[row][col]["char"] = ' ' 

            # are we now a blank line?
            if self.virt_lines[row][col-1]["hide"] :
                self.virt_lines[row][col]["hide"] = True

            col -= 1

            # eat whitespace backwards
            while col >= 0 and self.virt_lines[row][col]["char"] in whitespace : 
                self.virt_lines[row][col]["hide"] = True
                col -= 1

            # eat whitespace forward on next line
            row += 1
            col = 0
            while col < len(self.virt_lines[row]) and self.virt_lines[row][col]["char"] in whitespace : 
                self.virt_lines[row][col]["hide"] = True
                col += 1

        # Last char of the last line should be an EOL. There should be no
        # backslash on this last line.
        col = len(self.virt_lines[row])-1
        assert self.virt_lines[row][col]["char"] in eol, (row,col,self.virt_lines[row][col]["char"])
        col -= 1
        assert self.virt_lines[row][col]["char"] != '\\', (row,col,self.virt_lines[row][col]["char"])

    def __str__(self):
        # build string from the visible characters
        i = itertools.chain(*self.virt_lines)
        return "".join( [ c["char"] for c in i if not c["hide"] ] )

    def __iter__(self):
        # This iterator we will feed the characters that are still visible to
        # the tokenizer. Using ScannerIterator so we have pushback. The
        # itertools.chain() joins all the virt_lines together into one
        # contiguous array
        self.virt_iterator = ScannerIterator( [ c for c in itertools.chain(*self.virt_lines) if not c["hide"] ] )
        setattr(self.virt_iterator,"starting_file_line",self.starting_file_line)
        return self.virt_iterator

    def truncate(self,truncate_pos):
        # Created to allow the parser to cut off a block at a token boundary.
        # Need to parse something like:
        # foo : bar ; baz 
        # into a rule and a recipe but we won't know where the rule ends and
        # the (maybe) recipes begin until we fully tokenize the rule.
        # foo : bar ; baz 
        #           ^-----truncate here
        # (Only need this rarely)

        def split_2d_array( splitme, row_to_split, col_to_split ):
            # splite a 2-D array (array of strings to be exact) into two
            # arrays. The character at the split point belows to 'below'.
            above = splitme[:row_to_split]
            below = splitme[row_to_split+1:]
            line_to_split = splitme[row_to_split]
            left = line_to_split[:col_to_split] 
            right = line_to_split[col_to_split:] 

            if left :
                above.extend([left])
            below = [right] + below

            return (above,below)
            
        # split the recipe from the rule
        first_line_pos = self.virt_lines[0][0]["pos"]
        row_to_split = truncate_pos[VCHAR_ROW] - first_line_pos[VCHAR_ROW]

        above,below = split_2d_array(self.virt_lines, row_to_split, truncate_pos[VCHAR_COL] )
#        print("above=","".join([c["char"] for c in itertools.chain(*above) if not c["hide"]]))
#        print("below=","".join([c["char"] for c in itertools.chain(*below) if not c["hide"]]))

        self.virt_lines = above

        above,below = split_2d_array(self.phys_lines, row_to_split, truncate_pos[VCHAR_COL] )
        print("above=",above)
        print("below=",below)

        # recipe lines are what we found after the rule was parsed
        recipe_lines = below
        self.phys_lines = above

        # stupid human check
        assert recipe_lines[0][0]==';'

        # truncate the iterator (stop the iterator)
        self.virt_iterator.stop()

        return recipe_lines

    def starting_pos(self):
        # position of this line (in a file) is the position of the first char
        # of the first line
        return self.virt_lines[0][0].pos

#    @classmethod
#    def from_vchar_list(cls,vchar_list,starting_file_line):
#        # create a VirtualLine instance from an array of VChar instances
#        vline = cls([],starts_at_file_line)
#        TODO  -- not sure I need this and it looks like it'll be very hard so
#        leave it out for now

    @classmethod
    def from_string(cls,python_string):
        # create a VirtualLine instance from a single string (convenience
        # method for test/debug code)
        return cls([python_string],0)

    def get_phys_line(self):
        # rebuild a single physical line (needed when tokenizing recipes)
        return "".join(self.phys_lines) 

class RecipeVirtualLine(VirtualLine):
    # This is a block containing recipe(s). Don't collapse around backslashes. 
    def collapse_virtual_line(self):
        pass

