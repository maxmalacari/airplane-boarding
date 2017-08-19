# Airplane boarding simulation
# Max Malacari - 19 Aug 2017

# Random passenger seats (or seated in order)
# Includes a wait timer
# No lag between movements when there is a queue (ie. wait extra time step after movement resumes)

verbose = True
debug = False
delay = True

waitMultiplier = 2 # x nPassengers in the way of their seat is the number of steps they must wait
stowSteps = 2 # time steps taken to stow bag
bagProb = 1 # probability of having a carry on bag

import pygame as pg
import random as rand
import sys

# Set up the drawing window
wWidth = 200
wHeight = 600
rows = 20
seatsPerRow = 6 # ie. 737, should be an even number
halfRow = seatsPerRow/2
nSeats = rows * seatsPerRow
gridSpacesPerRow = seatsPerRow + 1 # include an aisle

# Some colours
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
darkBlue = (0,0,128)
white = (255,255,255)
black = (0,0,0)
yellow = (255,255,0)

w = wWidth / gridSpacesPerRow
h = wHeight / rows

pg.init()
screen = pg.display.set_mode((wWidth,wHeight+1))
screen.fill(black)

class Passenger():
    def __init__(self, seat, ident, hasBag):
        self.ident = ident
        self.seatNo = seat # what is our assigned seat
        self.seatRow = getSeatRow(seat)
        self.seatCol = getSeatCol(seat)
        self.currRow = -1 # what row are we currently in (-1 = not on plane yet)
        self.hasBag = hasBag
        self.seated = False # are we already seated?
        if hasBag:
            self.bagStowed = False # is bag stowed?
            self.waitTimer = stowSteps - 1 # extra steps to stow bag (in addition to one time step)
        else:
            self.bagStowed = True
        self.stowing = False
        self.waiting = False

    def show(self):
        if self.seated:
            pg.draw.circle(screen, green, (self.seatCol*w + w/2, self.seatRow*h + h/2), 5, 0)
        elif self.stowing:
            pg.draw.circle(screen, blue, (halfRow*w + w/2, self.currRow*h + h/2), 5, 0)
        elif self.waiting:
            pg.draw.circle(screen, yellow, (halfRow*w + w/2, self.currRow*h + h/2), 5, 0)
        else:
            pg.draw.circle(screen, red, (halfRow*w + w/2, self.currRow*h + h/2), 5, 0)

    def inRow(self):
        if self.currRow == self.seatRow:
            return True
        else:
            return False

    def checkObstruction(self, occupiedSeats):
        nPax = 0
        if self.seatCol > halfRow: # on this side of the aisle check for occupied seats in cols less than seatCol
            for col in range(halfRow+1, self.seatCol):
                if occupiedSeats[self.seatRow][col]:
                    nPax += 1
        else: # on this side of the aisle check for occupied seats in cols greater than seatCol
            for col in range(self.seatCol+1, halfRow):
                if occupiedSeats[self.seatRow][col]:
                    nPax += 1
        return nPax*waitMultiplier

        
def main():

    # Define number of passengers
    nPassengers = nSeats

    # assign seats in boarding order
    unseated = []
    assignSeats(unseated, nPassengers)

    # aisle
    aisle = []
    for r in range(0,rows):
        aisle.append(False)

    # seats
    occupiedSeats = []
    for r in range(0,rows):
        occupiedSeats.append([])
        for c in range(0,gridSpacesPerRow):
            occupiedSeats[r].append(False)
    
    # main time loop
    step = 0
    seated = []
    while len(unseated) > 0:

        step = step + 1
        if verbose:
            print "Timestep:", step
        
        screen.fill(black)
        drawSeatMap()
        
        for thePassenger in unseated:

            thePassenger.stowing = False # any stow flags active last time step are now complete

            if thePassenger.inRow(): # passenger is in their row, they can stow bag, then sit down
                if thePassenger.bagStowed: # the passenger either doesn't have a bag, or they've already stowed it
                    if not thePassenger.waiting: # if we're not already waiting for our timer to run down
                        thePassenger.waitTimer = thePassenger.checkObstruction(occupiedSeats)
                    if thePassenger.waitTimer == 0:
                        print "Passenger", thePassenger.ident, "seated!"
                        thePassenger.seated = True
                        thePassenger.stowing = False
                        thePassenger.waiting = False
                        aisle[thePassenger.currRow] = False # remove them from the aisle
                        unseated.remove(thePassenger) # remove them from the unseated list
                        seated.append(thePassenger)
                        occupiedSeats[thePassenger.seatRow][thePassenger.seatCol] = True # set their seat to occupied
                    else:
                        print "Passenger", thePassenger.ident, "is waiting", thePassenger.waitTimer, "time steps..."
                        thePassenger.waiting = True
                        thePassenger.waitTimer -= 1 # remove one time step from the wait timer
                elif not thePassenger.bagStowed and thePassenger.waitTimer == 0: # the passenger has a bag, they can stow it this step and "try" and sit down the next step
                    print "Passenger", thePassenger.ident, "is still stowing their bag"
                    thePassenger.stowing = True
                    thePassenger.bagStowed = True
                elif not thePassenger.bagStowed and thePassenger.waitTimer > 0:
                    print "Passenger", thePassenger.ident, "is stowing their bag"
                    thePassenger.waitTimer -= 1
                    thePassenger.stowing = True
            else: # passenger isn't in their row, they need to move still
                # can they move?
                if debug:
                    print thePassenger.ident, thePassenger.currRow+1, aisle[thePassenger.currRow+1] # debug
                if aisle[thePassenger.currRow + 1] == False:
                    thePassenger.currRow = thePassenger.currRow + 1
                    aisle[thePassenger.currRow] = True # move to next row
                    if (thePassenger.currRow - 1) >= 0: # make sure we were actually in the aisle
                        aisle[thePassenger.currRow - 1] = False # vacate current row
                    if verbose:
                        print "Passenger id:", thePassenger.ident, "Assigned seat:", thePassenger.seatNo, "Assigned row:", thePassenger.seatRow, "Current row:", thePassenger.currRow
            
            thePassenger.show() # draw passengers still in the unseated array

        for thePassenger in seated: # let's draw all the seated passengers
            thePassenger.show()

        pg.display.update()
        print ""
        if delay:
            pg.time.delay(200)

    # no more passengers on the unseated list, we're done!
    print "All passengers seated!"
    print step, "time steps taken to board", nPassengers, "passengers."

    # Stop from instantly closing on finish
    while(True):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit(); sys.exit();



# seats are assigned in boarding order
def assignSeats(passengers, nPassengers):
    seats = rand.sample(range(0,nSeats),nPassengers) # random seats
    for i in range(0, nPassengers): 
        seat = seats[i] # random seats
        #seat = i # seats in order
        p = i+1
        prob = rand.uniform(0,1)
        if prob <= bagProb:
            hasBag = True
        else:
            hasBag = False
        passengers.append(Passenger(seat, p, hasBag)) # assign seats in number order
        if verbose:
            if hasBag:
                print "Passenger", p, "has seat", seat, "and carry on"
            else:
                print "Passenger", p, "has seat", seat, "and no carry on"

                
# get row corresponding to a particular seat
def getSeatRow(seat):
    row = seat/seatsPerRow
    row = rows - row - 1 # reverse rows so plane fills from rear
    return row


# get column corresponding to a particular seat
def getSeatCol(seat):
    col = seat%seatsPerRow
    if col >= halfRow: # if we're more than halfway along the row, add the aisle
        col = col + 1
    return col


# draw the seat map
def drawSeatMap():
    for i in range(0,gridSpacesPerRow):
        for j in range(0,rows):
            pg.draw.lines(screen, white, False, ((i*w,j*h),((i+1)*w,j*h)), 1)
            pg.draw.lines(screen, white, False, (((i+1)*w,j*h),((i+1)*w,(j+1)*h)), 1)
            pg.draw.lines(screen, white, False, ((i*w,(j+1)*h),((i+1)*w,(j+1)*h)), 1)
            pg.draw.lines(screen, white, False, ((i*w,j*h),(i*w,(j+1)*h)), 1)
        
main()
