export\
CC=gcc

export

CC=gcc
LD=ld
RM=rm
export CC LD RM

# multiple directives?
# nope. Looks like only export only allows exporession on RHS
export override LD=ld
ifneq ("$(override LD)","ld")
$(error export override error)
endif

# make 3.81 "export define" not allowed ("missing separator")
# make 3.82 works
# make 4.0  works
# (See also error13.mk)
define foo
bar
endef
$(info $(call foo))

export foo

export\
a:=b
$(info a=$(a))

@:;@:
