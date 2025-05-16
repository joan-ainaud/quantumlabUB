"""
TODO:
Aharonov Bohm / Double slit: Allow closing some of the slits
Sliders: Allow manual input of specific value. Ex 2.00, instead of 2.01, 1.99
"""

from matplotlib import use
use('Agg')    #STOP MEMORY LEAKS  #https://stackoverflow.com/questions/72271763/matplotlib-memory-leak-when-saving-figure-in-a-loop
#matplotlib.use('module://kivy.garden.matplotlib.backend_kivyagg')
# Should this be used? Can't save to file then? Better not, implicitly draws figure using agg

from functools import partial

# Combine functions. For example useful for callbacks
def combF(f1, f2):
    def f(*args, **kwargs):
        f1(*args, **kwargs)
        f2(*args, **kwargs)

import random
import json
from pathlib import Path
mainDir = Path(__file__).parent

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand') # Red circles appear when right clicking without this???
import kivy
from kivy.app import App
from kivy.uix.label import Label

from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.dropdown import DropDown
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.slider import Slider
from kivy.core.window import Window

from kivy.animation import Animation

from kivy.metrics import dp, sp


from kivy.properties import ObjectProperty, NumericProperty, StringProperty, ReferenceListProperty, BooleanProperty
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
#from kivy.garden.matplotlib.backend_kivyagg import FigureCanvas
from crankNicolson.animate import FigureCanvasKivyAggModified
#from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.factory import Factory

import numpy as np
from numba import jit, njit
import numba
import crankNicolson.crankNicolson2D as mathPhysics
import crankNicolson.animate as animate
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 11})

####
# https://stackoverflow.com/questions/70629758/kivy-how-to-pass-arguments-to-a-widget-class
#####

#import warnings     # For debugging. Warnings stop the program, and thus also show where they occur
#warnings.filterwarnings('error')
#import matplotlib.cbook.deprecation
#warnings.filterwarnings('ignore', category=matplotlib.cbook.deprecation.MatplotlibDeprecationWarning)
#import gc

unit_dist = r"$a_0$"#'2 Å'#r"a_0"#
unit_time = r"$\frac{\hbar}{E_h}$"#'1/3 fs'#r""#
unit_energy = r"$E_h$" #'2 eV' #r"E_h"#
unit_mom = r"$\frac{\hbar}{a_0}$"#r'$\frac{1}{2}\hbar Å^{-1}$'#'1/3 eV·fs/Å'  #'2 eV · 1/3 fs / 2 Å'
# hred = 2 eV · 1/3 fs = 2/3 eV · fs
# ℏ ℏ ℏ ℏ


# We could be more general and just define a general button with image,
# but we use them for just particular cases anyway

class LightButton(Button):
    pass

class RoundedButton(Button):
    pass

class LightButtonImage(LightButton):
    def __init__(self, image_src, size_hint_image=1., **kwargs):
        self.image_src = image_src
        self.size_hint_image = size_hint_image
        super(LightButtonImage, self).__init__(**kwargs)
    pass

class ImageButton(Button):
    img_src = StringProperty('default')
    def pressed(self):
        spl = self.img_src.split('.')
        self.ids.my_image.source = spl[0] + '_pressed.' + spl[1]

    def released(self):
        self.ids.my_image.source = self.img_src

class RoundedImageButton(RoundedButton):
    img_src = StringProperty('images/play.png')

    def __init__(self, src, **kwargs):
        super(RoundedImageButton, self).__init__(**kwargs)
        self.img_src = src

class CenteredImage(Image):
    #img_src = StringProperty('default')
    def __init__(self, src, **kwargs):
        super(CenteredImage, self).__init__(**kwargs)
        self.source = src

class PlayButton(ToggleButton):
    def pressed(self):
        spl = 'images/play.png'.split('.')
        self.ids.my_image.source = spl[0] + ('_pressed.' if self.state == 'down' else '.')+ spl[1]

class SaveButton(ImageButton):
    def __init__(self, **kwargs):
        super(SaveButton, self).__init__(img_src='images/save.png', **kwargs)

class ReturnButton(ImageButton):
    def __init__(self, **kwargs):
        super(ReturnButton, self).__init__(img_src='images/return.png', **kwargs)

class HomeButton(ImageButton):
    def __init__(self, **kwargs):
        super(HomeButton, self).__init__(img_src='images/home.png', **kwargs)

class RestartButton(ImageButton):
    def __init__(self, **kwargs):
        super(RestartButton, self).__init__(img_src='images/restart.png', **kwargs)

class SettingsButton(ImageButton):
    def __init__(self, **kwargs):
        super(SettingsButton, self).__init__(img_src='images/settings.png', **kwargs)

class InfoButton(ImageButton):
    def __init__(self, **kwargs):
        super(InfoButton, self).__init__(img_src='images/info.png', **kwargs)

class ColoredGridLayout(GridLayout):
    pass

class ColoredBoxLayout(BoxLayout):
    r = NumericProperty(240./255)
    g = NumericProperty(240./255)
    b = NumericProperty(240./255)
    alpha = NumericProperty(1.)
    rgba = ReferenceListProperty(r,g,b,alpha)
    def __init__(self, rgba=(240./255, 240./255, 240./255, 1.), **kwargs):
        super(ColoredBoxLayout, self).__init__(**kwargs)
        self.rgba = rgba

class BoolCheckBox(CheckBox):
    pass

class FastGraphicsCheckbox(CheckBox):
    def on_active(self, *args):
        animate.optimizeGraphics = self.active




class GlobalVariable(GridLayout):
    def __init__(self, source, names, sliders, num=0, **kwargs):
        super(GlobalVariable, self).__init__(cols=4,**kwargs)
        self.num = num
        self.names = names
        self.sliders = sliders # List of: show variable i as a slider?
        self.source = source # List of variables, numpy array

        self.label = Label(text="Var.\n{}".format(num), size_hint_x=0.2)

        self.nameText = DataInput(attribute="names", index=self.num, holder=self, condition="unique", multiline=False, size_hint_x=0.3)

        self.valText = DataInput(attribute="source", index=self.num, holder=self, multiline=False, size_hint_x=0.3)

        self.sliderQuery = GridLayout(rows=2, size_hint_x=0.2)
        self.sliderQuery.add_widget(Label(text="Slider?"))
        sliderCheck = CheckBox(active=sliders[num])
        def updateSlider(checkbox, active):
            sliders[num] = active
        sliderCheck.bind(active=updateSlider)
        self.sliderQuery.add_widget(sliderCheck)



        #self.layout = GridLayout(cols=3, size=(100, 100))
        self.add_widget(self.label)
        self.add_widget(self.nameText)
        self.add_widget(self.valText)
        self.add_widget(self.sliderQuery)
        #self.add_widget(self.layout)

    """def on_value(self, instance, value):
        self.source[self.num] = self.value"""

class GlobalVariablesPopup(Popup):
    nVar = 16
    def __init__(self, window, **kwargs):
        self.window = window  # Window holds information such as QuantumSystem and Animation
        super(GlobalVariablesPopup, self).__init__(**kwargs)

        self.layout = GridLayout(cols=2)
        Clock.schedule_once(self._finish_init)

    def _finish_init(self, *args):
        #print(self.window.paramNames)
        for i in range(self.nVar):
            self.layout.add_widget(GlobalVariable(self.window.extra_param, self.window.paramNames, self.window.paramSliders, num=i))
        self.add_widget(self.layout)

    def on_dismiss(self):
        super(GlobalVariablesPopup, self).on_dismiss()
        # We need to wait to make sure all DataInputs finish on unfocus
        def updateStuff(*param):
            self.window.setVarDict()
            self.window.setSliders()
        Clock.schedule_once(updateStuff)


class SavedStatesPopup(Popup):
    def __init__(self, window, **kwargs):
        self.window = window
        super(SavedStatesPopup, self).__init__(**kwargs)

        Clock.schedule_once(self._finish_init)

    def _finish_init(self, *args):
        # Lambda in loops! Careful with using iterating variable
        # Same with function, using global variable instead of value during creation
        # https://stackoverflow.com/questions/19837486/lambda-in-a-loop
        #grid = self.ids.states
        #self.parts = []

        for state in self.window.savedStates:
            self.add_state(state)



    # Like this we can test everything gets correctly garbage collected (eventually)
    def on_dismiss(self):
        super(SavedStatesPopup, self).on_dismiss()
        #gc.collect()

    def add_state(self, state):
        lan = App.get_running_app().root.language
        grid = self.ids.states
        lbl = Label(text=state["name"])  # ,
        btnprev = Button(text="Preview" if lan == 'eng' else "Previsualitza" if lan == 'cat' else 'Previsualiza',
                         on_release=lambda x, state=state: Factory.PlotPopup(state).open())
        btnchan = Button(text="Change\nto this" if lan == 'eng' else "Canvia\na aquest" if lan == 'cat' else 'Cambia\na este',
                         on_release=lambda x, state=state: self.window.setState(state))
        btnsub = Button(text="Substract\nto current" if lan == 'eng' else "Substreu\na l'actual" if lan == 'cat' else 'Substrae\nal actual',
                        on_release=lambda x, state=state: self.window.substractComponent(state))

        btndel = Button(text="Delete" if lan == 'eng' else "Elimina" if lan == 'cat' else 'Elimina', background_color=(0.6, 0, 0, 0.8))

        def removeBind(*args, state=state,
                       lbl=lbl, btnprev=btnprev, btnchan=btnchan, btnsub=btnsub, btndel=btndel):
            # print(state["name"])
            for j in range(len(self.window.savedStates)):
                if self.window.savedStates[j]["name"] == state["name"]:
                    del self.window.savedStates[j]
                    break
            # self.window.savedStates.remove(state)
            grid.remove_widget(lbl)
            grid.remove_widget(btnprev)
            grid.remove_widget(btnchan)
            grid.remove_widget(btnsub)
            grid.remove_widget(btndel)
            self.window.ids.stateName.text = "est{}".format(len(self.window.savedStates))

        btndel.bind(on_release=removeBind)

        grid.add_widget(lbl)
        grid.add_widget(btnprev)
        grid.add_widget(btnchan)
        grid.add_widget(btnsub)
        grid.add_widget(btndel)

class SavedEigenstatesPopup(Popup):
    def __init__(self, window, **kwargs):
        self.window = window
        self.tol = 1e-6
        self.maxiter = 20
        self.isClose = False
        super(SavedEigenstatesPopup, self).__init__(**kwargs)

        Clock.schedule_once(self._finish_init)

    def add_state(self, state, grid, E, count=0, index=0):
        lbl = Label(text="E={:.4e} |{}".format(E, count))  # ,
        lan = App.get_running_app().root.language
        stateCopy = state.copy()
        btnprev = Button(text="Preview" if lan == 'eng' else "Previsualitza" if lan == 'cat' else 'Previsualiza',
                         on_release=lambda x, state=stateCopy: Factory.PlotPopup(state).open())
        btnchan = Button(text= "Change\nto this" if lan == 'eng' else "Canvia\na aquest" if lan == 'cat' else 'Cambia\na este',
                         on_release=lambda x, state=stateCopy: self.window.setState(state))
        btnsub = Button(text="Substract\nto current" if lan == 'eng' else "Substreu\na l'actual" if lan == 'cat' else 'Substrae\nal actual',
                        on_release=lambda x, state=stateCopy: self.window.substractComponent(state))

        # Bad, we are multiplying memory use here... We should not create more copies of states for each button

        btndel = Button(text="Delete" if lan == 'eng' else "Elimina" if lan == 'cat' else 'Elimina', background_color=(0.6, 0, 0, 0.8))

        def removeBind(*args, state=state,
                       lbl=lbl, btnprev=btnprev, btnchan=btnchan, btnsub=btnsub, btndel=btndel, E=E, count=count):
            # print(state["name"])
            rep = 0
            for j in range(len(self.window.QSystem.eigenstates)):
                if self.window.QSystem.eigenstates[j][0] == E:
                    if rep == count:
                        del self.window.QSystem.eigenstates[j]
                        break
                    else:
                        rep += 1

            grid.remove_widget(lbl)
            grid.remove_widget(btnprev)
            grid.remove_widget(btnchan)
            grid.remove_widget(btnsub)
            grid.remove_widget(btndel)

        btndel.bind(on_release=removeBind)

        grid.add_widget(lbl, index)
        grid.add_widget(btnprev, index)
        grid.add_widget(btnchan, index)
        grid.add_widget(btnsub, index)
        grid.add_widget(btndel, index)

    def _finish_init(self, *args):

        """def updateProgress(val):
            self.ids.progress.value = val*100
        self.callback = updateProgress"""

        # Lambda in loops! Careful with using iterating variable
        # Same with function, using global variable instead of value during creation
        # https://stackoverflow.com/questions/19837486/lambda-in-a-loop
        grid = self.ids.states
        #self.parts = []

        count = 0
        prev = None
        lan = App.get_running_app().root.language
        for E, eigen in self.window.QSystem.eigenstates:
            self.window.tempState["psi"] = eigen
            state = self.window.tempState

            if prev == E: count+=1
            lbl = Label(text="E={:.4e} |{}".format(E, count))#,
            prev = E

            stateCopy = state.copy()
            btnprev = Button(text="Preview" if lan == 'eng' else "Previsualitza" if lan == 'cat' else 'Previsualiza',
                             on_release = lambda x, state=stateCopy: Factory.PlotPopup(state).open())
            btnchan = Button(text="Change\nto this" if lan == 'eng' else "Canvia\na aquest" if lan == 'cat' else 'Cambia\na este',
                             on_release=lambda x, state=stateCopy: self.window.setState(state))
            btnsub = Button(text="Substract\nto current" if lan == 'eng' else "Substreu\na l'actual" if lan == 'cat' else 'Substrae\nal actual',
                            on_release=lambda x, state=stateCopy: self.window.substractComponent(state))

            # Bad, we are multiplying memory use here... We should not create more copies of states for each button

            btndel = Button(text="Delete" if lan == 'eng' else "Elimina" if lan == 'cat' else 'Elimina', background_color=(0.6,0,0,0.8))

            def removeBind(*args, state=state,
                           lbl=lbl, btnprev=btnprev, btnchan=btnchan, btnsub=btnsub, btndel=btndel, E=E, count=count):
                #print(state["name"])
                rep = 0
                for j in range(len(self.window.QSystem.eigenstates)):
                    if self.window.QSystem.eigenstates[j][0]==E:
                        if rep == count:
                            del self.window.QSystem.eigenstates[j]
                            break
                        else: rep+=1

                grid.remove_widget(lbl)
                grid.remove_widget(btnprev)
                grid.remove_widget(btnchan)
                grid.remove_widget(btnsub)
                grid.remove_widget(btndel)

            btndel.bind(on_release=removeBind)

            grid.add_widget(lbl)
            grid.add_widget(btnprev)
            grid.add_widget(btnchan)
            grid.add_widget(btnsub)
            grid.add_widget(btndel)
    def eigenFind(self):
        self.count = 0
        if not self.isClose: self.window.QSystem.setState(mathPhysics.func1)
        self.window.QSystem.renorm()
        def eigenLoop(*args):
            if self.count < self.maxiter:
                if self.window.QSystem.approximateEigenstate(tol=self.tol, maxiter=5, resetInit=False):
                    self.window.animation.manualUpdate(onlyDraw=True)
                    #self.dismiss()
                    qsys = self.window.QSystem
                    E = np.real(qsys.expectedValueOp(qsys.totalEnergyOp, doConjugate=False)) #np.real(self.window.QSystem.totalEnergy())
                    count = -1
                    index = 0
                    for Et, eigen in self.window.QSystem.eigenstates[::-1]:
                        if Et > E: index += 5
                        if Et == E: count += 1  # one time it is always found
                    #print(index)
                    self.window.tempState["psi"] = np.copy(qsys.psi)
                    self.add_state(self.window.tempState, self.ids.states, E, count=count, index=index)
                    self.isClose = False # We already found state. Now we are far form other eigenstates (orthogonal)
                    lan = App.get_running_app().root.language
                    self.ids.eigenButton.text = "Search next\nEigenstate" if lan == 'eng' else "Busca següent\nEigenestat" if lan == 'cat' else 'Busca siguiente\nEigenestado'
                    return
                else:
                    Clock.schedule_once(eigenLoop, 0.)
                self.count+=1
                self.ids.progress.value = self.count/self.maxiter * 100
            else:
                lan = App.get_running_app().root.language
                TextPopup("Keep\nsearching" if lan == 'eng' else "Continua\nbuscant" if lan == 'cat' else 'Continúa\nbuscando').open()
                self.window.animation.manualUpdate(onlyDraw=True)
                self.isClose = True
                self.ids.eigenButton.text = "Keep\nsearching" if lan == 'eng' else "Continua\nbuscant" if lan == 'cat' else 'Continúa\nbuscando'
                #self.dismiss()
        Clock.schedule_once(eigenLoop)





class DataInput(TextInput):
    """
    Holds an attribute which it can change/modify. The attribute is passed by value,
    so to modify it in the class instance it refers to that class instance needs to be passed.
    Then it can be modified with getattr(class/instance, attribute) and setattr     ## NOT GOOD PRACTICE before: vars(classInstance) / classInstance.__dict__.
    Which returns a dictionary of variables, mutable.
    """
    text_width = NumericProperty()
    def __init__(self, attribute = None, index=None, holder = None, condition = None, callback=None, centered=False, scientific=False, maxDecimal=6, **kwargs):
        self.scientific = False
        self.maxDecimal = maxDecimal
        self.centered = centered

        super(DataInput, self).__init__(**kwargs)
        self.attribute = attribute
        self.index = index
        self.holder = holder
        self.condition = condition
        self.callback = callback

        Clock.schedule_once(self.set_self)
        # .kv can't take data from another class during init. Everything needs to be init first
        # That's why the delay

    def set_self(self, dt):
        # Attribute is set in kivy language
        #print(id(self.attribute)) Check
        self.attributeVal = getattr(self.holder,self.attribute) if self.index is None else \
                            getattr(self.holder,self.attribute)[self.index]
        self.type = type(self.attributeVal)
        form = "{:." + str(self.maxDecimal) + ('f' if not self.scientific else 'e') +'}'
        self.text = str(self.attributeVal) if self.type is not float else form.format(self.attributeVal).rstrip('0')
        self.copy = self.text

    def _on_focus(self, instance, value, *largs):
        # When unfocusing also apply changes. Value: false -> unfocus
        super(DataInput, self)._on_focus(instance, value, *largs)
        if value == False and self.text != self.copy:
            self.on_text_validate()


    def update_padding(self, *args):
        '''
        Update the padding so the text is centered
        '''
        self.text_width = self._get_text_width(self.text, self.tab_width, self._label_cached)


    def on_text_validate(self):
        # Enter
        try:
            self.attributeVal = self.type(self.text)
            # Try first to see if it can be converted sucessfully
        except:
            #print("Couldn't convert properly")
            TextPopup("Invalid Input!").open()
            self.text = self.copy
            return
        if self.conditionHolds(self.attributeVal):
            if self.index is None:
                setattr(self.holder, self.attribute, self.type(self.text))
            else:
                getattr(self.holder, self.attribute)[self.index] = self.type(self.text)  # Dangerous, look here
            self.copy = self.text
        else:
            self.text = self.copy
        if self.callback != None:
            self.callback(self.attributeVal)

    def conditionHolds(self, val):
        if self.condition == None: return True
        elif self.condition == "fixed":
            TextPopup("Fixed Value", title="Warning").open()
            return False
        elif self.condition == "notNothing":
            if val == "": return False
        elif self.condition == "unique" and self.index != None:
            ### Not too general
            ### We assume here no name is allowed to be repeated as a name
            if val != "" and val in getattr(self.holder,self.attribute):
                TextPopup("Can't repeat!", title="Warning").open()
                return False
        elif self.condition == "nonnegative":
            if val < 0:
                TextPopup("Must be nonnegative!", title="Warning").open()
                return False
        elif self.condition == "positive":
            if val <= 0:
                TextPopup("Must be posiive!", title="Warning").open()
                return False
        elif self.condition.startswith("range"):

            left = self.condition.split('-')[1]
            right = self.condition.split('-')[2]
            if not (float(left) <= val <= float(right)):
            #if val < float(left) or float(right) < val:
                TextPopup("Must be between {0} and {1}".format(left, right), title="Warning").open()
                return False
        elif self.condition.startswith("gt"):
            if not (float(self.condition[2:]) < val):
                TextPopup("Must be greater than "+self.condition[2:], title="Warning").open()
                return False
        elif self.condition.startswith("geq"):
            if not (float(self.condition[2:]) <= val):
                TextPopup("Must be greater than or equal to "+self.condition[2:], title="Warning").open()
                return False
        elif self.condition.startswith("lt"):
            if not (val < float(self.condition[2:])):
                TextPopup("Must be less than "+self.condition[2:], title="Warning").open()
                return False
        elif self.condition.startswith("leq"):
            if not (val <= float(self.condition[2:])):
                TextPopup("Must be less than or equal to "+self.condition[2:], title="Warning").open()
                return False

        return True




class DataSlider(Slider):
    """
    Similar and linked to a DataInput, but user fiendly form of a Slider. Only numeric variables!
    """
    # By default step = 0, which means pixel resolution for changes
    def __init__(self, attribute = None, index=None, holder = None, callback=None, isPotential=True, **kwargs):
        self.attribute = attribute
        self.index = index
        self.holder = holder
        self.callback = callback
        self.isPotential = isPotential
        self.firstTime = True
        Clock.schedule_once(self.set_self)
        super(DataSlider, self).__init__(size_hint_min_y=sp(15), **kwargs)
        # .kv can't take data from another class during init. Everything needs to be init first
        # That's why the delay

    def set_self(self, dt):
        # Attribute is set in kivy language
        # print(id( self.attribute)) Check
        self.attributeVal = getattr(self.holder, self.attribute) if self.index is None else \
            getattr(self.holder,self.attribute)[self.index]

        self.text = str(self.attributeVal)
        self.copy = self.text

    def on_value(self, instance, val):
        # It gets fired when the slider is initalized! So things are not yet defined if not careful (super is called last)
        if self.index is None:
            setattr(self.holder, self.attribute, self.value)
        else:
            getattr(self.holder, self.attribute)[self.index] = self.value
        if self.callback is not None:
            self.callback(val)

        if not self.firstTime:
            if self.isPotential and self.holder.animation.paused or self.holder.animation.isOver: self.holder.animation.updatePotentialDraw()
            else: self.holder.animation.updating = True
        else: self.firstTime = not self.firstTime


class CustomDataSlider(BoxLayout):
    # Text showing value and name
    # Slider + custom slider ranges (max val and min val)

    ###### Maybe Clock once???? Need to check, maybe clock_once already inside slider/datainput is enough
    def __init__(self, name = None, attribute = None, index=None, holder = None, orientation="horizontal", min = -1., max = 1.,
                 isPotential=True, value=None, step=0., variableLimits=True, callback=None, **kwargs):
        super(CustomDataSlider, self).__init__(orientation=orientation, **kwargs)

        self.name = name if name is not None else self.attribute
        self.orientation = orientation
        self.attribute = attribute
        self.orientation = orientation
        self.variableLimits = variableLimits
        self.holder = holder
        self.index = index
        self.value = value
        self.min = min
        self.max=max
        self.orientation=orientation
        self.isPotential = isPotential
        self.step = step
        self.callback = callback
        Clock.schedule_once(self._finish_init)

    def _finish_init(self, dt):
        isHor = self.orientation == "horizontal"
        if isHor:
            self.size_hint_x = 1
            self.size_hint_y = None
            self.height = sp(80/2)
            sizeHintSlid = (0.7, 1)
        else:
            self.size_hint_x = None
            self.size_hint_y = 1
            self.width = sp(80/2)
            sizeHintSlid = (1, 1)

        val = float(getattr(self.holder, self.attribute) if self.index is None else getattr(self.holder, self.attribute)[self.index])

        if self.value is not None:
            setVal = self.value
        else:
            setVal = (self.min if val < self.min else (self.max if val > self.max else (val)))

        sizeHintText = (0.1, 1) if isHor else (1, None)

        self.label = Label(text="[b]" + self.name + "[/b] = \n{:.2f}".format(setVal),
                           size_hint=sizeHintText, markup=True, height=sp(40))

        def callback(newVal):
            # update Label
            self.label.text = "[b]" + self.name + "[/b] =\n{:.2f}".format(newVal)

            if self.callback is not None: self.callback(newVal)



        self.slider = DataSlider(self.attribute, self.index, self.holder, value=setVal,
                                 min=self.min, max=self.max, size_hint=sizeHintSlid,
                                 orientation=self.orientation, callback=callback, isPotential=self.isPotential, step=self.step)

        sizeHintText = (0.1, 1) if isHor else (1, None)
        self.minDat = DataInput(attribute="min", holder=self.slider, condition="lt{0}".format(self.slider.max),
                                size_hint=sizeHintText, centered=True, disabled=not self.variableLimits, height=sp(20))

        def updateMin(newMax):
            self.minDat.condition = "lt{0}".format(newMax)


        self.maxDat = DataInput(attribute="max", holder=self.slider, condition="gt{0}".format(self.slider.min),
                                size_hint=sizeHintText, centered=True, disabled=not self.variableLimits, height=sp(20))

        def updateMax(newMin):
            self.maxDat.condition = "gt{0}".format(newMin)

        self.maxDat.callback = updateMin
        self.minDat.callback = updateMax

        # Layout  [min] [----- slider -----] [max]
        #self.layout = BoxLayout(orientation=self.orientation)
        self.add_widget(self.label)
        if isHor:
            self.add_widget(self.minDat)
            self.add_widget(self.slider)
            self.add_widget(self.maxDat)
        else:
            self.add_widget(self.maxDat)
            self.add_widget(self.slider)
            self.add_widget(self.minDat)
        #self.add_widget(self.layout)



################################################################################################################
#--------------------------------------------------------------------------------------------------------------#
#                           FUNCIONS EN GENERAL                                                             #

from crankNicolson.crankNicolson2D import gaussianPacket
from crankNicolson.crankNicolson2D import eigenvectorHarmonic1D as eigenHarmonic
"""
def gaussianPacket(x, sigma, p0, extra_param=None):
    global hred
    return 1./(2*np.pi*sigma**2)**(0.25) * np.exp(-1./4. * ((x)/sigma)**2) * np.exp(1j/hred * p0*(x))
"""


@jit#(cache=True)
def heaviside(x, k=1.):
    """
    Heaviside. Analytic approximation: 1/(1 + e^-2kr). Larger k, better approximation, less smooth
    """
    return 1./(1. + np.exp(-2.*k*x))


# IMPORTANT
# IMPORTANT
# WARNING: eval() https://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html
# WARNING
# This creates a GLOBAL function. This is why it's allowed to return
# it seems locals can't change, but globals can
# https://stackoverflow.com/questions/41100196/exec-not-working-inside-function-python3-x
from numpy import sin, cos, tan, arcsin, arccos, arctan, hypot, arctan2, degrees, radians, deg2rad, rad2deg,\
                  sinh, cosh, tanh, arcsinh, arccosh, arctanh,\
                  around, rint, fix, floor, ceil, trunc,\
                  exp, expm1, exp2, log, log10, log2, log1p, logaddexp, logaddexp2,\
                  power, sqrt, i0, sinc,\
                  sign,\
                  pi

ln = log #for commodity
i = 1j

# Heaviside is not supported in numba


sandbox = None
class LocalOperator:
    """
    A local operator is an operator that only acts on a point and its closest neighbours
    i.e. It's useful because we can express any combination:
    L = fxx(x,y,t) ∂^2_x + fyy(x,y,t) ∂^2_y + fx(x,y,t) ∂_x + fy(x,y,t) ∂_y + F(x,y,t)
    It just simplfies creating an operator, to be used for defining the hamiltonian
    """

    # WE won't get into detail to create new opreators.
    # AS of now, we limit ourselves to already well defined operators (Px, Py, V, etc)

    def __init__(self, operator):
        if callable(operator):
            self.operator = operator
        else:
            def operatorFunc(op, X, dx, t=0, extra_param=np.array([]), dir=-1, onlyUpdate=True, operator=operator):
                op[:,:] = operator[:,:]
            self.operator = operatorFunc

    # L * psi.   Apply Operator
    def __mul__(self, state):
        if not(type(state) is OperableState):
            try:
                if state.isnumeric():
                    return self.__rmul__(state)
            except:
                pass
        state = state.state
        newState = state.copy()
        newState["psi"] = state["psi"].copy()
        #print(newState["psi"])

        sb = sandbox

        X = np.linspace(state["x0"], state["xf"], len(state["psi"]))
        Y = np.linspace(state["y0"], state["yf"], len(state["psi"][0]))
        mathPhysics.applyOperator2DFuncNoJit(X, Y, state["psi"], newState["psi"], self.operator, t=sb.QSystem.t, extra_param=sb.QSystem.extra_param)
        return OperableState(newState)

    # k L.  Multiply by number
    def __rmul__(self, other):
        # numero
        #if not callable(other):
        #sb = sandbox
        def operator(op, X, dx, t=0, extra_param=np.array([]), dir=-1, onlyUpdate=True):
            self.operator(op, X, dx, t, extra_param, dir, onlyUpdate)
            op *= other
        return LocalOperator(operator)

    # Multiply by ndarray
    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        ndarray, loc_op = inputs
        sb = sandbox
        #print(ufunc, ufunc is np.add, method)
        if ufunc is np.add:
            return self.__add__(ndarray)
        def operator(op, X, dx, t=0, extra_param=np.array([]), dir=-1, onlyUpdate=True):
            loc_op.operator(op, X, dx, t, extra_param, dir, onlyUpdate)
            ix = round((X[0] - sb.QSystem.X[0]) / dx[0])
            iy = round((X[1] - sb.QSystem.Y[0]) / dx[1])
            op *= ndarray[ix, iy]

        return LocalOperator(operator)



    # Add two operators. When we combine them we dont know if they overlap. WE'll havae to always update.
    # These local operators are only to be used to manipulate states. One operation at a time, not like kinetic energy
    def __add__(self, other):
        #print("adding", type(other))
        if type(other) is np.ndarray:
            other = other * LocalOperator(np.array([[1.,0.],[0.,0.],[0.,0.]]))   #  Other * Identity
        def operator(op, X, dx, t=0, extra_param=np.array([]), dir=-1, onlyUpdate=False):
            self.operator(op, X, dx, t, extra_param, dir, onlyUpdate=False)
            opCopy = op.copy()
            other.operator(opCopy, X, dx, t, extra_param, dir, onlyUpdate=False)
            op+=opCopy
        return LocalOperator(operator)

    __radd__ = __add__

    def __sub__(self, other):
        return self.__add__(-1*other)

    def exp(self, state, depth=10):
        final_state = state
        for n in range(depth,0,-1): #  depth, depth-1, ... , 1
            final_state = state + self*final_state / depth
        return final_state


class OperableState():
    # Dictionary holding state info
    def __init__(self, state):
        self.state = state

    def __add__(self, other):
        newState = self.state.copy()
        newState["psi"] = self.state["psi"].copy()
        newState["psi"] += other.state["psi"]
        return OperableState(newState)

    def __mul__(self, other):
        newState = self.state.copy()
        newState["psi"] = self.state["psi"].copy()
        newState["psi"]*=other
        return OperableState(newState)
    __rmul__ = __mul__

    def __truediv__(self, other):
        return 1/other * self

    def __matmul__(self, other):
        """
        # SHOULD ONLY BE USED BETWEEN OPERABLE STATES!
        # psi @     means using psi as a ket,
        # ie.   psi @ bra will evaluate
        """
        dx = (self.state["xf"] - self.state["x0"]) / (len(self.state["psi"]) - 1)
        dy = (self.state["yf"] - self.state["y0"]) / (len(self.state["psi"][0]) - 1)
        return mathPhysics.innerProduct2D(self.state["psi"], other.state["psi"], dx, dy)


    def __sub__(self, other):
        return self.__add__(-1*other)

    #To multiply with ndarrays
    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        ndarray, state = inputs
        return state * ndarray

class StateExpression(TextInput):
    """Expected to hold string python expression which is to be evaluated."""
    rememberExpression = ''
    def __init__(self, varDict={}, holder=None, **kwargs):
        super(StateExpression, self).__init__(**kwargs)
        self.holder = holder
        self.varDict = varDict

        self.stateDict = {}

        self.text = StateExpression.rememberExpression

        Clock.schedule_once(self.set_self)
        # .kv can't take data from another class during init. Everything needs to be init first
        # That's why the delay

    def set_self(self, *args):
        self.states = self.holder.window.savedStates

    def evaluate(self):
        pass

    def on_text_validate(self):
        # Enter
        lan = App.get_running_app().root.language
        tempName = self.holder.ids.stateName.text
        if tempName == "" or tempName[0] == ':' or tempName[0].isnumeric():
            Factory.TextPopup("Nom ha de començar amb\nuna lletra").open()
            return
        if not tempName.isidentifier():
            TextPopup("Nom invàlid!" if lan=='cat' else "Invalid name!" if lan=='eng' else "Nombre inválido!").open()
            return

        for state in self.states:
            if self.holder.ids.stateName.text == state["name"]:
                TextPopup("Nom ja fet servir!" if lan=='cat' else "Name already in use!" if lan=='eng' else "Nombre ya en uso!").open()
                return

        extra_param = self.holder.window.extra_param

        self.stateDict.clear()
        stateVar = {}
        sbox = self.holder.window
        for state in self.states:
            # Should we interpolate all states so we can operate on all of them?
            # But cost of interpolating every single time!!!
            #if state.get("x0")
            stateVar[state["name"]] = OperableState(state)
            self.stateDict[state["name"]] = "stateVar['"+state["name"]+"']"

        # we assume we are working with current size Nx/Ny
        # States that have been saved differently are interpolated
        K = LocalOperator(mathPhysics.kineticEnergy)
        Px = LocalOperator(-1j * mathPhysics.hred * np.array([[0., 0.], [-1./(2.*sbox.QSystem.dx), +1./(2.*sbox.QSystem.dx)] , [0.,0.]]) )
        Dx = LocalOperator( np.array([[0., 0.], [-1./(2.*sbox.QSystem.dx), +1./(2.*sbox.QSystem.dx)] , [0.,0.]]) )
        Py = LocalOperator(-1j * mathPhysics.hred * np.array([[0., 0.], [0.,0.], [-1./(2.*sbox.QSystem.dy), +1./(2.*sbox.QSystem.dy)]]))
        Dy = LocalOperator( np.array([[0., 0.], [0.,0.], [-1./(2.*sbox.QSystem.dy), +1./(2.*sbox.QSystem.dy)]]))
        I = LocalOperator(np.array([[1.,0.],[0.,0.],[0.,0.]]))
        H = LocalOperator(sbox.QSystem.totalEnergyOp)

        x = sbox.QSystem.Xmesh
        y = sbox.QSystem.Ymesh

        L = (x*Py-y*Px)

        V = np.copy(sbox.QSystem.psiMod)
        mathPhysics.set2DMatrix(sbox.QSystem.X, sbox.QSystem.Y,
                                sbox.QSystem.potential, V,
                                t=sbox.QSystem.t, extra_param=sbox.QSystem.extra_param)

        expression = self.text

        if expression == "": return
        try:
            # Things like {px} are substituted by their corresponding actual extra_param
            expressionFormated = expression.format(**self.stateDict, **self.varDict)
        except:
            TextPopup("Compte amb estats i/o\nvariables globals" if lan=='cat' else "Careful with states\nor global variables:" if lan=='eng' else "Cuidado con estados\ny/o variables globales").open()
            return
        #################
        # SAFETY CHECKS #
        #################
        if "print" in expression or "import" in expression or "sys" in expression or "os." in expression or "open" in expression \
                or "__" in expression:  # or "__builtins__" in expression:
            exit(print("ALERT: DO NOT DO THIS"))#: AIXÒ NO ES POT FER"))

        try:
            i = 1j
            evaluated = eval(expressionFormated)
            #print(evaluated)  #debug
            #print(type(evaluated))
            if type(evaluated) is not OperableState:# (complex, float, int):
                TextPopup(("Resultat numèric:" if lan=='cat' else "Numeric result:" if lan=='eng' else "Resultado numérico:")+"\n{}".format(evaluated)).open()
            else:
                tempState = evaluated.state.copy()

                tempState["name"] = self.holder.ids.stateName.text
                tempState["x0"] = sbox.QSystem.x0
                tempState["xf"] = sbox.QSystem.xf
                tempState["y0"] = sbox.QSystem.y0
                tempState["yf"] = sbox.QSystem.yf
                self.states.append(tempState)
                self.holder.add_state(tempState)
        except:
            TextPopup("La declaració ha de\nresultar en un estat" if lan=='cat' else "Statement has to\nresult in a state" if lan=='eng' else "Declaración ha de\nproducir un estado").open()
            return 0 # Returns True when everything is OK

    def conditionHolds(self, val):
        if self.condition == None: return True

        return True

    def on_text(self, object, value): # object will be self, it's quite redundant
        #super(StateExpression, self).on_text(value, *args, **kwargs)  #there is no default on text
        StateExpression.rememberExpression = value



class FunctionInput(TextInput):
    """Expected to hold string python expression which can be converted into a function."""

    def __init__(self, functionName=None, definitionName=None, varDict={}, holder=None, condition=None, jit = False, **kwargs):
        super(FunctionInput, self).__init__(**kwargs)
        self.functionName = functionName
        self.definitionName = definitionName
        self.holder = holder
        self.condition = condition
        self.varDict = varDict
        self.jit = jit
        Clock.schedule_once(self.set_self)
        # .kv can't take data from another class during init. Everything needs to be init first
        # That's why the delay

    def set_self(self, dt):
        self.definition = getattr(self.holder, self.definitionName)
        self.text = self.definition

    # This is a significant change, we want to ensure confirmation
    """def _on_focus(self, instance, value, *largs):
        super(DataInput, self)._on_focus(instance, value, *largs)
        if value == False and self.text != self.copy:
            self.on_text_validate()"""

    def on_text_validate(self):
        # Enter
        try:
            self.definition = self.text
            self.func = createFunc(self.definition, self.varDict)
            # If it can't create the function, it should not alter the values, it should fail here
            if self.conditionHolds(self.definition):
                setattr(self.holder, self.functionName, jit(self.func) if self.jit else self.func)
                setattr(self.holder, self.definitionName, self.definition)

            return 0 # Returns True when everything is OK
        except MaliciousInput:
            exit(print("ALERTA: AIXÒ NO ES POT FER"))
        except InvalidFormat:
            TextPopup("Compte amb les variables globals").open()
        except:
            TextPopup("Expressió Invàlida!\nRecorda multiplicar amb *\nI compte amb divisions per 0").open() #\nPer 1/r posa 1/(r+numPetit)


    def conditionHolds(self, val):
        if self.condition == None: return True

        return True



class InvalidFormat(Exception):
    pass

class MaliciousInput(Exception):
    pass



def createFunc(expression, variableDict):
    if expression == "": raise InvalidFormat
    try:
        # Interpret ^ as exponent: ** python. Otherwise should redefine __xor__
        expression = expression.replace('^', '**')
        # Things like {px} are substituted by their corresponding actual extra_param
        expressionFormated = expression.format(**variableDict)
    except:
        raise InvalidFormat #Exception("Could not replace global variables properly")

    #################
    # SAFETY CHECKS #
    #################
    if "print" in expression or "import" in expression or "sys" in expression or "os." in expression or "open" in expression\
            or "__" in expression:# or "__builtins__" in expression:
        raise MaliciousInput
        # This is very very bad. Someone is doing something really wrong

    exec("""
def funcManualGLOBAL(x, y, t=0., extra_param=np.array([])):
    r = sqrt(x*x + y*y)
    return {}""".format(expressionFormated), globals())

    # After defining the function, we test it once, to see if it works. If not, it will raise an exception,
    # which should be catched where createFunc is used
    if not np.isfinite( funcManualGLOBAL(0., 0., 0., np.array([0.5]*100)) ):
        raise ZeroDivisionError
        # it can happen for other reasons too though.
    return funcManualGLOBAL

class WindowManager(ScreenManager):
    language = StringProperty('cat')

class MainScreen(Screen):
    #def __init__(self, **kwargs):
    #    super(Screen, self).__init__(**kwargs)
    def change_language(self, lan):
        self.manager.language = lan
        if not(sandbox is None):
            if not(sandbox.animation is None):
                sandbox.animation.reset_plot(language=lan)

class SandboxScreen(Screen):
    paused = True

    settingsButton = ObjectProperty(None)

    not_opened = BooleanProperty(True)


    def __init__(self, **kwargs):
        #self._first_init()   # Can either initialize sandbox with start of application, which slows down startup but allows seamless transition
        # into sandbox and examples, or can delay as done (on_first enter) creation. This also allows to work with kivy variables like language!!!!!
        super(SandboxScreen, self).__init__(**kwargs)

        #Clock.schedule_once(self._finish_init)

    def on_enter(self, *args):
        """if self.not_opened:
            self._first_init()
            self._finish_init(1)
            self.not_opened = False"""
        self.animation.reset_plot()

    def first_enter(self, *args):
        if self.not_opened:
            self._first_init()
            self._finish_init(1)
            self.not_opened = False

    def _first_init(self):
        self.Nx = 200; self.Ny = 200; L = 10.
        self.x0, self.y0 = -L, -L
        self.xf, self.yf = L, L

        """actualNx = Nx; actualNy = Ny; actualL = L
        actualx0, actualy0 = x0, y0
        actualxf, actualyf = xf, yf"""

        # We allow 16 global variables, which can be named
        self.nVar = 16
        self.extra_param = np.zeros(self.nVar, dtype=np.float64)
        self.extra_param[0] = 0.
        self.extra_param[1] = 5.
        self.extra_param[2] = 0.
        self.extra_param[self.nVar-2] = -5.
        self.extra_param[self.nVar-1] = -2.5
        # A name can be assigned to each of these
        self.paramNames = ["Vx"] + ["Vh"] + ["Vw"]+[""]*(self.nVar-5) + ["px"] + ["py"]
        self.paramSliders = [True] + [False] + [True] + [False]*(self.nVar-2)
        self.sliders = []
        self.setSliders(firstInit=True)
        self.variablesDict = {}
        self.setVarDict()
        #self.variablesDict = {'px': 'extra_param[{}]'.format(self.nVar-2), 'py': 'extra_param[{}]'.format(self.nVar-1)}

        self.initState = mathPhysics.gaussian2D(7, 1., self.extra_param[self.nVar-2],
                                                7., 1., self.extra_param[self.nVar-1])
        self.initStateDef = \
            "gaussianPacket(x-7, 1, {px}) * gaussianPacket(y-7, 1, {py})"
            #"1/(2*pi)**0.5 * exp(-1./4. * ((x-7)**2 + (y-7)**2)) * exp(1j * ({px}*x + {py}*y))"

        self.potential = mathPhysics.potentialBarrierYCustom
        self.potentialDef = "{Vh} * exp(-((x-{Vx}) ** 2) / 0.1) / sqrt(0.1 * pi) * (0 if abs(y) < {Vw} else 1)"

        self.QSystem = mathPhysics.QuantumSystem2D(self.Nx, self.Ny, self.x0, self.y0, self.xf, self.yf, self.initState,
                                                   potential=self.potential, extra_param=self.extra_param)

        self.animation = animate.QuantumAnimation(self.QSystem, dtSim=0.01,
                                                  dtAnim=0.05, debugTime=True,
                                                  showPotential=True, varyingPotential=True,
                                                  showMomentum=True, showEnergy=True, forceEnergy=True, showNorm=False, forceNorm=True,
                                                  scalePsi=True, scaleMom=True, isKivy=True, drawClassical=True,
                                                  unit_dist=unit_dist, unit_time=unit_time, unit_energy=unit_energy, unit_mom=unit_mom,
                                                  toolbar=True, language=self.manager.language)

        self.savedStates = []

        self.tempState = {"psi": self.QSystem.psi, "x0": self.QSystem.x0, "xf": self.QSystem.xf
                             ,                        "y0": self.QSystem.y0, "yf": self.QSystem.yf,
                             "name": "temp"}

    def _finish_init(self, dt):
        self.plotBox = self.ids.plot
        box = BoxLayout(orientation="vertical")

        temp = self.animation.fig.canvas._on_size_changed
        self.animation.fig.canvas._on_size_changed = lambda *args: None#print("????")
        #box.add_widget(self.animation.navigation.actionbar)
        nav = self.animation.navigation
        gridnav = ColoredGridLayout(cols=11, height=sp(75/2), size_hint_y=None)

        mplSize = nav.actionbar.children[0].children[0].size # We make our custom buttons same size as matplotlib's
        mplBckCol = (113/255., 161/255., 179/255., 1) # had to do aproximate it manually #nav.actionbar.children[0].children[0].background_color
        mplWhiteCol = (240/255,240/255,240/255,255/255)

        # Control how psi is shown. Mod Squared / Phase / Real part / Imaginary part
        self.psiDropdown = DropDown()

        options = ["mod2", "phase", "real", "imag"]

        for option in options:
            btnPsioption = LightButtonImage(background_normal='', image_src='images/{}.png'.format(option),
                                          background_color=mplWhiteCol, text="", size_hint_y=None, size=mplSize,
                                          size_hint_image=0.8)
            btnPsioption.bind(on_release=lambda btn, option=option: self.animation.reset_plot(psiRepresentation="{}".format(option)))
            self.psiDropdown.add_widget(btnPsioption)

        btnPsi = LightButtonImage(background_normal='', image_src='images/psi.png', background_color=mplWhiteCol,
                            text="", size_hint=(None, 1), size=mplSize, size_hint_image=0.8)
        btnPsi.bind(on_release=self.psiDropdown.open)

        gridnav.add_widget(btnPsi)

        btnP = ToggleButton(background_normal='', background_down='', background_color=mplBckCol, state="down",
                            bold=True, color=(0, 0, 0, 1), text="P", font_size='30sp', size_hint=(None, 1),
                            size=mplSize)

        def showP(*args):
            self.animation.reset_plot(showMomentum=btnP.state is 'down')
            btnP.background_color = mplBckCol if btnP.state is 'down' else (0, 0, 0, 0)

        btnP.bind(on_release=showP)
        gridnav.add_widget(btnP)

        btnE = ToggleButton(background_normal='', background_down='', background_color=mplBckCol, state="down",bold=True, color=(0,0,0,1), text="E", font_size='30sp', size_hint=(None,1), size=mplSize)
        def showE(*args):
            self.animation.reset_plot(showEnergy=btnE.state is 'down')
            btnE.background_color = mplBckCol if btnE.state is 'down' else (0,0,0,0)
        btnE.bind(on_release=showE)
        gridnav.add_widget(btnE)



        btnV = ToggleButton(background_normal='', background_down='', background_color=mplBckCol, state="down", bold=True, color=(0, 0, 0, 1), text="V", font_size='30sp', size_hint=(None, 1), size=mplSize)

        def showV(*args):
            self.animation.reset_plot(showPotential=btnV.state is 'down')
            btnV.background_color = mplBckCol if btnV.state is 'down' else (0, 0, 0, 0)

        btnV.bind(on_release=showV)
        gridnav.add_widget(btnV)

        for i in range(9):
            kid = nav.actionbar.children[0].children[0]
            nav.actionbar.children[0].remove_widget(kid)
            if i != 0 and i != 2: gridnav.add_widget(kid)      # save and settings widget don't do anything anyways

        box.add_widget(gridnav)

        box.add_widget(self.animation.fig.canvas)

        self.plotBox.add_widget(box)

        for slider in self.sliders:
            self.plotBox.add_widget(slider)


        def reallowResizing(*args):
            self.animation.fig.canvas._on_size_changed = temp
        Clock.schedule_once(reallowResizing)

        #self.ids.renorm.bind(on_release = self.renorm)

        # Some bug appeared. When initializing everything matplotlib breaks because in generating canvas
        # it gets a 0 width, and divides by 0. We allow resizing canvas later only, to make sure kivy screens are well defined

        #print("yello0")   # This would print actually
        #Clock.schedule_once(lambda x: print("yello"))   # This not. The error happens in between, drawing is scheduled here

        #self.settingsButton.bind(on_release = self.dropdown.open)
        global sandbox
        sandbox = self

    def renorm(self, dt):
        """Manually Renormalize"""
        """# All the commented things are for testing, as renormalize is a harmless button by itself
        print("psi:",self.animation.axPsi.get_children())
        print("norm:",self.animation.axNorm.get_children())
        print("energy:",self.animation.axEnergy.get_children())
        print("momentum:",self.animation.axMomentum.get_children())"""

        """state = {"psi": self.QSystem.psiCopy, "x0": self.QSystem.x0, "xf": self.QSystem.xf
            , "y0": self.QSystem.y0, "yf": self.QSystem.yf,
         "name": "noname"}
        PlotPopup(state).open()"""
        """mathPhysics.expectedValueOperator2D(self.QSystem.X, self.QSystem.Y, self.QSystem.psi, self.QSystem.psiCopy,
                                        self.QSystem.totalEnergyOp, t=self.QSystem.t, extra_param=self.QSystem.extra_param, doConjugate=False)
        print(np.trapz(np.trapz(np.multiply(np.conj(self.QSystem.psi),self.QSystem.psiCopy)))*self.QSystem.dx*self.QSystem.dy)"""
        self.animation.QSystem.renorm()

    """
    The isidentifier() method returns True if the string is a valid identifier, otherwise False.

A string is considered a valid identifier if it only contains alphanumeric letters (a-z) and (0-9), or underscores (_). A valid identifier cannot start with a number, or contain any spaces.

"""
    def saveState(self):
        repeated = False
        if self.ids.stateName.text == '' or not self.ids.stateName.text.isidentifier():
            TextPopup("Nom invàlid!").open()
            return
        for state in self.savedStates:
            if self.ids.stateName.text == state["name"]: repeated = True

        if repeated:
            TextPopup("Nom ja fet servir!").open()

        else:
            self.savedStates.append({"psi": self.QSystem.psi.copy(), "x0": self.QSystem.x0, "xf": self.QSystem.xf
                                     ,                               "y0": self.QSystem.y0, "yf": self.QSystem.yf,
                                     "name": self.ids.stateName.text})
            self.ids.stateName.text = "est{}".format(len(self.savedStates))

    def setState(self, state):
        self.QSystem.setState(state)
        self.animation.manualUpdate(onlyDraw=True)
        #self.animation.reset_plot()

    def substractComponent(self, state):
        self.QSystem.substractComponent(state)
        self.animation.manualUpdate(onlyDraw=True)
        #self.animation.reset_plot()

    def stopPlaying(self):
        try: self.schedule.cancel()
        except: pass
        self.ids.pausePlay.state = 'normal'
        self.paused = True
        self.animation.paused = True

    def startPlaying(self):
        self.schedule = Clock.schedule_interval(self.play, self.animation.dtAnim)
        self.paused = False
        self.animation.paused = False

    def play(self, dt):
        if self.animation.paused:
            self.paused = self.animation.paused
            self.stopPlaying()
        else:
            self.animation.manualUpdate()
            #self.animation.update(self.animation.frame)
            #self.animation.frame += 1
            #self.animation.fig.canvas.draw()

    def setVarDict(self):
        self.variablesDict.clear()
        for i in range(self.nVar):
            if self.paramNames[i] != "": self.variablesDict[self.paramNames[i]] = "extra_param[{}]".format(i)
        """#This modifies reference of dict. So it doesn't work if other people hold a copy
        self.variablesDict = \
            {self.paramNames[i]: "extra_param[{}]".format(i) for i in range(self.nVar) if self.paramNames[i] != ""}"""

        #print("Variables: ", self.variablesDict)

    def setSliders(self, firstInit = False):
        if not firstInit:
            for slider in self.sliders:
                self.plotBox.remove_widget(slider)

        self.sliders.clear()
        for i in range(self.nVar):
            if self.paramSliders[i]:
                self.sliders.append(CustomDataSlider(name=self.paramNames[i], attribute="extra_param", index=i, holder=self,
                                                     orientation="vertical", value=float(self.extra_param[i]),
                                                     min=float(self.extra_param[i]-10.), max=float(self.extra_param[i]+10.)))
                # Careful with numpy, weird interaction with NumericProperty:
                # https://kivy.org/doc/stable/api-kivy.properties.html#kivy.properties.NumericProperty

        if not firstInit:
            for slider in self.sliders:
                self.plotBox.add_widget(slider)

    def newSystem(self):
        prevState = self.QSystem.psi
        x0Old = self.QSystem.x0
        xfOld = self.QSystem.xf
        y0Old = self.QSystem.y0
        yfOld = self.QSystem.yf
        self.QSystem = mathPhysics.QuantumSystem2D(self.Nx, self.Ny, self.x0, self.y0, self.xf, self.yf, prevState,
                                                   potential=self.potential, extra_param=self.extra_param,
                                                   x0Old=x0Old, xfOld=xfOld, y0Old=y0Old, yfOld=yfOld)

        self.animation.resetSystem(self.QSystem)

        #self.savedStates.clear()
        self.tempState = {"psi": self.QSystem.psi, "x0": self.QSystem.x0, "xf": self.QSystem.xf
                          ,                        "y0": self.QSystem.y0, "yf": self.QSystem.yf,
                          "name": "temp"}

        #self.animation.reset_lists()
        #self.animation.reset_plot()




class TextPopup(Popup):
    def __init__(self, text, **kwargs):
        super(TextPopup, self).__init__(**kwargs)
        self.add_widget(Label(text=text))

class PlotPopup(Popup):
    def __init__(self, data, **kwargs):
        super(PlotPopup, self).__init__(**kwargs)
        self.data = data
        #self._finish_init()
        #Clock.schedule_once(self._finish_init)

    #def _finish_init(self, *args):
        plotBox = BoxLayout(padding=20)

        self.fig, ax = plt.subplots()

        #self.ax = self.fig.gca()  # Just in case?
        #self.ax = self.fig.add_subplot()   # Maybe this doesn't always work

        if self.data["psi"].dtype == np.complex128:
            psiMod = np.empty((len(self.data["psi"]), len(self.data["psi"][0])), dtype=np.float64)
            psiMod[:,:] = mathPhysics.abs2(self.data["psi"])
        else:
            psiMod = self.data["psi"]

        # Didn't work on some other computers? ax not defined?
        datPlot = ax.imshow(psiMod.T, origin='lower',
                       extent=(self.data["x0"], self.data["xf"], self.data["y0"], self.data["yf"]),
                       aspect = 'equal', cmap = "viridis")

        self.fig.colorbar(datPlot, ax=ax, label=self.data.get("unit_col",r'$(2Å)^{-2}$'))

        ax.set_xlabel("x ({})".format(self.data.get("unit_ax",'2 Å')))
        ax.set_ylabel("y ({})".format(self.data.get("unit_ax", '2 Å')))

        plotBox.add_widget(FigureCanvasKivyAgg(self.fig))
        #self.fig.show()
        self.add_widget(plotBox)
        self.fig.canvas.draw()
        self.fig.canvas.disabled = True
        #print(gc.get_referrers(self.fig.canvas))


    def on_dismiss(self):
        # Attempts to fix memory leak, to no avail
        # self.fig.canvas.disabled = True
        #self.fig.canvas.clear_widgets()
        #self.children[0].clear_widgets()
        # """for atr in vars(self.fig.canvas).copy():
        #     delattr(self.fig.canvas, atr)"""
        # delattr(self.fig.canvas, "img_texture")
        # delattr(self.fig.canvas, "img_rect")
        #
        #self.fig.canvas.fig = None
        #self.fig.canvas = None

        animate.cleanFigClose(self.fig)

        #del self.fig
        #del self.data


        super(PlotPopup, self).on_dismiss()



class ExamplesScreen(Screen):
    def __init__(self, **kwargs):
        super(ExamplesScreen, self).__init__(**kwargs)

        Clock.schedule_once(self._finish_init)

    def newExample(self, definition, name, imgsrc=""):
        box = ColoredBoxLayout(orientation="horizontal", rgba=(0.1,0.1,0.1,0.7))
        box.add_widget(Image(source=imgsrc, size_hint_x=0.4))
        box.add_widget(Label(text=name, halign='right'))
        box.add_widget(ImageButton(img_src='images/play.png',width=sp(15*5), size_hint_x=None, text='', on_release=partial(self.switch, definition=definition)))
        self.ids.exampselect.add_widget(box)

    def _finish_init(self, *args):
        # ----------- ----------- ----------- ----------- -----------
        # WALL
        definition = {"zoomMom":1/3}  # Almost default. (None in such case)
        #self.ids.exampselect.add_widget(
        #    RoundedImageButton(src='images/preview/barrier.png',text="Barrera", on_release=partial(self.switch, definition=definition)))
        self.newExample(definition=definition,
            name='Tunneling',
            imgsrc='images/preview/barrier.png')
        # ----------- ----------- ----------- ----------- -----------
        ### WKB

        # ----------- ----------- ----------- ----------- -----------
        # GRAVITY
        definition = {"initState": mathPhysics.gaussian2D(0., 1., 0.,
                                                14, 1., 0.), "potential": mathPhysics.potentialGravity,
                      "zoomMom":1/3., "dtSim": 2**(-8), "Ny": 300, "y0": 0, "yf": 20, "scaleMom": False,
                      "separable":True, "init_x": mathPhysics.gaussian1D(0, 1, 0), "init_y": mathPhysics.gaussian1D(14, 1., 0),
                      "pot_y": mathPhysics.func1d(mathPhysics.potentialGravity, var='y'), "debugTime":True}

        #self.ids.exampselect.add_widget(
        #    RoundedImageButton(src='images/preview/gravity.png',text="Gravetat", on_release=partial(self.switch, definition=definition)))
        self.newExample(definition=definition,
            name='Gravity',
            imgsrc='images/preview/gravity.png')
        # ----------- ----------- ----------- ----------- -----------

        # ----------- ----------- ----------- ----------- -----------
        # FREE PROPAGATION

        def initStateFreeProp(x, y, t=0, extra_param=np.array([2.])):
            return gaussianPacket(x, 1.5, extra_param[0]) * gaussianPacket(y, 1.5, extra_param[1])

        def sliderFreeProp(args, ps):
            ps = self.manager.get_screen("playscreen")
            box = BoxLayout(orientation='horizontal', size_hint_x=0.1)

            def callback(*args):
                ps.QSystem.setState(initStateFreeProp)
                ps.animation.manualUpdate(onlyDraw=True)

            box.add_widget(CustomDataSlider(name="Px", attribute="extra_param", index=0,
                                    holder=ps, callback=callback,
                                    orientation="vertical", min=-4, max=4, value=None, isPotential=False))
            box.add_widget(CustomDataSlider(name="Py", attribute="extra_param", index=1,
                                            holder=ps, callback=callback,
                                            orientation="vertical", min=-4, max=4, value=None, isPotential=False))

            return box

        definition = {"initState": initStateFreeProp, "potential": mathPhysics.potential0,
                      "drawClassical": False, "drawExpected": False, "showEnergy": False, "plotWidget":sliderFreeProp,
                      'extra_param': np.array([1.5, 0.]), "zoomMom": 0.4,
                      "step": 'eigen', "dtSim": 0.04, "psiRepresentation": "phase"
                      }

        #self.ids.exampselect.add_widget(
        #    RoundedImageButton(src='images/preview/freeprop.png',text="Paquet\nLliure", on_release=partial(self.switch, definition=definition)))
        self.newExample(definition=definition,
                        name='Travelling Wave',
                        imgsrc='images/preview/freeprop.png')


        # ----------- ----------- ----------- ----------- -----------

        # ----------- ----------- ----------- ----------- -----------
        # FREE (DISPERSION)

        def sliderFree(args, ps):
            #box = BoxLayout(orientation='horizontal', size_hint_x=0.3)
            return CustomDataSlider(name="σ_0", attribute="extra_param", index=0, holder=self.manager.get_screen("playscreen"),
                                                     orientation="vertical", min=0.2, max=2, value=None)
            #return box

        def initStateFreeDisp(x, y, t=0, extra_param=np.array([2.])):
            return gaussianPacket(x,extra_param[0],0.)*gaussianPacket(y,extra_param[0],0)

        def initStateFreeDisp1D(x, t=0, extra_param=np.array([2.])):
            return gaussianPacket(x,extra_param[0],0.)

        def freeDispSetup(ax, dat, QSystem, units):
            #ax.set_title("Evolució de la dispersió")
            ax.set_ylabel(r'$\sigma^2$ ({})'.format(units["unit_dist"]))
            ax.set_ylim(top=40)
            ax.set_xlabel(r'$t$ ({})'.format(units["unit_time"]))
            tlist = np.linspace(0, 15, 300)
            sigmaT = QSystem.extra_param[0]**2 + tlist**2 * (mathPhysics.hred/(2*mathPhysics.M*QSystem.extra_param[0])**2)
            dat["teoric"], = ax.plot(tlist, sigmaT, '--')
            dat["predict"], = ax.plot(np.array([0.]), np.array([QSystem.varX(0.)**2]))
            #f = open("checks{:.2f}.dat".format(QSystem.extra_param[0]), "w")
            #f.write("")
            #f.close()

        def freeDispUpdate(ax, dat, QSystem, units):
            lin = dat["predict"]
            var = QSystem.extra_param[0]#lin.get_ydata()[0] #!!! This is var^2 !!!
            dat["predict"].set_data(np.append(lin.get_xdata(),QSystem.t), np.append(lin.get_ydata(), QSystem.varX(0.)**2))
            # no need to redraw
            """# Theoretical checks. This code can be used to compare inner product evolution
            x = QSystem.Xmesh
            y = QSystem.Ymesh

            psiTeoric = np.sqrt(1./(2.*np.pi*(1j*QSystem.t/2/var + var)**2))    *np.exp(-1./4.*(x**2 + y**2)/(1j/2. * QSystem.t + var**2))
            normaPsi = mathPhysics.euclidNorm(QSystem.psi, QSystem.dx, QSystem.dy)
            normaTeo = mathPhysics.euclidNorm(psiTeoric, QSystem.dx, QSystem.dy)
            teoricIpsi = mathPhysics.innerProduct2D(psiTeoric, QSystem.psi, QSystem.dx, QSystem.dy)/np.sqrt(normaPsi*normaTeo)
            #print("<teoric|psi> = ", teoricIpsi/(np.sqrt(normaPsi*normaTeo)))
            #print("norma teo    : ", normaTeo)
            #print("norma psi    : ", normaPsi)
            #Wow, horrible code
            #f = open("checks{:.2f}.dat".format(QSystem.extra_param[0]), "a")
            #f.write("{}\t{}\t{}\t{}\n".format(normaPsi,normaTeo,teoricIpsi.real,teoricIpsi.imag))
            #f.close()"""
            return False


        definition = {"initState": initStateFreeDisp, "potential": mathPhysics.potential0,
                      "drawClassical": False, "drawExpected": False, "showEnergy": False, "plotWidget": sliderFree,
                      'extra_param':np.array([1.5]), "zoomMom":0.3, "customPlot": (freeDispSetup, freeDispUpdate),
                      "step":'eigen', "dtSim": 0.04,
                      "separable": True, "init_x": initStateFreeDisp1D, "init_y": initStateFreeDisp1D
                      }

        #self.ids.exampselect.add_widget(
        #    RoundedButton(text="Dispersió\nLliure", on_release=partial(self.switch, definition=definition)))

        self.newExample(definition=definition,
                        name='Free Dispersion',
                        imgsrc='images/preview/freedisp.png')



        # ----------- ----------- ----------- ----------- -----------
        # ----------- ----------- ----------- ----------- -----------
        # UNCERTAINTY
        k = 0.5

        @jit
        def potentialClosingSoft(x, y, t, extra_param):
            global L
            # Heaviside. Analytic approximation: 1/(1 + e^-2kr). Larger k, better approximation
            r = np.sqrt(x * x + y * y)
            k = 1
            #return 100 * 1 / (1 + np.exp(-2 * k * (r - 10. / 2 + 9.5 / 2 * (1 - 1. / (1 + 0.2 * t))))) # 0.5 originally
            return 1/2*(1/4 + 80*tanh(0.01*(t**2)/(10+t)))*r**2 #min(100., 1/2*(1/4 + 80*tanh(0.01*t))*r**2)#+#20*(1-1/(1+0.2*t) ))*r**2)



        def uncertaintyPlotSetup(ax, dat, QSystem, units, zoomOut=False):
            XUncMin = 1 / np.linspace(0.5, 10., 10)  # better spacing
            YUncMin = mathPhysics.hred / 2 / XUncMin

            ax.set(xlabel=r'$\sigma_x$ ({})'.format(units["unit_dist"]),
                              ylabel=r'$\sigma_{{p_x}}$ ({})'.format(units["unit_mom"]),
                              title='Relation between uncertainties\n(variances $\\sigma_{p_x}$ i $\\sigma_x$)')

            zoom= 3 if zoomOut else 1
            ax.set_xlim(XUncMin[-1], XUncMin[0]*zoom)
            ax.set_ylim(YUncMin[0], YUncMin[-1]*zoom)

            ax.plot(XUncMin, YUncMin, 'r--', label=r'$\sigma_x \sigma_{p_x} = \hbar/2$')

            #ax.grid()  # Problems with grid disappearing when redrawing plot (do delete trace of points)

            ax.legend()


            ax.set_xscale('log')
            ax.set_yscale('log')
            if QSystem.separable:
                dat["datUnc"], = ax.plot(np.array([1/2.]), np.array([1.]))
                dat["datUncPoint"], = ax.plot(np.array([1./2.]), np.array([1.]), 'o')
            else:
                dat["datUnc"], = ax.plot(np.array([1.]), np.array([1. / 2.]))
                dat["datUncPoint"], = ax.plot(np.array([1.]), np.array([1. / 2.]), 'o')
            dat["sigmax"] = []
            dat["sigmapx"] = []

        def uncertaintyPlotUpdate(ax, dat, QSystem, units):
            varX = QSystem.varX()
            dat["sigmax"].append(varX)
            varPx = QSystem.varPx()
            dat["sigmapx"].append(varPx)

            """for it, patch in enumerate(ax.patches):
                dat["p{}".format(it)] = patch"""

            dat["datUnc"].set_data(dat["sigmax"], dat["sigmapx"])
            dat["datUncPoint"].set_data(varX, varPx)

            ax.redraw_in_frame()


        definition = {"initState": mathPhysics.gaussian2D(0., 1., 0.,
                                                          0., 1., 0.), "potential": potentialClosingSoft, "dtSim": 2.**(-7),
                      "separable":True, "init_x": mathPhysics.gaussian1D(0,1,0), "init_y": mathPhysics.gaussian1D(0,1,0),
                      "pot_x": mathPhysics.func1d(potentialClosingSoft, var='x'), "pot_y": mathPhysics.func1d(potentialClosingSoft, var='y'),
                      "drawClassical":False, "drawExpected": False, "showEnergy":False, "zoomMom":0.6, "scalePot": False,
                      "customPlot": (uncertaintyPlotSetup, uncertaintyPlotUpdate), "customPlotUpdate": True}

        self.newExample(definition=definition,
                        name='Uncertainty Principle',
                        imgsrc='images/preview/uncertainty.png')

        @jit
        def potentialClosingManual(x, y, t, extra_param):
            global L
            # Heaviside. Analytic approximation: 1/(1 + e^-2kr). Larger k, better approximation
            r = np.sqrt(x * x + y * y)
            return 100 * heaviside(r-extra_param[0], 1.)

        @jit
        def potentialClosingManual2(x, y, t, extra_param):
            global L
            # harmonic trap that can be modified
            return extra_param[0]/2 * (x*x + y*y)

        def plotUncManual(args, ps):
            #box = BoxLayout(orientation='horizontal')#, size_hint_x=0.3)
            #box.add_widget(plotUnc(args, ps))
            #box.add_widget(
            return CustomDataSlider(name="K", attribute="extra_param", index=0, holder=self.manager.get_screen("playscreen"),
                                                     orientation="vertical", min=0., max=10., value=1.)
            #return box




        definition = {"initState": mathPhysics.gaussian2D(0., 1., 0.,
                                                          0., 1., 0.), "potential": potentialClosingManual,
                      "drawClassical": False, "drawExpected": False, "showEnergy": False, 'extra_param':np.array([5.]), "zoomMom":0.6,
                      "customPlot": (partial(uncertaintyPlotSetup,zoomOut=True), uncertaintyPlotUpdate), "customPlotUpdate": True, "plotWidget": plotUncManual
                      }

        definition = {"initState": mathPhysics.gaussian2D(0., sqrt(1/2), 0.,
                                                          0., sqrt(1/2), 0.), "potential": potentialClosingManual2,
                      "drawClassical": False, "drawExpected": False, "showEnergy": False, 'extra_param': np.array([1.]),
                      "zoomMom": 0.6,
                      "customPlot": (partial(uncertaintyPlotSetup, zoomOut=True), uncertaintyPlotUpdate),
                      "customPlotUpdate": True, "plotWidget": plotUncManual,
                      "separable": True, "init_x": mathPhysics.gaussian1D(0, 1/sqrt(2), 0),
                      "init_y": mathPhysics.gaussian1D(0, 1/sqrt(2), 0),
                      "pot_x": mathPhysics.func1d(potentialClosingManual2, var='x'),
                      "pot_y": mathPhysics.func1d(potentialClosingManual2, var='y'), "scalePot": False
                      }


        self.newExample(definition=definition,
                        name='Uncertainty Principle (manual)',
                        imgsrc='images/preview/uncertaintymanual.png')
        # ----------- ----------- ----------- ----------- -----------

        # ----------- ----------- ----------- ----------- -----------
        # EHRENFEST 2. HARMONIC OSCILLATOR
        definition = {"initState": mathPhysics.gaussian2D(0., 0.6, -3.,
                                                          3., 0.6, 0.),
                      "init_x": mathPhysics.gaussian1D(0., 0.6, -3.), "init_y": mathPhysics.gaussian1D(3., 0.6, 0),
                      "potential": mathPhysics.potentialHarmonic, "separable": True,
                      "pot_x": mathPhysics.func1d(mathPhysics.potentialHarmonic), "pot_y": mathPhysics.func1d(mathPhysics.potentialHarmonic, var='y'),
                      "extra_param": np.array([2.]),
                      "dtSim": 2.**(-9), "scalePot":False, "zoomMom":1/3., "Nx": 300, "Ny": 300,   # dtSim: 0.00390625  2**(-8)
                      "drawClassical":True, "drawClassicalTrace":True, "drawExpected":True, "drawExpectedTrace":True,
                      "plotWidget": CustomDataSlider(name="k", attribute="extra_param", index=0, holder=self.manager.get_screen("playscreen"),
                                                     orientation="vertical", min=1., max=2., value=2.)}
        #self.ids.exampselect.add_widget(
        #    RoundedButton(text="Oscil·lador Harmònic", on_release=partial(self.switch, definition=definition)))

        self.newExample(definition=definition,
                        name='Harmonic Oscillator',
                        imgsrc='images/preview/harmonicoscillator.png')

        # ----------- ----------- ----------- ----------- -----------

        # ----------- ----------- ----------- ----------- -----------
        # Double Slit


        @jit
        def slit(x, n, width, dist):
            # only defined for positive x
            return x <= n/2*width + dist*(n-1)/2 and (x-width/2*(n%2)+dist/2*((n+1)%2))/(dist+width) % 1 >= dist/(dist+width)

        #----[ ]--[ ]--[ ]----
        #------[ ]---[ ]------

        @jit
        def potentialDoubleSlit(x, y, t, extra_param):
            # extra_param: [nSlits, slitWidth, slitSeparation, wallWidth]
            return 400. if (abs(x)<extra_param[3]/2 and not slit(abs(y), extra_param[0], extra_param[1], extra_param[2]))\
                   else 0.

        def slidersSlit(*args):
            box = BoxLayout(orientation='horizontal', width=sp(80/2)*3, size_hint_x=None)
            box.add_widget(CustomDataSlider(name="n", attribute="extra_param", index=0, holder=self.manager.get_screen("playscreen"),
                             orientation="vertical", min=1, max=10, step=1, value=None))
            box.add_widget(CustomDataSlider(name="w", attribute="extra_param", index=1,
                                            holder=self.manager.get_screen("playscreen"),
                                            orientation="vertical", min=0., max=3., value=None))
            box.add_widget(CustomDataSlider(name="d", attribute="extra_param", index=2,
                                            holder=self.manager.get_screen("playscreen"),
                                            orientation="vertical", min=0., max=3., value=None))
            return box

        x0A = -7
        xfA = 13
        NxA = 600
        NyA = 600
        p0A = 15

        dtSimA = 2**(-7)

        """NxA = 2000
        NyA = 600
        p0A = 34.6

        dtSimA = 2 ** (-9)"""


        def slitInterferenceSetup(ax, dat, QSystem, units):
            # ax.set_title("Mesura de pantalla")
            # ax.set_xlabel("y ({})".format(units["unit_dist"]))
            # ax.set_ylabel(r'$|\psi|^2 ({})^{{-2}}$'.format(units["unit_dist"]))
            # itx = int((-4 + QSystem.extra_param[5] - x0A)/(xfA-x0A)*NxA) # Initially gaussian packet starts at -6
            # dat["observed"], = ax.plot(QSystem.Y, QSystem.psiMod[itx, :])
            # ax.set_ylim(0., np.max(QSystem.psiMod))
            # We abuse we already know psiMod holds norm, no we don't actually. We changed how it works
            QSystem.modSquared()
            lan = App.get_running_app().root.language
            ax.set_title("Mesura de pantalla" if lan=='cat' else "Screen distribution" if lan=='eng' else "Medida de pantalla")
            ax.set_ylabel("y ({})".format(units["unit_dist"]))
            ax.set_xlabel(r'$|\psi|^2 ({})^{{-2}}$'.format(units["unit_dist"]))
            itx = int((-4 + QSystem.extra_param[5] - x0A) / (xfA - x0A) * NxA)  # Initially gaussian packet starts at -6
            dat["observed"], = ax.plot(QSystem.psiMod[itx, :], QSystem.Y)
            ax.set_xlim(0., np.max(QSystem.psiMod))
            ax.set_ylim(QSystem.Y[0], QSystem.Y[-1])

            # Matplotlib Aspect ratio is relative to data
            # We want a visual aspect ratio, to fit the y axis with the
            # wave function plot
            # - - -   Interference occupies 1/3
            ratio = 2.25

            # get x and y limits
            x_left, x_right = ax.get_xlim()
            y_low, y_high = ax.get_ylim()
            # set aspect ratio
            ax.set_aspect(abs((x_right - x_left) / (y_low - y_high)) * ratio)

        def slitInterferenceUpdate(ax, dat, QSystem, units):
            # itx = int((-4 + QSystem.extra_param[5] + QSystem.t*p0A/1.25 - x0A)/(xfA-x0A) * NxA)  # Moves with wave
            # dat["observed"].set_data(QSystem.Y, QSystem.psiMod[itx, :])
            # ax.set_ylim(0.) # Reset limits
            # ax.figure.draw_artist(ax.patch) # redraw background, if not lines are overdrawn
            QSystem.modSquared()
            itx = int(
                (-4 + QSystem.extra_param[5] + QSystem.t * p0A / 1.25 - x0A) / (xfA - x0A) * NxA)  # Moves with wave
            dat["observed"].set_data(QSystem.psiMod[itx, :], QSystem.Y)
            ax.set_xlim(0.)  # Reset limits
            ax.figure.draw_artist(ax.patch)  # redraw background, if not lines are overdrawn


            return False


        def extraUpdateClimSlit(instance):                              # We want to clearly see what propagates
            if instance.QSystem.t > 10/p0A:
                instance.datPsi.set_clim(vmax=np.max(instance.QSystem.psiMod[int(10./instance.QSystem.dx):].T), vmin=0.)

            ps = self.manager.get_screen("playscreen")
            Qs = ps.QSystem

            itx = int((-4 + Qs.extra_param[5] + Qs.t * p0A / 1.25 - x0A) / (xfA - x0A) * NxA)

            if instance.firstDraw:
                ps.extraArgs["screenLine"], = instance.axPsi.plot([Qs.X[itx], Qs.X[itx]], [Qs.Y[0], Qs.Y[-1]], '--')

            else:
                ps.extraArgs["screenLine"].set_data([Qs.X[itx], Qs.X[itx]], [Qs.Y[0], Qs.Y[-1]])

            return ps.extraArgs["screenLine"]  # We draw measure screen line

        definition = {"initState": mathPhysics.gaussian2D(-4., 1, p0A,
                                                          0., 2, 0.),
                      "potential": potentialDoubleSlit, "extraUpdates": [extraUpdateClimSlit], "extraUpdatesStart": True,
                      "extra_param": np.array([2, 1, 1, 0.5, 0., 0.]), "x0": x0A, "xf": xfA, "Nx": NxA, "Ny":NyA, "y0":-10, "yf": 10,
                      "dtSim": dtSimA, "stepsPerFrame":2, "scalePot": False,
                      "drawClassical": False, "drawExpected": False,
                      "customPlot": (slitInterferenceSetup, slitInterferenceUpdate), "customPlotFull": True,
                      "showMomentum": False, "showEnergy": False, "showNorm": False, "duration": 1., "plotWidget": slidersSlit}

        #self.ids.exampselect.add_widget(
        #    RoundedButton(text="Doble Escletxa", on_release=partial(self.switch, definition=definition)))

        self.newExample(definition=definition,
                        name='Slits',
                        imgsrc='images/preview/slit.png')

        # ----------- ----------- ----------- ----------- -----------
        # Double Slit + Aharonov Bohm effect
        # Very similar to double slit, just some extra things
        # MEANING OF ALPHA = -e FLUX / hc, which is numerically 2pi e FLUX/hred c. Which is [2pi FLUX]!!! phase (real: e/hred · flux )

        def slidersAharonov(*args):
            box = BoxLayout(orientation='horizontal', width=sp(80/2)*3, size_hint_x=None)
            stack = BoxLayout(orientation='vertical', width=sp(80/2), spacing=sp(10))
            stack.add_widget(CustomDataSlider(name="n", attribute="extra_param", index=0, holder=self.manager.get_screen("playscreen"),
                             orientation="vertical", min=2, max=10, step=2, value=None, variableLimits=False))
            stack.add_widget(CustomDataSlider(name="w", attribute="extra_param", index=1,
                                            holder=self.manager.get_screen("playscreen"),
                                            orientation="vertical", min=0., max=3., step=0.1, value=None, variableLimits=False))
            stack.add_widget(CustomDataSlider(name="d", attribute="extra_param", index=2,
                                            holder=self.manager.get_screen("playscreen"),
                                            orientation="vertical", min=0.5, max=3., step=0.1, value=None, variableLimits=False))
            box.add_widget(stack)
            box.add_widget(CustomDataSlider(name="α", attribute="extra_param", index=4,
                                            holder=self.manager.get_screen("playscreen"),
                                            orientation="vertical", min=-1., max=1., value=None))
            box.add_widget(CustomDataSlider(name="xP", attribute="extra_param", index=5,
                                            holder=self.manager.get_screen("playscreen"),
                                            orientation="vertical", min=-3, max=1, value=None))

            return box



        def AharonovA(x, y, alpha):
            x = x-1; y = y  # Solenoid is at (1,0), next to the slits but close as to not interact much
            k = alpha/(x*x+y*y+1e-10)
            return k * -y, k * x


        def aharonovExtraDrawings(instance=None):
            ps = self.manager.get_screen("playscreen")
            Qs = ps.QSystem

            if instance.updating or instance.firstDraw:
                Xm = Qs.Xmesh[::30, ::30]
                Ym = Qs.Ymesh[::30, ::30]
                Amesh = AharonovA(Xm, Ym, Qs.extra_param[4])  # A is constant with time

            if instance.firstDraw:
                ps.extraArgs["vectorPotential"] = instance.axPsi.quiver(Xm.T, Ym.T, Amesh[0].T, Amesh[1].T,
                                                                        pivot="mid", color='red', alpha=0.2, scale=5)
            elif instance.updating: ps.extraArgs["vectorPotential"].set_UVC(Amesh[0].T, Amesh[1].T)

            return ps.extraArgs["vectorPotential"]

        # A ~ alpha/r^2 (-y, x, 0)

        definition = {"initState": mathPhysics.gaussian2D(-4., 1, p0A, 0., 2, 0.),
                      "potential": potentialDoubleSlit, "extraUpdates": [extraUpdateClimSlit, aharonovExtraDrawings], "extraUpdatesStart":True, "extraUpdatesUpdate":True,
                      "extra_param": np.array([2, 1, 1, 0.5, 0.4, 0]), "x0": x0A, "xf": xfA, "Nx": NxA, "Ny": NyA, "y0": -10, "yf": 10,
                      "dtSim": dtSimA, "stepsPerFrame":2, "scalePot": False,
                      "drawClassical": False, "drawExpected": False,
                      "customPlot": (slitInterferenceSetup, slitInterferenceUpdate), "customPlotUpdate":True, "customPlotFull":True,
                      "showMomentum": False, "showEnergy": False, "showNorm": False, "duration": 1., "psiRepresentation": "phase",
                      "plotWidget": slidersAharonov, "customOperator": mathPhysics.aharonovBohmOperator,
                      }

        #self.ids.exampselect.add_widget(
        #    RoundedButton(text="Aharonov-Bohm", on_release=partial(self.switch, definition=definition)))

        self.newExample(definition=definition,
                        name='Aharonov-Bohm',
                        imgsrc='images/preview/aharonov.png')

    def switch(self, *args, definition=None, setExtraArgs=None):
        self.manager.get_screen("playscreen").set_self(definition, setExtraArgs=setExtraArgs)
        self.manager.transition.direction = "left"
        self.manager.current = "playscreen"
        self.manager.get_screen("playscreen").sourceScreen = "examples"






class GameCoin(Widget):
    def __init__(self, callbackClick = None, callbackMiss = None, callbackEnd = None, duration=2.5, **kwargs):
        super(GameCoin, self).__init__(width=dp(50/2), height=dp(50/2), **kwargs)
        self.cbClick = callbackClick
        self.cbMiss = callbackMiss
        self.cbEnd = callbackEnd
        self.duration = duration
        self.clicked = False
        Clock.schedule_once(self._finish_init)

    def _finish_init(self, *args):
        # We pick a transition, t, that makes the change start slow and then ramp up
        # Coin starts normal, then disappears after some time
        def complete(*args):
            if self.parent is not None: self.parent.remove_widget(self)
            if self.cbMiss is not None: self.cbMiss()
            if self.cbEnd is not None: self.cbEnd()
        self.anim = Animation(opacity=0, duration=self.duration, t="in_quint")
        self.anim.bind(on_complete=complete)
        self.anim.start(self.ids.image)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.clicked:
            self.clicked = True
            if self.cbClick is not None: self.cbClick()
            self.anim.cancel(self.ids.image)
            self.ids.image.opacity = 1

            def complete(*args):
                if self.parent is not None: self.parent.remove_widget(self)
                if self.cbEnd is not None: self.cbEnd()
            #little jump
            self.anim = Animation(pos_hint={"center_x":1.2}, duration=0.6)# + Animation(duration=0.2)
            self.anim.bind(on_complete=complete)
            self.anim.start(self)
        return super(GameCoin, self).on_touch_down(touch)


class GamesScreen(Screen):
    def __init__(self, **kwargs):
        super(GamesScreen, self).__init__(**kwargs)

        Clock.schedule_once(self._finish_init)

    def _finish_init(self, *args):
        # Move the particle!
        kHarm = 8.
        height = 100.
        extra_param = np.array([0., 0., 0., 0., 0., kHarm, height])


        def eigenHarmonic1D(x, t, extra_param=np.array([])):
            return mathPhysics.eigenvectorHarmonic1D(x, 0, kHarm)

        @njit#([numba.float64(numba.float64, numba.float64, numba.float64, numba.float64[:])])
        def potentialHarmonicWellMovingSoft(x, y, t, extra_param):
            res = 1 / 2. * extra_param[5] * ((x - extra_param[0] - extra_param[2] * (t - extra_param[4])) ** 2
                                    + (y - extra_param[1] - extra_param[3] * (t - extra_param[4])) ** 2
                                    )
            #return np.where(res>extra_param[6], extra_param[6], res)
            if res > extra_param[6]: return extra_param[6]
            return res

        @njit#([numba.float64(numba.float64, numba.float64, numba.float64, numba.float64[:])])
        def potentialHarmonicWellMoving(x, y, t, extra_param):
            res = 1 / 2. * extra_param[5] * ((x - extra_param[2]) ** 2 + (y - extra_param[3]) ** 2)
            if res > extra_param[6]: return extra_param[6]
            return res

        @njit#([numba.float64(numba.float64, numba.float64, numba.float64[:])])
        def potentialHarmonicWellMovingX(x, t, extra_param):
            res = 1 / 2. * extra_param[5] * (x - extra_param[2]) ** 2
            #if res > extra_param[6]: return extra_param[6]
            return res

        @njit#([numba.float64(numba.float64, numba.float64, numba.float64[:])])
        def potentialHarmonicWellMovingY(y, t, extra_param):
            res = 1 / 2. * extra_param[5] * (y - extra_param[3]) ** 2
            #if res > extra_param[6]: return extra_param[6]
            return res


        inicial2D = mathPhysics.eigenvectorHarmonic2DGenerator(0., 0, 0., 0, kHarm) # 2 2


        # Leaderboard stuff (json file)  # lazily copied from: https://stackoverflow.com/a/12309296
        def json_load_file(json_file):
            with open(json_file) as json_file:
                json_data = json.load(json_file)
                return json_data

        def json_dump_to_file(json_file, json_dict):
            with open(json_file, 'w') as outfile:
                json.dump(json_dict, outfile, indent=4)

        class LeaderboardInput(TextInput):
            # Only 5 characters, and upper leter
            def insert_text(self, substring, from_undo=False):
                s = substring.upper()[:5-len(self.text)]
                return super().insert_text(s, from_undo=from_undo)

        def setMoveGame(args):
            ps = self.manager.get_screen("playscreen")
            args["kHarm"] = 8.
            args["height"] = 100.
            np.copyto(extra_param, np.array([0., 0., 0., 0., 0., args["kHarm"], height]))
            args["goalRadius"] = 2.
            args["score"] = 0
            args["health"] = 3
            args["coins"] = 0
            args["newCoin"]=True # New coin can be scheduled to be created
            args["goalX"] = ps.QSystem.x0 + args["goalRadius"] + random.random() * (ps.QSystem.xf - ps.QSystem.x0 - 2 * args["goalRadius"])
            args["goalY"] = ps.QSystem.y0 + args["goalRadius"] + random.random() * (ps.QSystem.yf - ps.QSystem.y0 - 2 * args["goalRadius"])
            args["goalCircle"] = plt.Circle((args["goalX"], args["goalY"]), args["goalRadius"], alpha=0.2, color='black')
            args["firstDraw"] = True
            args["drawnCircle"] = None
            args["gameOver"] = False

            args["lbDir"] = (mainDir / "./leaderboard.json").resolve()
            args["leaderboard"] = json_load_file(args["lbDir"])

        ##### Three ideas for movement:
        #   - Soft movement. We change "speed" with keyboard
        #   - Direct movement. We change the position of the well directly
        #           - With keyboard
        #           - Directly with mouse!?


        def extra_keyboard_movegame(ps, keyboard, keycode, text, modifiers):
            if keycode[1] in ['up', 'down' , 'left' , 'right', 'w' , 'a' , 's' , 'd']:
                t = ps.QSystem.t
                ps.extra_param[0] = ps.extra_param[0] + ps.extra_param[2] * (t - ps.extra_param[4])
                ps.extra_param[1] = ps.extra_param[1] + ps.extra_param[3] * (t - ps.extra_param[4])
                ps.extra_param[4] = t
            if keycode[1] in ['up','w']:
                ps.extra_param[3] += 0.25
            if keycode[1] in ['down' , 's']:
                ps.extra_param[3] -= 0.25
            if keycode[1] in ['left' , 'a']:
                ps.extra_param[2] -= 0.25
            if keycode[1] in ['right' , 'd']:
                ps.extra_param[2] += 0.25
            return True

        point_text = {'cat': "Punts: ", 'eng': "Points: ", 'esp': "Puntos: "}
        money_text = {'cat': "Monedes: ", 'eng': "Coins: ", 'esp': "Monedas: "}
        health_text = {'cat': "Vides: ", 'eng': "Lifes: ", 'esp': "Vidas: "}

        def drawCircle(instance=None):  #Game Logic. Done in matplotlib directly (to be able to draw circles there),
                                        # which makes it a bit more of a mess than it needs to be, but it's the same
            ps = self.manager.get_screen("playscreen")

            ps.extraArgs["progress"].value = (instance.frame%(6/0.04)) / (6/0.04) * 100
            if ps.extraArgs["energyButton"].disabled:
                fig = ps.extraArgs["energyGraph"]

                # Redraw background. If not, bars don't get deleted when enregy goes down
                for patch in ps.extraArgs["energyAx"].patches:
                    if patch != ps.extraArgs["energyK"][0] and patch != ps.extraArgs["energyV"][0]: fig.draw_artist(patch)

                EKinetic = np.real(ps.QSystem.kineticEnergy())
                for bar in ps.extraArgs["energyK"]:
                    bar.set_height(np.real(ps.QSystem.kineticEnergy()))
                    fig.draw_artist(bar)
                for bar in ps.extraArgs["energyV"]:
                    bar.set_height(np.real(ps.QSystem.potentialEnergy()))
                    bar.set_y(EKinetic)
                    fig.draw_artist(bar)

                fig.canvas.drawOptimized()

            if ps.extraArgs["firstDraw"]:
                instance.drawnCircle = instance.axPsi.add_patch(ps.extraArgs["goalCircle"])
                ps.extraArgs["firstDraw"] = False
                instance.observedParticle = None
                ps.playButton.disabled = True # Pausing can cause cheating. L
            elif instance.frame%(6/0.04)==0: # Every 6 seconds
                instance.QSystem.modSquared()
                i, j = mathPhysics.generateAsDiscreteDistribution(instance.QSystem.psiMod)
                x, y = instance.QSystem.X[i], instance.QSystem.X[j]

                instance.observedParticle = instance.axPsi.add_patch(plt.Circle((x, y), radius=0.15, color='cyan'))

                lan = App.get_running_app().root.language
                if (x-ps.extraArgs["goalX"])**2 + (y-ps.extraArgs["goalY"])**2 <= ps.extraArgs["goalRadius"]**2:
                    instance.drawnCircle.set(color='green', alpha=0.5)
                    ps.extraArgs["score"] += 5 * ps.extraArgs["difficulty"] + 2 * (ps.extraArgs["difficulty"] - 1)**2

                    ps.extraArgs["labelScore"].text = point_text[lan] + "{}".format(ps.extraArgs["score"])

                else:
                    instance.drawnCircle.set(color='red', alpha=0.5)
                    ps.extraArgs["health"] -= 1
                    ps.extraArgs["labelHealth"].text=health_text[lan]+'♥' * ps.extraArgs["health"]
                    if ps.extraArgs["health"] == 0:
                        ps.stopPlaying()
                        #ps.playButton.disabled_color = 'red'
                        ps.playButton.disabled = True
                        ps.extraArgs["gameOver"] = True
                        ps.extraArgs["shop"].disabled = True

                        lb = ps.extraArgs["leaderboard"]
                        ranking = 6 # By default, not winner
                        for pos in range(1,5+1):
                            if lb[str(pos)]["score"] < ps.extraArgs["score"]:
                                ranking = pos
                                break

                        if ranking != 6:
                            for pos in range(5, ranking, -1):
                                lb[str(pos)] = lb[str(pos-1)]

                            lb[str(ranking)] = {"name":'', "score":ps.extraArgs["score"]}


                            layout = BoxLayout(orientation='vertical')
                            layout.add_widget(Label(text="Bona puntuació!\nIdentifica't" if lan=='cat' else "Good score!\nWrite your name:" if lan=='eng' else "Buena puntuación!\nRegístrate:"))
                            nameInput = LeaderboardInput(multiline=False, font_name='RobotoMono-Regular', size_hint=(None,None), height=50, width=100, pos_hint={"center_x":0.5, "center_y":0.5})
                            def nameSet(instance):
                                lb[str(ranking)]["name"] = nameInput.text
                                json_dump_to_file(ps.extraArgs["lbDir"], lb)

                                lbpopup = Popup(size_hint=(0.4, 0.4), title='Ranking')
                                lbpopup.add_widget(Label(
                                    text="{:>5}{:>10}{:>10}\n{}\n".format("POS", "NOM", "PUNTS", "-" * 25) + "".join(
                                        ["{:>5}{:>10}{:>10}\n".format(num, lb[str(num)]["name"], lb[str(num)]["score"]) for num in
                                         lb]),
                                    font_name='RobotoMono-Regular'))  # Font comes with kivy, so for sure everyone has it
                                lbpopup.open()

                            layout.add_widget(nameInput)
                            newRecord = Popup(size_hint=(0.4,0.4), title='Record!', on_dismiss=nameSet)
                            newRecord.add_widget(layout)
                            newRecord.open()

                        else:
                            lbpopup = Popup(size_hint=(0.4,0.4), title='Ranking')
                            lbpopup.add_widget(Label(text="{:>5}{:>10}{:>10}\n{}\n".format("POS", "NOM", "PUNTS", "-" * 25) + "".join(
        ["{:>5}{:>10}{:>10}\n".format(num, lb[str(num)]["name"], lb[str(num)]["score"]) for num in lb]),font_name='RobotoMono-Regular'))  # Font comes with kivy, so for sure everyone has it
                            lbpopup.open()

                        return instance.axPsi.text(0.5, 0.5, 'GAME OVER!', dict(size=30, fontweight=800, color='white'),
                                    horizontalalignment='center', verticalalignment='center',
                                    path_effects=[animate.peffects.withStroke(linewidth=4, foreground="black")],
                                    transform=instance.axPsi.transAxes), instance.drawnCircle, instance.observedParticle

                ps.stopPlaying()

                def newStep(*args):
                    ps.extraArgs["goalRadius"] = ps.extraArgs["goalRadius"] ** 0.9
                    ps.extraArgs["goalX"] = instance.QSystem.x0 + ps.extraArgs["goalRadius"] + random.random() * (
                                instance.QSystem.xf - instance.QSystem.x0 - 2 * ps.extraArgs["goalRadius"])
                    ps.extraArgs["goalY"] = instance.QSystem.y0 + ps.extraArgs["goalRadius"] + random.random() * (
                                instance.QSystem.yf - instance.QSystem.y0 - 2 * ps.extraArgs["goalRadius"])
                    instance.drawnCircle.remove()
                    ps.extraArgs["goalCircle"] = plt.Circle((ps.extraArgs["goalX"], ps.extraArgs["goalY"]),
                                                            ps.extraArgs["goalRadius"], alpha=0.2, color='black')
                    instance.drawnCircle = instance.axPsi.add_patch(ps.extraArgs["goalCircle"])
                    instance.observedParticle.remove()
                    #print(ps.extraArgs["score"])
                    ps.startPlaying()

                Clock.schedule_once(newStep, timeout=1)

                return instance.drawnCircle, instance.observedParticle

            """else:
                if instance.observedParticle is not None: instance.observedParticle.remove()"""

            return instance.drawnCircle

        """def extra_update_move(args):"""

        def coins_add(args, val):
            args["coins"]+=val
            lan = App.get_running_app().root.language
            args["labelCoins"].text = money_text[lan]+"{}".format(args["coins"])

        # dt is irrelevant, but is an argument used by schedule_once
        def createCoin(args, ps):
            if not args["gameOver"]:
                def coin_get(*arg):
                    coins_add(args, 1)

                def coin_end(*arg):
                    args["newCoin"] = True

                ps.plotRelative.add_widget(GameCoin(callbackClick=coin_get, callbackEnd=coin_end,
                                                pos_hint={"center_x":0.2+random.random()*0.6, "center_y":0.2+random.random()*0.6}))


        def extra_update_movement(args, ps):
            if args["newCoin"] is True:
                args["newCoin"] = False
                args["coinSchedule"] = Clock.schedule_once(lambda dt: partial(createCoin, args, ps)(), 5/args["difficulty"]) # Too fast??? Clock.schedule_once doesn't work too well

        def extra_info_movement(args, ps):
            lan = App.get_running_app().root.language
            layout = GridLayout(rows=4,cols=1, width = sp(500/2), size_hint_x=None, padding=20)

            args["labelScore"] = Label(text=point_text[lan]+"{}".format(args["score"]), size_hint_min_y=sp(22), size_hint=(1,0.07))
            try: args["labelHealth"] = Label(text=health_text[lan] + '♥'*args["health"], font_name='Arial', color=(1,0,0,1), size_hint_min_y=sp(22), size_hint=(1,0.07))  #Maybe Arial not in all machines?
            except: args["labelHealth"] = Label(text=health_text[lan]+"{}".format(args["health"]), size_hint_min_y=sp(30), size_hint=(1,0.07))  # No heart emoji then
            layout.add_widget(args["labelScore"])
            layout.add_widget(args["labelHealth"])

            args["labelCoins"] = Label(text=money_text[lan]+"{}".format(args["coins"]), color=(0.7,0.6,0,1), size_hint_min_y=sp(22), size_hint=(1,0.07))
            layout.add_widget(args["labelCoins"])
            args["coinSchedule"] = None

            args["progress"] = ProgressBar(size_hint_y=None, height=dp(25/2))
            #layout.add_widget(args["progress"])
            ps.plotRelative.add_widget(args["progress"])

            BtnHeight = sp(40)
            shopBig = BoxLayout(orientation="vertical")
            args["shop"] = shopBig
            shopBig.add_widget(Label(text="_________________________\n--------------- {} ---------------".format('Tenda ' if lan=='cat' else ' Shop ' if lan=='eng' else "Tienda"), size_hint_min_y=sp(60), size_hint=(1,0.14)))
            shop = GridLayout(rows=2, cols=2, spacing=sp(5))#, size_hint_y=0.3)

            def buyEnergy(btn):
                if args["coins"] >= 1:
                    coins_add(args, -1)

                    args["energyButton"].disabled = True

            energyGrid = GridLayout(cols=2,rows=1)#,size_hint_y=0.6)
            energyButtonBox = BoxLayout(padding=(sp(10),sp(20)))
            buttonPad = BoxLayout()


            args["energyButton"] = Button(text = "(1)"+ ("Mostra\nEnergia" if lan=='cat' else "Show\nEnergy" if lan=='eng' else "Muestra\nEnergía"),
                                          on_release=buyEnergy, size_hint_y=None, height=BtnHeight)

            buttonPad.add_widget(args["energyButton"])
            energyButtonBox.add_widget(buttonPad)
            energyGrid.add_widget(energyButtonBox)

            args["energyGraph"] = plt.figure()
            fig = args["energyGraph"]
            ax = fig.gca()
            args["energyAx"] = ax
            #ax.set_xlabel("")
            ax.get_xaxis().set_visible(False)
            ax.set_ylabel("Energia" if (lan=='cat' or lan=='esp') else 'Energy' + " ({})".format(unit_energy))
            ax.set_ylim([0., 100.])
            #ax.set_xticklabels([])
            plt.tick_params(
                axis='x',  # changes apply to the x-axis
                which='both',  # both major and minor ticks are affected
                bottom=False,  # ticks along the bottom edge are off
                top=False,  # ticks along the top edge are off
                labelbottom=False)  # labels along the bottom edge are off
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            args["energyK"] = ax.bar([0.],[np.real(ps.QSystem.kineticEnergy())], color='b')
            args["energyV"] = ax.bar([0.], [np.real(ps.QSystem.potentialEnergy())], bottom=[1.], color='y')
            ax.bar([0.], [500.], color='black') # "Background"
            #ax.legend(["K","V"], bbox_to_anchor=(1.04,1))
            FigureCanvasKivyAggModified(fig)
            #fig.canvas.size_hint_y=None
            #fig.canvas.height=300
            energyGrid.add_widget(fig.canvas)

            shopBig.add_widget(energyGrid)

            def prep(dt):
                fig.tight_layout()
                fig.canvas.draw()
            Clock.schedule_once(prep)

            #Buy health, button

            def extra_life(btn):
                if args["coins"] >= args["healthCost"]:
                    coins_add(args, -args["healthCost"])
                    args["healthCost"]+=2
                    args["healthButton"].text = "({})".format(args["healthCost"]) + ("Vida\nExtra" if (lan=='cat' or lan=='esp') else "Extra\nLife")
                    args["health"] += 1
                    args["labelHealth"].text = health_text[lan] + '♥' * args["health"]

            args["healthCost"] = 2
            args["healthButton"] = Button(text="({})".format(args["healthCost"]) + ("Vida\nExtra" if (lan=='cat' or lan=='esp') else "Extra\nLife"), on_release=extra_life, size_hint_y=None, height=BtnHeight)
            shop.add_widget(args["healthButton"])

            # Convert coins to points:
            def coin_to_point(btn):
                if args["coins"] >= 2:
                    coins_add(args, -2)
                    args["score"] += 1
                    lan = App.get_running_app().root.language
                    args["labelScore"].text = point_text[lan]+"{}".format(ps.extraArgs["score"])

            shop.add_widget(Button(text="(2)"+("Compra\nPunt" if lan=='cat' else "Buy\nPoint" if lan=='eng' else "Compra\nPunto"), on_release=coin_to_point, size_hint_y=None, height=BtnHeight))

            args["difficulty"] = 1
            args["difficultyCost"] = 5
            def raiseDifficulty(btn):
                if args["coins"] >= args["difficultyCost"]*args["difficulty"]:
                    coins_add(args, -args["difficulty"]*args["difficultyCost"])
                    args["difficulty"] += 1
                    if args["difficulty"] == 3: args["difficultyButton"].disabled = True
                    else: args["difficultyButton"].text = "({})".format(args["difficultyCost"] * args["difficulty"]) + ("Nou\nElectró" if lan=='cat' else "New\nElectron" if lan=='eng' else "Nuevo\nElectrón")

                    if args["coinSchedule"] is not None: args["coinSchedule"].cancel()
                    args["newCoin"] = True
                    ps.animation.frame = 1
                    #args["kHarm"] += 2
                    ps.QSystem.setState(mathPhysics.eigenvectorHarmonic2DGenerator(0., 1 if args["difficulty"] > 1 else 0, 0., 1 if args["difficulty"] > 2 else 0, args["kHarm"]))
                    ps.QSystem.renorm()
                    ps.animation.manualUpdate(onlyDraw=True)
                    ps.animation.rescalePsi()
                    ps.QSystem.t = 0.
                    ps.extra_param[0:4+1] = 0.
                    #ps.extra_param[5] = args["kHarm"]

            args["difficultyButton"] = Button(text="({})".format(args["difficultyCost"]*args["difficulty"]) + ("Renew\nAtom" if lan=='eng' else "Renova\nÀtom" if lan=='cat' else "Renueva\nÁtomo"),
                                              on_release=raiseDifficulty, size_hint_y=None, height=BtnHeight)
            shop.add_widget(args["difficultyButton"])

            shopBig.add_widget(shop)
            layout.add_widget(shopBig)


            args["sizeStep"] = 1

            obj_text = {'cat': "Objectiu\nmés gran", 'eng': "Bigger\ntarget", 'esp': "Objetivo\nmayor"}
            def raiseSize(btn):
                if args["coins"] >= args["sizeStep"]**2:
                    coins_add(args, -args["sizeStep"]**2)
                    args["sizeStep"]+=1
                    args["goalRadius"] *= sqrt(3)
                    args["goalCircle"].set(radius=args["goalRadius"])
                    args["sizeButton"].text = "({})".format(args["sizeStep"]**2) + obj_text[lan]

            args["sizeButton"] = Button(text="({})".format(args["sizeStep"]**2)+obj_text[lan],
                                        on_release=raiseSize, size_hint_y=None, height=BtnHeight)

            shop.add_widget(args["sizeButton"])

            return layout

        def extra_clean_moveGame(args):
            animate.cleanFigClose(args["energyGraph"])
            if args["coinSchedule"] is not None: args["coinSchedule"].cancel()

            """clock = Clock.schedule_once(lambda x: print("clock"), 0.5)
            def unscheduleAfter(dt):
                clock.cancel()
                print("?")
            Clock.schedule_once(unscheduleAfter, 1)"""# We can check like this no error is thrown for cancelling an
                                                      # already finished clock schedule



        def moveGameInfo():
            lan = App.get_running_app().root.language
            info_text = {'cat':
                             "AL laboratori tenim un àtom atrapat amb una pinça òptica \nMou la pinça, un pou atractiu, amb\nles fletxes del teclat ← ↑ → ↓ o WASD\n\n"
                             "Volem realitzar experiments amb l'àtom, porta'l fins els cercles marcats.\nQuan s'ompli la barra blava es realitzarà l'experiment,"
                             "\nmés val que allà el trobem, o perdrem finançament...\n"
                             "Però vigila que no el perdis! Pista: Vigila l'energia\n\nClica les monedes per comprar millores\n"
                             "Quants punts pots aconseguir?",
                         'eng':
                             "We have trapped an atom in the lab with optical tweezers \nMove the tweezers, an attractive well, with\nthe keyboard arrows ← ↑ → ↓ or WASD\n\n"
                             "We want to perform experiments with it, bring it to the circled areas\nWhen the blue bar is full, the experiment will be performed,"
                             "\nwe better observe it there, or we will lose funding...\n"
                             "But be careful not to lose it! Tip: Watch the energy\n\nClick fast to catch coins and buy upgrades\n"
                             "How many points can you get?",
                         'esp':
                             "Hemos atrapado un átomo con una pinza óptica. \nMueve la pinza, un pozo atractivo, con\nlas flechas del teclado ← ↑ → ↓ o WASD\n\n"
                             "Queremos realizar experimentos con el átomo, llévalo a las zonas marcadas!\nCuando se llene la barra azul se realizará el experimento,"
                             "\nmás vale que lo observemos ahí, o perdremos financiación...\n"
                             "Pero vigila no lo pierdas! Pista: Vigila la energía\n\nClica rápdio para atrapar las monedas y conseguir mejoras\n"
                             "Cuántos puntos puedes conseguir?",
                         }
            infoPopup = Popup(title="INFO", auto_dismiss=True, size_hint=(0.6, 0.6))
            infoPopup.add_widget(Label(text=info_text[lan], font_name="Arial"))
            infoPopup.open()
            #TextPopup("Mou el pou de potencial amb\nles fletxes del teclat ← ↑ → ↓\nTransporta l'electró per tal que es pugui\nobservar a les zones marcades").open()

        definition = {
            #"QSystem": QSystem,
            "initState": inicial2D, "potential":potentialHarmonicWellMoving, "extra_param":extra_param,
            "drawClassical": False, "drawExpected": False, "duration": None,#10.
            "extra_update": extra_update_movement, #"extraCommands": [('key_press_event', moveHarmonicWellKeyboard)],
            "extraUpdates": [drawCircle], "isFocusable":False, "plotWidget":extra_info_movement, "scalePsi": False,
            "showNorm": False, "showEnergy":False, "showMomentum":False, "debugTime":False, "extra_keyboard_action":extra_keyboard_movegame,
            "info_action": moveGameInfo, "extra_clean":extra_clean_moveGame
        }

        """definition = {
            "initState": inicial2D, "potential": potentialHarmonicWellMoving, "extra_param": extra_param,
            "drawClassical": False, "drawExpected": False, "duration": None,  # 10.
            "extra_update": extra_update_movement,  # "extraCommands": [('key_press_event', moveHarmonicWellKeyboard)],
            "extraUpdates": [drawCircle], "isFocusable": False, "plotWidget": extra_info_movement, "scalePsi": False,
            "showNorm": False, "showEnergy": False, "showMomentum": False, "debugTime": False, "extra_keyboard_action": extra_keyboard_movegame,
            "info_action": moveGameInfo, "extra_clean": extra_clean_moveGame,
            "separable": True, "init_x":  eigenHarmonic1D,
            "init_y": eigenHarmonic1D,
            "pot_x": potentialHarmonicWellMovingX,
            "pot_y": potentialHarmonicWellMovingY, "scalePot": False
        }"""
        """"initState": mathPhysics.eigenvectorHarmonic2DGenerator(0., 2, 0., 2, 8.),
            "potential": potentialHarmonicWellMoving
        }"""
        self.ids.gameSelect.add_widget(
            RoundedButton(text="Atom delivery", on_release=partial(self.switch, definition=definition, setExtraArgs=setMoveGame),
                   size_hint_y=None, height=dp(70), size_hint_x=0.4))


    def switch(self, *args, definition=None, setExtraArgs=None):
        self.manager.get_screen("playscreen").set_self(definition, setExtraArgs=setExtraArgs)
        self.manager.transition.direction = "left"
        self.manager.current = "playscreen"
        self.manager.get_screen("playscreen").sourceScreen = "games"




class ColoredLabel(Label):
    pass

class SaveGifPopup(Popup):
    def __init__(self, window, duration=5., fileName="resultat", animwidth=12., animheight=7., **kwargs):
        self.window = window  # Window holds information such as QuantumSystem and Animation
        self.duration = duration
        self.fileName = fileName
        self.animwidth = animwidth
        self.animheight = animheight
        super(SaveGifPopup, self).__init__(**kwargs)

    def saveAnimation(self, fName, duration, type):
        anim = self.window.animation
        animationToSave = animate.QuantumAnimation(
            anim.QSystem, dtSim=anim.dtSim, stepsPerFrame=anim.stepsPerFrame, width=self.animwidth, height=self.animheight,
            duration=duration, dtAnim=anim.dtAnim, callbackProgress=True,
            showPotential=True, varyingPotential=True,
            showMomentum=anim.showMomentum, showEnergy=anim.showMomentum, showNorm=anim.showNorm,
            scalePsi=anim.scalePsi, scaleMom=anim.scaleMom, isKivy=False,
            drawClassical=anim.drawClassical, drawClassicalTrace=anim.drawClassicalTrace, drawExpected=anim.drawExpected, drawExpectedTrace=anim.drawExpectedTrace,
            language=self.manager.language)
        #animationToSave.reset_plot()
        try:    animationToSave.saveAnimation(fName, type)
        except: TextPopup("Format Error").open()  #format probablement no suportat

    """def on_open(self):
        self.ids.Nx.text = str(self.window.animation.QSystem.Nx)
        self.ids.Ny.text = str(self.window.animation.QSystem.Ny)
        self.ids.x0.text = str(self.window.animation.QSystem.x0)
        self.ids.xf.text = str(self.window.animation.QSystem.xf)
        self.ids.y0.text = str(self.window.animation.QSystem.y0)
        self.ids.yf.text = str(self.window.animation.QSystem.yf)

        self.ids.t.text = str(self.window.animation.QSystem.t)

        self.ids.dtSim.text = str(self.window.animation.dtSim)"""

class ParametersPopup(Popup):
    lan = StringProperty()
    def __init__(self, window, **kwargs):
        self.window = window  # Window holds information such as QuantumSystem and Animation
        super(ParametersPopup, self).__init__(**kwargs)

    def setPotential(self):
        if (self.ids.potential.on_text_validate() == 0):
            self.window.QSystem.changePotential(self.window.potential)
            self.window.animation.manualUpdate(onlyDraw=True)
            #self.window.animation.reset_plot()

    def previewPotential(self):
        copy = self.window.potential
        copyDef = self.window.potentialDef

        if (self.ids.potential.on_text_validate() == 0):
            self.window.QSystem.setPotential(self.window.potential)

            self.window.potential = copy
            self.window.potentialDef = copyDef

            self.window.tempState["psi"] = self.window.QSystem.psiMod
            self.window.tempState["unit_col"] = unit_energy
            Factory.PlotPopup(self.window.tempState).open()

    def setInitState(self):
        if (self.ids.initState.on_text_validate() == 0):
            self.window.QSystem.setState(self.window.initState)
            self.window.animation.manualUpdate(onlyDraw=True)
            #self.window.animation.reset_plot()

    def previewInitState(self):
        copy = self.window.initState
        copyDef = self.window.initStateDef

        if (self.ids.initState.on_text_validate() == 0):
            self.window.QSystem.setTempState(self.window.initState)

            self.window.initState = copy
            self.window.initStateDef = copyDef

            self.window.tempState["psi"] = self.window.QSystem.psiCopy
            self.window.tempState["unit_col"] = r'$({})^{{-2}}$'.format(unit_dist)
            Factory.PlotPopup(self.window.tempState).open()

    """def on_open(self):
        self.ids.Nx.text = str(self.window.animation.QSystem.Nx)
        self.ids.Ny.text = str(self.window.animation.QSystem.Ny)
        self.ids.x0.text = str(self.window.animation.QSystem.x0)
        self.ids.xf.text = str(self.window.animation.QSystem.xf)
        self.ids.y0.text = str(self.window.animation.QSystem.y0)
        self.ids.yf.text = str(self.window.animation.QSystem.yf)

        self.ids.t.text = str(self.window.animation.QSystem.t)

        self.ids.dtSim.text = str(self.window.animation.dtSim)"""

class DebugPopup(Popup):
    lan = StringProperty()
    def __init__(self, window, **kwargs):
        self.window = window  # Window holds information such as QuantumSystem and Animation
        super(DebugPopup, self).__init__(**kwargs)

class PlayScreen(Screen):
    def __init__(self, sourceScreen = "examples", **kwargs):
        super(PlayScreen, self).__init__(**kwargs)
        self.sourceScreen = sourceScreen
        self.extra_param = np.array([1.])
        self.extra_on_enter = None
        self.animation = None

        # Keyboard: https://kivy.org/doc/stable/api-kivy.core.window.html
        self.extra_keyboard_action = None
        self._keyboard = None
        #self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        # self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None


    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if self.extra_keyboard_action is not None:
            self.extra_keyboard_action(self, keyboard, keycode, text, modifiers)

        return True

    def on_enter(self, *args):
        self.animation.reset_plot()
        #Clock.schedule_once( lambda x: self.animation.reset_plot() )
        if self.extra_on_enter is not None: self.extra_on_enter(self.extraArgs)

    def set_self(self, definition=None, setExtraArgs=None):
        #self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        #self._keyboard.bind(on_key_down=self._on_keyboard_down)

        if definition == None:
            definition = {}
        self.definition = definition

        self.extra_keyboard_action = None

        self.extra_on_enter = None

        self.paused = True
        self.Nx = 200; self.Ny = 200
        L = 10.
        self.x0, self.y0 = -L, -L
        self.xf, self.yf = L, L


        # We allow 16 global variables, which can be named
        self.nVar = 16
        self.extra_param = np.zeros(self.nVar, dtype=np.float64)
        self.extra_param[0] = 0.
        self.extra_param[self.nVar - 2] = -5.
        self.extra_param[self.nVar - 1] = -2.5
        # A name can be assigned to each of these
        self.paramNames = ["Vx"] + [""] * (self.nVar - 3) + ["px"] + ["py"]
        self.variablesDict = {}
        self.setVarDict()

        self.initState = mathPhysics.gaussian2D(7, 1., self.extra_param[self.nVar - 2],
                                                7., 1., self.extra_param[self.nVar - 1])
        self.initStateDef = \
            "gaussianPacket(x-7, 1, {px}) * gaussianPacket(y-7, 1, {py})"
        # "1/(2*pi)**0.5 * exp(-1./4. * ((x-7)**2 + (y-7)**2)) * exp(1j * ({px}*x + {py}*y))"

        self.potential = mathPhysics.potentialBarrier
        self.potentialDef = "exp(-(x ** 2) / 0.1) * 5 / sqrt(0.1 * pi)"

        self.extra_update = None
        self.extra_clean = None

        self.info_action = None

        self.customOperator = None
        self.renormStep = False
        self.step = 'fastest'


        self.separable = False
        self.pot_x = mathPhysics.potential0_1D
        self.pot_y = mathPhysics.potential0_1D
        self.init_x = None
        self.init_y = None

        for key in definition:
            vars(self)[key] = definition[key]

        if "QSystem" in self.definition:
            self.QSystem = self.definition["QSystem"]
        else:
            self.QSystem = mathPhysics.QuantumSystem2D(self.Nx, self.Ny, self.x0, self.y0, self.xf, self.yf,
                                                       self.initState,
                                                       potential=self.potential, extra_param=self.extra_param,
                                                       renormStep=self.renormStep, customOperator=self.customOperator,
                                                       step=self.step,
                                                       separable=self.separable, pot_x=self.pot_x, pot_y=self.pot_y, init_x=self.init_x, init_y=self.init_y)

        self.savedStates = []
        self.tempState = {"psi": self.QSystem.psi, "x0": self.QSystem.x0, "xf": self.QSystem.xf
            , "y0": self.QSystem.y0, "yf": self.QSystem.yf,
                          "name": "temp"}

        self.setExtraArgs = setExtraArgs
        self.extraArgs = {}
        if setExtraArgs is not None:
            setExtraArgs(self.extraArgs)

        animKeys = {"dtSim":0.01, "dtAnim":0.04, "stepsPerFrame":0, "debugTime":False, "duration":None,
                    "showPotential":True, "varyingPotential":True, "showMomentum":True, "showEnergy":True, "showNorm":False,
                    "scalePsi":True, "scaleMom":True, "zoomMom":1.,"scalePot":True, "isFocusable":True,
                    "drawClassical":True, "drawClassicalTrace":False, "drawExpected":True, "drawExpectedTrace":False,
                    "extraCommands":[], "extraUpdates":[], "extraUpdatesStart":False, "extraUpdatesUpdate":False,
                    "unit_dist":unit_dist,"unit_mom":unit_mom,"unit_time":unit_time,"unit_energy":unit_energy,
                    "customPlot":None, "customPlotUpdate":False, "customPlotFull":False,
                    "psiRepresentation": "mod2"}
        for key in animKeys:
            # Changes value to definition (dictionary), but if it's not in the dictionary leaves it as is (default)
            animKeys[key] = definition.get(key, animKeys[key])

        self.animation = animate.QuantumAnimation(self.QSystem, **animKeys,
                                                  isKivy=True, language=self.manager.language)

        self.plotBox = self.ids.plotBox#BoxLayout(size_hint=(1, 0.8))
        self.plotRelative = self.ids.plotRelative#RelativeLayout()
        self.plotRelative.add_widget(self.animation.fig.canvas)
        #self.plotBox.add_widget(self.plotRelative)

        # ADD HERE EXTRA THINGS LIKE SLIDERS? CAN PASS DOWN CUSTOM WIDGET
        ######
        if "plotWidget" in definition:
            if callable(definition["plotWidget"]): self.plotBox.add_widget(definition["plotWidget"](self.extraArgs, self))   # Careful here with callable()
            else: self.plotBox.add_widget(definition["plotWidget"])

        ######

        buttonBox = self.ids.buttonBox
        #buttonBox = BoxLayout(size_hint=(1, 0.2), orientation="horizontal", padding=10, spacing=20)

        if self.info_action is not None:
            buttonBox.add_widget(InfoButton(on_release=lambda *args: self.info_action()))
        restartButton = RestartButton(text="", on_release=self.resetAll)
        buttonBox.add_widget(restartButton)

        self.playButton = PlayButton(text="", state='normal' if self.paused else 'down',
                                  on_press= lambda x: self.startPlaying() if self.paused else self.stopPlaying())

        buttonBox.add_widget(self.playButton)

        returnButton = ImageButton(img_src='images/return.png',on_release = self.goBack)#, text="Retorna enrere")
        buttonBox.add_widget(returnButton)

        #mainBox = self.ids.mainBox
        #mainBox = BoxLayout(orientation="vertical")

        #mainBox.add_widget(self.plotBox)
        #mainBox.add_widget(buttonBox)
        #self.add_widget(mainBox)


        # should add here the option to open an example in the sandbox

    def goBack(self, *args):
        #self.clean()  Clean done on_leave
        self.manager.transition.direction = "right"
        self.manager.current = self.sourceScreen

    def clean(self):
        self.stopPlaying()
        #self.animation.fig.canvas.canvas.clear()
        animate.cleanFigClose(self.animation.fig)


        self.plotRelative.clear_widgets()
        #self.plotBox.clear_widgets()  #Clear actually just loops through children and deletes them.
                                      # WE can remove only non permanent (plotRelative) widgets
        for child in self.plotBox.children:
            if child != self.plotRelative:
                self.plotBox.remove_widget(child)
        self.ids.buttonBox.clear_widgets()
        #self.clear_widgets()
        if self.extra_clean is not None: self.extra_clean(self.extraArgs)

        ### Trying to fix memory leak, to no avail
        # print(vars(self.animation.fig.canvas))
        # print(len(vars(self.animation.fig)))
        # del self.animation.fig.canvas
        # print(len(vars(self.animation.fig)))
        # print(len(vars(self)), vars(self))
        # self.canvas.clear()

    def on_leave(self):
        self.clean()

    def resetAll(self, *args):
        self.clean()
        self.set_self(self.definition, setExtraArgs=self.setExtraArgs)
        Clock.schedule_once(lambda *args: Clock.schedule_once(self.on_enter))  # Everything is drawn next frame
                                                                               # so we need to wait 2 frames to resize things

    def stopPlaying(self):
        try: self.schedule.cancel()
        except: pass
        self.paused = True
        self.animation.paused = True
        if self._keyboard is not None: self._keyboard.unbind(on_key_down=self._on_keyboard_down)

    def startPlaying(self):
        self.schedule = Clock.schedule_interval(self.play, self.animation.dtAnim)
        self.paused = False
        self.animation.paused = False
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        # self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def play(self, dt):
        if self.animation.paused:
            self.paused = self.animation.paused
            self.stopPlaying()
        else:
            self.animation.manualUpdate()
            if self.extra_update is not None: self.extra_update(self.extraArgs, self)

    def setVarDict(self):
        self.variablesDict.clear()
        for i in range(self.nVar):
            if self.paramNames[i] != "": self.variablesDict[self.paramNames[i]] = "extra_param[{}]".format(i)
        """self.variablesDict = \
            {self.paramNames[i]: "extra_param[{}]".format(i) for i in range(self.nVar) if self.paramNames[i] != ""}"""




class quantumMovementApp(App):
    def build(self):
        return WindowManager()
        #return kv


class customPlotCreator():
    pass
    """The custom plot creator is charged with allowing the user
    to create a custom plot in the sandbox interactively. The main
    way to create a custom plot is determine """
    #def expressionX


    #we return a setup function and an update function.


if __name__ == "__main__":
    plt.style.use("dark_background")
    quantumMovementApp().run()