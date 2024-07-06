from PyQt6.QtCore import *
from PyQt6.QtGui import *
import sqlite3 as sql
from PyQt6.QtWidgets import *


class Explorer(QTreeWidget):
    def __init__(self, db_name, table_name):
        super().__init__()


        self.db_name = db_name
        self.table_name = table_name
        self.item = None

        self.setGeometry(700, 300, 800, 600)
        self.setColumnCount(1)
        self.setHeaderLabels(['Name'])
        self.insertTopLevelItem(0, self.con_tree())
        self.expandToDepth(0)

        self.itemChanged.connect(self.update_db)


        self.add_Action = QAction()
        self.add_Action.setText('Add foler')
        self.add_Action.triggered.connect(self.add_item)
        self.del_Action = QAction()
        self.del_Action.setText('Delete folder')
        self.del_Action.triggered.connect(self.del_item)
        self.ren_Action = QAction()
        self.ren_Action.setText('Rename folder')
        self.ren_Action.triggered.connect(self.ren_item)
        self.col_Action = QAction()
        self.col_Action.setText('Collapse')
        self.col_Action.triggered.connect(self.col_item)
        self.exp_Action = QAction()
        self.exp_Action.setText('Expand')
        self.exp_Action.triggered.connect(self.exp_item)
    
    def mouseDoubleClickEvent(self, e):
        e.accept()
        p = e.pos()
        if self.selectedItems() != [] and e.button() == Qt.MouseButton.LeftButton and self.selectedItems()[0].text(0) != 'root' and self.selectedItems()[0] == self.itemAt(p):
            self.selectedItems()[0].setExpanded(not self.selectedItems()[0].isExpanded())

    
    def mousePressEvent(self, e):
        p = e.pos()
        try:
            self.item = self.itemAt(p)
        except:
            pass

        print(self.item)
        return super().mousePressEvent(e)
    

    def con_tree(self):
        root = QTreeWidgetItem(['root', str(0), None])
        root = self.con_child(0, root)
        
        return root
    
    #Убрать из рекурсивной функции SELECT FROM
    def con_child(self, prnt, item):
        db = sql.connect(self.db_name)
        cur = db.cursor()
        cur.execute(f"SELECT * FROM {self.table_name} WHERE parent_id = ?", (prnt, ))
        els = cur.fetchall()
        for id, prnt_id, name in els:
            child = QTreeWidgetItem([name, str(id), str(prnt_id)])
            child.setFlags(child.flags() | Qt.ItemFlag.ItemIsEditable)
            child = self.con_child(id, child)
            item.addChild(child)
        cur.close()
        db.close()
        return item
    
    def add_item(self):
        db = sql.connect(self.db_name)
        cur = db.cursor()
        
        if  self.item is None: #self.selectedItems() == [] or self.item != self.selectedItems()[0] and not f:
            self.item = self.topLevelItem(0)

        folder = "New folder"
        folder_id = int(self.item.text(1))
        self.item.setExpanded(True)
        cur.execute(f'''INSERT INTO {self.table_name}(parent_id, name) VALUES(?, ?)''', [folder_id, folder])
        db.commit()
        cur.execute('''SELECT seq FROM sqlite_sequence WHERE  name = ? ''', [self.table_name])
        newid = cur.fetchone()[0]
        child = QTreeWidgetItem([folder, str(newid), str(folder_id)])
        child.setFlags(child.flags() | Qt.ItemFlag.ItemIsEditable)
        self.item.addChild(child)
        self.setCurrentItem(child)
        self.ren_item()
        cur.close()
        db.close()
    
    def del_item_rec(self, index):  #!!!!переделать
        db = sql.connect(self.db_name)
        cur = db.cursor()
        cur.execute(f'''SELECT id FROM {self.table_name} WHERE parent_id = ?''', [index])
        a = cur.fetchall()
        
        if a == []:
            self.ids.append(index)    
            return
        
        for id1 in a:
            self.del_item_rec(id1[0])
            self.ids.append(id1[0])
    
    def del_item(self):
        try:
            db = sql.connect(self.db_name)
            cur = db.cursor()
            el = self.selectedItems()[0]
            
        
            el.setSelected(False)
            del_id = int(el.text(1))
            self.ids = []
            self.del_item_rec(del_id)
            self.ids.append(del_id)
            self.ids = tuple(self.ids)   
            cur.execute(f"DELETE FROM {self.table_name} WHERE id IN {self.ids}")
            db.commit()

            el.parent().removeChild(el)
        except:
            pass
    
    def update_db(self):
        db = sql.connect(self.db_name)
        cur = db.cursor()
        cur.execute(f'''UPDATE {self.table_name} SET name = ? WHERE id = ?''', [self.selectedItems()[0].text(0), self.selectedItems()[0].text(1)])
        db.commit()
        cur.close()
        db.close()


    def ren_item(self):
        if self.selectedItems() != []:
            self.editItem(self.selectedItems()[0], 0)

        
    
    def contextMenuEvent(self, event):
        if self.selectedItems() == [] or self.selectedItems()[0].text(0) == 'root' or self.item != self.selectedItems()[0]:
            menu = QMenu()
            menu.addAction(self.add_Action)
            menu.addAction(self.col_Action)
            menu.addAction(self.exp_Action)
        else:
            menu = QMenu()
            menu.addAction(self.add_Action)
            menu.addAction(self.del_Action)
            menu.addAction(self.ren_Action)
            menu.addAction(self.col_Action)
            menu.addAction(self.exp_Action)

        menu.exec(event.globalPos())
    
        
    
    def col_item(self, f = False):
        self.childs = []
        if  self.selectedItems() == [] or self.item != self.selectedItems()[0] and not f:
            el = self.topLevelItem(0)
        else:
            el = self.selectedItems()[0]
        self.get_childs(el)
        for elem in self.childs:
            elem.setExpanded(False)
        if el.text(0) == 'root':
            el.setExpanded(True)
    
    def  exp_item(self, f = False):
        if  self.selectedItems() == [] or self.item != self.selectedItems()[0] and not f:
            el = self.topLevelItem(0)
        else:
            el = self.selectedItems()[0]
        self.childs = []
        self.get_childs(el)
        for elem in self.childs:
            elem.setExpanded(True)
        
    
    def get_childs(self, item):
        childs = item.childCount()
        for i in range(childs):
            self.get_childs(item.child(i))
        self.childs.append(item)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Insert:
            self.add_item()
        elif event.key() == Qt.Key.Key_Delete:
            self.del_item()
        elif event.key() == Qt.Key.Key_F4:
            self.exp_item(True)
        elif event.key() == Qt.Key.Key_F5:
            self.col_item(True)