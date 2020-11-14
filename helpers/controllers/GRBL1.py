# GRBL 1.0+ motion controller plugin

from __future__ import absolute_import
from __future__ import print_function
from helpers.controllers._GenericGRBL import _GenericGRBL
from helpers.controllers._GenericController import STATUSPAT, POSPAT, TLOPAT, DOLLARPAT, SPLITPAT, VARPAT
from helpers.CNC import CNC
import time


OV_FEED_100 = chr(0x90)        # Extended override commands
OV_FEED_i10 = chr(0x91)
OV_FEED_d10 = chr(0x92)
OV_FEED_i1 = chr(0x93)
OV_FEED_d1 = chr(0x94)

OV_RAPID_100 = chr(0x95)
OV_RAPID_50 = chr(0x96)
OV_RAPID_25 = chr(0x97)

OV_SPINDLE_100 = chr(0x99)
OV_SPINDLE_i10 = chr(0x9A)
OV_SPINDLE_d10 = chr(0x9B)
OV_SPINDLE_i1 = chr(0x9C)
OV_SPINDLE_d1 = chr(0x9D)

OV_SPINDLE_STOP = chr(0x9E)

OV_FLOOD_TOGGLE = chr(0xA0)
OV_MIST_TOGGLE = chr(0xA1)


class Controller(_GenericGRBL):
    def __init__(self, master):
        self.gcode_case = 0
        self.has_override = True
        self.master = master
        self.cnc_obj = CNC()
        self.thread_id = self.master.name
        #print("grbl1 loaded")

    def jog(self, dir):
        self.master.sendGCode("$J=G91 %s F100000" %
                              (dir))  # XXX is F100000 correct?

    def overrideSet(self):
        self.self.cnc_obj.vars["_OvChanged"] = False  # Temporary
        # Check feed
        diff = self.cnc_obj.vars["_OvFeed"] - self.cnc_obj.vars["OvFeed"]
        if diff == 0:
            pass
        elif self.cnc_obj.vars["_OvFeed"] == 100:
            self.master.serial_write(OV_FEED_100)
        elif diff >= 10:
            self.master.serial_write(OV_FEED_i10)
            self.cnc_obj.vars["_OvChanged"] = diff > 10
        elif diff <= -10:
            self.master.serial_write(OV_FEED_d10)
            self.cnc_obj.vars["_OvChanged"] = diff < -10
        elif diff >= 1:
            self.master.serial_write(OV_FEED_i1)
            self.cnc_obj.vars["_OvChanged"] = diff > 1
        elif diff <= -1:
            self.master.serial_write(OV_FEED_d1)
            self.cnc_obj.vars["_OvChanged"] = diff < -1
        # Check rapid
        target = self.cnc_obj.vars["_OvRapid"]
        current = self.cnc_obj.vars["OvRapid"]
        if target == current:
            pass
        elif target == 100:
            self.master.serial_write(OV_RAPID_100)
        elif target == 75:
            # FIXME: GRBL protocol does not specify 75% override command at all
            self.master.serial_write(OV_RAPID_50)
        elif target == 50:
            self.master.serial_write(OV_RAPID_50)
        elif target == 25:
            self.master.serial_write(OV_RAPID_25)
        # Check Spindle
        diff = self.cnc_obj.vars["_OvSpindle"] - self.cnc_obj.vars["OvSpindle"]
        if diff == 0:
            pass
        elif self.cnc_obj.vars["_OvSpindle"] == 100:
            self.master.serial_write(OV_SPINDLE_100)
        elif diff >= 10:
            self.master.serial_write(OV_SPINDLE_i10)
            self.cnc_obj.vars["_OvChanged"] = diff > 10
        elif diff <= -10:
            self.master.serial_write(OV_SPINDLE_d10)
            self.cnc_obj.vars["_OvChanged"] = diff < -10
        elif diff >= 1:
            self.master.serial_write(OV_SPINDLE_i1)
            self.cnc_obj.vars["_OvChanged"] = diff > 1
        elif diff <= -1:
            self.master.serial_write(OV_SPINDLE_d1)
            self.cnc_obj.vars["_OvChanged"] = diff < -1

    def parseBracketAngle(self, line, cline):
        self.master.sio_status = False
        fields = line[1:-1].split("|")
        self.cnc_obj.vars["pins"] = ""

        # Report if state has changed
        if self.cnc_obj.vars["state"] != fields[0] or self.master.runningPrev != self.master.running:
            self.master.controllerStateChange(fields[0])
        self.master.runningPrev = self.master.running
        self.cnc_obj.vars["state"] = fields[0]

        for field in fields[1:]:
            word = SPLITPAT.split(field)
            if word[0] == "MPos":
                try:
                    self.cnc_obj.vars["mx"] = float(word[1])
                    self.cnc_obj.vars["my"] = float(word[2])
                    self.cnc_obj.vars["mz"] = float(word[3])
                    self.cnc_obj.vars["wx"] = round(
                        self.cnc_obj.vars["mx"]-self.cnc_obj.vars["wcox"], CNC.digits)
                    self.cnc_obj.vars["wy"] = round(
                        self.cnc_obj.vars["my"]-self.cnc_obj.vars["wcoy"], CNC.digits)
                    self.cnc_obj.vars["wz"] = round(
                        self.cnc_obj.vars["mz"]-self.cnc_obj.vars["wcoz"], CNC.digits)
                    # if Utils.config.get("bCNC","enable6axis") == "true":
                    if len(word) > 4:
                        self.cnc_obj.vars["ma"] = float(word[4])
                        self.cnc_obj.vars["wa"] = round(
                            self.cnc_obj.vars["ma"]-self.cnc_obj.vars["wcoa"], CNC.digits)
                    if len(word) > 5:
                        self.cnc_obj.vars["mb"] = float(word[5])
                        self.cnc_obj.vars["wb"] = round(
                            self.cnc_obj.vars["mb"]-self.cnc_obj.vars["wcob"], CNC.digits)
                    if len(word) > 6:
                        self.cnc_obj.vars["mc"] = float(word[6])
                        self.cnc_obj.vars["wc"] = round(
                            self.cnc_obj.vars["mc"]-self.cnc_obj.vars["wcoc"], CNC.digits)
                    self.master._posUpdate = True
                except (ValueError, IndexError):
                    self.cnc_obj.vars["state"] = "Garbage receive %s: %s" % (
                        word[0], line)
                    print("error: {}".format(self.cnc_obj.vars["state"]))
                    break
            elif word[0] == "F":
                try:
                    self.cnc_obj.vars["curfeed"] = float(word[1])
                except (ValueError, IndexError):
                    self.cnc_obj.vars["state"] = "Garbage receive %s: %s" % (
                        word[0], line)
                    print("error: {}".format(self.cnc_obj.vars["state"]))
                    break
            elif word[0] == "FS":
                try:
                    self.cnc_obj.vars["curfeed"] = float(word[1])
                    self.cnc_obj.vars["curspindle"] = float(word[2])
                except (ValueError, IndexError):
                    self.cnc_obj.vars["state"] = "Garbage receive %s: %s" % (
                        word[0], line)
                    print("error: {}".format(self.cnc_obj.vars["state"]))
                    break
            elif word[0] == "Bf":
                try:
                    self.cnc_obj.vars["planner"] = int(word[1])
                    self.cnc_obj.vars["rxbytes"] = int(word[2])
                except (ValueError, IndexError):
                    self.cnc_obj.vars["state"] = "Garbage receive %s: %s" % (
                        word[0], line)
                    print("error: {}".format(self.cnc_obj.vars["state"]))
                    break
            elif word[0] == "Ov":
                try:
                    self.cnc_obj.vars["OvFeed"] = int(word[1])
                    self.cnc_obj.vars["OvRapid"] = int(word[2])
                    self.cnc_obj.vars["OvSpindle"] = int(word[3])
                except (ValueError, IndexError):
                    self.cnc_obj.vars["state"] = "Garbage receive %s: %s" % (
                        word[0], line)
                    print("error: {}".format(self.cnc_obj.vars["state"]))
                    break
            elif word[0] == "WCO":
                try:
                    self.cnc_obj.vars["wcox"] = float(word[1])
                    self.cnc_obj.vars["wcoy"] = float(word[2])
                    self.cnc_obj.vars["wcoz"] = float(word[3])
                    # if Utils.config.get("bCNC","enable6axis") == "true":
                    if len(word) > 4:
                        self.cnc_obj.vars["wcoa"] = float(word[4])
                    if len(word) > 5:
                        self.cnc_obj.vars["wcob"] = float(word[5])
                    if len(word) > 6:
                        self.cnc_obj.vars["wcoc"] = float(word[6])
                except (ValueError, IndexError):
                    self.cnc_obj.vars["state"] = "Garbage receive %s: %s" % (
                        word[0], line)
                    print("error: {}".format(self.cnc_obj.vars["state"]))
                    break
            elif word[0] == "Pn":
                try:
                    self.cnc_obj.vars["pins"] = word[1]
                    if 'S' in word[1]:
                        if self.cnc_obj.vars["state"] == 'Idle' and not self.master.running:
                            print("Stream requested by CYCLE START machine button")
                            self.master.event_generate("<<Run>>", when='tail')
                        else:
                            print("Ignoring machine stream request, because of state: ",
                                  self.cnc_obj.vars["state"], self.master.running)
                except (ValueError, IndexError):
                    break

        # Machine is Idle buffer is empty stop waiting and go on
        if self.master.sio_wait and not cline and fields[0] not in ("Run", "Jog", "Hold"):
            # if not self.master.running: self.master.jobDone() #This is not a good idea, it purges the controller while waiting for toolchange. see #1061
            self.master.sio_wait = False
            self.master._gcount += 1

    def parseBracketSquare(self, line):
        word = SPLITPAT.split(line[1:-1])
        # print word
        if word[0] == "PRB":
            self.cnc_obj.vars["prbx"] = float(word[1])
            self.cnc_obj.vars["prby"] = float(word[2])
            self.cnc_obj.vars["prbz"] = float(word[3])
            # if self.running:
            
            self.cnc_obj.vars[word[0]] = word[1:]
        if word[0] == "G92":
            self.cnc_obj.vars["G92X"] = float(word[1])
            self.cnc_obj.vars["G92Y"] = float(word[2])
            self.cnc_obj.vars["G92Z"] = float(word[3])
            # if Utils.config.get("bCNC","enable6axis") == "true":
            if len(word) > 4:
                self.cnc_obj.vars["G92A"] = float(word[4])
            if len(word) > 5:
                self.cnc_obj.vars["G92B"] = float(word[5])
            if len(word) > 6:
                self.cnc_obj.vars["G92C"] = float(word[6])
            self.cnc_obj.vars[word[0]] = word[1:]
            self.master._gUpdate = True
        if word[0] == "G28":
            self.cnc_obj.vars["G28X"] = float(word[1])
            self.cnc_obj.vars["G28Y"] = float(word[2])
            self.cnc_obj.vars["G28Z"] = float(word[3])
            self.cnc_obj.vars[word[0]] = word[1:]
            self.master._gUpdate = True
        if word[0] == "G30":
            self.cnc_obj.vars["G30X"] = float(word[1])
            self.cnc_obj.vars["G30Y"] = float(word[2])
            self.cnc_obj.vars["G30Z"] = float(word[3])
            self.cnc_obj.vars[word[0]] = word[1:]
            self.master._gUpdate = True
        elif word[0] == "GC":
            self.cnc_obj.vars["G"] = word[1].split()
            self.cnc_obj.updateG()
            self.master._gUpdate = True
        elif word[0] == "TLO":
            self.cnc_obj.vars[word[0]] = word[1]
            self.master._probeUpdate = True
            self.master._gUpdate = True
        else:
            self.cnc_obj.vars[word[0]] = word[1:]
