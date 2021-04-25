from tika import parser
import re
import os, sys
import threading
import time
import pprint


"""
    PDFから文字を抽出
"""
def parseRawPDF(filePath):
    if not os.path.isfile(filePath):
        raise Exception('これは存在しないファイルです！')

    # 変数初期化
    file_data = parser.from_file(filePath)
    newline_repatter = re.compile('¬…$')
    file_repatter = re.compile('^Page [0-9]+/[0-9]')
    code_repatter = re.compile('([0-9]+|¬[0-9]+)$')

    if file_data['content'] is None:
        raise Exception('写経元PDFファイルを選択してください！')
    raw_content_list = file_data['content'].splitlines()

    optimized_list = {}
    tmp_list = []
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
    if 'project' in fileDict:
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


def parseShakyouPDF(filePath):
    return formatCode(parseRawPDF(filePath))


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
    print(' +' + ('-'*55) + '+')
    print(' |' + (' '*55) + '|')
    print(' |' + 'Shakyou.py - v2.10'.center(55, ' ') + '|')
    print(' |' + (' '*55) + '|')
    print(' +' + ('-'*55) + '+')
    print('  → 写経を楽にしたいという煩悩に負けたあなたへ！')
    print('  → 写経用PDFを下にドラッグしてENTERすると、生成されます。\r\n')
    file_path = input(' [PDF]: ')

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
        if not os.path.exists(project_dir):
            os.mkdir(project_dir)

        # ローディング画面描画の停止
        load.flag = True
        load.join()

        # ファイル書き出し
        print('\r [*] 抽出に成功しました。以下のファイルに書き出し中...')
        for file_name in formatDict:
            print('  - '+ os.path.join(project_dir, file_name))
            with open(os.path.join(project_dir, file_name), 'w', encoding='utf-8') as f:
                f.write('\n'.join(formatDict[file_name]))
        print('\r\n [*] ファイル生成しました。動作保証はしません。')

    except Exception as e:
        load.flag = True
        load.join()
        print('\r [-] エラーが発生しました: '+ str(e))
    input()


if __name__ == "__main__":
    main()
