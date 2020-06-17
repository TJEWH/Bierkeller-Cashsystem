'''
  Titel:    Bierkeller-KassenApp
   Autor:    Tim Jacob Edelmann

   Version:    1.0.0
'''

import kivy

import Excel_Handler
from Excel_Handler import Pyxl
from Excel_Handler import Global

from collections import defaultdict
from kivy.clock import Clock
from kivy.app import App
from kivy.core.window import Window, WindowBase
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, NumericProperty, DictProperty, ListProperty

from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.button import Button
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label


def create_sub_lists():
    lst = ['bier', 'nalk', 'wein', 'other']
    lst_size = Excel_Handler.get_list_size(Pyxl.ws)
    lstp2 = []
    i = 0
    x = 2
    while x < lst_size:
        lst_buff = []
        while Pyxl.ws.cell(row=x, column=2).value == lst[i]:
            lst_buff.append(Pyxl.ws.cell(row=x, column=1).value)
            x += 1
        i += 1
        lstp2.append(lst_buff)
    return lstp2


def get_open_accounts():
    lst = []
    lst_size = Excel_Handler.get_list_size(Pyxl.log)

    for i in range(2, lst_size):
        if Pyxl.log.cell(row=i, column=3).value is not None and Pyxl.log.cell(row=i, column=3).value != 'BEZAHLT':
            lst.append((Pyxl.log.cell(row=i, column=3).value, Pyxl.log.cell(row=i, column=2).value))
    d = defaultdict(float)
    for x, y in lst:
        d[x] += float(y)
    # In lst_merged sind die Gesamtschulden, die mit einer Person verbunden sind festgehalten
    lst_merged = [(x, round(y, 2)) for x, y in d.items()]
    return lst_merged


def missing_param():
    Popup(title='ERROR', title_size=20, title_align='center',
          content=Label(text='Es fehlen Parameter!', font_size=20, halign='center'), size_hint=(.3, .2)).open()


def wrong_input():
    Popup(title='ERROR', title_size=20, title_align='center',
          content=Label(text='Der Input ist fehlerhaft!\nDer Name muss aus drei Buchstaben bestehen\nund die Zimmernummer im EWH vorhanden sein',
                        font_size=16, halign='center'), size_hint=(.4, .25)).open()

def open_popup(popup):
    this_popup = popup
    this_popup.open()


# Edit Button Class
class TypeInPopup(Popup):
    def set_value(self, value):
        temp = Global.total
        string = str(value).replace(',', '.')
        Global.total = float(string)
        Global.text += '\n-> von ' + str("%.2f" % temp) + '€ zu ' + str(
            "%.2f" % float(string)) + '€ geändert\n'


# Buy on commission account
class CommissionPopup(Popup):
    def get_contact(self, name, room):
        room_buff = 1
        if room[:2] == "00":
            room_buff = room[-1:]
        elif room[:1] == "0":
            room_buff = room[-2:]
        if len(name) < 3 or room == '' or int(room_buff) <= 0 or int(room[:1]) > 8 or int(room[1:]) > 23:
            open_popup(CommissionPopup())
            wrong_input()
        Global.debtor_id = str(str(name)[:3].lower() + room)


class ScrollableLabel(ScrollView):
    text = StringProperty('')


class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior, RecycleGridLayout):
    selected_row = NumericProperty(0)

    def get_nodes(self):
        nodes = self.get_selectable_nodes()
        if self.nodes_order_reversed:
            nodes = nodes[::-1]
        if not nodes:
            return None, None

        selected = self.selected_nodes
        if not selected:
            self.select_node(nodes[0])
            self.selected_row = 0
            return None, None

        if len(nodes) == 1:
            return None, None

        last = nodes.index(selected[-1])
        self.clear_selection()
        return last, nodes

    def select_current(self):
        last, nodes = self.get_nodes()
        if not nodes:
            return
        self.select_node(nodes[self.selected_row])


class SelectableButton(RecycleDataViewBehavior, Button):
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super(SelectableButton, self).refresh_view_attrs(rv, index, data)

    def apply_selection(self, rv, index, is_selected):
        self.selected = is_selected


class ListOpenAccounts(Popup):
    data_items = ListProperty([])
    row_data = DictProperty({})
    col1_data = ListProperty([])
    col2_data = ListProperty([])
    col1_row_controller = ObjectProperty(None)
    col2_row_controller = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ListOpenAccounts, self).__init__(**kwargs)
        self.init_items()
        Clock.schedule_once(self.set_default_first_row, .0005)

    def on_mouse_select(self, instance):
        if (self.col1_row_controller.selected_row != instance.index
                or self.col2_row_controller.selected_row != instance.index):
            self.col1_row_controller.selected_row = instance.index
            self.col2_row_controller.selected_row = instance.index
            self.col1_row_controller.select_current()
            self.col2_row_controller.select_current()
        self.row_data = self.col1_data[instance.index]

        Global.debtor_id = self.col1_data[instance.index]['text']
        Global.debts = float(self.col2_data[instance.index]['Id'])

    def set_default_first_row(self, dt):
        self.col1_row_controller.select_node(0)
        self.col2_row_controller.select_node(0)
        Global.debtor_id = self.col1_data[0]['text']
        Global.debts = float(self.col2_data[0]['Id'])

    def update(self):
        self.col1_data = [{'text': str(x[1]), 'Id': str(x[2]), 'Name': x[0], 'selectable': True}
                          for x in self.data_items]

        self.col2_data = [{'text': str("%.2f" % x[2] + '€').replace(".", ","), 'Id': x[2], 'Name': x[0], 'selectable': True}
                          for x in self.data_items]

    def init_items(self):
        rows = get_open_accounts()

        i = 0
        for row in rows:
            self.data_items.append([i, row[0], row[1]])
            i += 1
        self.update()


# Main Class
class RegisterGUI(GridLayout):
    Window.size = (1000, 666)
    Pyxl.get_product_nr(Pyxl)
    Global.product_idx = Global.products
    lst_op_acc = ObjectProperty(None)

    def __init__(self, ** kwargs):
        super(RegisterGUI, self).__init__(**kwargs)

        self.set_spinner_values()

### Calculation methods
    def add_single(self, number, type):
        if number == '-- Anzahl auswählen --' or type == '-- Artikel auswählen --':
            return missing_param()
        else:
            prod = Global.product_idx[1][type]
            temp = int(number) * (Pyxl.active_excel.cell(row=prod, column=3).value +
                                  Pyxl.active_excel.cell(row=prod, column=5).value)
            Global.total += temp
            Global.le_total = temp
            if Pyxl.active_excel.cell(row=prod, column=2).value == 'other':
                string = Pyxl.format_text(Pyxl, number, type, 2, '+')

                Global.text += string
                Global.le_text = string
            else:
                string = Pyxl.format_text(Pyxl, number, type, 0, '+')
                Global.text += string
                Global.le_text = string
            # print(Global.total)

    def add_crates(self, number, type):
        if number == '-- Anzahl auswählen --' or type == '-- Artikel auswählen --':
            return missing_param()
        else:
            prod = Global.product_idx[1][type]
            temp = int(number) * (Pyxl.active_excel.cell(row=prod, column=4).value +
                                  Pyxl.active_excel.cell(row=prod, column=6).value)
            string = Pyxl.format_text(Pyxl, number, type, 1, '+')

            Global.total += temp
            Global.le_total = temp

            Global.text += string
            Global.le_text = string
            # print(Global.total)

    def sub_sg_deposit(self, number, type):
        if number == '-- Anzahl auswählen --' or type == '-- Artikel auswählen --':
            return missing_param()
        else:
            prod = Global.product_idx[1][type]
            temp = int(number) * Pyxl.active_excel.cell(row=prod, column=5).value
            string = Pyxl.format_text(Pyxl, number, type, 0, '–')

            Global.total -= temp
            Global.le_total = temp

            Global.text += string
            Global.le_text = string
            # print(Global.total)

    def sub_cr_deposit(self, number, type):
        if number == '-- Anzahl auswählen --' or type == '-- Artikel auswählen --':
            return missing_param()
        else:
            prod = Global.product_idx[1][type]
            temp = int(number) * Pyxl.active_excel.cell(row=prod, column=6).value
            string = Pyxl.format_text(Pyxl, number, type, 1, '–')

            Global.total -= temp
            Global.le_total = temp

            Global.text += string
            Global.le_text = string
            # print(Global.total)

    #TODO Alternative zu Edit-Button, Rückgängig machen
    def remove_last_entry(self, button):
        Global.total -= Global.le_total
        Global.text = Global.text[-len(Global.le_text):]
        button.disabled = True

    ### Spinner methods
    def set_spinner_values(self):
        values = create_sub_lists()
        spinners = ['bier_spinner', 'nalk_spinner', 'wein_spinner', 'other_spinner']
        for x in range(0, 4):
            for y in range(1, 5):
                if x is 3 and y is 2:
                    return
                self.ids[spinners[x] + str(y)].values = values[x]

    def reset_all_spinners(self):
        nbr_lst = ['nbr_spinner1','nbr_spinner2','nbr_spinner3','nbr_spinner4','nbr_spinner5','nbr_spinner6','nbr_spinner7',
               'nbr_spinner8','nbr_spinner9','nbr_spinner10','nbr_spinner11','nbr_spinner12','nbr_spinner13']
        type_lst = ['bier_spinner1', 'bier_spinner2', 'bier_spinner3', 'bier_spinner4', 'nalk_spinner1', 'nalk_spinner2',
                    'nalk_spinner3', 'nalk_spinner4', 'wein_spinner1', 'wein_spinner2', 'wein_spinner3', 'wein_spinner4',
                    'other_spinner1']
        for i in nbr_lst:
            spinner_buff = self.ids[i]
            spinner_buff.text = '-- Anzahl auswählen --'
            spinner_buff.color = [0, 0, 0, 0.5]
        for j in type_lst:
            spinner_buff = self.ids[j]
            spinner_buff.text = '-- Artikel auswählen --'
            spinner_buff.color = [0, 0, 0, 0.5]

    '''TODO
    def spinner_status(self, spinner1, spinner2, button):
        if spinner1.text[:1] != "-" and spinner2.text[:1] != "-":
            button.disabled = False'''


    def reset_spinner(self, spinner1, spinner2):
        spinner1.text = '-- Anzahl auswählen --'
        spinner1.color = [0, 0, 0, 0.5]
        spinner2.text = '-- Artikel auswählen --'
        spinner2.color = [0, 0, 0, 0.5]

    def set_spinner_color_on_open(self, spinner):
        if spinner.text[:1] == "-" and spinner.is_open is False:
            spinner.color = [0, 0, 0, 0.5]
        elif spinner.text[:1] == "-" and spinner.is_open is True:
            spinner.color = [0, 0, 0, 0.5]
        elif spinner.text[:1] != "-":
            spinner.color = [1, 1, 1, 1]

    def set_spinner_color(self, spinner):
        if spinner.text[:1] == "-" and spinner.is_open is True:
            spinner.color = [0, 0, 0, 0.5]
        elif spinner.text[:1] != "-":
            spinner.color = [1, 1, 1, 1]

    def remove_lst_element(self, spinner, string):
        lst = self.ids[spinner]
        for a in lst.values:
            if a == string:
                return lst.values.remove(string)


### Right Panel

    ### Open Accounts Button
    def pay_debt(self):
        name = Global.debtor_id
        debts = Global.debts
        if name == '':
            return
        Global.total += debts
        Global.text += '+  Schulden von ' + name + '\n'
        Global.debt_payed = True
        self.ids['commission_btn'].disabled = True

    def display_open_accounts(self):
        self.lst_op_acc = ListOpenAccounts()
        open_popup(self.lst_op_acc)

    def update_open_accounts(self):
        get_open_accounts()
        self.lst_op_acc = ListOpenAccounts()

    def get_on_mouse(self, instance):
        self.lst_op_acc.on_mouse_select(instance)

    ### CheckBox methods
    def check_on_commission(self, instance, value):
        if value is True:
            open_popup(CommissionPopup())
            Global.commission = value

    def switch_to_employee(self, instance, value):
        self.cancel()
        if value is True:
            Global.product_idx = Global.emp_products
            Pyxl.active_excel = Pyxl.emp
        else:
            Global.product_idx = Global.products
            Pyxl.active_excel = Pyxl.ws
        return value

    def reset_checkboxes(self):
        cb1 = self.ids['checkbox_value1']
        cb2 = self.ids['checkbox_value2']
        cb1.active = False
        cb2.active = False

    def reset_single_checkbox(self, scb):
        cb = self.ids[scb]
        cb.active = False

    ### Cart methods
    def console_output(self):
        label = self.ids['console_op']
        label.text = str(Global.text)
        label.color = [1, 1, 1, 1]
        label.valign = 'top'
        label.halign = "left"

    def reset_output(self):
        label = self.ids['console_op']
        label.text = 'Warenkorb leer'
        label.color = [0, 0, 0, 0.35]
        label.valign = 'middle'
        label.halign = "center"

    ### Sum methods
    def update_sum(self):
        label = self.ids['total']
        label.text = str("%.2f" % Global.total + '€').replace(".", ",")

### Lower Buttons Panel
    def dismiss(self):
        reg_app.stop()

    def cancel(self):
        self.ids['commission_btn'].disabled = False
        Global.total = 0
        Global.text = ''
        Global.commission = False
        Global.debtor_id = ""
        Global.debt_payed = False
        Global.debts = 0
        # print('Vorgang abgebrochen')

    def edit(self):
        open_popup(TypeInPopup())

    def finish(self):
        print(Global.total)
        Pyxl.logEntry(Pyxl, Global.total)
        Pyxl.log_payed_account(Pyxl, Global.debtor_id, Global.debts)
        self.ids['commission_btn'].disabled = False
        Global.total = 0
        Global.text = ''
        Global.commission = False
        Global.debt_payed = False
        Global.debtor_id = ""
        Global.debts = 0


class RegisterApp(App):
    def build(self):
        Window.clearcolor = (0.25, 0.25, 0.25, 1)
        WindowBase.fullscreen = 'auto'
        return RegisterGUI()


reg_app = RegisterApp()
reg_app.run()


#TODO Design
    #Priorität 1
#Das Warenkorb Label soll Scrollable sein, falls größer als Maximum -> Siehe ScollableLabel im kv
    #Priorität 2
#Die Anzahl an Artikeln sowohl über Dropdown als auch Texteingabe ermöglichen -> if spinner_open & keyboard_event
#Hinzufügen Btn default disabled=True, wenn Artikel und anzahl ausgewält wird er False gesetzt
#Scroll wheel distance auf dp(10) dür SpinnerOption
#Offene Rechnungen Popup, bei button: background down, kein blau, schrift größer


#TODO Funktionalität
    #Priorität 1
#Kommissionskäufe nicht genutze Kästen von Summe entfernen -> bei Kommissionskauf wird der Umsatz verbucht und bei Schuldenbegleichung, verfälscht gesamtumsatz
#Letzte Eingabe Rückgängig -> Eingabe und Summe in Eingabe speichern, bei Aufruf eingabe[-len(last_entry):], sum - last_sum
    #Priorität 2
#AutoFocus bei Texteingabe für Popups hinzufügen, mit Tab Input wechseln und mit Enter bestätigen
#Auf Wunsch digitale Rechnung an Email senden -> Würde von zugang zu Internet abhängen
#Einkäufe zu Mitarbeiterpreis in Extraspalte verbuchen
#Bei Texteingaben mit Komma


#TODO Codeoptimierung
    #Priorität 1
#Propertys statt Global-Class Konstanten nutzen
    #Priorität 2
#Printtext für alle Bestellungen, aber kurzschreibweise nutzen -> 4x Augustiner-Flaschen = 3,66€ wird zu 4xagtrF=3,66€
#im kv im TabelPanel die Label anordnung vereinfachen (keine leeren Label)
#Validieren, dass eingegebene Zahlen auch zahlen sind
#Überlegen welche Daten zu Sitzungsbeginn statisch erstellt werden sollten (Preislisten) und welche sich ändern (Auf Rechnung Liste)


#TODO Später
#Code nach fertigstellung ausführlich dokumentieren
#ExcelSheet mit Mitarbeiterpreisen richtige Preise
#Weine hinzufügen
#Anwendung fertigstellen -> pyinstaller
#GGf für verschiedene Endgeräte bereitstellen und die Excel wird über Bierkeller nextcloud synchronisiert
#Weiteres ExcelSheet, wo Anzahl der umgesetzen Artikel registriert wird für Statistiken
#Weiteres ExcelSheet mit preisen für Externe
#Wenn in der Log Datei gewisse Länge erreicht ist Daten in Archiv.xlsx schreiben, die noch zu erstellen ist
#Langfristig kann man überlegen eine Datenbank statt der Excel anzulegen