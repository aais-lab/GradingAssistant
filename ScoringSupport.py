# MARK: import
import tkinter
from tkinter import filedialog, messagebox
import datetime
import configparser
import re
from pathlib import Path

# MARK: Setting Class
class Settings:
    def __init__(self) -> None:
        
        self._shape = {
                        "General":[
                                {"name":"UI_MARGIN_BOTTOM", "required":True },
                                {"name":"CLASS_NAME", "required":True },
                                {"name":"GENERATE_LOGFILE", "required":True},
                                {"name":"DEFAULT_SELECT_ROOT_PATH", "required":True}
                            ],
                       "Class":[
                                {"name":"RUN_COMMAND", "required":True},
                                {"name":"SELECT_ROOT_PATH", "required":False},
                                {"name":"CHILD_TYPE", "required":True},
                                {"name":"FILENAME_REGEX", "required":False},
                                {"name":"FILE_TYPE", "required":False}
                            ]
                        }
        
        self._settings = configparser.ConfigParser()
        self._settings.read('config.ini', encoding='utf-8') 
        self.SOURCE_PATH = Path(__file__).parent
        self.HOME_PATH = Path.home()
        if not self._check():
            exit()
        
    def get(self, section: str, key: str) -> str | int | None:
        if self.isSettingExists(section, key):
            return self._settings[section][key]
        else:
            return None
        
    def isSettingExists(self, section: str, key: str) -> bool:
        if key.lower() in map(lambda x:x[0], self._settings.items(section)):
            return True
        else:
            return False
    
    def get_sectionList(self) -> list:
        return self._settings.sections()
    
    def get_keyList(self, section: str) -> dict:
        return self._settings.items(section.upper())
    
    def _check(self):
        # general settings check
        general_keylist = [i[0] for i in self.get_keyList("GENERAL")]
        for settings in self._shape["General"]:
            if settings["required"] :
                if not settings["name"].lower() in general_keylist:
                    tkinter.Tk().withdraw()
                    messagebox.showinfo("ERROR","GENERALに必須属性{}が設定されていません".format(settings["name"]))
                    return False
        
        # class settings check
        for className in eval(self.get("GENERAL", "CLASS_NAME")):
            class_keylist = [i[0] for i in self.get_keyList(className)]
            for settings in self._shape["Class"]:
                if settings["required"] :
                    if not settings["name"].lower() in class_keylist:
                        tkinter.Tk().withdraw()
                        messagebox.showinfo("ERROR","{}に必須属性{}が設定されていません".format(className,settings["name"]))
                        return False
        return True

# MARK: Window Class
class Window:
    def __init__(self, title: str, width: int = 300, height: int = 300,) -> None:
        self.root = tkinter.Tk()
        self.root.title(title)
        margin_buttom = int(GLOBAL_SETTINGS.get("GENERAL", "UI_MARGIN_BOTTOM"))
        self.root.geometry(f"{width}x{height}+{self.root.winfo_screenwidth() - width}+{self.root.winfo_screenheight() - (height + margin_buttom)}")
        self.root.configure(background="white")
        
    def Show(self) -> None :
        self.root.mainloop()
        
    def write_Log(self, target: str, text: str) -> None:
        with open(target, "a") as f:
            f.write(text + "\n")
            
    def generate_RuntimeLogtext(self, action: list) -> str:
        log = [str(datetime.datetime.now().replace(microsecond=0))+"\t"] + action
        return "\t".join(log)
    
    def open_selectFileDialog(self, root: Path) -> Path | None:
        path = Path(filedialog.askopenfilename(initialdir=root))
        if not len(str(path)):
            path = None
        return path
    
    def open_selectDirDialog(self, root: Path) -> Path | None:
        path = Path(filedialog.askdirectory(initialdir=root))
        if not len(str(path)):
            path = None
        return path
    
    def open_msgDialog(self, title: str, text: str) -> None:
        tkinter.Tk().withdraw()
        messagebox.showinfo(title, text)
        
    def Close(self) -> None:
        self.root.destroy()
        self.root.quit()

# MARK: ClassSelect Class
class ClassSelect(Window):
    def __init__(self) -> None:
        super().__init__("科目選択", height=240)
        self.select_ClassName = ""
        
        for target in eval(GLOBAL_SETTINGS.get("GENERAL", "CLASS_NAME")):
            button = tkinter.Button(self.root, text=target, font=('MSゴシック', '20'), padx=2, pady=2, relief=tkinter.RAISED, width=18, height=2, background='white')
            button.bind("<ButtonPress>", self._set_className)
            button.pack(padx=5, pady=5)
    
    def _set_className(self, event):
        self.select_ClassName = event.widget.cget("text")
        self.Close()

# MARK: CheckSetting Class
class CheckSetting(Window):
    def __init__(self, ClassName) -> None:
        super().__init__(ClassName+" 採点設定", height=400)
        
        self.target_ClassName = ClassName
        self.autoinput_path = ""
        self.checkfolder_path = ""
        self.logdir_path = ""
        self.logfiles = {}
        
        self.checkfolder_label = tkinter.StringVar()
        self.checkfolder_label.set("採点対象")
        self.autoinput_label = tkinter.StringVar()
        self.autoinput_label.set("自動入力対象")
        
        selector_frame = tkinter.Frame(self.root, relief=tkinter.FLAT, background='white')
        selector_frame.pack(fill=tkinter.BOTH, pady=10, padx=10)
        tkinter.Label(selector_frame, text='採点rootフォルダを選択', font=('MSゴシック', '15', 'bold'), anchor=tkinter.NW, background='white').pack()
        self.check_folder_button = tkinter.Button(selector_frame, textvariable=self.checkfolder_label, font=('MSゴシック', '20'), padx=2, pady=2, relief=tkinter.RAISED, width=19, height=2, background='white', command=self._set_folderpath("check"))
        self.check_folder_button.pack(anchor=tkinter.W, pady=5)
        tkinter.Label(selector_frame, text='自動入力フォルダを選択', font=('MSゴシック', '15', 'bold'), anchor=tkinter.NW, background='white').pack()
        self.check_folder_button = tkinter.Button(selector_frame, textvariable=self.autoinput_label, font=('MSゴシック', '20'), padx=2, pady=2, relief=tkinter.RAISED, width=19, height=2, background='white', command=self._set_folderpath("autoinput"))
        self.check_folder_button.pack(anchor=tkinter.W, pady=5)
        
        runner_frame = tkinter.Frame(self.root, relief=tkinter.FLAT, background='white')
        runner_frame.pack(fill=tkinter.BOTH, pady=10, padx=10)
        tkinter.Label(runner_frame, text="採点", font=('MSゴシック', '15', 'bold'), anchor=tkinter.NW, background='white').pack()
        tkinter.Button(runner_frame, text='開始', font=('MSゴシック', '20'), padx=2, pady=2, relief=tkinter.RAISED, width=19, height=2, background='white', command=self._start_Check).pack(anchor=tkinter.W, pady=5)
        tkinter.Button(runner_frame, text='終了', font=('MSゴシック', '20'), padx=2, pady=2, relief=tkinter.RAISED, width=19, height=2, background='white', command=self.Close).pack(anchor=tkinter.W, pady=5)  
        
        self.Show()
    
    def _set_folderpath(self, target: str) -> None:
        def inner():
            # filedialog
            if  GLOBAL_SETTINGS.isSettingExists(self.target_ClassName, "SELECTROOT_PATH"):
                folderpath = self.open_selectDirDialog(GLOBAL_SETTINGS.get(self.target_ClassName, "SELECTROOT_PATH"))
            elif GLOBAL_SETTINGS.isSettingExists("GENERAL", "DEFAULT_SELECT_ROOT_PATH"):
                folderpath = self.open_selectDirDialog(GLOBAL_SETTINGS.get("GENERAL", "DEFAULT_SELECT_ROOT_PATH"))
            else :
                self.open_msgDialog("ERROR","デフォルトパスが設定されていないためホームディレクトリを開きます")
                folderpath = self.open_selectDirDialog(GLOBAL_SETTINGS.HOME_PATH)
            
            # error hundring
            if str(folderpath) == ".":
                print("pathは指定されませんでした")
                return None
            
            # set target path
            if target == "autoinput":
                self.autoinput_path = folderpath
                self.autoinput_label.set(folderpath.name)
            else:
                self.checkfolder_path = folderpath
                self.checkfolder_label.set(folderpath.name)
        return inner

    def _setting_Logfiles(self,) -> None:
        self.logdir_path = GLOBAL_SETTINGS.SOURCE_PATH.joinpath("log", self.checkfolder_label.get())
        if self.logdir_path.exists():
            for file in self.logdir_path.iterdir():
                self.logfiles[file.stem] = file
            self.write_Log(self.logfiles["Runtime"], self.generate_RuntimeLogtext(["Start", str(self.checkfolder_path)]))
            return
        
        self.logdir_path.mkdir()
        for file in eval(GLOBAL_SETTINGS.get("GENERAL", "GENERATE_LOGFILE")):
            self.logdir_path.joinpath(file+".txt").touch()
            self.logfiles[file] = self.logdir_path.joinpath(file+".txt")
        self.write_Log(self.logfiles["Runtime"], self.generate_RuntimeLogtext(["Start", str(self.checkfolder_path)]))
        self.write_Log(self.logfiles["Runtime"], self.generate_RuntimeLogtext(["Create", f"logfiles{list(self.logfiles.keys())} in {self.logdir_path}"]))
            
    def _write_startlog(self) -> None :
        log_str = self.generate_RuntimeLogtext(["Write", "CurrentSetting -> " + str(self.logfiles["Settings"])])
        self.write_Log(self.logfiles["Runtime"] ,log_str)
        
        # CurrentSettingsの書き出し
        log_str = f"[{str(datetime.datetime.now().replace(microsecond=0))}]\n" \
                    f"\t科目　　：{self.target_ClassName}\n" \
                    f"\t採点対象：{self.checkfolder_path}\n" \
                    f"\t自動入力：{self.autoinput_path}\n" \
                    f"\tログ出力：{self.logdir_path}\n"
        self.write_Log(self.logfiles["Settings"] ,log_str)
    
    def _start_Check(self) -> None:
        if self.checkfolder_path == "":
            self.open_msgDialog("ERROR","採点対象のフォルダが選択されていません")
            return
        if self.autoinput_path == "":
            tkinter.Tk().withdraw()
            if not messagebox.askyesno("", "自動入力対象が選択されていません。採点を開始してもよろしいですか"):
                return
        self.isStartCheck = 1
        
        self._setting_Logfiles()
        self._write_startlog()
        self.Close()
        
class Execute(Window):
    def __init__(self, checkfolder: Path, logfiles: Path, inputfolder: Path = None) -> None:
        self.checkfolder_path = checkfolder
        self.inputfolder_path = inputfolder
        self.logfiles = logfiles
        
        super().__init__(checkfolder.name)
        self.Show()
    

def check(classname: str, checkroot: Path, log: Path, input: Path = None):
    childtype = eval(GLOBAL_SETTINGS.get(classname.upper(), "CHILD_TYPE"))
    pathlist = get_checkpath(childtype, checkroot)
    index = 0
    while 0 <= index < len(pathlist):
        runner = Execute(pathlist[index], log, input)
        
    pass

def get_checkpath(childtype: str, rootpath: Path) -> list:
    if childtype == "dir":
        return [f for f in rootpath.iterdir() if f.is_dir()]
    elif childtype == "file":
        return [f for f in rootpath.iterdir() if f.is_file() if not f in [".DS_Store", "reportlist.xlsx"]]

# MARK: Main process
if __name__ == "__main__":
    # 設定読み込み
    GLOBAL_SETTINGS = Settings()
    
    # 科目選択
    checking_class = ClassSelect()
    checking_class.Show()
    if checking_class.select_ClassName == "":
        exit()
    
    # 採点時の設定
    check_setting = CheckSetting(checking_class.select_ClassName)
    
    check(checking_class.select_ClassName, check_setting.checkfolder_path, check_setting.logfiles, check_setting.autoinput_path)
    # check("IP", Path("/Users/nao/Desktop/手伝い/プログラミング基礎/採点/第07回演習/data"))
