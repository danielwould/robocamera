# -*- coding: ascii -*-
# $Id: CNC.py,v 1.8 2014/10/15 15:03:49 bnv Exp $
#
# Author: vvlachoudis@gmail.com
# Date: 24-Aug-2014

from __future__ import absolute_import
from __future__ import print_function
import os
import re
import math
import types

#import undo
#import Unicode
import pickle
import json
#import binascii


IDPAT = re.compile(r".*\bid:\s*(.*?)\)")
PARENPAT = re.compile(r"(\(.*?\))")
SEMIPAT = re.compile(r"(;.*)")
OPPAT = re.compile(r"(.*)\[(.*)\]")
CMDPAT = re.compile(r"([A-Za-z]+)")
BLOCKPAT = re.compile(r"^\(Block-([A-Za-z]+):\s*(.*)\)")
AUXPAT = re.compile(r"^(%[A-Za-z0-9]+)\b *(.*)$")

STOP = 0
SKIP = 1
ASK = 2
MSG = 3
WAIT = 4
UPDATE = 5

XY = 0
XZ = 1
YZ = 2

CW = 2
CCW = 3

WCS = ["G54", "G55", "G56", "G57", "G58", "G59"]

DISTANCE_MODE = {"G90": "Absolute",
                 "G91": "Incremental"}
FEED_MODE = {"G93": "1/Time",
             "G94": "unit/min",
             "G95": "unit/rev"}
UNITS = {"G20": "inch",
         "G21": "mm"}
PLANE = {"G17": "XY",
         "G18": "XZ",
         "G19": "YZ"}

# Modal Mode from $G and variable set
MODAL_MODES = {
    "G0"	: "motion",
    "G1"	: "motion",
    "G2"	: "motion",
    "G3"	: "motion",
    "G38.2"	: "motion",
    "G38.3"	: "motion",
    "G38.4"	: "motion",
    "G38.5"	: "motion",
    "G80"	: "motion",

    "G54": "WCS",
    "G55": "WCS",
    "G56": "WCS",
    "G57": "WCS",
    "G58": "WCS",
    "G59": "WCS",

    "G17": "plane",
    "G18": "plane",
    "G19": "plane",

    "G90"	: "distance",
    "G91"	: "distance",

    "G91.1": "arc",

    "G93": "feedmode",
    "G94": "feedmode",
    "G95": "feedmode",

    "G20"	: "units",
    "G21"	: "units",

    "G40"	: "cutter",

    "G43.1": "tlo",
    "G49": "tlo",

    "M0"	: "program",
    "M1"	: "program",
    "M2"	: "program",
    "M30"	: "program",

    "M3": "spindle",
    "M4": "spindle",
    "M5": "spindle",

    "M7": "coolant",
    "M8": "coolant",
    "M9": "coolant",
}

ERROR_HANDLING = {}
TOLERANCE = 1e-7
MAXINT = 1000000000  # python3 doesn't have maxint


# ------------------------------------------------------------------------------
# Return a value combined from two dictionaries new/old
# ------------------------------------------------------------------------------
def getValue(name, new, old, default=0.0):
    try:
        return new[name]
    except:
        try:
            return old[name]
        except:
            return default


class CNC:
    inch = False
    lasercutter = False
    laseradaptive = False
    acceleration_x = 25.0  # mm/s^2
    acceleration_y = 25.0  # mm/s^2
    acceleration_z = 25.0  # mm/s^2
    feedmax_x = 3000
    feedmax_y = 3000
    feedmax_z = 2000
    travel_x = 300
    travel_y = 300
    travel_z = 60
    accuracy = 0.01  # sagitta error during arc conversion
    digits = 4
    startup = "G90"
    stdexpr = False  # standard way of defining expressions with []
    comment = ""  # last parsed comment
    developer = False
    drozeropad = 0

    drillPolicy = 1		# Expand Canned cycles
    toolPolicy = 1		# Should be in sync with ProbePage
    # 0 - send to grbl
    # 1 - skip those lines
    # 2 - manual tool change (WCS)
    # 3 - manual tool change (TLO)
    # 4 - manual tool change (No Probe)

    toolWaitAfterProbe = True  # wait at tool change position after probing
    appendFeed = False  # append feed on every G1/G2/G3 commands to be used
    # for feed override testing

    # ----------------------------------------------------------------------

    def __init__(self):
        self.vars = {
            "prbx": 0.0,
            "prby": 0.0,
            "prbz": 0.0,
            "prbcmd": "G38.2",
            "prbfeed": 10.,
            "errline": "",
            "wx": 0.0,
            "wy": 0.0,
            "wz": 0.0,
            "mx": 0.0,
            "my": 0.0,
            "mz": 0.0,
            "wa": 0.0,
            "wb": 0.0,
            "wc": 0.0,
            "ma": 0.0,
            "mb": 0.0,
            "mc": 0.0,
            "wcox": 0.0,
            "wcoy": 0.0,
            "wcoz": 0.0,
            "wcoa": 0.0,
            "wcob": 0.0,
            "wcoc": 0.0,
            "curfeed": 0.0,
            "curspindle": 0.0,
            "_camwx": 0.0,
            "_camwy": 0.0,
            "G": [],
            "TLO": 0.0,
            "motion": "G0",
            "WCS": "G54",
            "plane": "G17",
            "feedmode": "G94",
            "distance": "G90",
            "arc": "G91.1",
            "units": "G20",
            "cutter": "",
            "program": "M0",
            "spindle": "M5",
            "coolant": "M9",

            "tool": 0,
            "feed": 0.0,
            "rpm": 0.0,

            "planner": 0,
            "rxbytes": 0,

            "OvFeed": 100,  # Override status
            "OvRapid": 100,
            "OvSpindle": 100,
            "_OvChanged": False,
            "_OvFeed": 100,  # Override target values
            "_OvRapid": 100,
            "_OvSpindle": 100,

            "diameter": 3.175,  # Tool diameter
            "cutfeed": 1000.,  # Material feed for cutting
            "cutfeedz": 500.,  # Material feed for cutting
            "safe": 3.,
            "state": "",
            "pins": "",
            "msg": "",
            "stepz": 1.,
            "surface": 0.,
            "thickness": 5.,
            "stepover": 40.,

            "PRB": None,

            "version": "",
            "controller": "",
            "running": False,
            # "enable6axisopt" : 0,
        }
        self.initPath()

    # ----------------------------------------------------------------------
    # Update G variables from "G" string
    # ----------------------------------------------------------------------

    def updateG(self):
        for g in self.vars["G"]:
            if g[0] == "F":
                self.vars["feed"] = float(g[1:])
            elif g[0] == "S":
                self.vars["rpm"] = float(g[1:])
            elif g[0] == "T":
                self.vars["tool"] = int(g[1:])
            else:
                var = MODAL_MODES.get(g)
                if var is not None:
                    self.vars[var] = g

    # ----------------------------------------------------------------------
    def __getitem__(self, name):
        return self.vars[name]

    # ----------------------------------------------------------------------
    def __setitem__(self, name, value):
        self.vars[name] = value

    # ----------------------------------------------------------------------

    def initPath(self, x=None, y=None, z=None, a=None, b=None, c=None):
        if x is None:
            self.x = self.xval = self.vars['wx'] or 0
        else:
            self.x = self.xval = x
        if y is None:
            self.y = self.yval = self.vars['wy'] or 0
        else:
            self.y = self.yval = y
        if z is None:
            self.z = self.zval = self.vars['wz'] or 0
        else:
            self.z = self.zval = z
        if a is None:
            self.a = self.aval = self.vars['wa'] or 0
        else:
            self.a = self.aval = a
        if b is None:
            self.b = self.bval = self.vars['wb'] or 0
        else:
            self.b = self.bval = b
        if c is None:
            self.c = self.cval = self.vars['wc'] or 0
        else:
            self.c = self.cval = c

        self.ival = self.jval = self.kval = 0.0
        self.uval = self.vval = self.wval = 0.0
        self.dx = self.dy = self.dz = 0.0
        self.di = self.dj = self.dk = 0.0
        self.rval = 0.0
        self.pval = 0.0
        self.qval = 0.0
        self.unit = 1.0
        self.mval = 0
        self.lval = 1
        self.tool = 0
        self._lastTool = None

        self.absolute = True		# G90/G91     absolute/relative motion
        self.arcabsolute = False  # G90.1/G91.1 absolute/relative arc
        self.retractz = True		# G98/G99     retract to Z or R
        self.gcode = None
        self.plane = XY
        self.feed = 0		# Actual gcode feed rate (not to confuse with cutfeed
        self.totalLength = 0.0
        self.totalTime = 0.0

    # ----------------------------------------------------------------------
    # Number formating
    # ----------------------------------------------------------------------

    @staticmethod
    def fmt(c, v, d=None):
        if d is None:
            d = CNC.digits
        # Don't know why, but in some cases floats are not truncated by format string unless rounded
        # I guess it's vital idea to round them rather than truncate anyway!
        v = round(v, d)
        return ("%s%*f" % (c, d, v)).rstrip("0").rstrip(".")

    # ----------------------------------------------------------------------
    @staticmethod
    def gcode(g, pairs):
        s = "g%d" % (g)
        for c, v in pairs:
            s += " %c%g" % (c, round(v, CNC.digits))
        return s

    # ----------------------------------------------------------------------
    @staticmethod
    def _gcode(g, **args):
        s = "g%d" % (g)
        for n, v in args.items():
            s += ' ' + CNC.fmt(n, v)
        return s

    # ----------------------------------------------------------------------
    @staticmethod
    def _gotoABC(g, x=None, y=None, z=None, a=None, b=None, c=None, **args):
        s = "g%d" % (g)
        if x is not None:
            s += ' '+CNC.fmt('x', x)
        if y is not None:
            s += ' '+CNC.fmt('y', y)
        if z is not None:
            s += ' '+CNC.fmt('z', z)
        if a is not None:
            s += ' '+CNC.fmt('a', a)
        if b is not None:
            s += ' '+CNC.fmt('b', b)
        if c is not None:
            s += ' '+CNC.fmt('c', c)
        for n, v in args.items():
            s += ' ' + CNC.fmt(n, v)
        return s

    @staticmethod
    def _goto(g, x=None, y=None, z=None, **args):
        s = "g%d" % (g)
        if x is not None:
            s += ' '+CNC.fmt('x', x)
        if y is not None:
            s += ' '+CNC.fmt('y', y)
        if z is not None:
            s += ' '+CNC.fmt('z', z)
        for n, v in args.items():
            s += ' ' + CNC.fmt(n, v)
        return s
    # ----------------------------------------------------------------------

    @staticmethod
    def grapidABC(x=None, y=None, z=None, a=None, b=None, c=None, **args):
        return CNC._gotoABC(0, x, y, z, a, b, c, **args)

    @staticmethod
    def grapid(x=None, y=None, z=None, **args):
        return CNC._goto(0, x, y, z, **args)

    # ----------------------------------------------------------------------
    @staticmethod
    def glineABC(x=None, y=None, z=None, a=None, b=None, c=None, **args):
        return CNC._gotoABC(1, x, y, z, a, b, c, **args)

    @staticmethod
    def gline(x=None, y=None, z=None, **args):
        return CNC._goto(1, x, y, z, **args)

    # ----------------------------------------------------------------------
    @staticmethod
    def glinev(g, v, feed=None):
        pairs = zip("xyz", v)
        if feed is not None:
            pairs.append(("f", feed))
        return CNC.gcode(g, pairs)

    # ----------------------------------------------------------------------
    @staticmethod
    def garcv(g, v, ijk):
        return CNC.gcode(g, zip("xyz", v) + zip("ij", ijk[:2]))

    # ----------------------------------------------------------------------
    @staticmethod
    def garc(g, x=None, y=None, z=None, i=None, j=None, k=None, **args):
        s = "g%d" % (g)
        if x is not None:
            s += ' '+CNC.fmt('x', x)
        if y is not None:
            s += ' '+CNC.fmt('y', y)
        if z is not None:
            s += ' '+CNC.fmt('z', z)
        if i is not None:
            s += ' '+CNC.fmt('i', i)
        if j is not None:
            s += ' '+CNC.fmt('j', j)
        if k is not None:
            s += ' '+CNC.fmt('k', k)
        for n, v in args.items():
            s += ' ' + CNC.fmt(n, v)
        return s

    # ----------------------------------------------------------------------
    @staticmethod
    def zexit(z, d=None):
        if CNC.lasercutter:
            return "m5"
        else:
            return "g0 %s" % (CNC.fmt("z", z, d))

    # ----------------------------------------------------------------------
    # @return line in broken a list of commands, None if empty or comment
    # ----------------------------------------------------------------------

    @staticmethod
    def parseLine(line):
        # skip empty lines
        if len(line) == 0 or line[0] in ("%", "(", "#", ";"):
            return None

        # remove comments
        line = PARENPAT.sub("", line)
        line = SEMIPAT.sub("", line)

        # process command
        # strip all spaces
        line = line.replace(" ", "")

        # Insert space before each command
        line = CMDPAT.sub(r" \1", line).lstrip()
        return line.split()

    # -----------------------------------------------------------------------------
    # @return line,comment
    #	line broken in a list of commands,
    #       None,"" if empty or comment
    #       else compiled expressions,""
    # ----------------------------------------------------------------------
    @staticmethod
    def compileLine(line, space=False):
        line = line.strip()
        if not line:
            return None
        if line[0] == "$":
            return line

        # to accept #nnn variables as _nnn internally
        line = line.replace('#', '_')
        CNC.comment = ""

        # execute literally the line after the first character
        if line[0] == '%':
            # special command
            pat = AUXPAT.match(line.strip())
            if pat:
                cmd = pat.group(1)
                args = pat.group(2)
            else:
                cmd = None
                args = None
            if cmd == "%wait":
                return (WAIT,)
            elif cmd == "%msg":
                if not args:
                    args = None
                return (MSG, args)
            elif cmd == "%update":
                return (UPDATE, args)
            elif line.startswith("%if running") and not self.vars["running"]:
                # ignore if running lines when not running
                return None
            else:
                try:
                    return compile(line[1:], "", "exec")
                except Exception as e:
                    print("Compile line error: \n")
                    print(e)
                    return None

        # most probably an assignment like  #nnn = expr
        if line[0] == '_':
            try:
                return compile(line, "", "exec")
            except:
                # FIXME show the error!!!!
                return None

        # commented line
        if line[0] == ';':
            CNC.comment = line[1:].strip()
            return None

        out = []		# output list of commands
        braket = 0		# bracket count []
        paren = 0		# parenthesis count ()
        expr = ""		# expression string
        cmd = ""		# cmd string
        inComment = False  # inside inComment
        for i, ch in enumerate(line):
            if ch == '(':
                # comment start?
                paren += 1
                inComment = (braket == 0)
                if not inComment:
                    expr += ch
            elif ch == ')':
                # comment end?
                paren -= 1
                if not inComment:
                    expr += ch
                if paren == 0 and inComment:
                    inComment = False
            elif ch == '[':
                # expression start?
                if not inComment:
                    if CNC.stdexpr:
                        ch = '('
                    braket += 1
                    if braket == 1:
                        if cmd:
                            out.append(cmd)
                            cmd = ""
                    else:
                        expr += ch
                else:
                    CNC.comment += ch
            elif ch == ']':
                # expression end?
                if not inComment:
                    if CNC.stdexpr:
                        ch = ')'
                    braket -= 1
                    if braket == 0:
                        try:
                            out.append(compile(expr, "", "eval"))
                        except:
                            # FIXME show the error!!!!
                            pass
                        # out.append("<<"+expr+">>")
                        expr = ""
                    else:
                        expr += ch
                else:
                    CNC.comment += ch
            elif ch == '=':
                # check for assignments (FIXME very bad)
                if not out and braket == 0 and paren == 0:
                    for i in " ()-+*/^$":
                        if i in cmd:
                            cmd += ch
                            break
                    else:
                        try:
                            return compile(line, "", "exec")
                        except:
                            # FIXME show the error!!!!
                            return None
            elif ch == ';':
                # Skip everything after the semicolon on normal lines
                if not inComment and paren == 0 and braket == 0:
                    CNC.comment += line[i+1:]
                    break
                else:
                    expr += ch

            elif braket > 0:
                expr += ch

            elif not inComment:
                if ch == ' ':
                    if space:
                        cmd += ch
                else:
                    cmd += ch

            elif inComment:
                CNC.comment += ch

        if cmd:
            out.append(cmd)

        # return output commands
        if len(out) == 0:
            return None
        if len(out) > 1:
            return out
        return out[0]

    # ----------------------------------------------------------------------
    # Break line into commands
    # ----------------------------------------------------------------------
    @staticmethod
    def breakLine(line):
        if line is None:
            return None
        # Insert space before each command
        line = CMDPAT.sub(r" \1", line).lstrip()
        return line.split()

    # ----------------------------------------------------------------------
    # Instead of the current code, override with the custom user lines
    # @param program a list of lines to execute
    # @return the new list of lines
    # ----------------------------------------------------------------------
    @staticmethod
    def compile(program):
        lines = []
        for j, line in enumerate(program):
            newcmd = []
            cmds = CNC.compileLine(line)
            if cmds is None:
                continue
            if isinstance(cmds, str):
                cmds = CNC.breakLine(cmds)
            else:
                # either CodeType or tuple, list[] append it as is
                lines.append(cmds)
                continue

            for cmd in cmds:
                c = cmd[0]
                try:
                    value = float(cmd[1:])
                except:
                    value = 0.0
                if c.upper() in ("F", "X", "Y", "Z", "I", "J", "K", "R", "P"):
                    cmd = CNC.fmt(c, value)
                else:
                    opt = ERROR_HANDLING.get(cmd.upper(), 0)
                    if opt == SKIP:
                        cmd = None

                if cmd is not None:
                    newcmd.append(cmd)
            lines.append("".join(newcmd))
        return lines
