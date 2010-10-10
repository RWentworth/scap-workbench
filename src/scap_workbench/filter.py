# -*- coding: utf-8 -*-
#
# Copyright 2010 Red Hat Inc., Durham, North Carolina.
# All Rights Reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors:
#      Maros Barabas        <mbarabas@redhat.com>
#      Vladimir Oberreiter  <xoberr01@stud.fit.vutbr.cz>

import re
import gtk
import abstract
import logging
from events import EventObject

logger = logging.getLogger("scap-workbench")

class Filter:
    """Abstract class for defining filters"""

    def __init__(self, name, render):
        self.name = name
        self.active = False
        self.render = render

        self.__render()

    def __render(self):
        self.box = gtk.HBox()
        label = gtk.Label(self.name)
        label.set_justify(gtk.JUSTIFY_LEFT)

        alig = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
        alig.set_padding(5, 5, 10, 5)
        alig.add(label)
        self.box.pack_start(alig, True, True)

        self.button = gtk.Image()
        pic = self.button.render_icon(gtk.STOCK_CANCEL, size=gtk.ICON_SIZE_MENU, detail=None)
        self.button.set_from_pixbuf(pic)
        alig = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
        alig.set_padding(5, 5, 10, 5)
        alig.add(self.button)
        eb = gtk.EventBox()
        eb.connect("button-press-event", self.__cb_button)
        eb.add(alig)
        self.box.pack_end(eb, False, False)

        self.eb = gtk.EventBox()
        self.eb.add(self.box)
        self.eb.set_border_width(2)
        """
        self.eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        self.eb.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse("yellow"))
        self.eb.connect("enter-notify-event", self.__cb_enter)
        self.eb.connect("leave-notify-event", self.__cb_leave)
        self.eb.connect("button-press-event", self.__cb_btn_press)
        """
        self.eb.set_state(gtk.STATE_SELECTED)
        self.eb.show_all()
    
    """
    def __cb_enter(self, widget, event):
        if widget.get_state() == gtk.STATE_NORMAL: widget.set_state(gtk.STATE_ACTIVE)

    def __cb_leave(self, widget, event):
        if widget.get_state() == gtk.STATE_ACTIVE: widget.set_state(gtk.STATE_NORMAL)
    """

    def __cb_btn_press(self, widget, event):
        if event.button == 1:
            if  widget.get_state() == gtk.STATE_SELECTED: widget.set_state(gtk.STATE_ACTIVE)
            else: widget.set_state(gtk.STATE_SELECTED)


    def __cb_button(self, widget, event):
        self.active = not self.active
        if self.active: 
            self.eb.hide()
            stock = gtk.STOCK_APPLY
            self.render.del_filter(self)
        else: 
            self.eb.show()
            stock = gtk.STOCK_CANCEL

        #pic = self.button.render_icon(stock, size=gtk.ICON_SIZE_MENU, detail=None)
        #self.button.set_from_pixbuf(pic)

    def get_widget(self):
        return self.eb

class Search(EventObject):

    def __init__(self, render):

        self.render = render
        self.render.add_sender(id, "search")
        self.__render()

    def __render(self):
        self.box = gtk.HBox()

        self.entry = gtk.Entry()
        alig = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
        alig.set_padding(5, 5, 10, 5)
        alig.add(self.entry)
        self.box.pack_start(alig, True, True)

        self.button = gtk.Button()
        self.button.set_relief(gtk.RELIEF_NONE)
        self.button.set_label("Search")
        self.button.connect("clicked", self.cb_search)
        alig = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
        alig.set_padding(5, 5, 10, 5)
        alig.add(self.button)
        self.box.pack_start(alig, True, True)

        self.box.show_all()

    def get_widget(self):
        return self.box

    def cb_search(self, widget):
        self.render.emit("search")

class Renderer(abstract.MenuButton,EventObject):

    def __init__(self,id, core, box):

        self.core = core
        self.filters = []
        self.id = id
        EventObject.__init__(self, self.core)
        self.core.register(id, self)
        self.render(box)
        self.add_sender(id, "filter_add")
        self.add_sender(id, "filter_del")

    def render(self, box):
        """Render Box for filters"""

        #search
        self.expander = ExpandBox(box, "Search / Filters", self.core)
        filter_box = self.expander.get_widget()
        alig_filters = self.add_frame(filter_box, "Search")
        self.search = Search(self)
        self.expander.get_widget().pack_start(self.search.get_widget(), True, True)

        #filter
        alig_filters = self.add_frame(filter_box, "Active filters")
        self.menu = gtk.Menu()

        #btn choose filter
        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        button.set_label("Add filter")
        button.connect_object("event", self.cb_chooseFilter, self.menu)
        filter_box.pack_end(button, False, True)
        box.show_all()

    def get_search_text(self):
        return self.search.entry.get_text()

    def add_filter_to_menu(self, filter_info):
        """ Function add filter tu popup menu
            If filter_info == None set own filter and callBack function is render_filter which
            create window for set own filter. Must def in child.
        """
        tooltips = gtk.Tooltips()
        if filter_info != None:
            menu_items = gtk.MenuItem(filter_info["name"])
            tooltips.set_tip(menu_items, filter_info["description"])
            filter_info.update({"active":False})     # if filter is active
        else:
            menu_items = gtk.MenuItem("User filter...")
            
        menu_items.show()
        self.menu.append(menu_items)
        menu_items.connect("activate", self.cb_menu, filter_info)
    
    def cb_menu(self, widget, filter_info):
        
        if filter_info != None:
            # if filter is activated yet
            if  filter_info["active"] == False:
                self.add_filter(filter_info)
            else:
                 msg = gtk.MessageDialog()
                 msg.set_markup("Filter is olready active.")
                 msg.show()
        else:
            self.render_filter()
        
    def render_filter(self):
        """abstract"""
        pass

    def cb_chooseFilter(self, menu, event):
        if event.type == gtk.gdk.BUTTON_PRESS:
            menu.popup(None, None, None, event.button, event.time)
            return True
        return False

    def add_filter(self, filtr_info):
        """ Add filter to list active filter and emit signal filter was added"""
        filtr_info["active"] = True
        filter = Filter(filtr_info["name"], self)
        self.expander.get_widget().pack_start(filter.get_widget(), True, True)
        self.filters.append({   "id":           filter,
                                "ref_model":    None,                       # model before filtering
                                "filtr_info":   filtr_info
                            })
        self.emit("filter_add")

    def del_filter(self, filter):
        """ remove filter from active filters and emit signal deleted"""
        filter.eb.destroy()
        for item in self.filters:
            if item["id"] == filter:
                item["filtr_info"]["active"] = False
                self.filters.remove(item)
        self.emit("filter_del")
        
    def init_filter(self):
        """ clean all acive filters"""
        for item in self.filters:
            item["filtr_info"]["active"] = False
            item["id"].eb.destroy()
        self.filters = []
        

class ExpandBox(abstract.EventObject):
    """
    Create expand box. Set only to conteiner.
    """
    
    def __init__(self, box, text, core=None):
        """
        @param box Container for this expandBox.
        @param text Button name for show or hide expandBox
        @param show If ExpanBox should be hidden/showed False/True
        """
        self.core = core
        
        # body for expandBox
        rollBox = gtk.HBox()
        box.pack_start(rollBox, True, True)

        alig = gtk.Alignment()
        alig.set_padding(5, 5, 5, 5) # top, bottom, left, right
        self.frameContent = gtk.VBox()
        alig.add(self.frameContent)
        rollBox.pack_start(alig, True, True)
        
        # create icons
        self.arrowTop = gtk.Image()
        self.arrowBottom = gtk.Image()
        self.pixbufShow = self.arrowTop.render_icon(gtk.STOCK_GO_FORWARD, size=gtk.ICON_SIZE_MENU, detail=None)
        self.pixbufHide = self.arrowBottom.render_icon(gtk.STOCK_GO_BACK, size=gtk.ICON_SIZE_MENU, detail=None)
        self.arrowTop.set_from_pixbuf(self.pixbufShow)
        self.arrowBottom.set_from_pixbuf(self.pixbufShow)
        
        # create label
        self.label = gtk.Label(text)
        self.label.set_angle(90)

        #create button
        hbox = gtk.VBox()
        hbox.pack_start(self.arrowTop, False, True)        
        hbox.pack_start(self.label, True, True)
        hbox.pack_start(self.arrowBottom, False, True)
        btn = gtk.Button()
        btn.add(hbox)
        rollBox.pack_start(btn, False, True)
        btn.connect("clicked", self.cb_changed)

    def cb_changed(self, widget=None):
        logger.debug("Expander switched to %s", self.frameContent.get_property("visible"))
        if self.frameContent.get_property("visible"):
            self.frameContent.hide_all()
            self.arrowTop.set_from_pixbuf(self.pixbufShow)
            self.arrowBottom.set_from_pixbuf(self.pixbufShow)
        else:
            self.frameContent.show_all()
            self.arrowTop.set_from_pixbuf(self.pixbufHide)
            self.arrowBottom.set_from_pixbuf(self.pixbufHide)

    def get_widget(self):
        return self.frameContent

class ItemFilter(Renderer):
    
    def __init__(self, core, builder):

        self.id_filter = 0
        objectBild = builder.get_object("tailoring:refines:box_filter")
        Renderer.__init__(self, "gui:btn:tailoring:refines:filter", core, objectBild)
        self.expander.cb_changed()
#-------------------------------------------------------------------------------
 
        filter = {"name":           "Select rule List",
                  "description":    "Select rule end get them to list.",
                  "func":           self.search_pokus,        # func for metch row in model func(model, iter)
                  "param":           [],                    # param tu function
                  "result_tree":    False,               # if result shoul be in tree or list
                  }
                  
        filter1 = {"name":           "Select rule/group with s",
                  "description":    "Select rule/group end get them to list.",
                  "func":           self.search_pokus1,        # func for metch row in model func(model, iter)
                  "param":           [],                    # param tu function
                  "result_tree":    True,               # if result shoul be in tree or list
                  }

        filter2 = {"name":          "Select rule Tree",
                  "description":    "Select rule end get them to tree.",
                  "func":           self.search_pokus,        # func for metch row in model func(model, iter)
                  "param":           [],                    # param tu function
                  "result_tree":    True,                       # if result shoul be in tree or list
                  }
                  
        self.add_filter_to_menu(filter)
        self.add_filter_to_menu(filter1)
        self.add_filter_to_menu(filter2) 
        self.add_filter_to_menu(None)

       #test filter
    def search_pokus(self, model, iter, params):
        pattern = re.compile("rule",re.IGNORECASE)
        if pattern.search(model.get_value(iter, 3),0,4) != None:
            return True
        else:
            return False
            
    def search_pokus1(self, model, iter, params):
        pattern = re.compile("how to",re.IGNORECASE)
        if pattern.search(model.get_value(iter, 3)) != None:
            return True
        else:
            return False
#-------------------------------------------------------------------------------

    def label_to_table(self, name, table, x, x1, y, y1):
        label = gtk.Label(name)
        label.set_use_markup(True)
        table.attach(label, x, x1, y, y1, xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL)

    def add_to_label(self, widget, table, x, x1, y, y1):
        table.attach(widget, x, x1, y, y1, xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL)

    def fill_comoBox(self, combo, list, active = 0):
        for item in list:
            combo.append_text(item)
            combo.set_active(active)

    def get_active_text(self, combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0]

    def render_filter(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("User filter")
        #self.window.set_size_request(325, 240)
        self.window.connect("delete_event", self.delete_event)
        self.window.set_modal(True)
        self.window.set_property("resizable", False)
        
        alig = gtk.Alignment()
        alig.set_padding(10, 0, 10, 10)

        box_main = gtk.VBox()
        alig.add(box_main)
        
        #information for filter
        table = gtk.Table()
       
        self.label_to_table("Name filter:", table,  0, 1, 0, 1)
        self.label_to_table("Search in rule/group:", table,  0, 1, 2, 3)
        self.label_to_table("Search text in:", table,  0, 1, 3, 4)
        self.label_to_table("Serch text:", table,  0, 1, 4, 5)
        self.label_to_table("Selected:", table,  0, 1, 5, 6)
        self.label_to_table("Result structure:", table,  0, 1, 6, 7)
        
        self.name = gtk.Entry()
        self.name.set_text("None")
        self.add_to_label(self.name, table, 1, 2, 0, 1)
        
        self.searchIn = gtk.combo_box_new_text()
        self.fill_comoBox(self.searchIn, ["Role/Group", "Role", "Group"] )
        self.add_to_label(self.searchIn, table, 1, 2, 2, 3)
        
        self.searchColumn = gtk.combo_box_new_text()
        self.fill_comoBox(self.searchColumn, ["Text", "ID"] )
        self.add_to_label(self.searchColumn, table, 1, 2, 3, 4)
        
        self.text = gtk.Entry()
        self.add_to_label(self.text, table, 1, 2, 4, 5)
        
        self.selected = gtk.combo_box_new_text()
        self.fill_comoBox(self.selected, ["False/True", "False", "True"])
        self.add_to_label(self.selected, table, 1, 2, 5, 6)

        self.struct = gtk.combo_box_new_text()
        self.fill_comoBox(self.struct, ["Tree", "List"])
        self.add_to_label(self.struct, table, 1, 2, 6, 7)
        
        box_main.pack_start(table,True,True)
        
        
        #buttons
        box_btn = gtk.HButtonBox()
        box_btn.set_layout(gtk.BUTTONBOX_END)
        btn_filter = gtk.Button("Add filter")
        btn_filter.connect("clicked", self.cb_setFilter)
        box_btn.pack_start(btn_filter)
        btn_filter = gtk.Button("Cancel")
        btn_filter.connect("clicked", self.cb_cancel)
        box_btn.pack_start(btn_filter)
        box_main.pack_start(box_btn, True, True, 20)
        
        self.window.add(alig)
        self.window.show_all()
        return self.window

    def cb_setFilter(self, widget):
        
        filter = {"name":          self.name.get_text(),
                  "description":   "",
                  "func":           self.filter_func,        # func for metch row in model func(model, iter)
                  "param":           {},                    # param tu function
                  "result_tree":    self.get_active_text(self.struct)   # if result shoul be in tree or list
                  }
        params = {"searchIn": self.searchIn.get_active(),
                  "seachrData": self.searchColumn.get_active(),
                  "selected": self.selected.get_active(),
                  "text":      self.text.get_text()}
        filter["param"] = params
        self.add_filter(filter)
        self.window.destroy()

    def filter_func(self, model, iter, params):

        #search in
        ROLE_GROUP = 0
        ROLE = 1
        GROUP = 2

        #search data
        TEXT = 0
        ID = 1

        #selected
        TRUE_FALSE = 0
        FALSE = 1
        TRUE = 2

        #data in model
        COLUMN_ID       = 0
        COLUMN_NAME     = 1
        COLUMN_PICTURE  = 2
        COLUMN_TEXT     = 3
        COLUMN_COLOR    = 4
        COLUMN_SELECTED = 5
        COLUMN_PARENT   = 6
        
        column = [COLUMN_NAME, COLUMN_ID]
        
        vys = True
        
        # if is role or group
        if params["searchIn"] == ROLE_GROUP:
            vys = True
        else:
            pattern = re.compile("role",re.IGNORECASE)
            if pattern.search(model.get_value(iter, COLUMN_TEXT), 0, 4) != None:
                r_g = True 
            else:
                r_g = False

            if params["searchIn"] == ROLE:
                vys = vys and r_g
            if params["searchIn"] == GROUP:
                vys = vys and not r_g
            if not vys:
                return vys
        
        # search text if is set
        if params["text"] <> "":
            pattern = re.compile(params["text"],re.IGNORECASE)
            if pattern.search(model.get_value(iter, column[params["seachrData"]])) != None:
                vys = vys and True 
            else:
                vys = vys and False
            if not vys:
                return vys
        
        # if is selected, not selected or bouth
        if params["selected"] == TRUE_FALSE:
            return vys
        elif params["selected"] == FALSE:
            return vys and (model.get_value(iter, COLUMN_SELECTED) == False)
        elif params["selected"] == TRUE:
            return vys and (model.get_value(iter, COLUMN_SELECTED) == True)
  

    def cb_cancel(self, widget):
        self.window.destroy()

    def delete_event(self, widget, event):
        self.window.destroy()


class ScanFilter(Renderer):

    #data in model
    COLUMN_ID = 0               # id of rule
    COLUMN_RESULT = 1           # Result of scan
    COLUMN_FIX = 2              # fix
    COLUMN_TITLE = 3            # Description of rule
    COLUMN_DESC = 4             # Description of rule
    COLUMN_COLOR_TEXT_TITLE = 5 # Color of text description
    COLUMN_COLOR_BACKG = 6      # Color of cell
    COLUMN_COLOR_TEXT_ID = 7    # Color of text ID
        
    def __init__(self, core, builder):
        self.id_filter = 0
        objectBild = builder.get_object("scan:box_filter")
        Renderer.__init__(self, "gui:btn:menu:scan:filter", core, objectBild)
        self.expander.cb_changed()
#-------------------------------------------------------------------------------        
        filter = {"name":           "Pass",
                  "description":    "Select result pass.",
                  "func":           self.search_result,        # func for metch row in model func(model, iter)
                  "param":           ["Pass"],                    # param tu function
                  "result_tree":    False,               # if result shoul be in tree or list
                  }
                  
        filter1 = {"name":          "ERROR",
                  "description":    "Select result error.",
                  "func":           self.search_result,        # func for metch row in model func(model, iter)
                  "param":           ["error"],                    # param tu function
                  "result_tree":    False,               # if result shoul be in tree or list
                  }

        filter2 = {"name":          "FAIL",
                  "description":    "Select result fail.",
                  "func":           self.search_result,        # func for metch row in model func(model, iter)
                  "param":           ["fail"],                    # param tu function
                  "result_tree":    False,                       # if result shoul be in tree or list
                  }
                  
        self.add_filter_to_menu(filter)
        self.add_filter_to_menu(filter1)
        self.add_filter_to_menu(filter2) 
        self.add_filter_to_menu(None)

    #filter
    def search_result(self, model, iter, params):
        pattern = re.compile(params[0],re.IGNORECASE)
        if pattern.search(model.get_value(iter, ScanFilter.COLUMN_RESULT)) != None:
            return True
        else:
            return False
#-------------------------------------------------------------------------------
    def label_to_table(self, name, table, x, x1, y, y1):
        label = gtk.Label(name)
        label.set_use_markup(True)
        table.attach(label, x, x1, y, y1, xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL)

    def add_to_label(self, widget, table, x, x1, y, y1):
        table.attach(widget, x, x1, y, y1, xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL)

    def fill_comoBox(self, combo, list, active = 0):
        for item in list:
            combo.append_text(item)
            combo.set_active(active)
            
    def render_filter(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("User filter")
        #self.window.set_size_request(325, 240)
        self.window.connect("delete_event", self.delete_event)
        self.window.set_modal(True)
        self.window.set_property("resizable", False)
        
        alig = gtk.Alignment()
        alig.set_padding(10, 0, 10, 10)

        box_main = gtk.VBox()
        alig.add(box_main)

        #information for filter
        table = gtk.Table()
       
        self.label_to_table("Name filter:", table,  0, 1, 0, 1)
        self.label_to_table("Search text in:", table,  0, 1, 1, 2)
        self.label_to_table("Serch text:", table,  0, 1, 2, 3)

        box = gtk.VBox()
        label = gtk.Label("Result:")
        box.pack_start(label, True, True)
        but = gtk.Button("changed")
        but.connect("clicked", self.cb_changed)
        box.pack_start(but, True, False)
        self.add_to_label(box, table, 0, 1, 3, 12)
        
        self.name = gtk.Entry()
        self.name.set_text("None")
        self.add_to_label(self.name, table, 1, 2, 0, 1)
        
        self.searchColumn = gtk.combo_box_new_text()
        self.fill_comoBox(self.searchColumn, ["Title", "ID", "Decription"] )
        self.add_to_label(self.searchColumn, table, 1, 2, 1, 2)
        
        self.text = gtk.Entry()
        self.add_to_label(self.text, table, 1, 2, 2, 3)

        self.res_pass = gtk.CheckButton("PASS")
        self.res_pass.set_active(True)
        self.add_to_label(self.res_pass, table, 1, 2, 3, 4)
        
        self.res_error = gtk.CheckButton("ERROR")
        self.res_error.set_active(True)
        self.add_to_label(self.res_error, table, 1, 2, 4, 5)
        
        self.res_fail = gtk.CheckButton("FAIL")
        self.res_fail.set_active(True)
        self.add_to_label(self.res_fail, table, 1, 2, 5, 6)
        
        self.res_unknown = gtk.CheckButton("UNKNOWN")
        self.res_unknown.set_active(True)
        self.add_to_label(self.res_unknown, table, 1, 2, 6, 7)

        self.res_not_app = gtk.CheckButton("NOT APPLICABLE")
        self.res_not_app.set_active(True)
        self.add_to_label(self.res_not_app, table, 1, 2, 7, 8)
        
        self.res_not_check = gtk.CheckButton("NOT CHECKED")
        self.res_not_check.set_active(True)
        self.add_to_label(self.res_not_check, table, 1, 2, 8, 9)
        
        self.res_not_select = gtk.CheckButton("NOT SELECTED")
        self.res_not_select.set_active(True)
        self.add_to_label(self.res_not_select, table, 1, 2, 9, 10)
        
        self.res_info = gtk.CheckButton("INFORMATIONAL")
        self.res_info.set_active(True)
        self.add_to_label(self.res_info, table, 1, 2, 10, 11)
        
        self.res_fix = gtk.CheckButton("FIXED")
        self.res_fix.set_active(True)
        self.add_to_label(self.res_fix, table, 1, 2, 11, 12)
        
        
        box_main.pack_start(table,True,True)
        #buttons
        box_btn = gtk.HButtonBox()
        box_btn.set_layout(gtk.BUTTONBOX_END)
        btn_filter = gtk.Button("Add filter")
        btn_filter.connect("clicked", self.cb_setFilter)
        box_btn.pack_start(btn_filter)
        btn_filter = gtk.Button("Cancel")
        btn_filter.connect("clicked", self.cb_cancel)
        box_btn.pack_start(btn_filter)
        box_main.pack_start(box_btn, True, True, 20)
        
        self.window.add(alig)
        self.window.show_all()
        return self.window

    def cb_changed(self, widget):
        
        self.res_pass.set_active(not self.res_pass.get_active())
        self.res_error.set_active(not self.res_error.get_active())
        self.res_fail.set_active(not self.res_fail.get_active())
        self.res_unknown.set_active(not self.res_unknown.get_active())
        self.res_not_app.set_active(not self.res_not_app.get_active())
        self.res_not_check.set_active(not self.res_not_check.get_active())
        self.res_not_select.set_active(not self.res_not_select.get_active())
        self.res_info.set_active(not self.res_info.get_active())
        self.res_fix.set_active(not self.res_fix.get_active())
        
    def cb_setFilter(self, widget):
        
        filter = {"name":          self.name.get_text(),
                  "description":   "",
                  "func":           self.filter_func,        # func for metch row in model func(model, iter)
                  "param":           {},                    # param tu function
                  "result_tree":    False   # if result shoul be in tree or list
                  }
        
        res = []
        if not self.res_pass.get_active():
            res.append("PASS")
        if not self.res_error.get_active():
            res.append("ERROR")
        if not self.res_fail.get_active():
            res.append("FAIL")
        if not self.res_unknown.get_active():
            res.append("UNKNOWN")
        if not self.res_not_app.get_active():
            res.append("NOT APPLICABLE")
        if not self.res_not_check.get_active():
            res.append("NOT CHECKED")
        if not self.res_not_select.get_active():
            res.append("NOT SELECTED")
        if not self.res_info.get_active():
            res.append("INFORMATIONAL")
        if not self.res_fix.get_active():
            res.append("FIXED")

        params = {"seachrData": self.searchColumn.get_active(),
                  "text":       self.text.get_text(),
                  "res":        res}

        filter["param"] = params
        self.add_filter(filter)
        self.window.destroy()



    def filter_func(self, model, iter, params):

        #search data
        TITLE = 0
        ID = 1
        DESC = 3

        #data in model
        COLUMN_ID = 0               # id of rule
        COLUMN_RESULT = 1           # Result of scan
        COLUMN_FIX = 2              # fix
        COLUMN_TITLE = 3            # Description of rule
        COLUMN_DESC = 4             # Description of rule
        COLUMN_COLOR_TEXT_TITLE = 5 # Color of text description
        COLUMN_COLOR_BACKG = 6      # Color of cell
        COLUMN_COLOR_TEXT_ID = 7    # Color of text ID
        
        column = [COLUMN_TITLE, COLUMN_ID, COLUMN_DESC]
        
        vys = True
        # search text if is set
        if params["text"] <> "":
            pattern = re.compile(params["text"],re.IGNORECASE)
            if pattern.search(model.get_value(iter, column[params["seachrData"]])) != None:
                vys = vys and True 
            else:
                vys = vys and False
            if not vys:
                return vys
        
        #type of result
        if len(params["res"]) > 0:
            if model.get_value(iter, COLUMN_RESULT) in params["res"]:
                vys = vys and False
        return vys
  
    def cb_cancel(self, widget):
        self.window.destroy()
        
    def delete_event(self, widget, event):
        self.window.destroy()