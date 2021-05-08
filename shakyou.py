from tika import parser
import re
import os, sys
import threading
import time
import zipfile


"""
    PDFから文字を抽出
"""
def parseRawPDF(filePath):
    if not os.path.isfile(filePath):
        raise Exception('これは存在しないファイルです！')

    # 変数初期化
    file_data = parser.from_file(filePath)
    newline_repatter = re.compile('¬…$|…')
    file_repatter = re.compile('^Page [0-9]+/[0-9]')
    code_repatter = re.compile('([0-9]+|¬[0-9]+)$')

    if file_data['content'] is None:
        raise Exception('写経元PDFファイルを選択してください！')
    raw_content_list = file_data['content'].splitlines()

    optimized_list = {}
    tmp_list = []
    php_dir_list = []
    php_flag = False
    index = 0
    pt = 0
    filename_before = 'project'
    filename_after = ''
    for line in raw_content_list:
        result = code_repatter.search(line)

        # コード判定
        if bool(result):
            pt = int(result.group(1).replace('¬', ''))
            index += 1
            if index != pt:
                index = 1
                optimized_list[filename_after] = tmp_list
                tmp_list = []

            tmp_list.append(code_repatter.sub('', line))

        # コードが改行されているか判定
        elif bool(newline_repatter.search(line)):
            tmp_list[index-1] = tmp_list[index-1] + newline_repatter.sub('', line)

        # ファイル名取得
        elif bool(file_repatter.search(line)):
            filename_after = filename_before
            filename_before = file_repatter.sub('', line)

    if len(tmp_list) == 0 and filename_before == 'project':
        return {}

    optimized_list[filename_before] = tmp_list
    return optimized_list


"""
    抽出したコードをフォーマット
"""
def formatCode(fileDict, indent=4):
    space = ' '*indent
    indent_lv = 0
    indent_dict = {}

    # プロジェクト名抽出
    if 'project' in fileDict and len(fileDict['project']) > 0:
        project = fileDict['project'][0]
        del fileDict['project']
    else:
        project = 'Unknown'

    if '' in fileDict:
        del fileDict['']
    if fileDict is None or len(fileDict) <= 0:
        raise Exception('これ本当に写経元PDFですか？')

    # コードにインデントを追加
    for f in fileDict:
        tmp_list = []
        for line in fileDict[f]:
            if bool(re.search('{$', line)):
                tmp_list.append((space * indent_lv) + line)
                indent_lv += 1
                continue
            elif bool(re.search('}$', line)):
                indent_lv -=1
                tmp_list.append((space * indent_lv) + line)
                continue
            tmp_list.append((space * indent_lv) + line)
        indent_dict[f] = tmp_list
    
    return (project, indent_dict)


"""
    [Java] パッケージごとにフォルダで分ける
"""
def makePackageDir(project, fileDict):
    package_repatter = re.compile('^package +')

    for file_name in list(fileDict):
        if len(fileDict[file_name]) <= 0:
            continue
        
        # パッケージ名取得
        result = package_repatter.search(fileDict[file_name][0])
        dirpath = file_name
        if bool(result):
            dirpath = package_repatter.sub('', fileDict[file_name][0]).replace(';', '').replace('.', '\\') + '\\' + dirpath
        fileDict[dirpath] = fileDict.pop(file_name)

    return (project, fileDict)


"""
    [PHP] 階層ごとにフォルダで分ける
"""
def makePHPSrcDir(project, fileDict):
    dir_repatter = re.compile('^Src[0-9]+: +')

    for file_name in list(fileDict):
        if file_name.lower().endswith('.txt') and file_name in fileDict:
            for line in fileDict[file_name]:
                result = dir_repatter.search(line)
                if not bool(result):
                    continue

                dirpath = dir_repatter.sub('', line).lstrip('/')
                rep_name = os.path.basename(dirpath)
                if rep_name in fileDict:
                    fileDict[dirpath] = fileDict.pop(rep_name)

    return (project, fileDict)


def parseShakyouPDF(filePath):
    project, formatDict = formatCode(parseRawPDF(filePath))

    php_flag = False
    for f in formatDict:
        if str(f).lower().endswith('.php'):
            php_flag = True
            break

    if php_flag:
        return makePHPSrcDir(project, formatDict)
    else:
        return makePackageDir(project, formatDict)


def getZipArchive(project, formatDict, zipPath):
    with zipfile.ZipFile(zipPath, 'w', compression=zipfile.ZIP_DEFLATED) as new_zip:
        for file_name in formatDict:
            new_zip.writestr(os.path.join(project, file_name), '\n'.join(formatDict[file_name]))


class LoadingThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.flag = False
        self.text = ''
    
    def spinner_gen(self):
        while True:
            yield '|'
            yield '/'
            yield '-'
            yield '\\'

    def run(self):
        for spinner in self.spinner_gen():
            time.sleep(0.1)
            sys.stdout.write('\r [' + spinner + '] '+ self.text)
            sys.stdout.flush()
            if self.flag: break


def main():
    # PDFファイル入力
    print("""
:'######::'##::::'##::::'###::::'##:::'##:'##:::'##::'#######::'##::::'##:
'##... ##: ##:::: ##:::'## ##::: ##::'##::. ##:'##::'##.... ##: ##:::: ##:
 ##:::..:: ##:::: ##::'##:. ##:: ##:'##::::. ####::: ##:::: ##: ##:::: ##:
. ######:: #########:'##:::. ##: #####::::::. ##:::: ##:::: ##: ##:::: ##:
:..... ##: ##.... ##: #########: ##. ##:::::: ##:::: ##:::: ##: ##:::: ##:
'##::: ##: ##:::: ##: ##.... ##: ##:. ##::::: ##:::: ##:::: ##: ##:::: ##:
. ######:: ##:::: ##: ##:::: ##: ##::. ##:::: ##::::. #######::. #######::
:......:::..:::::..::..:::::..::..::::..:::::..::::::.......::::.......:::
""")
    print('  → Shakyou.py v3.20  |  hirosuke-pi')
    print('  → 写経を楽にしたいという煩悩に負けたあなたへ！')
    print('  → 写経用PDFを下にドラッグしてENTERすると、生成されます。\r\n')
    file_path = input(' [PDF]: ').replace('"', '')

    dirname = os.path.dirname(file_path)
    print()

    # ローディング画面描画
    load = LoadingThread()
    load.text = '写経プログラムを抽出中...'
    load.start()

    try:
        # PDF解析開始
        project, formatDict = parseShakyouPDF(file_path)
        project_dir = os.path.join(dirname, project)

        # フォルダ作成
        for file_name in formatDict:
            dirpath = os.path.join(project_dir, os.path.dirname(file_name))
            os.makedirs(dirpath, exist_ok=True)

        # ローディング画面描画の停止
        load.flag = True
        load.join()

        # ファイル書き出し
        print('\r [+] 抽出に成功しました。以下のファイルに書き出し中...')
        print(' [*] '+ project_dir)
        for file_name in formatDict:
            print('  - '+file_name)
            with open(os.path.join(project_dir, file_name), 'w', encoding='utf-8') as f:
                f.write('\n'.join(formatDict[file_name]))
        print('\r\n [+] ファイル生成しました。動作保証はしません。')

    except Exception as e:
        load.flag = True
        load.join()
        print('\r [-] エラーが発生しました: '+ str(e))


if __name__ == "__main__":
    while True:
        main()
        print('\r\n')
