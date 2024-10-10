# MARK: import
import tkinter
from tkinter import filedialog, messagebox
import datetime
import configparser
import re
from pathlib import Path
import shutil
from functools import wraps
import subprocess
import json
import pyautogui
import time

# MARK: Setting Class
class Settings:
    def __init__(self) -> None:
        
        self._shape = {
                        "General":[
                                {"name":"UI_MARGIN_BOTTOM", "required":True },
                                {"name":"CLASS_NAME", "required":True },
                                {"name":"GENERATE_LOGFILE", "required":True},
                                {"name":"GENERATE_LOGDIR", "required":False},
                                {"name":"DEFAULT_SELECT_ROOT_PATH", "required":True},
                                {"name":"EXCLUDED_FILE_NAME", "required":False}
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
        if self.exists(section, key):
            return eval(self._settings[section][key])
        else:
            return None
        
    def exists(self, section: str, key: str) -> bool:
        if key.lower() in map(lambda x:x[0], self._settings.items(section)):
            return True
        else:
            return False
    
    def get_sectionList(self) -> list:
        return self._settings.sections()
    
    def get_KeyValueList(self, section: str) -> dict:
        return self._settings.items(section.upper())
    
    def _show_Message(self, title: str, text: str) -> None:
        tkinter.Tk().withdraw()
        messagebox.showinfo(title, text)
    
    def _check(self):
        # general settings check
        general_keylist = [i[0] for i in self.get_KeyValueList("GENERAL")]
        for settings in self._shape["General"]:
            if settings["required"] :
                if not settings["name"].lower() in general_keylist:
                    self._show_Message("ERROR","GENERALに必須属性{}が設定されていません".format(settings["name"]))
                    return False
        
        # class settings check
        for className in self.get("GENERAL", "CLASS_NAME"):
            class_keylist = [i[0] for i in self.get_KeyValueList(className)]
            for settings in self._shape["Class"]:
                if settings["required"] :
                    if not settings["name"].lower() in class_keylist:
                        self._show_Message("ERROR","{}に必須属性{}が設定されていません".format(className,settings["name"]))
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
        
    def _write_Log(self, target: str, text: str) -> None:
        with open(target, "a") as f:
            f.write(text + "\n")
            
    def _generate_RuntimeLogText(self, action: list) -> str:
        log = [str(datetime.datetime.now().replace(microsecond=0))+"\t"] + action
        return "\t".join(log)
    
    def _select_File(self, root: Path, any: bool = False) -> Path | None:
        if any:
            path = [Path(p) for p in filedialog.askopenfilenames(initialdir=root)]
            pass
        else:
            path = Path(filedialog.askopenfilename(initialdir=root))
            
        if not len(str(path)):
            path = None
                
        return path
    
    def _select_Dir(self, root: Path) -> Path | None:
        path = Path(filedialog.askdirectory(initialdir=root))
        if not len(str(path)):
            path = None
        return path
    
    def _show_Message(self, title: str, text: str) -> None:
        tkinter.Tk().withdraw()
        messagebox.showinfo(title, text)
    
    def _ask_YesNo(self, title: str, text: str) -> bool:
        tkinter.Tk().withdraw()
        return messagebox.askyesno(title, text)
        
    def Close(self) -> None:
        self.root.destroy()
        self.root.quit()

# MARK: ClassSelect Class
class ClassSelect(Window):
    def __init__(self) -> None:
        super().__init__("科目選択", height=240)
        self.select_ClassName = ""
        
        for target in GLOBAL_SETTINGS.get("GENERAL", "CLASS_NAME"):
            tkinter.Button(self.root, text=target, font=('MSゴシック', '20'), \
                            padx=2, pady=2, relief=tkinter.RAISED, width=18, height=2, background='white', \
                            command=self._set_className(target)) \
                            .pack(padx=5, pady=5)
    
    def _set_className(self, target):
        def inner():
            self.select_ClassName = target
            self.Close()
        return inner

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
            if  GLOBAL_SETTINGS.exists(self.target_ClassName, "SELECT_ROOT_PATH"):
                folderpath = self._select_Dir(GLOBAL_SETTINGS.get(self.target_ClassName, "SELECT_ROOT_PATH"))
            elif GLOBAL_SETTINGS.exists("GENERAL", "DEFAULT_SELECT_ROOT_PATH"):
                folderpath = self._select_Dir(GLOBAL_SETTINGS.get("GENERAL", "DEFAULT_SELECT_ROOT_PATH"))
            else :
                self._show_Message("ERROR","デフォルトパスが設定されていないためホームディレクトリを開きます")
                folderpath = self._select_Dir(GLOBAL_SETTINGS.HOME_PATH)
            
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

    def _setup_LogFiles(self,) -> None:
        self.logdir_path = GLOBAL_SETTINGS.SOURCE_PATH.joinpath("log", self.checkfolder_label.get())
        if self.logdir_path.exists():
            for file in self.logdir_path.iterdir():
                self.logfiles[file.stem] = file
            self._write_Log(self.logfiles["Runtime"], self._generate_RuntimeLogText(["Start", str(self.checkfolder_path)]))
            return
        
        self.logdir_path.mkdir()
        for file in GLOBAL_SETTINGS.get("GENERAL", "GENERATE_LOGFILE"):
            self.logdir_path.joinpath(file+".txt").touch()
            self.logfiles[file] = self.logdir_path.joinpath(file+".txt")
        if GLOBAL_SETTINGS.exists("GENERAL", "GENERATE_LOGDIR"):
            for dir in GLOBAL_SETTINGS.get("GENERAL", "GENERATE_LOGDIR"):
                self.logdir_path.joinpath(dir).mkdir()
                self.logfiles["dir_"+dir] = self.logdir_path.joinpath(dir)
                
        self._write_Log(self.logfiles["Runtime"], self._generate_RuntimeLogText(["Start", str(self.checkfolder_path)]))
        self._write_Log(self.logfiles["Runtime"], self._generate_RuntimeLogText(["Create", f"logfiles{list(self.logfiles.keys())} in {self.logdir_path}"]))
            
    def _write_StartLog(self) -> None :
        log_str = self._generate_RuntimeLogText(["Write", "CurrentSetting -> " + str(self.logfiles["Settings"])])
        self._write_Log(self.logfiles["Runtime"] ,log_str)
        
        # CurrentSettingsの書き出し
        log_str = f"[{str(datetime.datetime.now().replace(microsecond=0))}]\n" \
                    f"\t科目　　：{self.target_ClassName}\n" \
                    f"\t採点対象：{self.checkfolder_path}\n" \
                    f"\t自動入力：{self.autoinput_path}\n" \
                    f"\tログ出力：{self.logdir_path}\n"
        self._write_Log(self.logfiles["Settings"] ,log_str)
    
    def _start_Check(self) -> None:
        if self.checkfolder_path == "":
            self._show_Message("ERROR","採点対象のフォルダが選択されていません")
            return
        if self.autoinput_path == "":
            if not self._ask_YesNo("", "自動入力対象が選択されていません。採点を開始してもよろしいですか"):
                return
        self.isStartCheck = 1
        
        self._setup_LogFiles()
        self._write_StartLog()
        self.Close()

# MARK: Execute Class
class Execute(Window):
    def __init__(self, checkroot: Path, filetype: list, namingRule: str, runcommand: str, logfiles: Path, inputroot: Path = "") -> None:
        self.next_index = 0
        self.current_run_file = ""
        self.run_window_name = checkroot.name
        
        self.naming_rule = re.compile(namingRule)
        self.valid_filetype = filetype
        self.logfiles = logfiles
        self.run_command = runcommand
        
        self.exclude_files = GLOBAL_SETTINGS.get("GENERAL", "EXCLUDED_FILE_NAME")
        
        self.check_files_path = self._get_CheckFilePath(checkroot)
        if inputroot == "":
            self.input_files_path = []
        else:
            self.input_files_path = self._get_InputFilePath(inputroot)
        
        super().__init__(checkroot.name, *self._calc_WindowSize(len(self.check_files_path)+len(self.input_files_path)))
        
        RunningFrame = tkinter.Frame(self.root, relief=tkinter.FLAT, background='white')
        RunningFrame.pack(fill=tkinter.BOTH, pady=10, padx=10)
        tkinter.Label(RunningFrame, text='実行', font=('MSゴシック', '15', 'bold'), anchor=tkinter.NW, background='white').pack()
        for file in self.check_files_path:
            tkinter.Button(RunningFrame, text=file.name, font=('MSゴシック', '20'), \
                            padx=2, pady=2, relief=tkinter.RAISED, width=18, height=2, background='white', \
                            command=self._Run_Button(file)) \
                            .pack(padx=5, pady=5)
                            
        # TODO: 採点中に採点対象のフォルダを変更できるようにしたらいいかも
        InputFrame = tkinter.Frame(self.root, relief=tkinter.FLAT, background='white')
        InputFrame.pack(fill=tkinter.BOTH, pady=10, padx=10)
        if len(self.input_files_path) == 0:
            tkinter.Label(InputFrame, text='自動入力：なし', font=('MSゴシック', '15', 'bold'), anchor=tkinter.NW, background='white').pack()
        else:
            tkinter.Label(InputFrame, text='自動入力', font=('MSゴシック', '15', 'bold'), anchor=tkinter.NW, background='white').pack()
            for file in self.input_files_path:
                tkinter.Button(InputFrame, text=file.name, font=('MSゴシック', '20'), \
                            padx=2, pady=2, relief=tkinter.RAISED, width=18, height=2, background='white', \
                            command=self._AutoInput_Button(file)) \
                            .pack(padx=5, pady=5)
                            
        progress_frame = tkinter.Frame(self.root, relief=tkinter.FLAT, background='white')
        progress_frame.pack(fill=tkinter.BOTH, pady=10, padx=10)
        before_button = tkinter.Button(progress_frame, text="＜", font=('MSゴシック', '20'), padx=2, pady=2, width=8, background='white', command=self._goto_Before)
        before_button.pack(side=tkinter.LEFT)
        next_button = tkinter.Button(progress_frame, text="＞", font=('MSゴシック', '20'), padx=2, pady=2, width=8, background='white', command=self._goto_next)
        next_button.pack(side=tkinter.LEFT)
        
        self.Show()
        
    def _calc_WindowSize(self, button_cnt):
        width = 300
        height = (40 * 2) + (72 * button_cnt) + 80
        return [width, height]
    
    def _get_CheckFilePath(self, root: Path) -> list:
        for file in [f for f in root.iterdir() if f.is_file() and (not f in self.exclude_files)]:
            # ファイル形式チェック
            if self._isValid_FileType(file):
                self._TypeOK_(file)
            else:
                self._TypeNG_(file)
        
        for file in [f for f in root.iterdir() if f.is_file() and (not f in self.exclude_files)]:
            # ファイル命名規則チェック
            if self._isValid_FileName(file):
                self._NameOK_(file)
            else:
                self._NameNG_(file)
                
        return [f for f in root.iterdir() if f.is_file() and (not f in self.exclude_files)]
    
    def _get_InputFilePath(self, root: Path, filetype: list = [".json"]) -> list:
        exclude_files = GLOBAL_SETTINGS.get("GENERAL", "EXCLUDED_FILE_NAME")
        return [f for f in root.iterdir() if f.is_file() and (not f in self.exclude_files) and (f.suffix in filetype)]
            
    def _NameOK_(self, file: Path):
        pass
    
    def _NameNG_(self, file: Path):
        self._write_Log(self.logfiles["Badname"], f"{file.parent.name}\t{file.name}")
    
    def _TypeOK_(self, file: Path):
        pass
    
    def _TypeNG_(self, file: Path):
        self._write_Log(self.logfiles["Badtype"], f"{file.parent.name}\t{file.name}")
                
    def _isValid_FileType(self, file: Path) -> bool:
        if file.suffix in self.valid_filetype:
            return True
        else:
            return False
    
    def _isValid_FileName(self, file: Path) -> bool:
        if re.fullmatch(self.naming_rule, str(file.stem)):
            return True
        else:
            return False
    
    def _Run_Button(self, file: Path):
        def inner():
            self.Run(file)
            log_text = self._generate_RuntimeLogText(["Run", f"{file.parent.name}/{file.name}"])
            self._write_Log(self.logfiles["Runtime"], log_text)
            self.current_run_file = file.name
        return inner
    
    def Run(self, file: Path):
        pass
    
    def _AutoInput_Button(self, file: Path):
        def inner():
            json = self._get_InputJsonData(file)
            for content in json:
                if content["type"].lower() == "key":
                    self._autoInput_key(file)
                elif content["type"].lower() == "text":
                    self._autoInput_text(content["input"], content["target"])
                else:
                    self._show_Message("ERROR", "typeにはkeyもしくはtextを設定してください")
            log_text = self._generate_RuntimeLogText(["Input", f"{file.parent.name}/{file.name}", "->", self.current_run_file])
            self._write_Log(self.logfiles["Runtime"], log_text)
        return inner
    
    def _autoInput_key(self, file: Path):
        self.set_AutoInputScript_Key()
        subprocess.Popen(["python", str(self.autoinput_key_scriptfile), str(file)])
    
    def set_AutoInputScript_Key(self):
        pass
    
    def _autoInput_text(self, contents: list, target: str):
        inputdata = json.dumps(contents, ensure_ascii=False)
        if target == "":
            target = self.current_run_file
        print(type(target))
        print(type(inputdata))
        applescript_code = f"""tell application "Terminal"
                                    set all_windows to every window
                                    set target to "{target}"
                                    set messages to {inputdata}
                                    repeat with cur_window in all_windows
                                        if name of cur_window contains target then
                                            tell cur_window
                                                repeat with message in messages
                                                    do script message in selected tab
                                                    delay 0.2
                                                end repeat
                                            end tell
                                        end if
                                    end repeat
                                end tell
                            """
        subprocess.Popen(["osascript", "-e", applescript_code])
    
    def _get_InputJsonData(self, file: Path) -> json:
        with open(file, 'r') as f:
            data = json.load(f)
        return data
 
    def _close_Window(self,):
        self.set_CloseScript()
        subprocess.Popen(["osascript", "-e", self.close_script])
    
    def set_CloseScript(self):
        pass
    
    def _goto_next(self):
        self.next_index = 1
        self._close_Window()
        self.Close()
    
    def _goto_Before(self):
        self.next_index = -1
        self._close_Window()
        self.Close()
        
    
# MARK: IP Execute Class
class IP_Execute(Execute):
    def __init__(self, checkfolder: Path, logfiles: list, inputfolder: Path = "") -> None:
        self.close_script = ""
        self.autoinput_key_scriptfile = ""
        
        super().__init__(checkroot = checkfolder, \
                        filetype = GLOBAL_SETTINGS.get("IP", "FILE_TYPE"), \
                        namingRule = GLOBAL_SETTINGS.get("IP", "FILENAME_REGEX"), \
                        runcommand = GLOBAL_SETTINGS.get("IP", "RUN_COMMAND"), \
                        logfiles = logfiles, \
                        inputroot = inputfolder 
                        )
        
        self.set_CloseScript()
        self.set_AutoInputScript_Key()
    
    def _NameNG_(self, file: Path):
        return super()._NameNG_(file)
    
    def _NameOK_(self, file: Path):
        return super()._NameOK_(file)
    
    def _TypeOK_(self, file: Path):
        # TODO:zipを許容して入ってきたやつがzipだった時の処理（13週目の時計を想定）
        if file.suffix == ".zip":
            shutil.unpack_archive(file, file.parent.joinpath("unzip"))
            unzippath = file.parent.joinpath("unzip")
            
            # ディレクトリが出てきたらunzipに移動
            if unzippath.joinpath(file.stem).is_dir():
                shutil.copytree(unzippath.joinpath(file.stem), unzippath, dirs_exist_ok=True)
                shutil.rmtree(unzippath.joinpath(file.stem))
            # そのまま移動できる採点対象の形式のやつはそのまま移動（.py）
            for innerfile in [f for f in unzippath.iterdir() if f.is_file() and (not f in self.exclude_files)]:
                if innerfile.suffix in self.valid_filetype:
                    shutil.move(innerfile, innerfile.parent.parent.joinpath(innerfile.name))
            # dataフォルダがあった場合はそのまま採点対象フォルダに移動
            if self._is_dataDirectory_exists(unzippath):
                if self._is_dataDirectory_exists(unzippath.parent):
                    shutil.copytree(unzippath.joinpath("data"), unzippath.parent.joinpath("data"), dirs_exist_ok=True)
                else:
                    shutil.move(unzippath.joinpath("data"), unzippath.parent.joinpath("data"))
            shutil.rmtree(unzippath)
            
        return super()._TypeOK_(file)
    
    def _TypeNG_(self, file: Path):
        # valid filetype: .py
        movepath = self.logfiles["dir_Badtype"].joinpath(file.parent.name)
        if not movepath.exists():
                movepath.mkdir()
        if file.suffix == ".zip":
            # 展開して中身を確認
            shutil.unpack_archive(file, file.parent.joinpath("unzip"))
            
            # zipをbadtypeへ移動
            shutil.move(file, movepath)
            
            # 展開先pathを格納
            unzippath = file.parent.joinpath("unzip")
            # ディレクトリが出てきたらunzipに移動
            if unzippath.joinpath(file.stem).is_dir():
                shutil.copytree(unzippath.joinpath(file.stem), unzippath, dirs_exist_ok=True)
                shutil.rmtree(unzippath.joinpath(file.stem))
            # そのまま移動できる採点対象の形式のやつはそのまま移動（.py）
            for innerfile in [f for f in unzippath.iterdir() if f.is_file() and (not f in self.exclude_files)]:
                if innerfile.suffix in self.valid_filetype:
                    shutil.move(innerfile, innerfile.parent.parent.joinpath(innerfile.name))
            # dataフォルダがあった場合はそのまま採点対象フォルダに移動
            if self._is_dataDirectory_exists(unzippath):
                if self._is_dataDirectory_exists(unzippath.parent):
                    shutil.copytree(unzippath.joinpath("data"), unzippath.parent.joinpath("data"), dirs_exist_ok=True)
                else:
                    shutil.move(unzippath.joinpath("data"), unzippath.parent.joinpath("data"))
            shutil.rmtree(unzippath)
            
        # .txtと拡張子なしは想定してるので.pyに変えてコピーを作成
        elif file.suffix in [".txt",""]:
            shutil.copy(file, file.with_suffix(".py"))
            
            # コピー元のファイルを削除
            if file.suffix == "":
                # 拡張子なしの場合はディレクトリとして認識されるので一旦.txtをつけてから移動して消す
                file.rename(movepath.joinpath(file.with_suffix(".txt").name))
                movepath.joinpath(file.with_suffix(".txt").name).rename(movepath.joinpath(file.name))
            else:
                # 拡張子があるやつは移動
                shutil.move(file, movepath)
        else:
            # どういう状態のファイルかわかんないので移動は人間に任せる
            self._show_Message("Wait!", "想定していない形式があります。\n対応が終了するまでダイアログを消さないでください！\n\"{}\"".format(file.parent.name))
            shutil.move(file, movepath)
            
        return super()._TypeNG_(file)
    
    def _is_dataDirectory_exists(self, unzippath: Path) -> bool:
        path = [f for f in unzippath.iterdir() if f.is_dir() and (f.name == "data")]
        if len(path):
            return True
        else:
            return False
    
    def Run(self, file: Path):
        applescript_code = f"""
                        tell application "Terminal"
                        activate
                        set newWindow to do script "{self.run_command} {str(file)}"
                        set custom title of newWindow to "{self.run_window_name}/{file.name}"
                        set bounds of front window to {0, 550, 500, 900}
                        end tell
                    """
        subprocess.Popen(["osascript", "-e", applescript_code])
        return super().Run(file)    
    
    def set_AutoInputScript_Key(self):
        self.autoinput_key_scriptfile = Path("./autoinput_code/autoinput_key.py").absolute()
        return super().set_AutoInputScript_Key()
    
    def set_CloseScript(self):
        self.close_script = f"""
                tell application "Terminal"
                set all_windows to every window
                repeat with cur_window in all_windows
                    if name of cur_window contains "{self.run_window_name}" then
                        tell cur_window
                            activate
                            tell application "System Events"
                                keystroke "c" using control down
                            end tell
                            delay 1
                            close cur_window
                        end tell
                    end if
                end repeat
            end tell
            """
        return super().set_CloseScript()

# MARK: function
def check(classname: str, checkroot: Path, log: Path, input: Path = None):
    childtype = GLOBAL_SETTINGS.get(classname.upper(), "CHILD_TYPE")
    pathlist = get_checkpath(childtype, checkroot, GLOBAL_SETTINGS.get("GENERAL", "EXCLUDE_FILE_NAME"))
    index = 0
    
    match classname.upper():
        case "IP":
            while 0 <= index < len(pathlist):
                runner = IP_Execute(pathlist[index], log, input)
                if runner.next_index == 0:
                    return
                index += runner.next_index
            return
        
        case "AP":
            return
        
        case "MAS":
            return

def get_checkpath(childtype: str, rootpath: Path, exclude_files: list) -> list:
    if childtype == "dir":
        return [f for f in rootpath.iterdir() if f.is_dir()]
    elif childtype == "file":
        return [f for f in rootpath.iterdir() if f.is_file() if not f in exclude_files]

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
