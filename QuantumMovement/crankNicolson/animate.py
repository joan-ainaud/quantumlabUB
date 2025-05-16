# ! ! !TO DO
# Fix sacle and cutoff to work with new implementation of changing between mod2/phase/real/imag representation
# Ek: Vermell, V: Blau,  E: Lila
from matplotlib.artist import Artist
from matplotlib import animation
import matplotlib.pyplot as plt
import matplotlib.patheffects as peffects
from matplotlib.colors import LinearSegmentedColormap
#basic_cols=['#75b765', '#101010', '#ffd700']
basic_cols=['#00ffff', '#101010', '#ff0000']
div_cmap=LinearSegmentedColormap.from_list('bl_div_cmap', basic_cols)

if (__name__ == "crankNicolson.animate"):
    import crankNicolson.crankNicolson2D as mathPhysics
    from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg, NavigationToolbar2Kivy
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from kivy.graphics.texture import Texture
    from kivy.graphics import Rectangle, Color

    from kivy.clock import Clock

    # Supposedly faster kivy-matplotlib alternative? https://github.com/mp-007/kivy_matplotlib_widget # But better not

    #https://github.com/kivy-garden/garden.matplotlib/blob/master/backend_kivyagg.py
    #https://github.com/kivy-garden/garden.matplotlib/blob/master/backend_kivy.py
    #
    class FigureCanvasKivyAggModified(FigureCanvasKivyAgg):
        def drawOptimized(self):
            """Basically copy of original draw, but original first updates matplotlib figure and then pastes figure into kivy
            This is the latter, the kivy figure must be updated outside manually, i.e. blitting, which is faster than using .draw()
            matplotlib draw() is very slow (because we redraw axis, ticks, everything we don't need to always)!
            """
            self.canvas.clear()   # THIS IS IMPORTANT. Else, memory leak!!!
            """#
            try:
                FigureCanvasAgg.update(self)
            except:
                FigureCanvasKivyAgg.draw_idle(self)
            FigureCanvasAgg.flush_events(self)"""

            if self.blitbox is None:
                l, b, w, h = self.figure.bbox.bounds
                w, h = int(w), int(h)
                buf_rgba = self.get_renderer().buffer_rgba()
            else:
                bbox = self.blitbox
                l, b, r, t = bbox.extents
                w = int(r) - int(l)
                h = int(t) - int(b)
                t = int(b) + h
                reg = self.copy_from_bbox(bbox)
                buf_rgba = reg.to_string()
            texture = Texture.create(size=(w, h))
            texture.flip_vertical()
            color = self.figure.get_facecolor()
            with self.canvas:
                Color(*color)
                Rectangle(pos=self.pos, size=(w, h))
                Color(1.0, 1.0, 1.0, 1.0)
                self.img_rect = Rectangle(texture=texture, pos=self.pos,
                                          size=(w, h))
            texture.blit_buffer(bytes(buf_rgba), colorfmt='rgba', bufferfmt='ubyte')
            self.img_texture = texture

    # Another problem with FigureCanvasKivyAgg: It doesn't get closed properly?
    # Something is going on that stops them from being Garbage Collected (freed from memory once deleted, not more in use)

else:
    import crankNicolson2D as mathPhysics  # Problems with making it work outside of folder
import numpy as np
import time
#import matplotlib.style as mplstyle

# mplstyle.use('fast')
"""On performance:
    https://matplotlib.org/stable/users/explain/performance.html"""

#plt.rcParams['figure.constrained_layout.use'] = True   # Not reaaaally working

#matplotlib.rcParams['keymap.back'].remove('left')
#matplotlib.rcParams['keymap.forward'].remove('right')


# fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)

def cleanFigClose(fig):
    """
    Close figure trying to avoid memory leaks!!!
    :param fig: figure to be closed cleanly
    """
    try: fig.canvas.canvas.clear()  # this is for the kivy widget. Makes no sense otherwise
    except: pass
    fig.clf()
    plt.close(fig)

#from colorsys import hls_to_rgb
from matplotlib.colors import hsv_to_rgb
def Complex2HSV(z, rmin=None, rmax=None, hue_start=90, mod="mod2"):
    """
    https://stackoverflow.com/a/36082859
    """
    # get amplidude of z and limit to [rmin, rmax]
    amp = np.abs(z) if mod=="mod" else mathPhysics.abs2(z) if mod=="mod2" else np.ones_like(z, dtype=np.int)
    #amp = mathPhysics.abs2(z)    #We can use mod or mod^2. Mod allows better focus on phase
    if rmin != None: amp = np.where(amp < rmin, rmin, amp)
    if rmax != None: amp = np.where(amp > rmax, rmax, amp)
    ph = np.angle(z, deg=True) + hue_start
    # HSV are values in range [0,1]
    h = (ph % 360) / 360
    s = 0.85 * np.ones_like(h)
    v = amp/np.max(amp)#(amp -rmin) / (rmax - rmin)
    return hsv_to_rgb(np.dstack((h,s,v)))

# We transpose!!! Because we take [i,j] -> i corresponds to x, j to y
# Whereas in matrix representation (imshow), i would be row (y) and j column (x)
def plotComplexData(arr, type='mod2', mod="mod2"):
    if type=='phase':
        return Complex2HSV(arr.T, mod=mod)
    elif type=='real':
        return arr.real.T
    elif type=='imag':
        return arr.imag.T
    return mathPhysics.abs2(arr).T

def plotComplex(arr, ax, type, range):
    """
    Returns plot (matplotlib drawing) of complex function, with different possible formats
    :param arr: Wave function data, psi. Can be 1d or 2d complex array
    :param ax: axis to be drawn on
    :param type: type of plot: Modulus^2, phase, real, imaginary
    :param range: Either boundaries (x0, xf, y0, yf) for 2D data or X array for 1D [x0, x0+dx, ..., xf]
    :return: Plotted wavefunction
    """
    if arr.ndim == 1:
        if type != 'phase':
            return ax.plot(range, plotComplexData(arr, type))
        else:
            ax.margins(0.)
            data = plotComplexData(arr)
            ymin, ymax = (data.min(), data.max())
            dat = ax.imshow(plotComplexData(arr, type, mod="phase"),extent=(range[0],range[-1], ymin, ax.get_ylim()[1]),interpolation='bilinear', aspect='auto')
            filll = ax.fill_between(range, data, ymax, color='w')
            plott = ax.plot(range, data, 'k')
            return dat, filll, plott

    if type=='phase':
        return ax.imshow(plotComplexData(arr, type), origin='lower', extent=range, aspect='equal', interpolation='none')
    elif type=='mod2':
        return ax.imshow(plotComplexData(arr, type), origin='lower', extent=range, aspect='equal',
                         cmap="viridis", interpolation='none')
    else:
        maxV = np.max(plotComplexData(arr, type))
        minV = np.min(plotComplexData(arr, type))
        sym = max(maxV, abs(minV))
        return ax.imshow(plotComplexData(arr, type), origin='lower', extent=range, aspect='equal',
                     cmap=div_cmap, interpolation='none', vmin=-sym,vmax=sym)

optimizeGraphics = True

class QuantumAnimation:  # inches
    def __init__(self, QSystem, width=6.4, height=4.8,
                 dtSim=0.01, dtAnim=0.05, duration=None, realTime=True,
                 showEnergy=False, forceEnergy=False, showNorm=False, forceNorm=False, showMomentum=False, showPotential=False, varyingPotential=False,
                 psiRepresentation="mod2", momRepresentation="mod2",
                 potentialCutoff=None, psiCutoff=None, scalePsi=False, scaleMom=False, zoomMom=1., scalePot=True,
                 extraCommands=[], extraUpdates=None, extraUpdatesStart=False, extraUpdatesUpdate=False, isKivy=False, stepsPerFrame=0,
                 debugTime=False, callbackProgress=False, isFocusable=True,
                 drawClassical=False, drawClassicalTrace=False, drawExpected=False, drawExpectedTrace=False,
                 unit_dist='Å', unit_time='fs', unit_energy='eV', unit_mom=r'$\frac{1}{2}\hbar Å^{-1}$',
                 toolbar=False, customPlot=None, customPlotUpdate=False, customPlotFull=False,
                 language='eng'):
        """
        Declaration of a Quantum Animation
        :param QSystem: Quantum System. The physics happen here, see crankNikolson2D QuantumSystem class.
        :param width: width of figure (inches)
        :param height: height of figure (inches)
        :param dtSim: dt of Simulation. The system will be evolved (Crank-Nicolson 2D ADI) with this dt.
        :param dtAnim: dt of Animation. Should be a multiple of dtSim. Every frame corresponds to dtAnim, and thus
        the quantum system is evolved dtAnim/dtSim times each frame.
        :param duration: Duration of animation.
        :param showEnergy: set to True to show Kinetic/Potential/Total Energy
        :param showNorm: set to True to show how the norm evolves (doesn't always remain constant)
        :param showMomentum: set to True to show the system in momentum space
        :param showPotential: set to True to show the potential acting on the system
        :param varyingPotential: set to update the potential in case it will evolve. Important for games
        :param potentialCutoff: Don't draw potential at points where it's value is below cutoff
        :param psiCutoff: Don't draw psi at points where it's value (module) is below cutoff
        :param scalePsi: set to True to rescale colorscale of position space. Helps see if the particle dissipates, but
        makes it harder to see how small is the probability of each section in absolute terms
        :param scaleMom: set to True to rescale colorsacale of momentum space.
        :param extraCommands: Trigger actions, for example on click, and command to execute:
        extraCommands = [(action1, command1), (action2, command2), ...]. command: function. Action, ex: 'key_press_event'
        :param extraUpdates: Run some extra functions every update
        :param isKivy: Links canvas to Kivy Backend and disables automatic animation
        :param customPlot: Tuple: (createPlot, updatePlot). updatePlot should return True if redraw necessary.
        :param language: 3word string representing language. Available: eng, esp, cat
        """

        self.dtAnim = dtAnim
        self.dtSim = dtSim
        self.stepsPerFrame = stepsPerFrame  # If 0, that means try "real time" with dtAnim
        self.imagdt = False

        if (int(dtSim / dtAnim) != dtSim // dtAnim): print(
            "WARNING: dtAnim is not a multiple of dtSim, can't do real time")
        self.QSystem = QSystem
        self.width = width
        self.height = height
        self.frame = 0

        self.duration = duration
        self.realTime = realTime
        if (duration == None or isKivy):
            self.frames = None
        elif realTime:
            self.frames = int(duration / dtAnim + 1)
        else:
            self.frames = int(duration / (dtAnim if stepsPerFrame == 0 else dtSim * stepsPerFrame))
        # Simulation time. Careful...

        self.showEnergy = showEnergy
        self.forceEnergy = forceEnergy
        self.showNorm = showNorm
        self.forceNorm = forceNorm
        self.showMomentum = showMomentum
        self.showPotential = showPotential
        self.varyingPotential = varyingPotential
        self.potentialCutoff = potentialCutoff

        self.psiRepresentation = psiRepresentation
        self.momRepresentation = momRepresentation
        self.psiCutoff = psiCutoff
        self.scalePsi = scalePsi
        self.scaleMom = scaleMom
        self.zoomMom = zoomMom
        self.scalePot = scalePot

        self.customPlot = customPlot
        self.customPlotUpdate = customPlotUpdate
        self.customPlotFull = customPlotFull

        self.unit_dist = unit_dist
        self.unit_energy = unit_energy
        self.unit_time = unit_time
        self.unit_mom = unit_mom

        self.units = {"unit_dist": unit_dist, "unit_energy": unit_energy, "unit_time": unit_time, "unit_mom": unit_mom}

        self.language = language

        self.paused = isKivy  #if isKivy we start paused, else the animation is ready to play
        self.text = None

        self.debugTime = debugTime
        self.callbackProgress = callbackProgress

        self.extraCommands = extraCommands
        self.extraUpdates = extraUpdates
        self.extraUpdatesStart = extraUpdatesStart
        self.extraUpdatesUpdate = extraUpdatesUpdate
        # Extra Commands: [(action1, command1), (action2, command2), ...]

        self.TList = []
        self.KList = []
        self.VList = []
        self.EList = []
        self.NormList = []
        self.potentialMat = np.ndarray((self.QSystem.Nx + 1, self.QSystem.Ny + 1), dtype=np.float64)
        # Nx+1 points!!! x0, x1, ..., xNx
        self.isKivy = isKivy

        if not self.isKivy:
            self.fig = plt.figure(figsize=(width, height))#, layout="constrained")
        else:
            self.fig = plt.figure()#layout="constrained")  # Not working with this old matplotlib version

            FigureCanvasKivyAggModified(self.fig, is_focusable=isFocusable)  # Canvas is now Kivy Canvas
            # If we do a Kivy Canvas, we can't use FuncAnimation which implements blitting automatically,
            # so we need to implement blitting manually. To do this, we need to keep track of when we update the figure
            # self.drawEvent = self.fig.canvas.mpl_connect('draw_event', self.on_draw) # For Blitting, if it worked?
            # self.bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)
            if toolbar: self.navigation = NavigationToolbar2Kivy(self.fig.canvas)

        # fig.canvas.mpl_disconnect(fig.canvas.manager.key_press_handler_id)

        if not self.isKivy: self.pauseEvent = self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)


        self.actExtCommands = []
        if self.extraCommands != None:
            for action, command in self.extraCommands:
                self.actExtCommands.append( self.fig.canvas.mpl_connect(action, command) )

        # Code
        self.axEnergy = None
        self.axNorm = None
        self.axMomentum = None
        self.axCustom = None

        self.datPsi = None
        self.datPot = None
        self.datMom = None
        self.datCustom = None
        self.lineK = None
        self.lineV = None
        self.lineE = None
        self.lineN = None

        self.drawnPos = None
        self.drawnMom = None
        self.drawnParticle = None
        self.drawnParticleMom = None

        self.drawClassical = drawClassical; self.drawClassicalTrace = drawClassicalTrace; self.drawExpected = drawExpected; self.drawExpectedTrace = drawExpectedTrace

        self.updating = False
        self.firstDraw = True

        if self.isKivy:
            Clock.schedule_once(lambda t:
            self.reset_plot(
            drawClassical=drawClassical, drawClassicalTrace=drawClassicalTrace, drawExpected=drawExpected, drawExpectedTrace=drawExpectedTrace,
            forceRecreate=True))
        else:
            self.reset_plot(
                drawClassical=drawClassical, drawClassicalTrace=drawClassicalTrace, drawExpected=drawExpected, drawExpectedTrace=drawExpectedTrace,
                forceRecreate=True)

        self.isOver = False

        if not self.isKivy:
            self.animation = animation.FuncAnimation(self.fig, self.update, interval=dtAnim * 1000, blit=True,
                                                     frames=self.frames)


    def reset_plot(self, width=None, height=None,
                   showEnergy=None, forceEnergy=None, showNorm=None, forceNorm=None, showMomentum=None, showPotential=None,
                   scalePsi=None, scaleMom=None, zoomMom=None, scalePot=None, psiRepresentation=None, momRepresentation=None,
                   drawClassical=None, drawClassicalTrace=None, drawExpected=None, drawExpectedTrace=None,
                   forceRecreate = False, customPlot = None, language=None):

        recreate = False

        if width != None: self.width = width
        if height != None:  self.height = height
        if showEnergy != None: self.showEnergy = showEnergy; recreate = True
        if forceEnergy != None: self.forceEnergy = forceEnergy
        if showNorm != None: self.showNorm = showNorm; recreate = True
        if forceNorm != None: self.forceNorm = forceNorm
        if showMomentum != None: self.showMomentum = showMomentum; recreate = True
        if showPotential != None: self.showPotential = showPotential; recreate = True
        if scalePsi != None: self.scalePsi = scalePsi
        if scaleMom != None: self.scaleMom = scaleMom
        if psiRepresentation != None: self.psiRepresentation = psiRepresentation; recreate = True
        if momRepresentation != None: self.momRepresentation = momRepresentation; recreate = True
        if zoomMom != None: self.zoomMom = zoomMom
        if scalePot != None: self.scalePot = scalePot
        if drawClassical != None: self.drawClassical = drawClassical
        if drawClassicalTrace != None: self.drawClassicalTrace = drawClassicalTrace
        if drawExpected != None: self.drawExpected = drawExpected
        if drawExpectedTrace != None: self.drawExpectedTrace = drawExpectedTrace
        if customPlot != None: self.customPlot = customPlot
        if language != None: self.language = language
        lan = self.language

        if not self.isKivy: self.fig.figsize = (self.width, self.height)
        if recreate or forceRecreate:
            extraSubplots = 0
            if self.showEnergy: extraSubplots += 1
            if self.showNorm: extraSubplots += 1
            if self.showMomentum: extraSubplots += 1

            self.fig.clf()  # Clear figure

            cplot = self.customPlot is not None
            extraSubplots += cplot

            self.axPsi = self.fig.add_subplot(1, 2 + (extraSubplots > 0), (1, 2))

            if cplot:
                if extraSubplots == 1:
                    self.axCustom = self.fig.add_subplot(3,3,6) if not self.customPlotFull else self.fig.add_subplot(1,3,3)
                elif extraSubplots == 2 and self.showMomentum:
                    self.axCustom = self.fig.add_subplot(3, 3, 3)
                    cplot = 0
                else: self.axCustom = self.fig.add_subplot(4, 3, 3)
            else:
                self.axCustom = None

            if self.showEnergy:
                self.axEnergy = self.fig.add_subplot(3+cplot, 3, 3*(1+cplot))  # (2, 6, 11)
            else:
                self.axEnergy = None
            if self.showNorm:
                self.axNorm = self.fig.add_subplot(3+cplot, 3, 3*(2+cplot))  # (2, 6, 12)
            else:
                self.axNorm = None
            if self.showMomentum:
                if extraSubplots == 1:
                    self.axMomentum = self.fig.add_subplot(1, 3, 3)
                elif not self.showNorm: self.axMomentum = self.fig.add_subplot(3+cplot, 3, (6+3*cplot,9+3*cplot))
                else: self.axMomentum = self.fig.add_subplot(3+cplot, 3, 3*(3+cplot))  # (2, 3, 3)
            else:
                self.axMomentum = None

            # First drawing
            ###self.QSystem.modSquared()  ### Not generic
            lan = self.language
            title = "Position Space" if lan == 'eng' else "Espai de posicions" if lan == 'cat' else 'Espacio de posiciones'
            if self.scalePsi: title += " (rescaled color)" if lan == 'eng' else " (color reescalat)" if lan == 'cat' else " (color reescalado)"
            self.axPsi.set_title(title)
            self.axPsi.set_xlabel("x ({})".format(self.unit_dist))
            self.axPsi.set_ylabel("y ({})".format(self.unit_dist))
            self.datPsi = plotComplex(self.QSystem.psi,self.axPsi,self.psiRepresentation,(self.QSystem.x0, self.QSystem.xf, self.QSystem.y0, self.QSystem.yf))
            """self.axPsi.imshow(self.QSystem.psiMod.T, origin='lower',
                                            extent=(self.QSystem.x0, self.QSystem.xf, self.QSystem.y0, self.QSystem.yf),
                                            aspect='equal', cmap="viridis",
                                            interpolation='none')  # , animated=True) # Doesn't do anything for imshow?"""
            if self.showPotential:
                self.QSystem.potentialMatrix(self.potentialMat)
                self.datPot = self.axPsi.imshow(self.potentialMat.T, origin='lower',
                                                extent=(self.QSystem.x0, self.QSystem.xf, self.QSystem.y0, self.QSystem.yf),
                                                aspect='equal', cmap='gist_heat', alpha=0.3,
                                                interpolation='none')  # , animated=True)
                # self.fig.colorbar(datPot, ax=ax1, label="Potencial: Força constant cap a baix")

            if self.customPlot is not None:
                self.datCustom = {}
                # First plot
                self.customPlot[0](self.axCustom, self.datCustom, self.QSystem, self.units)


            if self.showEnergy:
                self.axEnergy.set_title("Energy" if lan == 'eng' else "Energia" if lan == 'cat' else "Energía")
                if len(self.TList) == 0: self.axEnergy.set_xlim(self.QSystem.t, self.QSystem.t + 5)
                """# Reshaping axis is slow. This is to make sure we almost surely don't need to
                minValE = min(np.min(self.potentialMat) - 1., 0.)
                maxValE = np.real(self.QSystem.potentialEnergy() + self.QSystem.kineticEnergy() -
                                               minValE)
                visibilityDelta = (maxValE-minValE)*0.02"""
                # In many cases though, the previous measure means we don't see in detail the values of energy.
                Ktemp = np.real(self.QSystem.kineticEnergy())
                Vtemp = np.real(self.QSystem.potentialEnergy())
                minValE = min(Ktemp, Vtemp)
                maxValE = max(Ktemp, Ktemp+Vtemp)
                visibilityDelta = (maxValE - minValE) * 0.04
                self.axEnergy.set_ylim(minValE-visibilityDelta, maxValE+visibilityDelta)
                self.axEnergy.set_ylabel("({})".format(self.unit_energy))
                if not self.showNorm: self.axEnergy.set_xlabel("t ({})".format(self.unit_time))
                self.lineK, = self.axEnergy.plot(self.TList, self.KList, 'red',
                                                 label="K")  # , animated=True)  #Doesn't seem to speed up anything. Just complicates things
                self.lineV, = self.axEnergy.plot(self.TList, self.VList, 'blue', label="V")  # , animated=True)
                self.lineE, = self.axEnergy.plot(self.TList, self.EList, 'purple', label="E")  # , animated=True)   #Colors before were gray here and nothing for others
                self.axEnergy.grid()
                self.axEnergy.legend()

            if self.showNorm:
                self.axNorm.set_title("Normalization" if lan == 'eng' else "Normalització" if lan == 'cat' else "Normalización")
                self.axNorm.set_xlabel("t ({})".format(self.unit_time))
                if len(self.TList) == 0: self.axNorm.set_xlim(self.QSystem.t, self.QSystem.t + 5)  # 0, 5
                ####
                self.axNorm.set_ylim(1 - 0.001, 1. + 0.001)
                ##### SI es vol optimitzar fent blitting s'ha d'evitar fer canvis de límit
                self.lineN, = self.axNorm.plot(self.TList, self.NormList)  # , animated=True)  #Doesn't work wit hKivy?

            if self.showMomentum:
                self.QSystem.momentumSpaceModSquared()
                title = "Momentum space" if lan == 'eng' else "Espai de moments" if lan == 'cat' else "Espacio de momentos"
                if self.scaleMom: title += " (rescaled color)" if lan == 'eng' else " (color reescalat)" if lan == 'cat' else " (color reescalado)"
                self.axMomentum.set_title(title)
                self.axMomentum.set_xlabel("Px ({})".format(self.unit_mom))
                self.axMomentum.set_ylabel("Py ({})".format(self.unit_mom))
                self.datMom = self.axMomentum.imshow(self.QSystem.psiMod.T, origin='lower',
                                                     extent=(self.QSystem.Px[0], self.QSystem.Px[-1],
                                                             self.QSystem.Py[0], self.QSystem.Py[-1]),
                                                     cmap='hot', aspect='equal', interpolation='none')  # , animated = True)
                if 0 < self.zoomMom < 1.:
                    self.axMomentum.set_xlim(self.QSystem.Px[0] * self.zoomMom, self.QSystem.Px[-1] * self.zoomMom)
                    self.axMomentum.set_ylim(self.QSystem.Py[0] * self.zoomMom, self.QSystem.Py[-1] * self.zoomMom)


            self.drawnParticle = None
            self.drawnParticleMom = None
            self.drawnPos = None
            self.drawnMom = None


        if self.drawnParticle is not None: self.drawnParticle.remove()
        if self.drawnParticleMom is not None and self.showMomentum: self.drawnParticleMom.remove()
        if self.drawClassical:
                                          # Particle deviates, so it is only adjusted to the QSystem the first time it is shown
            if drawClassical is not None: self.particle = mathPhysics.ClassicalParticle(self.QSystem)
            self.drawnParticle = plt.Circle((self.particle.x, self.particle.y), (self.QSystem.xf-self.QSystem.x0)/100.,
                                            color='whitesmoke', alpha=0.5)
            self.axPsi.add_patch(self.drawnParticle)

            if self.showMomentum:
                self.drawnParticleMom = plt.Arrow(0.,0., self.particle.px, self.particle.py,
                                                color='white', alpha=0.5)
                #(self.QSystem.Px[-1] - self.QSystem.Px[0]) / 100.
                self.axMomentum.add_patch(self.drawnParticleMom)

        else: self.drawnParticle = None; self.drawnParticleMom = None

        if self.drawnPos is not None: self.drawnPos.remove()
        if self.drawnMom is not None and self.showMomentum: self.drawnMom.remove()
        if self.drawExpected:
            self.drawnPos = plt.Circle((self.QSystem.expectedX(), self.QSystem.expectedY()),
                                    (self.QSystem.xf - self.QSystem.x0) / 150.,
                                    color='orange', alpha=0.5)
            self.axPsi.add_patch(self.drawnPos)

            if self.showMomentum:
                self.drawnMom = plt.Arrow(0.,0., self.QSystem.expectedPx(), self.QSystem.expectedPy(),
                                                color='brown', alpha=0.5)

                self.axMomentum.add_patch(self.drawnMom)

        else: self.drawnPos = None; self.drawnMom = None

        if self.extraUpdatesStart and self.extraUpdates is not None:
            for action in self.extraUpdates:
                updated = action(instance=self)
                # except: updated = action()
                """if updated != None:
                    if type(updated) is tuple:
                        for el in updated:
                            self.fig.draw_artist(el)
                    else:
                        self.fig.draw_artist(updated)"""


        self.fig.tight_layout()   # In newer matplotlib versions we should use constrained layouts
        if self.isKivy: self.fig.canvas.draw()

        self.firstDraw = False

    def reset_lists(self):
        self.KList = []
        self.VList = []
        self.EList = []
        self.NormList = []
        self.TList = []
        self.potentialMat = np.ndarray((self.QSystem.Nx + 1, self.QSystem.Ny + 1), dtype=np.float64)

    def setExtCommands(self, newCommands):
        for oldCommand in self.actExtCommands:
            self.fig.canvas.mpl_disconnect(oldCommand)
        self.actExtCommands.clear()

        self.extraCommands = newCommands
        for action, command in newCommands:
            self.actExtCommands.append(self.fig.canvas.mpl_connect(action, command))

    def addExtCommands(self, newCommands):
        self.extraCommands += newCommands
        for action, command in newCommands:
            self.actExtCommands.append(self.fig.canvas.mpl_connect(action, command))

    def on_key_press(self, event):
        if event.key == 'p':
            if self.paused:
                # self.animation.resume()
                self.text.remove()
                self.text = None
                if not self.isKivy: self.animation.event_source.start()
            else:
                # self.animation.pause()

                self.text = self.axPsi.text(0.5, 0.5, 'Paused!', dict(size=30, fontweight=800, color='white'),
                                          horizontalalignment='center', verticalalignment='center',
                                          path_effects=[peffects.withStroke(linewidth=4, foreground="black")])
                self.fig.canvas.draw()
                if not self.isKivy: self.animation.event_source.stop()

            self.paused = not self.paused

    def lineRedraw(self, ax, line, datax, datay, frame):
        # It is assumed there is a point of data for each frame
        line.set_data(datax, datay)
        if datax[frame] > ax.get_xlim()[1]:
            ax.set_xlim(ax.get_xlim()[0], 2 * ax.get_xlim()[1])
            self.redraw = True
        if datay[frame] < ax.get_ylim()[0]:
            axlim0 = ax.get_ylim()[0]
            axlim1 = ax.get_ylim()[1]

            try: ax.set_ylim(datay[frame] - (axlim1 - axlim0) * 0.05, axlim1)
            except:
                ax.relim()
                ax.autoscale_view()
            self.redraw = True
        if datay[frame] > ax.get_ylim()[1]:
            axlim0 = ax.get_ylim()[0]
            axlim1 = ax.get_ylim()[1]

            try: ax.set_ylim(axlim0, datay[frame] + (axlim1 - axlim0) * 0.05)
            except:
                ax.relim()
                ax.autoscale_view()
            self.redraw = True

    def update(self, frame, onlyDraw=False):
        changes = []
        t0 = time.time()
        self.redraw = False  # Will try to not redraw, only blit, except when necessary (bounds change, etc.)
        if not onlyDraw:
            if self.duration is not None and self.callbackProgress and frame % 10 == 0: print(
                "{:5.2f} %".format(100 * frame / self.frames))


            if self.frames == None and self.duration != None:
                # if frame == self.frames-1:
                if self.QSystem.t >= self.duration:
                    if not self.isKivy: self.fig.canvas.mpl_disconnect(self.pauseEvent)
                    if not self.isKivy: self.animation.event_source.stop()
                    if self.text != None: self.text.remove()
                    self.text = self.axPsi.text(0.5, 0.5, 'TIME!', dict(size=30, fontweight=800, color='white'),
                                              horizontalalignment='center', verticalalignment='center',
                                              path_effects=[peffects.withStroke(linewidth=4, foreground="black")],
                                              transform=self.axPsi.transAxes)

                    self.isOver = True

            self.frame = frame  # Redundant?

            for _ in range(max(1, int(self.dtAnim / self.dtSim)) if self.stepsPerFrame == 0 else self.stepsPerFrame):
                if self.imagdt:
                    self.QSystem.evolveImagStep(self.dtSim)
                else:
                    self.QSystem.evolveStep(self.dtSim)
                    if self.drawClassical:
                        for _ in range(8): self.particle.evolveStep(self.dtSim/8)


            if self.debugTime: print("Time step (x{:d}):  {:12.8f}".format(max(1, int(self.dtAnim / self.dtSim)) if self.stepsPerFrame == 0 else self.stepsPerFrame
                                                                                      , time.time() - t0), " (s)", end=' <> ')

        #self.QSystem.modSquared()
        if self.psiCutoff != None:
            self.QSystem.psiMod[self.QSystem.psiMod < self.psiCutoff] = None
        # this is not optimal. It would be nice to have a numpy function that finds minimum and maximum on same loop # https://stackoverflow.com/questions/12200580/numpy-function-for-simultaneous-max-and-min
        if self.scalePsi and self.psiRepresentation!='phase': self.rescalePsi()#self.datPsi.set_clim(vmax=np.max(self.datPsi.get_array()),
                                                              #                     vmin=0. if self.psiRepresentation == 'mod2' else np.min(self.datPsi.get_array()))
                                                                                        #self.QSystem.psiMod.T

        self.datPsi.set_data(plotComplexData(self.QSystem.psi,self.psiRepresentation))#self.QSystem.psiMod.T)
        changes.append(self.datPsi)

        if self.showPotential:
            if self.varyingPotential:
                self.QSystem.potentialMatrix(self.potentialMat)
                if self.potentialCutoff != None:
                    self.potentialMat[self.potentialMat < self.potentialCutoff] = None
                #if onlyDraw: self.datMom.set_clim(vmax=np.max(self.QSystem.psiMod.T), vmin=0.)  # Being general we are slower!
                if self.scalePot: self.datPot.set_clim(vmax=np.max(self.potentialMat), vmin=np.min(self.potentialMat))    # CAN BE OPTIMIZED
                self.datPot.set_data(self.potentialMat.T)
            changes.append(self.datPot)  # Maybe it won't change, but it needs to be shown

        if self.drawClassical and not self.imagdt:
            #Redraw
            if self.drawnParticle != None and not self.drawClassicalTrace: self.drawnParticle.remove()
            self.drawnParticle = plt.Circle((self.particle.x, self.particle.y), (self.QSystem.xf - self.QSystem.x0) / 100.,
                                            color='whitesmoke', alpha=0.5)
            self.axPsi.add_patch(self.drawnParticle)

            """#Recenter  This is to not create a new patch every time.
            if self.drawnParticle == None:
                self.drawnParticle = plt.Circle((self.particle.x, self.particle.y), (self.QSystem.xf - self.QSystem.x0) / 100.,
                                                color='whitesmoke', alpha=0.5)
                self.axPsi.add_patch(self.drawnParticle)
            else:
                self.drawnParticle.set(center=(self.particle.x, self.particle.y))"""
            #self.drawnParticle.set(center=(self.particle.x, self.particle.y)) # "Faster" but doesn't allow trace

        if self.drawExpected:
            if self.drawnPos != None and not self.drawExpectedTrace: self.drawnPos.remove()
            self.drawnPos = plt.Circle((self.QSystem.expectedX(), self.QSystem.expectedY()),
                                       (self.QSystem.xf - self.QSystem.x0) / 150.,
                                       color='orange', alpha=0.5)
            self.axPsi.add_patch(self.drawnPos)
            #self.drawnPos.set(center=(self.QSystem.expectedX(), self.QSystem.expectedY()))  #"Faster" but doesn't allow trace

        for patch in self.axPsi.patches:
            changes.append(patch)

        if self.customPlot is not None:
            self.redraw = self.customPlot[1](self.axCustom, self.datCustom, self.QSystem, self.units)
            for dat in self.datCustom.values():
                if issubclass(type(dat), Artist): changes.append(dat)

        self.TList.append(self.QSystem.t)
        if self.showEnergy or self.forceEnergy:   #Always store it?
            self.KList.append(np.real(self.QSystem.kineticEnergy()))
            self.VList.append(np.real(self.QSystem.potentialEnergy()))
            self.EList.append(self.VList[-1] + self.KList[-1])

            if self.showEnergy:
                length = len(self.KList)
                self.lineRedraw(self.axEnergy, self.lineK, self.TList, self.KList, length-1)  # lineK.set_data(TList, KList)
                self.lineRedraw(self.axEnergy, self.lineV, self.TList, self.VList, length-1)  # lineV.set_data(TList, VList)
                self.lineRedraw(self.axEnergy, self.lineE, self.TList, self.EList, length-1)  # lineE.set_data(TList, EList)
                changes.append(self.lineK)
                changes.append(self.lineV)
                changes.append(self.lineE)
        """else:
            self.KList.append(None)
            self.VList.append(None)
            self.EList.append(None)"""

        if self.showNorm or self.forceNorm:
            self.NormList.append(np.real(self.QSystem.norm()))
            if self.showNorm:
                self.lineRedraw(self.axNorm, self.lineN, self.TList, self.NormList,
                                len(self.NormList)-1)  # lineN.set_data(TList, NormList)
                changes.append(self.lineN)
        """else:
            self.NormList.append(None)"""

        if self.showMomentum:
            self.QSystem.momentumSpaceModSquared()
            if self.scaleMom: self.datMom.set_clim(vmax=np.max(self.QSystem.psiMod.T), vmin=0.)
            self.datMom.set_data(self.QSystem.psiMod.T)
            changes.append(self.datMom)

            # Draw expected and classical momentum as arrows.
            # But if they are very close to 0, the drawing of the arrow turns out
            # ugly, so instead for P ~ 0, a circle at 0 is drawn instead of an arrow.
            if self.drawClassical and not self.imagdt:
                self.drawnParticleMom.remove()
                # No funciona? Versió més moderna potser només de matplotlib # self.drawnParticleMom.set_data(dx=self.particle.px, dy=self.particle.py)


                if abs(self.particle.px) > (self.QSystem.Px[1]-self.QSystem.Px[0]) / 4 or abs(self.particle.py) > (self.QSystem.Py[1] - self.QSystem.Py[0]) / 4:
                    self.drawnParticleMom = plt.Arrow(0., 0., self.particle.px, self.particle.py, color='white', alpha=0.5)
                else:
                    self.drawnParticleMom = plt.Circle((0,0), radius=min((self.QSystem.Px[1] - self.QSystem.Px[0])/4,
                                                                         (self.QSystem.Py[1] - self.QSystem.Py[0])/4), color='white')
                self.axMomentum.add_patch(self.drawnParticleMom)
                changes.append(self.drawnParticleMom)

            if self.drawExpected and not self.imagdt:
                self.drawnMom.remove()

                expPx = self.QSystem.expectedPx()
                expPy = self.QSystem.expectedPy()

                if abs(expPx) > (self.QSystem.Px[1] - self.QSystem.Px[0]) / 4 or abs(expPy) > (
                        self.QSystem.Py[1] - self.QSystem.Py[0]) / 4:
                    self.drawnMom = plt.Arrow(0., 0., expPx, expPy, color='brown',
                                                      alpha=0.5)
                else:
                    self.drawnMom = plt.Circle((0, 0), radius=min((self.QSystem.Px[1] - self.QSystem.Px[0]) / 4,
                                                                          (self.QSystem.Py[1] - self.QSystem.Py[
                                                                              0]) / 4), color='brown')
                self.axMomentum.add_patch(self.drawnMom)
                changes.append(self.drawnMom)


        if self.extraUpdates != None:
            for action in self.extraUpdates:
                updated = action(instance=self)
                # except: updated = action()
                if updated != None:
                    if type(updated) is tuple:
                        for el in updated:
                            changes.append(el)
                    else:
                        changes.append(updated)


        if self.debugTime: print("+ E/Moment/anim_data/etc:  {:12.8f}".format(time.time() - t0), " (s)", end=' <> ')

        # Blitting
        return changes

    """def on_draw(self, event):  # Blitting doesn't seem to work. Won't plot anything. Not clear if it even works faster
        self.bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        self.fig.draw_artist(self.datPsi)
        if self.showPotential:
            self.fig.draw_artist(self.datPot)
        if self.showEnergy:
            self.fig.draw_artist(self.lineE)
            self.fig.draw_artist(self.lineK)
            self.fig.draw_artist(self.lineV)
        if self.showNorm:
            self.fig.draw_artist(self.lineN)
        if self.showMomentum:
            self.fig.draw_artist(self.datMom)"""

    def manualUpdate(self, onlyDraw=False):
        if self.frame == self.frames or self.isOver: return
        t0 = time.time()


        changedArtists = self.update(self.frame, onlyDraw=onlyDraw)

        ###self.fig.canvas.draw()
        # Problem with Kivy
        # "Expected way to reflect changes is just with .draw()"
        # Problem with that, draw is slow! We can't optimize drawing of matplotlib figure
        # That's why we extended the kivy Canvas class

        #Smart update, no axis etc. Doesn't work on Kivy either (update() not defined)
        if self.redraw or not optimizeGraphics:
            self.fig.canvas.draw()
            """# Same?
            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()"""
        else:
            # ... etc, update only necessary stuff
            # redrawing axis every time slows down
            for artistChanged in changedArtists:
                # print("Frame: ", self.frame, ",  artist: ", artistChanged)
                self.fig.draw_artist(artistChanged)

            #self.fig.canvas.blit(self.fig.bbox)

            self.fig.canvas.drawOptimized()  #Pastes matplotlib figure into kivy

        #self.fig.canvas.flush_events() #??

        if not onlyDraw: self.frame += 1
        self.updating = False
        # plt.pause(0.001)
        if self.debugTime: print("+ Ploting:  {:12.8f}".format(time.time() - t0), " (s),   FPS = ",
                                 1. / (time.time() - t0))

    def updatePotentialDraw(self, *args):
        # Updates potential but other stuff too. For example for visualizing changes in parameters
        #t0 = time.time()
        if self.showPotential:
            self.updating = True
            self.QSystem.potentialMatrix(self.potentialMat)
            if self.potentialCutoff != None:
                self.potentialMat[self.potentialMat < self.potentialCutoff] = None
            # if onlyDraw: self.datMom.set_clim(vmax=np.max(self.QSystem.psiMod.T), vmin=0.)  # Being general we are slower!
            if self.scalePot: self.datPot.set_clim(vmax=np.max(self.potentialMat), vmin=np.min(self.potentialMat))  # CAN BE OPTIMIZED
            self.datPot.set_data(self.potentialMat.T)

            self.fig.draw_artist(self.datPsi)
            self.fig.draw_artist(self.datPot)

            artists = set()  # Using a set makes sure we don't repeat draw stuff
            for patch in self.axPsi.patches:
                #self.fig.draw_artist(patch)
                artists.add(patch)
            for line in self.axPsi.lines:
                #self.fig.draw_artist(line)
                artists.add(line)
            for coll in self.axPsi.collections:
                #self.fig.draw_artist(coll)
                artists.add(coll)

            if self.extraUpdatesUpdate and self.extraUpdates is not None:
                for action in self.extraUpdates:
                    updated = action(instance=self)
                    # except: updated = action()
                    if updated != None:
                        if type(updated) is tuple:
                            for el in updated:
                                artists.add(el)
                        else:
                            artists.add(updated)
            if self.customPlotUpdate and self.customPlot is not None:
                self.customPlot[1](self.axCustom, self.datCustom, self.QSystem, self.units)
                for dat in self.datCustom.values():
                    if issubclass(type(dat), Artist): artists.add(dat)

            for art in artists:
                self.fig.draw_artist(art)


            self.fig.canvas.drawOptimized()
            #print("Took {:12.8f} s, in FPS: {:12.8f}".format(time.time()-t0, 1./(time.time()-t0)))
            self.updating = False

    def resetSystem(self, QSystem):
        self.QSystem = QSystem
        self.frame = 0
        self.reset_lists()
        self.reset_plot(forceRecreate=True)

    def rescalePsi(self):
        vmax = np.max(self.datPsi.get_array())
        if self.psiRepresentation == 'mod2':
            self.datPsi.set_clim(vmax=np.max(vmax), vmin=0.)
        else:
            vmin = np.min(self.datPsi.get_array())
            maxVal = max(vmax, abs(vmin))
            self.datPsi.set_clim(vmax=maxVal, vmin=-maxVal)

    def saveAnimation(self, outputName, type="gif"):
        #https://stackoverflow.com/questions/19646520/memory-usage-for-matplotlib-animation
        # Depends on current directory
        from pathlib import Path
        #cwd = Path.cwd()   # Depends on how main.py is run. If run from terminal
                           # path will be main.py folder. PyCharm by default
                           # sets current working directory to Project Folder
        mainDir = Path(__file__).parent.parent       # main.py directory path (parent of parent of animate.py)


        relPath = "./Resultats/{}".format(outputName)
        if type == "gif":
            relPath += ".gif"
            absPath = (mainDir / relPath).resolve()
            writergif = animation.PillowWriter(fps=int(1 / self.dtAnim))
            self.animation.save(absPath, writer=writergif) #dpi for resolution, default 100
            #self.animation.save('./Resultats/{}.gif'.format(outputName), writer=writergif)
        elif type == "mp4":
            relPath += ".mp4"
            absPath = (mainDir / relPath).resolve()
            FFwriter = animation.FFMpegWriter(fps=int(1 / self.dtAnim))
            self.animation.save(absPath, writer=FFwriter)
        else:
            print("Output format not supported")



if __name__ == "__main__":
    print("No s'hauria d'executar directament aquest fitxer")