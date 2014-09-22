#!/usr/bin/env python3

# Regression tests for pymake.py
#
# Test Makefile rules
#
# davep 22-Sep-2014

import sys

from sm import *

# require Python 3.x 
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

def rule_test() :
    # parse a full rule! 
    rule_test_list = ( 
        # normal rules
        ( "all : this is a test", RuleExpression(
                                    ( Expression( (Literal("all"),) ),
                                      RuleOp(":"),
                                      PrerequisiteList( 
                                        ( Literal("this"),Literal("is"),Literal("a"),Literal("test"), )
                                      ),
                                    ),
                                  ),
                            ),

        ( "all : ", RuleExpression(
                        ( Expression( (Literal("all"),) ),
                          RuleOp(":"),
                          PrerequisiteList( 
                                ( Literal(""), ) 
                          ),
                        ),
                    ),
                ),

        # target specific variables
        ( "all : CC=gcc",
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC=|gcc", 
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("="),
                                      Expression( (Literal("|gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC=:gcc", 
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("="),
                                      Expression( (Literal(":gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC:=gcc",
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp(":="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC::=gcc", 
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("::="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC+=gcc",
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("+="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        # *= not in assignment_operators
        ( "all : CC*=gcc",
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC*"),) ),
                                      AssignOp("="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "all : CC!=gcc", 
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("!="),
                                      Expression( (Literal("gcc"),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        # trailing spaces should be preserved
        ( "all : CC=gcc  # this is a comment",
                          RuleExpression(
                                ( Expression( (Literal("all"),) ),
                                  RuleOp(":"),
                                  AssignmentExpression( 
                                    ( Expression( (Literal("CC"),) ),
                                      AssignOp("="),
                                      # trailing spaces are preserved
                                      Expression( (Literal("gcc  "),) ),
                                    ),
                                  ),
                                ),
                          ),
                     ),

        ( "hello there all you rabbits : hello there all you rabbits", 
                          RuleExpression(
                                ( Expression( (Literal("hello"),Literal("there"),Literal("all"),Literal("you"),Literal("rabbits"), ), ),
                                  RuleOp(":"),
                                  PrerequisiteList( 
                                    ( Literal("hello"),Literal("there"),Literal("all"),Literal("you"),Literal("rabbits"), ),
                                  ),
                                ),
                          ),
                     ),

#        ( "$(hello there all you) rabbits : hello there all you rabbits", () ),
#        ( "$(hello there all you) rabbits : $(hello) there all you rabbits", () ),
        ( "$(hello $(there $(all $(you) rabbits))) : $(hello) there all you rabbits", () ),

        ( "all : ; @echo $@", RuleExpression
                                ( (Expression( (Literal("all"),) ),
                                   RuleOp(":"),
                                   PrerequisiteList( () ) 
                                  ) 
                                ) 
                              ),

        # static pattern rule

        # order only prereq
    )

    for test in rule_test_list : 
        # source, validate
        s,v = test[0],test[1]
        print("test={0}".format(s))
        my_iter = ScannerIterator(s)

        tokens = tokenize_assignment_or_rule(my_iter)
        print( "tokens={0}".format(str(tokens)) )
        print( "     v={0}".format(str(v)) )

        assert tokens==v

if __name__=='__main__':
    rule_test()
