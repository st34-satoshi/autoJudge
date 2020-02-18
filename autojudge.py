# -*- coding: utf-8 -*-
import requests
import os
import sys
import time
import subprocess
from bs4 import BeautifulSoup

LOGIN_URL = 'https://atcoder.jp/login?continue=https%3A%2F%2Fatcoder.jp%2Fcontests%2F'
CONTEST_URL = 'https://atcoder.jp/contests/'
CONF_FILE = 'setting.conf'
TESTCASES_PATH = 'testcase'
TLE_TIME = 2

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
COLORRESET = "\033[0m"


class ExecuteTestCases:

    def __init__(self, testcases, test_name):
        self.test_name = test_name
        self.testinfo = testcases[0]
        self.testCases = testcases[1:]
        self.result = {}
        self.result["build"] = 0
        self.result["result"] = {"AC": 0, "WA": 0, "TLE": 0}

    def Execute(self, srcpath=""):
        """テストを実行"""

        print(YELLOW + "Judging " + self.testinfo["contest"] + "/" + self.testinfo["testname"] + "..." + COLORRESET)
        if (srcpath == ""):
            srcpath = self.__GetPath()
        self.__Build(srcpath)
        if (self.result["build"] == 0):
            self.__Run()
        self.__Result()

    def __GetPath(self):
        """
        未指定時にソースコードの場所を取得
        設定ファイル(CONF_FILE)記載の相対パス/コンテスト名/テスト名.cppを返す
        """
        codepath = os.path.join(self.test_name + ".cpp")
        workpath = "."
        with open(CONF_FILE, "r") as f:
            while True:
                line = f.readline().rstrip('\n')
                if not line:
                    break
                element = line.split(':')
                if (element[0] == "srcpath"):
                    workpath = element[1]
        return os.path.join(workpath, codepath)

    def __Build(self, srcpath):
        """
        ソースコード(c++)をビルドし、結果をresult["build"]に格納
        ビルド成功(0), ビルド失敗(1), ソース無(2)
        """
        print(RED, end="")
        if (os.path.exists(srcpath) == True):
            cmd = 'g++ -std=c++14 -o tmp ' + srcpath
            if (subprocess.run(cmd, shell = True).returncode == 0):
                self.result["build"] = 0
            else:
                self.result["build"] = 1
        else:
            self.result["build"] = 2
        print(COLORRESET, end="")

    def __Run(self):
        try:
            execcmd = ""
            if os.name == "nt":
                execcmd = "tmp.exe"
            else:
                execcmd = "./tmp"
            for i,testcase in enumerate(self.testCases):
                print("testcase " + str(i + 1) + ": ", end="")
                proc = subprocess.Popen(execcmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
                proc.stdin.write(testcase["input"].encode())
                proc.stdin.flush()
                proc.stdout.flush()
                try:
                    proc.wait(TLE_TIME)
                    ans = proc.stdout.read().decode().replace('\r\n','\n')
                    out = testcase["output"].replace('\r\n','\n')
                    if out == ans:
                        self.result["result"]["AC"] += 1
                        print(GREEN + "AC" + COLORRESET)
                    else:
                        self.result["result"]["WA"] += 1
                        print(YELLOW + "WA" + COLORRESET)
                        print(RED + " predicted:"+ ans.rstrip('\r\n') + "\n" + " result:" + out.rstrip('\r\n') + COLORRESET)
                except:
                    self.result["result"]["TLE"] += 1
                    print(YELLOW + "TLE" + COLORRESET)
                    proc.terminate()
                    # process終了後timeoutを設けない場合、tmp.exeが削除できないことがある。
                    time.sleep(1)

        finally:
            if (os.path.exists(execcmd) == True):
                os.remove(execcmd)

    def __Result(self):
        """
        テスト結果を出力する
        全て正解=> AC, 実行時間オーバー=> TLE, 誤りを含む=> WA, コンパイルエラー=> CE
        """

        if self.result["build"] == 2:
            print(RED, end="")
            print("src file is not found")
            print("please write exact path on " + CONF_FILE + " or specify path(-p)")
            print(COLORRESET, end="")
            return

        if self.result["build"] == 1:
            RESULT = YELLOW + "CE" + COLORRESET
        elif self.result["result"]["AC"] == len(self.testCases):
            RESULT = GREEN + "AC" + COLORRESET
        elif self.result["result"]["TLE"] >= 1:
            RESULT = YELLOW + "TLE" + COLORRESET
        else: 
            RESULT = YELLOW + "WA" + COLORRESET
        print("result: " + RESULT)


class ManageTestCases:

    def __init__(self, contest_name):
        os.makedirs(TESTCASES_PATH, exist_ok=True)
        self.config = {}
        self.contest = contest_name
        self.__update_conf()
        
    def __update_conf(self):
        try:        
            with open(CONF_FILE, "r") as f:
                while True:
                    line = f.readline().rstrip('\r\n')
                    if not line:
                        break
                    element = line.split(':')
                    self.config[element[0]] = element[1]
        except:
            print("cannot open config file.")

    def get_test_cases(self, test_name, is_login=False):
        file_name = self.contest + "@" + test_name + ".txt"
        test_info = [{"contest": self.contest, "testname": test_name}]
        if file_name in os.listdir(TESTCASES_PATH):
            test_cases = self.__ReadFile(file_name)
        else:
            test_cases = self.__ScrapePage(test_name, is_login)
            self.__WriteFile(file_name, test_cases)
        return test_info + test_cases

    def __fetch_test_cases(self, test_name, is_login=False):
        file_name = self.contest + "@" + test_name + ".txt"
        test_cases = self.__ScrapePage(test_name, is_login)
        self.__WriteFile(file_name, test_cases)

    def fetch_all_test(self):
        # test of A to F
        for test in ["a", "b", "c", "d", "e", "f"]:
            self.__fetch_test_cases(self.contest + "_" + test)

    def __ReadFile(self, file_name):
        testcases = []
        targ_path = os.path.join(TESTCASES_PATH, file_name)
        with open(targ_path, "r") as f:
            while True:
                st = f.readline().rstrip('\r\n')
                if 'test case' in st:
                    testcase = {}
                    continue
                if 'input' in st:
                    mode = "input"
                    testcase[mode] = ""
                    continue
                if 'output' in st:
                    mode = "output"
                    testcase[mode] = ""
                    continue        
                if '---fin---' in st:
                    testcases.append(testcase)
                    continue
                if not st:
                    break
                testcase[mode] += st + "\n"
        return testcases

    def __WriteFile(self, file_name, test_cases):
        target_path = os.path.join(TESTCASES_PATH, file_name)
        with open(target_path, "w") as f:
            for i, q in enumerate(test_cases):
                f.write("[test case " + str(i) + "]\n")
                f.write("---input---\n")
                f.write(q["input"])
                f.write("---output---\n")
                f.write(q["output"])
                f.write("---fin---\n")
                
    def __ScrapePage(self, test_name, is_login):
        session = requests.session()
        if is_login:
            self.__LoginPage(session)
 
        pageAll = session.get(CONTEST_URL + str(self.contest) + "/tasks/" + str(test_name))
        testcases = self.__AnalyzePage(pageAll)
        return testcases

    def __LoginPage(self, session):
        """認証が必要なページにログインする"""

        res = session.get(LOGIN_URL + str(self.contest))
        page = BeautifulSoup(res.text, 'lxml')            
        csrf_token = page.find(attrs={'name': 'csrf_token'}).get('value')
        login_info = {
            "csrf_token": csrf_token,
            "username": self.config["username"],
            "password": self.config["password"],
        }
        session.post(LOGIN_URL + str(self.contest), data=login_info)

    def __AnalyzePage(self, page_org):
        """取得した問題のページから問題部分を抽出する"""

        page = BeautifulSoup(page_org.text, 'lxml').find_all(class_ = "part")
        quest_list = []
        quest = {}
        for element in page:
            ele_h3 = element.findChild("h3")
            ele_pre = element.findChild("pre")
            if 'Sample' not in str(ele_h3):
                continue
            if 'Input' in str(ele_h3):
                quest = {}
                quest["input"] = str(ele_pre).lstrip("<pre>").rstrip("</pre>").replace('\r\n','\n')
            else:
                quest["output"] = str(ele_pre).lstrip("<pre>").rstrip("</pre>").replace('\r\n', '\n')
                quest_list.append(quest)
        return quest_list
        

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("contest_name", help="set contest name(ex. abc143)", type=str)
    if len(sys.argv) == 2:
        # initialize all problems test
        args = parser.parse_args()
        ac = ManageTestCases(args.contest_name)
        ac.fetch_all_test()
    if len(sys.argv) == 3:
        parser.add_argument("problem_name", help="set problem name(ex. a)", type=str)
        args = parser.parse_args()
        ac = ManageTestCases(args.contest_name)
        testcases = ac.get_test_cases(args.contest_name+"_"+args.problem_name, True)
        ex = ExecuteTestCases(testcases, args.problem_name)
        ex.Execute()
