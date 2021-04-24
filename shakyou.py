from tika import parser
import re
import os


"""
    PDFから文字を抽出
"""
def parseRawPDF(filePath):
    # 変数初期化
    file_data = parser.from_file(filePath)
    newline_repatter = re.compile('¬…$')
    file_repatter = re.compile('^Page [0-9]+/[0-9]')
    code_repatter = re.compile('([0-9]+|¬[0-9]+)$')

    optimized_list = {}
    tmp_list = []
    index = 0
    pt = 0
    filename_before = 'project'
    filename_after = ''
    for line in file_data['content'].splitlines():
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


def main():
    print('### Shakyou.py - v1.00')
    print('[+] 写経を楽にしたいという煩悩に負けたあなたへ！')
    print('[+] 写経用PDFを下にドラッグしてENTERすると、生成されます\r\n')
    file_path = input('[PDF]: ')
    dirname = os.path.dirname(file_path)

    print('\r\n[*] 写経プログラムを抽出中...')
    project, formatDict = parseShakyouPDF(file_path)
    project_dir = os.path.join(dirname, project)

    if len(formatDict) <= 0:
        print('\r\n[-] エラーが発生しました。残念でした。')
        input()
        return

    if not os.path.exists(project_dir):
        os.mkdir(project_dir)

    print('[*] ファイル生成しました。動作保証はしません。')
    for file_name in formatDict:
        print(' - '+ os.path.join(project_dir, file_name))
        with open(os.path.join(project_dir, file_name), 'w', encoding='utf-8') as f:
            f.write('\n'.join(formatDict[file_name]))
    input('\r\n[+] ENTERキーを押して終了します...')


if __name__ == "__main__":
    main()
