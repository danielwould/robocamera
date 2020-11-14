# Generic motion controller definition
# All controller plugins inherit features from this one

from __future__ import absolute_import
from __future__ import print_function

from helpers.CNC import CNC, WCS
import time
import re

STATUSPAT = re.compile(
    r"^<(\w*?),MPos:([+\-]?\d*\.\d*),([+\-]?\d*\.\d*),([+\-]?\d*\.\d*)(?:,([+\-]?\d*\.\d*))?(?:,([+\-]?\d*\.\d*))?(?:,([+\-]?\d*\.\d*))?,WPos:([+\-]?\d*\.\d*),([+\-]?\d*\.\d*),([+\-]?\d*\.\d*)(?:,([+\-]?\d*\.\d*))?(?:,([+\-]?\d*\.\d*))?(?:,([+\-]?\d*\.\d*))?(?:,.*)?>$")
POSPAT = re.compile(
    r"^\[(...):([+\-]?\d*\.\d*),([+\-]?\d*\.\d*),([+\-]?\d*\.\d*)(?:,([+\-]?\d*\.\d*))?(?:,([+\-]?\d*\.\d*))?(?:,([+\-]?\d*\.\d*))?(:(\d*))?\]$")
TLOPAT = re.compile(r"^\[(...):([+\-]?\d*\.\d*)\]$")
DOLLARPAT = re.compile(r"^\[G\d* .*\]$")
SPLITPAT = re.compile(r"[:,]")
VARPAT = re.compile(r"^\$(\d+)=(\d*\.?\d*) *\(?.*")


class _GenericController:
    def executeCommand(self, oline, line, cmd):
        return False

    def hardResetPre(self):
        pass

    def hardResetAfter(self):
        pass

    def viewStartup(self):
        pass

    def checkGcode(self):
        pass

    def viewSettings(self):
        pass

    def grblRestoreSettings(self):
        pass

    def grblRestoreWCS(self):
        pass

    def grblRestoreAll(self):
        pass

    def purgeControllerExtra(self):
        pass

    def overrideSet(self):
        pass

    def hardReset(self):
        self.master.busy()
        if self.master.serial is not None:
            self.hardResetPre()
            self.master.openClose()
            self.hardResetAfter()
        self.master.openClose()
        self.master.stopProbe()
        self.master._alarm = False
        self.cnc_obj.vars["_OvChanged"] = True  # force a feed change if any
        self.master.notBusy()

    # ----------------------------------------------------------------------
    def softReset(self, clearAlarm=True):
        if self.master.serial:
            self.master.serial_write(b"\030")
        self.master.stopProbe()
        if clearAlarm:
            self.master._alarm = False
        self.master.cnc_obj.vars["_OvChanged"] = True  # force a feed change if any

    # ----------------------------------------------------------------------
    def unlock(self, clearAlarm=True):
        if clearAlarm:
            self.master._alarm = False
        self.master.sendGCode("$X")

    # ----------------------------------------------------------------------
    def home(self, event=None):
        self.master._alarm = False
        self.master.sendGCode("$H")

    def viewStatusReport(self):
        self.master.serial_write(b"?")
        self.master.sio_status = True

    def viewParameters(self):
        self.master.sendGCode("$#")

    def viewState(self):  # Maybe rename to viewParserState() ???
        self.master.sendGCode("$G")

    # ----------------------------------------------------------------------
    def jog(self, dir):
        # print("jog",dir)
        self.master.sendGCode("G91G0%s" % (dir))
        self.master.sendGCode("G90")

    # ----------------------------------------------------------------------
    def goto(self, x=None, y=None, z=None, a=None, b=None, c=None):
        cmd = "G90G0"
        if x is not None:
            cmd += "X%g" % (x)
        if y is not None:
            cmd += "Y%g" % (y)
        if z is not None:
            cmd += "Z%g" % (z)
        if a is not None:
            cmd += "A%g" % (a)
        if b is not None:
            cmd += "B%g" % (b)
        if c is not None:
            cmd += "C%g" % (c)
        self.master.sendGCode("%s" % (cmd))

    # ----------------------------------------------------------------------
    def _wcsSet(self, x, y, z, a=None, b=None, c=None):
        #global wcsvar
        #p = wcsvar.get()
        p = WCS.index(self.cnc_obj.vars["WCS"])
        if p < 6:
            cmd = "G10L20P%d" % (p+1)
        elif p == 6:
            cmd = "G28.1"
        elif p == 7:
            cmd = "G30.1"
        elif p == 8:
            cmd = "G92"

        pos = ""
        if x is not None and abs(float(x)) < 10000.0:
            pos += "X"+str(x)
        if y is not None and abs(float(y)) < 10000.0:
            pos += "Y"+str(y)
        if z is not None and abs(float(z)) < 10000.0:
            pos += "Z"+str(z)
        if a is not None and abs(float(a)) < 10000.0:
            pos += "A"+str(a)
        if b is not None and abs(float(b)) < 10000.0:
            pos += "B"+str(b)
        if c is not None and abs(float(c)) < 10000.0:
            pos += "C"+str(c)
        cmd += pos
        self.master.sendGCode(cmd)
        self.viewParameters()
        self.master.event_generate("<<Status>>",
                                   data=(_("Set workspace %s to %s") % (WCS[p], pos)))
        # data=(_("Set workspace %s to %s")%(WCS[p],pos)))
        self.master.event_generate("<<CanvasFocus>>")

    # ----------------------------------------------------------------------
    def feedHold(self, event=None):
        if event is not None and not self.master.acceptKey(True):
            return
        if self.master.serial is None:
            return
        self.master.serial_write(b"!")
        self.master.serial.flush()
        self.master._pause = True

    # ----------------------------------------------------------------------
    def resume(self, event=None):
        if event is not None and not self.master.acceptKey(True):
            return
        if self.master.serial is None:
            return
        self.master.serial_write(b"~")
        self.master.serial.flush()
        self.master._msg = None
        self.master._alarm = False
        self.master._pause = False

    # ----------------------------------------------------------------------
    def pause(self, event=None):
        if self.master.serial is None:
            return
        if self.master._pause:
            self.master.resume()
        else:
            self.master.feedHold()

    # ----------------------------------------------------------------------
    # Purge the buffer of the controller. Unfortunately we have to perform
    # a reset to clear the buffer of the controller
    # ---------------------------------------------------------------------
    def purgeController(self):
        self.master.serial_write(b"!")
        self.master.serial.flush()
        time.sleep(1)
        # remember and send all G commands
        G = " ".join([x for x in self.cnc_obj.vars["G"] if x[0] == "G"])  # remember $G
        TLO = self.cnc_obj.vars["TLO"]
        self.softReset(False)			# reset controller
        self.purgeControllerExtra()
        self.master.runEnded()
        if G:
            self.master.sendGCode(G)			# restore $G
        self.master.sendGCode("G43.1Z%s" % (TLO))  # restore TLO
        self.viewState()

    # ----------------------------------------------------------------------

    def parseLine(self, line, cline, sline):
        if not line:
            return True

        elif line[0] == "<":
            if not self.master.sio_status:
                print("{}:{}".format(self.master.name,line))
            else:
                self.parseBracketAngle(line, cline)

        elif line[0] == "[":
            print("{}:{}".format(self.master.name,line))
            self.parseBracketSquare(line)

        elif "error:" in line or "ALARM:" in line:
            print("error: {}".format(line))
            self.master._gcount += 1
            # print "gcount ERROR=",self._gcount
            if cline:
                del cline[0]
            if sline:
                self.cnc_obj.vars["errline"] = sline.pop(0)
            if not self.master._alarm:
                self.master._posUpdate = True
            self.master._alarm = True
            self.cnc_obj.vars["state"] = line
            if self.master.running:
                self.master._stop = True

        elif line.find("ok") >= 0:
            print(line)
            self.master._gcount += 1
            if cline:
                del cline[0]
            if sline:
                del sline[0]
            # print "SLINE:",sline
#			if  self._alarm and not self.running:
#				# turn off alarm for connected status once
#				# a valid gcode event occurs
#				self._alarm = False

        elif line[0] == "$":
            print(line)
            pat = VARPAT.match(line)
            if pat:
                self.cnc_obj.vars["grbl_%s" % (pat.group(1))] = pat.group(2)

        # and self.running:
        elif line[:4] == "Grbl" or line[:13] == "CarbideMotion":
            #tg = time.time()
            print(line)
            self.master._stop = True
            del cline[:]  # After reset clear the buffer counters
            del sline[:]
            self.cnc_obj.vars["version"] = line.split()[1]
            # Detect controller
            if self.master.controller in ("GRBL0", "GRBL1"):
                self.master.controllerSet(
                    "GRBL%d" % (int(self.cnc_obj.vars["version"][0])))

        else:
            # We return false in order to tell that we can't parse this line
            # Sender will log the line in such case
            return False

        # Parsing succesfull
        return True